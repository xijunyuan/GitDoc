"""
GitDoc MCP Server
=================
MCP (Model Context Protocol) server exposing GitDoc's .docx parsing,
word-level diff, and version control capabilities to AI assistants.

Supports two transports:
  - stdio (default): for Claude Desktop / Claude Code / Cursor
  - streamable-http: for remote MCP clients (--transport http)

Usage:
  python mcp_server.py                     # stdio mode
  python mcp_server.py --transport http    # HTTP mode (127.0.0.1:18522)
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path
from tempfile import NamedTemporaryFile

# Ensure backend/ is on sys.path so sibling imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from docx_parser import DocxParser, DocumentContent
from diff_engine import DiffEngine
from git_operations import GitRepo

# ---------------------------------------------------------------------------
# MCP application
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "GitDoc",
    host="127.0.0.1",
    port=18522,
)

_diff_engine = DiffEngine()


# ============================================================================
# Error-safe async runner
# ============================================================================

async def _run_in_thread(fn, *args, **kwargs):
    """Run a blocking call in a thread pool so the asyncio event loop
    stays responsive (critical for stdio transport)."""
    return await asyncio.to_thread(fn, *args, **kwargs)


async def _safe_call(func_name, fn, *args, **kwargs):
    """Call *fn* in a thread and return its result, or an error dict.

    Thread-pool execution prevents git subprocess / file-I/O calls
    from blocking the asyncio event loop in stdio mode.
    """
    try:
        return await _run_in_thread(fn, *args, **kwargs)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error in {func_name}: {e}"}


# ============================================================================
# Tool: read_docx
# ============================================================================

@mcp.tool()
async def read_docx(path: str) -> dict:
    """Parse any .docx file and return its structured text content.

    Extracts paragraphs, tables, and list items in document order.
    Returns both the structured block list and the concatenated full text.
    Does NOT require a Git repository — works on any .docx file.

    Args:
        path: Absolute path to the .docx file (e.g. C:\\Users\\...\\doc.docx).
    """
    return await _safe_call("read_docx", _read_docx_impl, path)


def _read_docx_impl(path: str) -> dict:
    _validate_docx_path(path)
    blocks = DocxParser.extract_blocks(path)
    return {
        "path": path,
        "block_count": len(blocks),
        "blocks": [b.to_dict() for b in blocks],
        "full_text": "\n\n".join(b.text for b in blocks),
    }


# ============================================================================
# Tool: get_history
# ============================================================================

@mcp.tool()
async def get_history(docx_path: str, max_count: int = 50) -> dict:
    """Get the Git commit history for a tracked .docx document.

    Requires the document to have been initialized with GitDoc
    (a .gitdoc/.git repository must exist alongside the document).

    Args:
        docx_path:  Absolute path to the tracked .docx file.
        max_count:  Maximum number of commits to return (default 50, max 200).
    """
    return await _safe_call("get_history", _get_history_impl, docx_path, max_count)


def _get_history_impl(docx_path: str, max_count: int) -> dict:
    _validate_docx_path(docx_path)
    repo = _require_repo(docx_path)
    commits = repo.get_history(max_count=min(max_count, 200))
    return {
        "docx_path": docx_path,
        "total_count": len(commits),
        "commits": [c.model_dump() for c in commits],
    }


# ============================================================================
# Tool: diff_versions
# ============================================================================

@mcp.tool()
async def diff_versions(docx_path: str, from_hash: str, to_hash: str) -> dict:
    """Compare two Git-tracked versions of a document with word-level diff.

    Shows exactly which words were added, deleted, or unchanged between
    the two commits. Accepts both full (40-char) and short (8-char) hashes.

    Args:
        docx_path:  Absolute path to the tracked .docx file.
        from_hash:  The older commit hash (full or short, e.g. "abc12345").
        to_hash:    The newer commit hash (full or short).
    """
    return await _safe_call("diff_versions", _diff_versions_impl, docx_path, from_hash, to_hash)


def _diff_versions_impl(docx_path: str, from_hash: str, to_hash: str) -> dict:
    _validate_docx_path(docx_path)
    repo = _require_repo(docx_path)

    from_full = _resolve_hash(repo, from_hash)
    to_full = _resolve_hash(repo, to_hash)

    content1 = _load_content_at_commit(repo, from_full)
    content2 = _load_content_at_commit(repo, to_full)

    result = _diff_engine.compute_structured_diff(content1, content2)
    result["from_hash"] = from_full
    result["to_hash"] = to_full
    result["from_short"] = from_hash
    result["to_short"] = to_hash
    return result


# ============================================================================
# Tool: preview_version
# ============================================================================

@mcp.tool()
async def preview_version(docx_path: str, commit_hash: str) -> dict:
    """Get the plain text content of a document at a specific Git version.

    Args:
        docx_path:   Absolute path to the tracked .docx file.
        commit_hash: The commit hash to preview (full or short).
    """
    return await _safe_call("preview_version", _preview_version_impl, docx_path, commit_hash)


def _preview_version_impl(docx_path: str, commit_hash: str) -> dict:
    _validate_docx_path(docx_path)
    repo = _require_repo(docx_path)
    full_hash = _resolve_hash(repo, commit_hash)

    docx_bytes = repo.get_file_content_at_commit(full_hash, repo.docx_filename)
    if docx_bytes is None:
        raise ValueError(
            f"Could not retrieve '{repo.docx_filename}' at commit {full_hash}"
        )

    content = _parse_docx_bytes(docx_bytes)
    return {
        "hash": full_hash,
        "short_hash": commit_hash,
        "text": content.full_text,
        "block_count": len(content.blocks),
    }


# ============================================================================
# Tool: diff_files
# ============================================================================

@mcp.tool()
async def diff_files(file1: str, file2: str) -> dict:
    """Compare any two .docx files with word-level diff.

    Does NOT require a Git repository — works on any two .docx files.
    Useful for comparing drafts, revisions, or arbitrary documents.

    Args:
        file1: Absolute path to the older (original) .docx file.
        file2: Absolute path to the newer (changed) .docx file.
    """
    return await _safe_call("diff_files", _diff_files_impl, file1, file2)


def _diff_files_impl(file1: str, file2: str) -> dict:
    _validate_docx_path(file1)
    _validate_docx_path(file2)

    blocks1 = DocxParser.extract_blocks(file1)
    blocks2 = DocxParser.extract_blocks(file2)

    content1 = DocumentContent(blocks1)
    content2 = DocumentContent(blocks2)

    result = _diff_engine.compute_structured_diff(content1, content2)
    result["file1"] = file1
    result["file2"] = file2
    return result


# ============================================================================
# Internal helpers
# ============================================================================

def _validate_docx_path(path: str) -> None:
    """Raise a user-friendly error if *path* is not a valid .docx file."""
    if not path:
        raise ValueError("Path cannot be empty.")
    p = Path(path)
    if not p.exists():
        raise ValueError(f"File not found: {path}")
    if p.suffix.lower() not in (".docx", ".doc"):
        raise ValueError(
            f"Not a Word document: {path} (expected .docx or .doc)"
        )


def _require_repo(docx_path: str) -> GitRepo:
    """Return a GitRepo for *docx_path*, or raise if not initialized."""
    repo = GitRepo(docx_path)
    if not repo.is_initialized():
        raise ValueError(
            f"No GitDoc repository found for {docx_path}. "
            f"Initialize it first with the GitDoc Word Add-in, "
            f"or POST to /api/init on the GitDoc backend."
        )
    return repo


def _resolve_hash(repo: GitRepo, hash_str: str) -> str:
    """Resolve a partial commit hash to a full 40-char hash."""
    if len(hash_str) >= 40:
        return hash_str
    commits = repo.get_history(max_count=500)
    for c in commits:
        if c.hash.startswith(hash_str) or c.short_hash.startswith(hash_str):
            return c.hash
    raise ValueError(
        f"No commit found matching hash '{hash_str}'. "
        f"Use get_history to list available commits."
    )


def _load_content_at_commit(repo: GitRepo, commit_hash: str) -> DocumentContent:
    """Retrieve and parse a .docx file as it existed at *commit_hash*."""
    docx_bytes = repo.get_file_content_at_commit(
        commit_hash, repo.docx_filename
    )
    if docx_bytes is None:
        raise ValueError(
            f"Could not retrieve '{repo.docx_filename}' at commit {commit_hash}."
        )
    return _parse_docx_bytes(docx_bytes)


def _parse_docx_bytes(data: bytes) -> DocumentContent:
    """Parse raw .docx bytes into a DocumentContent via a temp file.

    python-docx works with file paths, so we stage the bytes to a
    temporary .docx file and hand that path to DocxParser.
    """
    with NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        blocks = DocxParser.extract_blocks(tmp_path)
        return DocumentContent(blocks)
    finally:
        os.unlink(tmp_path)


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GitDoc MCP Server — Word document intelligence for AI assistants"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport mode: stdio for local clients, http for remote (default: stdio)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        print("GitDoc MCP Server → http://127.0.0.1:18522/mcp")
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
