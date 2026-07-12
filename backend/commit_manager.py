"""
Commit Manager
==============
Orchestrates the auto-commit workflow for GitDoc.

Flow:
1. Ensure the Git repository is initialized
2. Extract text content from the .docx file
3. Cache the extracted text as JSON
4. Stage and commit the .docx binary to Git
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List

from config import Settings
from models import CommitInfo, CommitResponse
from git_operations import GitRepo
from docx_parser import DocxParser, DocumentContent


class CommitManager:
    """
    Orchestrates automatic and manual commits for a .docx document.

    Responsibilities:
    - Initializing the Git repository (if needed)
    - Extracting and caching document text
    - Creating commits with standardized messages
    - Providing version history
    """

    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path).resolve()
        self.repo = GitRepo(str(self.docx_path))

    # ---- Repository management ----

    def ensure_repo(self, author: str = "GitDoc User") -> bool:
        """
        Ensure the Git repository exists. Initializes it if not already present.
        Returns True on success.
        """
        if not self.repo.is_initialized():
            return self.repo.init()
        return True

    # ---- Commit operations ----

    def auto_commit(self, author: str = "GitDoc User",
                    message: Optional[str] = None) -> CommitResponse:
        """
        Create a commit for the current state of the .docx file.

        1. Ensures the repo exists
        2. Verifies the document file is accessible
        3. Generates a commit message if none provided
        4. Extracts and caches document text
        5. Commits the .docx binary to Git

        Args:
            author: Display name for the commit author.
            message: Custom commit message. Auto-generated if None.

        Returns:
            CommitResponse with success status and commit hash.
        """
        if not self.repo.is_initialized():
            self.repo.init()

        if not self.docx_path.exists():
            return CommitResponse(
                success=False,
                message="文档文件未找到 (Document file not found)"
            )

        # Generate commit message
        if message is None:
            version = self.repo.get_commit_count() + 1
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[auto] 保存 v{version} - {ts}"

        # Check if there are actual changes before committing
        if self.repo.get_commit_count() > 0 and not self.repo.has_uncommitted_changes():
            return CommitResponse(
                success=False,
                message="文档内容未变更，无需提交 (No changes to commit)"
            )

        # Commit the .docx binary
        commit_hash = self.repo.commit(message=message, author=author)
        if commit_hash is None:
            return CommitResponse(
                success=False,
                message="提交失败：文档内容未变更 (Commit failed: no changes)"
            )

        # Extract text and cache it for fast diff/preview later
        cache_dir = Settings.get_cache_dir(str(self.docx_path))
        DocxParser.extract_and_cache(
            str(self.docx_path), commit_hash, cache_dir
        )

        return CommitResponse(
            success=True,
            hash=commit_hash,
            message=f"已提交为版本 {commit_hash[:8]} (Committed as {commit_hash[:8]})"
        )

    # ---- History ----

    def get_history(self, max_count: int = 100) -> List[CommitInfo]:
        """
        Retrieve the version history for this document.
        Returns an empty list if the repository is not yet initialized.
        """
        if not self.repo.is_initialized():
            return []
        commits = self.repo.get_history(max_count=max_count)
        # Add version tags (v1, v2, ...) in reverse order
        total = len(commits)
        for i, c in enumerate(commits):
            c.version_tag = f"v{total - i}"
        return commits

    def get_commit_count(self) -> int:
        """Return the total number of commits."""
        if not self.repo.is_initialized():
            return 0
        return self.repo.get_commit_count()
