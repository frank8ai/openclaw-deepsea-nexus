#!/usr/bin/env python3
"""Snapshot the Chroma vector DB directory (safe, non-destructive)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path


def _safe_path(value: str) -> Path:
    text = str(value or "").strip()
    if not text:
        return Path.cwd()
    try:
        return Path(text).expanduser().resolve()
    except RuntimeError:
        if text.startswith("~/"):
            home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
            if home:
                return (Path(home) / text[2:]).resolve()
            return (Path.cwd() / text[2:]).resolve()
        return Path(text).resolve()


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _resolve_openclaw_home() -> Path:
    raw = os.environ.get("OPENCLAW_HOME")
    if raw:
        return _safe_path(raw)
    return _safe_path("~/.openclaw")


def _resolve_workspace_root() -> Path:
    raw = os.environ.get("OPENCLAW_WORKSPACE")
    if raw:
        return _safe_path(raw)
    return (_resolve_openclaw_home() / "workspace").resolve()


def _resolve_db_path() -> Path:
    raw = os.environ.get("NEXUS_VECTOR_DB")
    if raw:
        return _safe_path(raw)
    return (_resolve_workspace_root() / "memory" / ".vector_db_restored").resolve()


def _resolve_snapshots_dir() -> Path:
    base = (
        _resolve_workspace_root() / "memory" / "archives" / "vector_db_snapshots"
    ).resolve()
    base.mkdir(parents=True, exist_ok=True)
    return base


def _rsync_copy(src: Path, dst: Path) -> bool:
    if shutil.which("rsync") is None:
        return False
    cmd = ["rsync", "-a", f"{src}/", f"{dst}/"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"rsync failed: {result.stderr.strip()}")
    return True


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)


def _collection_count(db_path: Path, collection: str) -> int:
    try:
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
    except Exception:
        return -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(_resolve_db_path()))
    ap.add_argument("--collection", default=os.environ.get("NEXUS_COLLECTION", "deepsea_nexus_restored"))
    ap.add_argument("--out-dir", default=str(_resolve_snapshots_dir()))
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    src = _safe_path(args.db)
    if not src.exists() or not src.is_dir():
        raise SystemExit(f"vector db not found: {src}")

    label = f"_{args.label}" if args.label else ""
    dst = _safe_path(args.out_dir) / f"{src.name}_snapshot_{_ts()}{label}"
    if dst.exists():
        raise SystemExit(f"snapshot already exists: {dst}")

    t0 = time.time()
    dst.mkdir(parents=True, exist_ok=False)

    used_rsync = False
    try:
        used_rsync = _rsync_copy(src, dst)
    except RuntimeError:
        used_rsync = False

    if not used_rsync:
        # fallback to copytree into existing dst
        # copytree expects dst to be empty; remove and recreate
        shutil.rmtree(dst)
        _copytree(src, dst)

    count = _collection_count(src, args.collection)
    manifest = {
        "ts": datetime.now().isoformat(),
        "src": str(src),
        "dst": str(dst),
        "collection": args.collection,
        "count": count,
        "elapsed_sec": round(time.time() - t0, 2),
        "method": "rsync" if used_rsync else "copytree",
    }
    with open(dst / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
