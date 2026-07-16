"""
GitDoc Backend — FastAPI Server
================================
Main entry point for the GitDoc Python backend.

Serves both the Word add-in frontend and the REST API from a single
HTTPS endpoint on port 18521.

Run:
    python main.py
    python main.py --http   (for plain HTTP, no SSL)
"""

import json
import os
import sys
import tempfile
import subprocess
import signal
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import Settings
from models import (
    InitRequest, InitResponse,
    CommitRequest, CommitResponse,
    RollbackRequest, RollbackResponse,
    HistoryResponse, CommitInfo,
    DiffResponse, DiffSegment, BlockDiff, DiffStats,
    PreviewResponse,
    StatusResponse, ShutdownResponse,
    NoteSaveRequest, NotesResponse
)
from git_operations import GitRepo
from commit_manager import CommitManager
from rollback_manager import RollbackManager
from diff_engine import DiffEngine
from docx_parser import DocxParser
from file_watcher import DocxFileWatcher


# ===================== Global State =====================

active_docs: Dict[str, dict] = {}
_diff_engine: DiffEngine = DiffEngine()

# SSL certificate paths (project-relative, resolved at startup)
_ssl_keyfile: Optional[str] = None
_ssl_certfile: Optional[str] = None


def _resolve_ssl_paths() -> tuple:
    """Find SSL certificate files. Returns (keyfile, certfile) or (None, None)."""
    candidates = [
        # Project certs directory
        Path(__file__).parent.parent / "scripts" / "certs",
        # Same directory as main.py
        Path(__file__).parent / "certs",
    ]
    for base in candidates:
        key = base / "localhost.key"
        crt = base / "localhost.crt"
        if key.exists() and crt.exists():
            return (str(key), str(crt))
    return (None, None)


def _get_frontend_dir() -> Path:
    """Locate the frontend static files directory."""
    candidates = [
        Path(__file__).parent.parent / "frontend" / "word-addin",
        Path(__file__).parent / "frontend" / "word-addin",
    ]
    for d in candidates:
        if (d / "index.html").exists():
            return d
    return Path(__file__).parent.parent / "frontend" / "word-addin"


# ===================== Helpers =====================

def _get_cm(docx_path: str) -> CommitManager:
    cm = CommitManager(docx_path)
    cm.ensure_repo()
    return cm


def _extract_text_from_commit(repo: GitRepo, commit_hash: str,
                              docx_filename: str, cache_dir: Path) -> str:
    cached = DocxParser.load_cached_text(commit_hash, cache_dir)
    if cached is not None:
        return cached

    docx_data = repo.get_file_content_at_commit(commit_hash, docx_filename)
    if docx_data is None:
        raise HTTPException(status_code=404,
                          detail=f"Version {commit_hash[:8]} not found")

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(docx_data)
        tmp_path = tmp.name

    try:
        text = DocxParser.extract_text(tmp_path)
        DocxParser.extract_and_cache(tmp_path, commit_hash, cache_dir)
        return text
    finally:
        os.unlink(tmp_path)


# ===================== Lifespan =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[GitDoc] Backend starting on {Settings.HOST}:{Settings.PORT}")
    yield
    print("[GitDoc] Shutting down...")
    for doc_path, info in active_docs.items():
        watcher = info.get("watcher")
        if watcher:
            watcher.stop()
    active_docs.clear()
    print("[GitDoc] Backend stopped.")


# ===================== FastAPI App =====================

app = FastAPI(
    title="GitDoc Backend",
    version="0.1.0",
    description="文档版本控制 (Document Version Control) — API + Frontend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== Routes =====================

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    git_ver = None
    try:
        r = subprocess.run(
            ["git", "--version"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if r.returncode == 0:
            git_ver = r.stdout.strip()
    except Exception:
        pass

    tracked = list(active_docs.keys())[0] if active_docs else None

    return StatusResponse(
        status="ok",
        repo_initialized=len(active_docs) > 0,
        tracked_docx=tracked,
        python_version=sys.version.split()[0],
        git_version=git_ver
    )


@app.post("/api/init", response_model=InitResponse)
async def init_repo(req: InitRequest):
    if not Path(req.docx_path).exists():
        raise HTTPException(status_code=404,
                          detail="Document not found")

    docx_path = req.docx_path
    if docx_path in active_docs:
        return InitResponse(
            success=True,
            message="Already initialized",
            repo_path=str(Settings.get_gitdoc_dir(docx_path))
        )

    cm = CommitManager(docx_path)
    if not cm.ensure_repo():
        raise HTTPException(status_code=500,
                          detail="Failed to initialize Git repository")

    def on_docx_change():
        try:
            result = cm.auto_commit(author=req.author)
            if result.success:
                print(f"[GitDoc] Auto-commit: {result.message}")
        except Exception as e:
            print(f"[GitDoc] Auto-commit error: {e}")

    watcher = DocxFileWatcher(docx_path, on_docx_change)
    watcher.start()

    active_docs[docx_path] = {
        "commit_manager": cm,
        "watcher": watcher,
        "author": req.author
    }

    return InitResponse(
        success=True,
        message="Repository initialized, file watcher started",
        repo_path=str(Settings.get_gitdoc_dir(docx_path))
    )


@app.post("/api/select-docx", response_model=InitResponse)
async def select_docx(req: InitRequest):
    """
    Switch the tracked document. Same as init but for manual path selection.
    """
    return await init_repo(req)


@app.post("/api/commit", response_model=CommitResponse)
async def create_commit(req: CommitRequest):
    if not Path(req.docx_path).exists():
        raise HTTPException(status_code=404, detail="Document not found")
    cm = _get_cm(req.docx_path)
    return cm.auto_commit(author=req.author, message=req.message)


@app.get("/api/history", response_model=HistoryResponse)
async def get_history(docx_path: str = Query(..., description="Document path")):
    cm = _get_cm(docx_path)
    commits = cm.get_history()
    current = commits[0].version_tag if commits else None
    return HistoryResponse(commits=commits, current_version=current)


@app.get("/api/diff", response_model=DiffResponse)
async def get_diff(
    from_hash: str = Query(..., description="Old hash"),
    to_hash: str = Query(..., description="New hash"),
    docx_path: str = Query(..., description="Document path")
):
    cm = _get_cm(docx_path)
    repo = cm.repo
    cache_dir = Settings.get_cache_dir(docx_path)
    docx_filename = Path(docx_path).name

    text1 = _extract_text_from_commit(repo, from_hash, docx_filename, cache_dir)
    text2 = _extract_text_from_commit(repo, to_hash, docx_filename, cache_dir)

    result = _diff_engine.simple_text_diff(text1, text2)

    return DiffResponse(
        from_hash=from_hash,
        to_hash=to_hash,
        blocks=[BlockDiff(**result["blocks"][0])],
        stats=DiffStats(**result["stats"])
    )


@app.post("/api/rollback", response_model=RollbackResponse)
async def rollback(req: RollbackRequest):
    if not Path(req.docx_path).exists():
        raise HTTPException(status_code=404, detail="Document not found")

    # Pause file watcher to prevent git lock conflicts with auto-commit
    doc_info = active_docs.get(req.docx_path)
    watcher = doc_info.get("watcher") if doc_info else None
    if watcher and watcher.is_running:
        watcher.stop()
        print(f"[GitDoc] Watcher paused for rollback: {req.docx_path}")

    try:
        rm = RollbackManager(req.docx_path)
        return rm.rollback(req.commit_hash, save_as_new=req.save_as_new)
    finally:
        # Always resume the watcher, even if rollback fails
        if watcher and not watcher.is_running:
            watcher.start()
            print(f"[GitDoc] Watcher resumed after rollback: {req.docx_path}")


# ===================== Notes (per-version annotations) =====================


def _get_notes_path(docx_path: str) -> Path:
    """Return the path to the notes.json file for a document."""
    return Settings.get_gitdoc_dir(docx_path) / "notes.json"


def _load_notes(docx_path: str) -> dict:
    """Load notes dict from disk, or return empty dict if none exist."""
    path = _get_notes_path(docx_path)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_notes(docx_path: str, notes: dict) -> None:
    """Write notes dict to disk atomically."""
    path = _get_notes_path(docx_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


@app.get("/api/notes", response_model=NotesResponse)
async def get_notes(docx_path: str = Query(..., description="Document path")):
    """Get all user notes for a document, keyed by commit hash."""
    return NotesResponse(notes=_load_notes(docx_path))


@app.post("/api/notes")
async def save_note(req: NoteSaveRequest):
    """Save or update a note for a specific commit."""
    notes = _load_notes(req.docx_path)
    if req.note.strip():
        notes[req.commit_hash] = req.note.strip()
    else:
        notes.pop(req.commit_hash, None)  # Delete note if empty
    _save_notes(req.docx_path, notes)
    return {"success": True, "commit_hash": req.commit_hash}


@app.get("/api/preview", response_model=PreviewResponse)
async def preview(
    commit_hash: str = Query(..., description="Commit hash"),
    docx_path: str = Query(..., description="Document path")
):
    cm = _get_cm(docx_path)
    repo = cm.repo
    cache_dir = Settings.get_cache_dir(docx_path)
    docx_filename = Path(docx_path).name

    text = _extract_text_from_commit(repo, commit_hash, docx_filename, cache_dir)

    return PreviewResponse(
        hash=commit_hash,
        text=text[:10000],
        block_count=len(text.split("\n\n"))
    )


@app.post("/api/shutdown", response_model=ShutdownResponse)
async def shutdown():
    print("[GitDoc] Shutdown requested by client")
    for doc_path, info in active_docs.items():
        watcher = info.get("watcher")
        if watcher:
            watcher.stop()
    active_docs.clear()
    return ShutdownResponse(success=True, message="Backend shutting down")


# ===================== Frontend Static Files =====================

_frontend_dir = _get_frontend_dir()
if _frontend_dir and _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")


# ===================== Entry Point =====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitDoc Backend")
    parser.add_argument("--http", action="store_true",
                        help="Use plain HTTP instead of HTTPS")
    args = parser.parse_args()

    import socket

    def _check_port(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False

    if not _check_port(Settings.HOST, Settings.PORT):
        print(f"[GitDoc] Port {Settings.PORT} is in use. Backend may already be running:")
        print(f"         https://localhost:{Settings.PORT}/api/status")
        sys.exit(0)

    _ssl_keyfile, _ssl_certfile = _resolve_ssl_paths()
    use_ssl = (not args.http) and _ssl_keyfile and _ssl_certfile

    protocol = "https" if use_ssl else "http"
    print(f"GitDoc Backend v0.1.0")
    print(f"Frontend:  {protocol}://localhost:{Settings.PORT}")
    print(f"API docs:  {protocol}://localhost:{Settings.PORT}/docs")
    print(f"SSL:       {'enabled' if use_ssl else 'disabled (use --http to force HTTP)'}")

    uvicorn.run(
        app,
        host=Settings.HOST,
        port=Settings.PORT,
        ssl_keyfile=_ssl_keyfile if use_ssl else None,
        ssl_certfile=_ssl_certfile if use_ssl else None,
        log_level="info"
    )
