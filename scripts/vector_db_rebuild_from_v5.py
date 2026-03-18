#!/usr/bin/env python3
"""Rebuild vector DB embeddings from Memory v5 items."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List


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


def _resolve_default_memory_v5_root() -> Path:
    return (_resolve_workspace_root() / "memory" / "95_MemoryV5").resolve()


def _resolve_default_db_path() -> Path:
    raw = os.environ.get("NEXUS_VECTOR_DB")
    if raw:
        return _safe_path(raw)
    return (_resolve_workspace_root() / "memory" / ".vector_db_restored").resolve()


def _iter_items(root: Path, agent: str, user: str) -> Iterable[Path]:
    if agent == "all":
        agents = [p for p in root.iterdir() if p.is_dir()]
    else:
        agents = [root / agent]
    for agent_dir in agents:
        if not agent_dir.exists():
            continue
        if user == "all":
            users = [p for p in agent_dir.iterdir() if p.is_dir()]
        else:
            users = [agent_dir / user]
        for user_dir in users:
            items_dir = user_dir / "items"
            if not items_dir.exists():
                continue
            for item_path in items_dir.glob("*.json"):
                yield item_path


def _load_item(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_meta(item: Dict, agent_id: str, user_id: str) -> Dict:
    meta = {
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "category": item.get("category", ""),
        "source_id": item.get("source_id", ""),
        "agent_id": agent_id,
        "user_id": user_id,
        "tags": item.get("tags", []) or [],
        "keywords": item.get("keywords", []) or [],
        "entities": item.get("entities", []) or [],
    }
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(_resolve_default_memory_v5_root()))
    ap.add_argument("--agent", default="main")
    ap.add_argument("--user", default="default")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--collection", default=os.environ.get("NEXUS_COLLECTION", "deepsea_nexus_restored"))
    ap.add_argument("--db", default=str(_resolve_default_db_path()))
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
    args = ap.parse_args()

    root = _safe_path(args.root)
    items = list(_iter_items(root, args.agent, args.user))
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    if not items:
        raise SystemExit("no memory v5 items found")

    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer

    client = chromadb.PersistentClient(
        path=str(_safe_path(args.db)),
        settings=Settings(anonymized_telemetry=False),
        tenant="default_tenant",
        database="default_database",
    )
    col = client.get_or_create_collection(args.collection)
    embedder = SentenceTransformer(args.model)

    total = 0
    batch_ids: List[str] = []
    batch_docs: List[str] = []
    batch_metas: List[Dict] = []

    def _flush():
        nonlocal total, batch_ids, batch_docs, batch_metas
        if not batch_ids:
            return
        embeddings = embedder.encode(batch_docs, show_progress_bar=False)
        try:
            embeddings = embeddings.tolist()
        except Exception:
            embeddings = [e.tolist() for e in embeddings]
        col.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas, embeddings=embeddings)
        total += len(batch_ids)
        batch_ids, batch_docs, batch_metas = [], [], []

    for item_path in items:
        item = _load_item(item_path)
        item_id = str(item.get("id") or "")
        content = str(item.get("content") or "")
        if not item_id or not content:
            continue
        # infer agent/user from path
        agent_id = item_path.parents[2].name
        user_id = item_path.parents[1].name
        batch_ids.append(item_id)
        batch_docs.append(content)
        batch_metas.append(_build_meta(item, agent_id, user_id))

        if len(batch_ids) >= args.batch:
            _flush()

    _flush()
    print(json.dumps({"rebuilt": total, "collection": args.collection}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
