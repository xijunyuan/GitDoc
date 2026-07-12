"""
GitDoc Data Models
==================
Pydantic request/response models for the FastAPI backend.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ===================== Request Models =====================


class InitRequest(BaseModel):
    """Request to initialize a Git repository for a document."""
    docx_path: str
    author: str = "GitDoc User"
    email: str = "user@gitdoc.local"


class CommitRequest(BaseModel):
    """Request to create a manual commit (Save Version button)."""
    docx_path: str
    message: str = "[manual] 保存版本"
    author: str = "GitDoc User"


class RollbackRequest(BaseModel):
    """Request to rollback a document to a specific commit."""
    commit_hash: str
    docx_path: str


# ===================== Response Models =====================


class StatusResponse(BaseModel):
    """Health check / connection test response."""
    status: str                # "ok" | "error"
    repo_initialized: bool
    tracked_docx: Optional[str] = None
    python_version: Optional[str] = None
    git_version: Optional[str] = None


class InitResponse(BaseModel):
    """Response after initializing a document repository."""
    success: bool
    message: str
    repo_path: Optional[str] = None


class CommitResponse(BaseModel):
    """Response after creating a commit."""
    success: bool
    hash: Optional[str] = None
    message: str


class CommitInfo(BaseModel):
    """A single commit entry in the version history."""
    hash: str                   # Full commit hash
    short_hash: str             # Abbreviated hash (first 8 chars)
    author: str
    timestamp: datetime
    message: str
    version_tag: str = ""       # e.g. "v1", "v2"


class HistoryResponse(BaseModel):
    """Response containing the version history for a document."""
    commits: List[CommitInfo]
    current_version: Optional[str] = None


class DiffSegment(BaseModel):
    """A single segment in a diff (one contiguous run of same operation)."""
    operation: Literal["equal", "insert", "delete"]
    text: str


class BlockDiff(BaseModel):
    """Diff result for a single content block (paragraph/table)."""
    block_index: int
    block_type: str             # "paragraph" | "table" | "full_text"
    segments: List[DiffSegment]


class DiffStats(BaseModel):
    """Character-level statistics for a diff."""
    insertions: int
    deletions: int
    equal: int


class DiffResponse(BaseModel):
    """Response containing the structured diff between two versions."""
    from_hash: str
    to_hash: str
    blocks: List[BlockDiff]
    stats: DiffStats


class PreviewResponse(BaseModel):
    """Response containing the plain text of a specific version."""
    hash: str
    text: str                   # Full plain text (truncated if too long)
    block_count: int


class RollbackResponse(BaseModel):
    """Response after performing a rollback operation."""
    success: bool
    backup_path: Optional[str] = None
    message: str


class ShutdownResponse(BaseModel):
    """Response after shutting down the backend."""
    success: bool
    message: str = "Backend shutting down"
