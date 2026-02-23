#!/usr/bin/env python3
"""Audit recent writes for the tiered write contract.

Focus:
- tags must include: priority:<P0|P1|P2|GOLD>, kind:<...>
- optional: source:<...>

Requires:
  pip env has chromadb, and env vars point to the shared store.

Run:
  NEXUS_VECTOR_DB=... NEXUS_COLLECTION=... python3 scripts/nexus_audit_contract.py --limit 200
"""

import argparse
import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List


PRIORITY_RE = re.compile(r"^\s*priority:(P0|P1|P2|GOLD)\s*$", flags=re.IGNORECASE)
KIND_RE = re.compile(r"^\s*kind:([a-z_]+)\s*$", flags=re.IGNORECASE)
SOURCE_RE = re.compile(r"^\s*source:([^,]+)\s*$", flags=re.IGNORECASE)
SPLIT_RE = re.compile(r"[,;\n]")


def _extract_tag_items(meta: Dict[str, Any]) -> List[str]:
    if not isinstance(meta, dict):
        return []
    raw = meta.get("tags")
    if raw is None:
        raw = meta.get("tag")
    items: List[str] = []
    if isinstance(raw, list):
        for item in raw:
            text = str(item).strip()
            if text:
                items.append(text)
    elif isinstance(raw, str):
        for chunk in SPLIT_RE.split(raw):
            text = chunk.strip()
            if text:
                items.append(text)
    return items


def _extract_contract(meta: Dict[str, Any]) -> Dict[str, str]:
    """
    Parse contract fields from both tags and explicit metadata fields.
    """
    tags = _extract_tag_items(meta)
    priority = ""
    kind = ""
    source = ""

    for tag in tags:
        if not priority:
            m = PRIORITY_RE.match(tag)
            if m:
                priority = m.group(1).upper()
                continue
        if not kind:
            m = KIND_RE.match(tag)
            if m:
                kind = m.group(1).lower()
                continue
        if not source:
            m = SOURCE_RE.match(tag)
            if m:
                source = m.group(1).strip()

    # metadata fallback: supports strict schema migrations
    if not priority and isinstance(meta.get("priority"), str):
        p = meta.get("priority", "").strip().upper()
        if p in {"P0", "P1", "P2", "GOLD"}:
            priority = p
    if not kind and isinstance(meta.get("kind"), str):
        k = meta.get("kind", "").strip().lower()
        if k:
            kind = k
    if not source:
        if isinstance(meta.get("source"), str) and meta.get("source", "").strip():
            source = meta.get("source", "").strip()
        elif isinstance(meta.get("source_file"), str) and meta.get("source_file", "").strip():
            source = meta.get("source_file", "").strip()

    return {"priority": priority, "kind": kind, "source": source, "tags": tags}


def _source_bucket(contract: Dict[str, str], meta: Dict[str, Any]) -> str:
    has_contract = bool(contract.get("priority") and contract.get("kind"))
    if has_contract:
        return "new_contract"
    if isinstance(meta, dict) and meta.get("source_file"):
        return "legacy_source_file"
    return "legacy_unknown"


def _coverage_payload(total: int, count_priority: int, count_kind: int, count_source: int) -> Dict[str, Any]:
    return {
        "sampled": total,
        "coverage": {
            "priority": (count_priority / total) if total else 0.0,
            "kind": (count_kind / total) if total else 0.0,
            "source": (count_source / total) if total else 0.0,
        },
        "counts": {
            "priority": count_priority,
            "kind": count_kind,
            "source": count_source,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=200)
    ap.add_argument('--show-missing', type=int, default=8, help='Include up to N missing samples in report')
    args = ap.parse_args()

    vector_db = os.environ.get('NEXUS_VECTOR_DB', '').strip()
    collection = os.environ.get('NEXUS_COLLECTION', '').strip()
    if not vector_db or not collection:
        raise SystemExit('Missing NEXUS_VECTOR_DB or NEXUS_COLLECTION')

    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=vector_db,
        settings=Settings(anonymized_telemetry=False),
        tenant='default_tenant',
        database='default_database',
    )
    col = client.get_or_create_collection(collection)

    # Best-effort: "recent" isn't guaranteed in Chroma; we random-sample by reading
    # the first N may bias towards older imported docs. Provide a where-filter option
    # via tags prefix if needed in future.
    res = col.get(limit=max(1, args.limit))
    metas = res.get('metadatas') or []

    total = len(metas)
    ok_priority = 0
    ok_kind = 0
    ok_source = 0

    by_group = defaultdict(list)
    missing_samples = []

    for idx, meta in enumerate(metas):
        meta = meta if isinstance(meta, dict) else {}
        contract = _extract_contract(meta)
        bucket = _source_bucket(contract, meta)
        by_group[bucket].append(contract)

        has_priority = bool(contract["priority"])
        has_kind = bool(contract["kind"])
        has_source = bool(contract["source"])

        if has_priority:
            ok_priority += 1
        if has_kind:
            ok_kind += 1
        if has_source:
            ok_source += 1

        if len(missing_samples) < max(0, int(args.show_missing)) and (not has_priority or not has_kind):
            missing_samples.append(
                {
                    "index": idx,
                    "priority": contract["priority"],
                    "kind": contract["kind"],
                    "source": contract["source"],
                    "tags": contract["tags"][:10],
                }
            )

    grouped = {}
    for group, rows in by_group.items():
        g_total = len(rows)
        g_priority = sum(1 for item in rows if item.get("priority"))
        g_kind = sum(1 for item in rows if item.get("kind"))
        g_source = sum(1 for item in rows if item.get("source"))
        grouped[group] = _coverage_payload(g_total, g_priority, g_kind, g_source)

    report = {
        'vector_db': vector_db,
        'collection': collection,
        **_coverage_payload(total, ok_priority, ok_kind, ok_source),
        'group_coverage': grouped,
        'missing_samples': missing_samples,
        'note': (
            'Sampling uses col.get(limit=N) which may bias towards older imported docs; '
            'group_coverage helps separate legacy records from new contract writes.'
        ),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
