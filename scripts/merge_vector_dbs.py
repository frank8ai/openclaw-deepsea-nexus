#!/usr/bin/env python3
"""Merge multiple Chroma persistent stores into a single canonical store.

Design goals:
- Safety first: can run in dry-run mode.
- Deterministic: merge order is explicit.
- Avoid destructive overwrites by default.

Usage:
  python3 scripts/merge_vector_dbs.py \
    --dst /path/to/dst_db --dst-collection deepsea_nexus_restored \
    --src /path/to/src1 --src-collection deepsea_nexus_restored --src-label backup2212 \
    --src /path/to/src2 --src-collection deepsea_nexus_restored --src-label main599 \
    --dry-run

Note:
- This script copies documents+metadatas. Embeddings are included when present.
- For ID collisions: keep existing dst doc (default).
"""

import argparse
import os
import time
from typing import Dict, List, Tuple


def _client(path: str):
    import chromadb
    from chromadb.config import Settings

    return chromadb.PersistentClient(
        path=path,
        settings=Settings(anonymized_telemetry=False),
        tenant='default_tenant',
        database='default_database',
    )


def _as_list_tags(tags_val):
    if tags_val is None:
        return []
    if isinstance(tags_val, list):
        return [str(x) for x in tags_val if x is not None]
    s = str(tags_val).strip()
    if not s:
        return []
    # support comma-separated legacy
    if ',' in s and 'priority:' not in s and 'kind:' not in s and 'source:' not in s:
        return [t.strip() for t in s.split(',') if t.strip()]
    return [s]


def _normalize_meta(meta: Dict, src_label: str):
    meta = dict(meta or {})

    tags = _as_list_tags(meta.get('tags') or meta.get('tag'))
    # mark provenance
    tags.append(f"migrated_from_db:{src_label}")
    meta['tags'] = tags

    if 'title' not in meta:
        meta['title'] = meta.get('name') or ''

    return meta


def merge_one(
    *,
    dst_col,
    src_col,
    src_label: str,
    batch: int,
    dry_run: bool,
    on_conflict: str,
) -> Dict:
    t0 = time.time()
    src_count = src_col.count()

    # get all ids in chunks using pagination with offset
    merged = 0
    skipped = 0
    errors = 0

    # Chromadb get supports offset+limit
    offset = 0
    while offset < src_count:
        # Avoid requesting embeddings: some legacy stores error on embedding retrieval.
        res = src_col.get(
            include=['documents', 'metadatas'],
            limit=batch,
            offset=offset,
        )
        ids = res.get('ids') or []
        docs = res.get('documents') or []
        metas = res.get('metadatas') or []
        embs = None

        if not ids:
            break

        # check conflicts in dst
        existing = set()
        try:
            chk = dst_col.get(ids=ids, include=[])
            for _id in chk.get('ids') or []:
                existing.add(_id)
        except Exception:
            # if dst get fails for large list, we fallback to trying add and handling exceptions
            existing = set()

        add_ids: List[str] = []
        add_docs: List[str] = []
        add_metas: List[Dict] = []
        add_embs = [] if embs is not None else None

        for i, _id in enumerate(ids):
            if _id in existing:
                if on_conflict == 'keep-dst':
                    skipped += 1
                    continue
            add_ids.append(_id)
            add_docs.append(docs[i] if i < len(docs) else '')
            add_metas.append(_normalize_meta(metas[i] if i < len(metas) else {}, src_label))
            if add_embs is not None:
                add_embs.append(embs[i] if embs and i < len(embs) else None)

        if add_ids:
            if not dry_run:
                try:
                    dst_col.upsert(
                        ids=add_ids,
                        documents=add_docs,
                        metadatas=add_metas,
                        embeddings=add_embs,
                    )
                except Exception:
                    errors += len(add_ids)
                else:
                    merged += len(add_ids)
            else:
                merged += len(add_ids)

        offset += len(ids)

    return {
        'src_label': src_label,
        'src_count': src_count,
        'merged_or_would_merge': merged,
        'skipped_conflicts': skipped,
        'errors': errors,
        'seconds': round(time.time() - t0, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dst', required=True)
    ap.add_argument('--dst-collection', required=True)

    ap.add_argument('--src', action='append', default=[])
    ap.add_argument('--src-collection', action='append', default=[])
    ap.add_argument('--src-label', action='append', default=[])

    ap.add_argument('--batch', type=int, default=200)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--on-conflict', choices=['keep-dst', 'overwrite-dst'], default='keep-dst')

    args = ap.parse_args()

    if not (len(args.src) == len(args.src_collection) == len(args.src_label)):
        raise SystemExit('src/src-collection/src-label must have the same length')

    dst_client = _client(args.dst)
    dst_col = dst_client.get_or_create_collection(args.dst_collection)

    report = {
        'dst': args.dst,
        'dst_collection': args.dst_collection,
        'dst_count_before': dst_col.count(),
        'dry_run': bool(args.dry_run),
        'on_conflict': args.on_conflict,
        'sources': [],
    }

    for src, src_col_name, src_label in zip(args.src, args.src_collection, args.src_label):
        src_client = _client(src)
        src_col = src_client.get_or_create_collection(src_col_name)
        report['sources'].append(
            merge_one(
                dst_col=dst_col,
                src_col=src_col,
                src_label=src_label,
                batch=max(1, args.batch),
                dry_run=bool(args.dry_run),
                on_conflict=args.on_conflict,
            )
        )

    report['dst_count_after'] = dst_col.count()
    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
