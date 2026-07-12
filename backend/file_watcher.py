"""
File Watcher
============
Monitors a .docx file for modifications and triggers auto-commits
after a debounce period (no new modifications for 3 seconds).

Uses the watchdog library to listen for filesystem events.
Thread-safe start/stop operations.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from config import Settings


class DocxFileHandler(FileSystemEventHandler):
    """
    Watchdog event handler with debounce logic.

    When a file modification is detected, starts a timer.
    If the file changes again before the timer fires, the timer resets.
    Only after the debounce period passes with no new modifications
    does it trigger the callback.
    """

    def __init__(self, docx_path: str, debounce_seconds: float,
                 on_change: Callable[[], None]):
        self.docx_path = str(Path(docx_path).resolve())
        self.debounce_seconds = debounce_seconds
        self.on_change = on_change
        self._last_trigger = 0.0
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """Called by watchdog when a file in the watched directory changes."""
        if not isinstance(event, FileModifiedEvent):
            return

        # Normalize paths for comparison (Windows path casing)
        event_path = str(Path(event.src_path).resolve())

        if event_path == self.docx_path:
            with self._lock:
                now = time.time()
                # Skip if we already handled a modification in this debounce window
                if now - self._last_trigger < self.debounce_seconds * 0.5:
                    return
                self._last_trigger = now

                # Cancel any pending timer
                if self._timer and self._timer.is_alive():
                    self._timer.cancel()

                # Start a new debounce timer
                self._timer = threading.Timer(self.debounce_seconds, self._fire)
                self._timer.daemon = True
                self._timer.start()

    def _fire(self):
        """Called after the debounce period with no further modifications."""
        try:
            self.on_change()
        except Exception as e:
            print(f"[GitDoc] Auto-commit callback failed: {e}")


class DocxFileWatcher:
    """
    Manages the lifecycle of a watchdog file observer for a .docx file.

    Usage:
        watcher = DocxFileWatcher(docx_path, on_change_callback)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(self, docx_path: str, on_change: Callable[[], None],
                 debounce_seconds: Optional[float] = None):
        self.docx_path = Path(docx_path).resolve()
        self.debounce = debounce_seconds if debounce_seconds is not None else Settings.DEBOUNCE_SECONDS
        self.on_change = on_change
        self._observer: Optional[Observer] = None
        self._handler: Optional[DocxFileHandler] = None

    def start(self):
        """
        Start watching the .docx file's directory for modifications.
        Safe to call multiple times (no-op if already running).
        """
        if self._observer is not None:
            return

        watch_dir = str(self.docx_path.parent)
        if not Path(watch_dir).exists():
            return

        self._handler = DocxFileHandler(
            str(self.docx_path), self.debounce, self.on_change
        )
        self._observer = Observer()
        self._observer.schedule(
            self._handler, watch_dir, recursive=False
        )
        self._observer.daemon = True
        self._observer.start()

    def stop(self):
        """
        Stop watching for file changes.
        Safe to call multiple times (no-op if not running).
        """
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
            self._handler = None

    @property
    def is_running(self) -> bool:
        """Check whether the file watcher is currently active."""
        return self._observer is not None and self._observer.is_alive()
