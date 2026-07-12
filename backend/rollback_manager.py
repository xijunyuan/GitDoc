"""
Rollback Manager
================
Handles document rollback with a safety backup mechanism.

Flow:
1. Verify the repository is initialized and the target commit exists
2. Create a timestamped backup of the current document
3. Restore the target version's .docx from Git
4. Return the result with backup path info
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Settings
from models import RollbackResponse
from git_operations import GitRepo


class RollbackManager:
    """
    Manages safe rollback of a .docx document to a previous version.

    Always creates a backup before overwriting the current file,
    so the user can recover if they rollback by mistake.
    """

    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path).resolve()
        self.repo = GitRepo(str(self.docx_path))
        self.backups_dir = Settings.get_backups_dir(str(self.docx_path))

    # ---- Backup ----

    def backup_current(self) -> Path:
        """
        Create a timestamped backup of the current document.
        The backup is placed in .gitdoc/backups/ alongside the document.

        Returns the path to the backup file.
        """
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_rollback_{timestamp}_{self.docx_path.name}"
        backup_path = self.backups_dir / backup_name
        shutil.copy2(str(self.docx_path), str(backup_path))
        return backup_path

    # ---- Rollback ----

    def rollback(self, commit_hash: str) -> RollbackResponse:
        """
        Rollback the document to a specific commit.

        Steps:
        1. Verify the repository is initialized
        2. Find the target commit in history (partial hash matching supported)
        3. Create a safety backup of the current file
        4. Restore the .docx from the target commit
        5. Return success with backup path information

        Args:
            commit_hash: Full or partial commit hash to rollback to.

        Returns:
            RollbackResponse with success status, backup path, and message.
        """
        if not self.repo.is_initialized():
            return RollbackResponse(
                success=False,
                message="Git 仓库未初始化 (Repository not initialized)"
            )

        # Verify the commit exists (supports partial hash matching)
        history = self.repo.get_history(max_count=200)
        matching = [c for c in history if c.hash.startswith(commit_hash)]
        if not matching:
            return RollbackResponse(
                success=False,
                message=f"未找到版本 '{commit_hash}' (Commit not found in history)"
            )

        target = matching[0]

        # Create safety backup before overwriting
        backup_path = self.backup_current()

        # Restore the .docx from the target commit
        success = self.repo.restore_file(target.hash, self.docx_path.name)

        if not success:
            return RollbackResponse(
                success=False,
                backup_path=str(backup_path),
                message="从 Git 恢复文档失败，当前文件已备份 (Failed to restore from Git, current file backed up)"
            )

        return RollbackResponse(
            success=True,
            backup_path=str(backup_path),
            message=(
                f"文档已回滚至版本 {target.short_hash} ({target.version_tag})\n"
                f"当前文件已备份至: {backup_path.name}\n"
                f"请在 Word 中重新打开文档以查看变更。\n\n"
                f"Document rolled back to {target.short_hash}. "
                f"Backup saved. Please reopen in Word."
            )
        )
