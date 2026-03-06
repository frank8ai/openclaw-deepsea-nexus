"""Lightweight file lock for vector DB writes.

Purpose:
- Prevent concurrent writes to Chroma persistent store across agents/processes.
- Reduce corruption risk from overlapping add/upsert operations.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager

try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore


def _resolve_lock_path(persist_path: str) -> str:
    persist_path = os.path.expanduser(str(persist_path))
    if not persist_path:
        persist_path = os.path.expanduser("~/.openclaw/workspace/memory/.vector_db_restored")
    return os.path.join(persist_path, ".vector_db.lock")


@contextmanager
def vector_db_write_lock(persist_path: str, timeout_sec: float = 30.0, poll_sec: float = 0.1):
    """Acquire an exclusive lock on the vector DB directory."""
    lock_path = _resolve_lock_path(persist_path)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")

    if fcntl is None:
        # Best-effort if fcntl is unavailable.
        yield
        handle.close()
        return

    deadline = time.time() + max(0.0, float(timeout_sec))
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() >= deadline:
                raise TimeoutError("vector_db lock timeout")
            time.sleep(max(0.01, float(poll_sec)))

    try:
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        handle.close()
