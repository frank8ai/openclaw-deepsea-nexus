#!/usr/bin/env python3
"""Health check for Chroma vector DB. Optionally auto-restore from snapshots."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path


def _resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def _resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", _resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


def _resolve_db_path() -> Path:
    return Path(
        os.environ.get(
            "NEXUS_VECTOR_DB",
            _resolve_workspace_root() / "memory" / ".vector_db_restored",
        )
    ).expanduser().resolve()


def _resolve_snapshots_dir() -> Path:
    return (
        _resolve_workspace_root() / "memory" / "archives" / "vector_db_snapshots"
    ).resolve()


def _log_path() -> Path:
    log_dir = (_resolve_workspace_root() / "logs").resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "vector_db_health.jsonl"


def _collection_count(db_path: Path, collection: str) -> int:
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False),
        tenant="default_tenant",
        database="default_database",
    )
    col = client.get_collection(collection)
    return int(col.count())


def _latest_snapshot(snapshots_dir: Path) -> Path | None:
    if not snapshots_dir.exists():
        return None
    candidates = [p for p in snapshots_dir.iterdir() if p.is_dir()]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _restore_from_snapshot(snapshot: Path, dst: Path) -> None:
    if dst.exists():
        backup = dst.parent / f"{dst.name}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(dst, backup)
    shutil.copytree(snapshot, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(_resolve_db_path()))
    ap.add_argument("--collection", default=os.environ.get("NEXUS_COLLECTION", "deepsea_nexus_restored"))
    ap.add_argument("--min-count", type=int, default=1)
    ap.add_argument("--auto-restore", action="store_true")
    ap.add_argument("--snapshots-dir", default=str(_resolve_snapshots_dir()))
    args = ap.parse_args()

    db_path = Path(os.path.expanduser(args.db)).resolve()
    snapshots_dir = Path(os.path.expanduser(args.snapshots_dir)).resolve()
    started = time.time()

    payload = {
        "ts": datetime.now().isoformat(),
        "db": str(db_path),
        "collection": args.collection,
        "ok": False,
        "count": -1,
        "elapsed_sec": 0.0,
    }

    try:
        count = _collection_count(db_path, args.collection)
        payload["count"] = count
        payload["ok"] = count >= int(args.min_count)
    except Exception as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"

    if not payload["ok"] and args.auto_restore:
        snap = _latest_snapshot(snapshots_dir)
        if snap is not None:
            _restore_from_snapshot(snap, db_path)
            payload["restored_from"] = str(snap)
            try:
                payload["count_after_restore"] = _collection_count(db_path, args.collection)
                payload["ok"] = payload["count_after_restore"] >= int(args.min_count)
            except Exception as exc:
                payload["restore_error"] = f"{type(exc).__name__}: {exc}"

    payload["elapsed_sec"] = round(time.time() - started, 2)

    log_path = _log_path()
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
