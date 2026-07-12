"""
Git Operations
==============
Encapsulates all Git CLI interactions for GitDoc.
Uses subprocess to call git with --git-dir and --work-tree flags.

The Git repository lives in .gitdoc/.git alongside the tracked .docx file.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from config import Settings
from models import CommitInfo


class GitRepo:
    """
    Manages a Git repository for a specific .docx document.

    The repository is stored in .gitdoc/.git with the work-tree set to
    the document's parent directory. This keeps all Git metadata hidden
    in a single .gitdoc folder without cluttering the user's directory.
    """

    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path).resolve()
        self.doc_dir = self.docx_path.parent
        self.gitdoc_dir = Settings.get_gitdoc_dir(str(self.docx_path))
        self.git_dir = self.gitdoc_dir / ".git"
        self.docx_filename = self.docx_path.name

    # ---- Internal: run git commands ----

    def _run_git(self, *args: str, capture_output: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command with --git-dir and --work-tree pre-set.
        Returns the CompletedProcess for the caller to inspect.
        """
        cmd = [
            "git",
            "--git-dir", str(self.git_dir),
            "--work-tree", str(self.doc_dir),
            *args
        ]
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

    def _run_git_bytes(self, *args: str) -> Optional[bytes]:
        """
        Run a git command and return raw stdout bytes.
        Used for retrieving binary .docx content from git.
        """
        cmd = [
            "git",
            "--git-dir", str(self.git_dir),
            "--work-tree", str(self.doc_dir),
            *args
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if proc.returncode != 0:
            return None
        return proc.stdout

    # ---- Repository lifecycle ----

    def init(self) -> bool:
        """
        Initialize the Git repository inside .gitdoc/.git.
        Safe to call multiple times (idempotent).
        """
        self.gitdoc_dir.mkdir(parents=True, exist_ok=True)
        result = self._run_git("init")
        if result.returncode != 0:
            return False

        # Configure default user identity for this repo
        self._run_git("config", "user.name", Settings.GIT_AUTHOR_NAME)
        self._run_git("config", "user.email", Settings.GIT_AUTHOR_EMAIL)

        # Create a .gitignore to prevent tracking metadata inside .gitdoc
        ignore_path = Settings.get_gitignore_path(str(self.docx_path))
        if not ignore_path.exists():
            ignore_path.write_text(
                ".gitdoc/\n"
                + f"{Settings.BACKUPS_DIR_NAME}/\n"
                + f"{Settings.CACHE_DIR_NAME}/\n"
                + "*.gitignore\n"
            )

        return True

    def is_initialized(self) -> bool:
        """Check whether a Git repository already exists."""
        return (self.git_dir / "HEAD").exists()

    # ---- Staging and committing ----

    def add(self, file_path: str) -> bool:
        """Stage a file for commit."""
        result = self._run_git("add", file_path)
        return result.returncode == 0

    def commit(self, message: str, author: str = "GitDoc User") -> Optional[str]:
        """
        Stage and commit the tracked .docx file.
        Returns the commit hash on success, or None if nothing changed / error.
        """
        # Stage the .docx
        self.add(self.docx_filename)

        # Set author via environment variables
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = author
        env["GIT_COMMITTER_NAME"] = author

        result = subprocess.run(
            [
                "git",
                "--git-dir", str(self.git_dir),
                "--work-tree", str(self.doc_dir),
                "commit", "-m", message
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

        if result.returncode != 0:
            return None

        # Retrieve the new commit hash
        hash_result = self._run_git("rev-parse", "HEAD")
        if hash_result.returncode != 0:
            return None
        return hash_result.stdout.strip()

    # ---- History and inspection ----

    def get_history(self, max_count: int = 100) -> List[CommitInfo]:
        """
        Retrieve the commit history, newest first.
        Returns an empty list if no commits exist.
        """
        result = self._run_git(
            "log", f"--max-count={max_count}",
            "--format=%H|%h|%an|%at|%s"
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) < 5:
                continue
            full_hash, short_hash, author, timestamp_str, message = parts
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str))
            except (ValueError, OSError):
                timestamp = datetime.now()
            commits.append(CommitInfo(
                hash=full_hash,
                short_hash=short_hash,
                author=author,
                timestamp=timestamp,
                message=message
            ))
        return commits

    def get_file_content_at_commit(self, commit_hash: str, file_path: str) -> Optional[bytes]:
        """
        Retrieve a file's binary content as it existed at a specific commit.
        Used for diff preview and rollback operations.
        """
        return self._run_git_bytes("show", f"{commit_hash}:{file_path}")

    def restore_file(self, commit_hash: str, file_path: str) -> bool:
        """
        Restore a file from a specific commit to the working tree.
        This overwrites the current file on disk.
        """
        result = self._run_git("checkout", commit_hash, "--", file_path)
        return result.returncode == 0

    def get_commit_count(self) -> int:
        """Return the total number of commits in the repository."""
        result = self._run_git("rev-list", "--count", "HEAD")
        if result.returncode != 0:
            return 0
        try:
            return int(result.stdout.strip())
        except ValueError:
            return 0

    def has_uncommitted_changes(self) -> bool:
        """
        Check if the tracked .docx has uncommitted changes.
        Returns True if there are changes to commit.
        """
        # Check if the file differs from HEAD
        result = self._run_git("diff", "--quiet", "HEAD", "--", self.docx_filename)
        # diff --quiet returns 0 if no differences, 1 if differences exist
        return result.returncode != 0
