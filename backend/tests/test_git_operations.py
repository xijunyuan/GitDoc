"""
Tests for Git Operations Module
================================
Tests the GitRepo class that encapsulates Git CLI interactions.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_operations import GitRepo
from config import Settings


class TestGitRepo(unittest.TestCase):
    """Test suite for GitRepo class."""

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory with a test .docx file."""
        cls.tmp_dir = tempfile.mkdtemp(prefix="gitdoc_test_")
        cls.docx_path = os.path.join(cls.tmp_dir, "test.docx")

        # Create a minimal .docx-like file (just content for git to track)
        with open(cls.docx_path, "w", encoding="utf-8") as f:
            f.write("Test document content v1")

        cls.repo = GitRepo(cls.docx_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        if os.path.exists(cls.tmp_dir):
            shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def test_01_init_creates_git_repo(self):
        """init() should create a valid Git repository."""
        result = self.repo.init()
        self.assertTrue(result)
        self.assertTrue(self.repo.is_initialized())

        # Check that HEAD exists
        head_path = self.repo.git_dir / "HEAD"
        self.assertTrue(head_path.exists())

        # Commit the initial content so subsequent tests can retrieve it
        commit_hash = self.repo.commit("Initial commit with v1 content")
        self.assertIsNotNone(commit_hash)
        TestGitRepo._v1_hash = commit_hash

    def test_02_is_initialized_before_init(self):
        """is_initialized() should return False for a new, uninitialized location."""
        # Use a completely separate temp directory with no .gitdoc
        import tempfile
        other_dir = tempfile.mkdtemp(prefix="gitdoc_test_other_")
        try:
            new_path = os.path.join(other_dir, "nonexistent.docx")
            new_repo = GitRepo(new_path)
            self.assertFalse(new_repo.is_initialized())
        finally:
            shutil.rmtree(other_dir, ignore_errors=True)

    def test_03_init_is_idempotent(self):
        """Calling init() multiple times should be safe."""
        self.assertTrue(self.repo.init())
        self.assertTrue(self.repo.init())  # Second call

    def test_04_commit_returns_hash(self):
        """commit() should return a valid commit hash."""
        # Write new content
        with open(self.docx_path, "w", encoding="utf-8") as f:
            f.write("Test document content v2 - modified")

        commit_hash = self.repo.commit("Test commit message")
        self.assertIsNotNone(commit_hash)
        self.assertEqual(len(commit_hash), 40)  # Full SHA-1 hash
        self.assertTrue(all(c in "0123456789abcdef" for c in commit_hash))
        self._v2_hash = commit_hash

    def test_05_commit_no_changes(self):
        """commit() should return None when there are no changes."""
        result = self.repo.commit("Should not commit")
        self.assertIsNone(result)

    def test_06_get_history_returns_commits(self):
        """get_history() should return the commit we just made."""
        history = self.repo.get_history()
        self.assertGreaterEqual(len(history), 1)

        first = history[0]
        self.assertIsNotNone(first.hash)
        self.assertIsNotNone(first.short_hash)
        self.assertIsNotNone(first.author)
        self.assertIsNotNone(first.timestamp)
        self.assertTrue(len(first.message) > 0)

    def test_07_get_commit_count(self):
        """get_commit_count() should return the correct number."""
        count = self.repo.get_commit_count()
        self.assertGreaterEqual(count, 1)

    def test_08_get_file_content_at_commit(self):
        """Should retrieve file content from a specific commit."""
        content = self.repo.get_file_content_at_commit(
            self._v1_hash, "test.docx"
        )
        self.assertIsNotNone(content)
        self.assertIn(b"v1", content)

    def test_09_restore_file(self):
        """restore_file() should overwrite the working copy."""
        # Restore to the first version (v1 content)
        result = self.repo.restore_file(self._v1_hash, "test.docx")
        self.assertTrue(result)

        # Verify content was restored
        with open(self.docx_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("v1", content)

    def test_10_has_uncommitted_changes(self):
        """Should detect changes after file modification."""
        # Modify file
        with open(self.docx_path, "w", encoding="utf-8") as f:
            f.write("New content after restore")

        # Should detect changes
        self.assertTrue(self.repo.has_uncommitted_changes())

        # Commit the changes
        self.repo.commit("Commit the changes")
        self.assertFalse(self.repo.has_uncommitted_changes())


if __name__ == "__main__":
    unittest.main()
