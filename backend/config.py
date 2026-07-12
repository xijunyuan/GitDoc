"""
GitDoc Backend Configuration
=============================
Paths, default values, and constants for the GitDoc backend.
"""

import os
from pathlib import Path


class Settings:
    """Centralized configuration for the GitDoc backend."""

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 18521

    # Directory names
    GITDOC_DIR_NAME: str = ".gitdoc"
    CACHE_DIR_NAME: str = "cache"
    BACKUPS_DIR_NAME: str = "backups"

    # File watcher settings
    DEBOUNCE_SECONDS: float = 3.0  # Wait time after last file modification

    # History settings
    MAX_HISTORY_COUNT: int = 100

    # Commit message defaults
    AUTO_COMMIT_MESSAGE_PREFIX: str = "[auto]"
    MANUAL_COMMIT_MESSAGE_PREFIX: str = "[manual]"

    # Git author defaults
    GIT_AUTHOR_NAME: str = "GitDoc User"
    GIT_AUTHOR_EMAIL: str = "user@gitdoc.local"

    # --- Path helpers ---

    @staticmethod
    def get_gitdoc_dir(docx_path: str) -> Path:
        """Return the .gitdoc metadata directory path alongside the document."""
        return Path(docx_path).resolve().parent / Settings.GITDOC_DIR_NAME

    @staticmethod
    def get_cache_dir(docx_path: str) -> Path:
        """Return the cache directory for extracted text JSON files."""
        return Settings.get_gitdoc_dir(docx_path) / Settings.CACHE_DIR_NAME

    @staticmethod
    def get_backups_dir(docx_path: str) -> Path:
        """Return the backups directory for pre-rollback safety copies."""
        return Settings.get_gitdoc_dir(docx_path) / Settings.BACKUPS_DIR_NAME

    @staticmethod
    def get_config_path(docx_path: str) -> Path:
        """Return the path to the per-document config.json."""
        return Settings.get_gitdoc_dir(docx_path) / "config.json"

    @staticmethod
    def get_gitignore_path(docx_path: str) -> Path:
        """Return the path to the .gitignore file."""
        return Settings.get_gitdoc_dir(docx_path) / ".gitignore"
