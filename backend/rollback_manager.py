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

    def rollback(self, commit_hash: str, save_as_new: bool = False) -> RollbackResponse:
        """
        Rollback the document to a specific commit.

        When the file is locked by Word:
        - If save_as_new=False: return locked_by_word=True, let the frontend ask
        - If save_as_new=True: save restored content as a new file alongside
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
        total = len(history)
        for i, c in enumerate(history):
            if c.hash == target.hash:
                target.version_tag = f"v{total - i}"
                break

        backup_path = self.backup_current()

        # Try to restore the .docx from the target commit
        success = self.repo.restore_file(target.hash, self.docx_path.name)

        if not success:
            if save_as_new:
                return self._save_as_new(target, backup_path)
            else:
                # File is locked by Word — ask the frontend what to do
                vtag = target.version_tag or target.short_hash
                return RollbackResponse(
                    success=True,
                    locked_by_word=True,
                    backup_path=str(backup_path),
                    message=(
                        f"当前文档正被 Word 打开，无法直接覆盖。\n\n"
                        f"请选择:\n"
                        f"  • 关闭文档 → 关闭 Word 中的文件后重试覆盖\n"
                        f"  • 另存为新文件 → 将回滚内容保存为 原名_{vtag}.docx"
                    )
                )

        # Direct overwrite succeeded
        rollback_msg = (
            f"文档已回滚至版本 {target.short_hash}\n"
            f"Rolled back to {target.short_hash}"
        )
        self.repo.commit(rollback_msg, author="GitDoc Rollback")

        return RollbackResponse(
            success=True,
            backup_path=str(backup_path),
            message=(
                f"文档已回滚至版本 {target.short_hash} ({target.version_tag})\n"
                f"当前文件已备份至: {backup_path.name}\n"
                f"请在 Word 中重新打开文档以查看变更。"
            )
        )

    def _save_as_new(self, target, backup_path: Path) -> RollbackResponse:
        """Save the restored content as a new file alongside the original."""
        content = self.repo.get_file_content_at_commit(
            target.hash, self.docx_path.name
        )
        if content is None:
            return RollbackResponse(
                success=False,
                backup_path=str(backup_path),
                message="从 Git 读取历史版本失败"
            )

        stem = self.docx_path.stem
        suffix = self.docx_path.suffix
        vtag = target.version_tag or target.short_hash
        restored_path = self.docx_path.parent / f"{stem}_{vtag}{suffix}"
        restored_path.write_bytes(content)

        self.repo.add(restored_path.name)
        marker_msg = f"[rollback] 回滚至 {vtag} → 另存为 {restored_path.name}"
        self.repo.commit(marker_msg, author="GitDoc Rollback")

        return RollbackResponse(
            success=True,
            backup_path=str(backup_path),
            restored_path=str(restored_path),
            message=(
                f"回滚文件已保存为:\n"
                f"{restored_path}\n\n"
                f"请在 Word 中关闭当前文档后打开此文件。\n"
                f"当前版本已备份至: {backup_path.name}"
            )
        )
