#!/usr/bin/env python3
"""
Audit recent summary records across vector stores and migrate missing items
back to the canonical main store.

Outputs:
- JSON report
- Markdown summary report
- Optional rollback script (when migration inserts records)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_openclaw_workspace() -> Path:
    raw = os.environ.get("OPENCLAW_WORKSPACE")
    if raw:
        return Path(raw).expanduser().resolve()
    return (resolve_openclaw_home() / "workspace").resolve()


def default_report_dir() -> Path:
    return (REPO_ROOT / "docs" / "reports").resolve()


def ensure_chroma_importable() -> None:
    try:
        import chromadb  # noqa: F401
        return
    except Exception:
        pass

    workspace_venv = resolve_openclaw_workspace() / ".venv-nexus" / "lib"
    if workspace_venv.exists():
        for child in workspace_venv.iterdir():
            site_packages = child / "site-packages"
            if site_packages.exists():
                os.sys.path.insert(0, str(site_packages))
    try:
        import chromadb  # noqa: F401
        return
    except Exception as exc:
        raise RuntimeError(
            f"chromadb is unavailable. Use {resolve_openclaw_workspace() / '.venv-nexus' / 'bin' / 'python'} "
            "or install chromadb in current runtime."
        ) from exc


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(value)
    return str(value)


def to_iso(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    return dt.astimezone(timezone.utc).isoformat()


def parse_tags(meta: Dict[str, Any]) -> List[str]:
    tags_val = meta.get("tags")
    if tags_val is None:
        tags_val = meta.get("tag")
    if tags_val is None:
        tags_val = meta.get("labels")

    if tags_val is None:
        return []
    if isinstance(tags_val, list):
        return [normalize_text(item).strip() for item in tags_val if normalize_text(item).strip()]
    text = normalize_text(tags_val).strip()
    if not text:
        return []
    if "," in text:
        return [chunk.strip() for chunk in text.split(",") if chunk.strip()]
    return [text]


def parse_timestamp(meta: Dict[str, Any]) -> Optional[datetime]:
    candidates = [
        "indexed_at",
        "created_at",
        "updated_at",
        "timestamp",
        "ts_iso",
        "ts",
        "date",
    ]
    for key in candidates:
        if key not in meta:
            continue
        value = meta.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            raw = float(value)
            if raw > 10_000_000_000:
                raw /= 1000.0
            try:
                return datetime.fromtimestamp(raw, tz=timezone.utc)
            except Exception:
                continue
        text = normalize_text(value).strip()
        if not text:
            continue
        # Try epoch-like string
        if re.fullmatch(r"\d+(\.\d+)?", text):
            raw = float(text)
            if raw > 10_000_000_000:
                raw /= 1000.0
            try:
                return datetime.fromtimestamp(raw, tz=timezone.utc)
            except Exception:
                continue
        # Try ISO format
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def is_summary_record(content: str, meta: Dict[str, Any]) -> bool:
    title = normalize_text(meta.get("title", "")).lower()
    source_file = normalize_text(meta.get("source_file", "")).lower()
    body = normalize_text(content).lower()
    tags = [item.lower() for item in parse_tags(meta)]

    tag_hits = any(
        token in tag
        for tag in tags
        for token in (
            "summary",
            "摘要",
            "type:summary",
            "kind:summary",
            "turn_summary",
            "structured_summary",
        )
    )
    if tag_hits:
        return True
    if "摘要" in title or "summary" in title:
        return True
    if "summary" in source_file or "摘要" in source_file:
        return True
    if body.startswith("[摘要]") or "## 📋 总结" in body:
        return True
    return False


def summary_signature(title: str, content: str) -> str:
    title_norm = re.sub(r"\s+", " ", normalize_text(title).strip().lower())
    content_norm = re.sub(r"\s+", " ", normalize_text(content).strip().lower())
    raw = f"{title_norm}|{content_norm[:1600]}"
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()


def sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in (meta or {}).items():
        key_s = normalize_text(key).strip()
        if not key_s:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[key_s] = value
        elif isinstance(value, list):
            out[key_s] = ",".join([normalize_text(v).strip() for v in value if normalize_text(v).strip()])
        else:
            out[key_s] = normalize_text(value)
    return out


def discover_vector_stores(main_db: Path) -> List[Path]:
    stores: List[Path] = []
    seen = set()

    def add(path: Path) -> None:
        p = path.expanduser().resolve()
        if not p.exists() or not p.is_dir():
            return
        if str(p) in seen:
            return
        seen.add(str(p))
        stores.append(p)

    add(main_db)
    workspace_root = resolve_openclaw_workspace()
    memory_root = workspace_root / "memory"
    if memory_root.exists():
        for child in sorted(memory_root.iterdir()):
            if child.is_dir() and child.name.startswith(".vector_db"):
                add(child)
    archives_root = memory_root / "archives"
    if archives_root.exists():
        for child in sorted(archives_root.iterdir()):
            if child.is_dir() and child.name.startswith(".vector_db"):
                add(child)
    add(workspace_root / "skills" / "memory" / ".vector_db")
    return stores


def chroma_client(path: Path):
    ensure_chroma_importable()
    import chromadb
    from chromadb.config import Settings

    return chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False),
        tenant="default_tenant",
        database="default_database",
    )


def iter_collection_rows(collection, batch_size: int = 200) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
    total = int(collection.count())
    offset = 0
    while offset < total:
        data = collection.get(include=["documents", "metadatas"], limit=batch_size, offset=offset)
        ids = data.get("ids") or []
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        if not ids:
            break
        for idx, doc_id in enumerate(ids):
            content = normalize_text(docs[idx] if idx < len(docs) else "")
            meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}
            yield normalize_text(doc_id), content, dict(meta)
        offset += len(ids)


def build_record(
    *,
    db_path: Path,
    collection_name: str,
    doc_id: str,
    content: str,
    metadata: Dict[str, Any],
    timestamp: Optional[datetime],
) -> Dict[str, Any]:
    title = normalize_text(metadata.get("title", ""))
    return {
        "db_path": str(db_path),
        "collection": collection_name,
        "doc_id": doc_id,
        "title": title,
        "content": content,
        "metadata": metadata,
        "timestamp_iso": to_iso(timestamp),
        "timestamp_epoch": timestamp.timestamp() if timestamp else None,
        "signature": summary_signature(title, content),
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def generate_rollback_script(path: Path, main_db: str, main_collection: str, ids: List[str]) -> None:
    payload = json.dumps(ids, ensure_ascii=False)
    script = f"""#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import json
import chromadb
from chromadb.config import Settings

ids = json.loads({payload!r})
client = chromadb.PersistentClient(
    path={main_db!r},
    settings=Settings(anonymized_telemetry=False),
    tenant='default_tenant',
    database='default_database',
)
col = client.get_or_create_collection({main_collection!r})
if ids:
    col.delete(ids=ids)
print(json.dumps({{'rolled_back_ids': len(ids), 'collection': {main_collection!r}}}))
PY
"""
    write_text(path, script)
    os.chmod(path, 0o755)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--migrate-missing", action="store_true")
    parser.add_argument(
        "--main-db",
        default=os.environ.get(
            "NEXUS_VECTOR_DB",
            str(resolve_openclaw_workspace() / "memory" / ".vector_db_restored"),
        ),
    )
    parser.add_argument(
        "--main-collection",
        default=os.environ.get("NEXUS_COLLECTION", "deepsea_nexus_restored"),
    )
    parser.add_argument(
        "--report-dir",
        default=str(default_report_dir()),
    )
    args = parser.parse_args()

    main_db = Path(os.path.expanduser(args.main_db)).resolve()
    main_collection = str(args.main_collection).strip()
    report_dir = Path(os.path.expanduser(args.report_dir)).resolve()
    run_at = now_utc()
    run_tag = run_at.strftime("%Y%m%dT%H%M%SZ")
    cutoff = run_at - timedelta(days=max(1, int(args.days)))

    stores = discover_vector_stores(main_db)
    scanned: List[Dict[str, Any]] = []
    scan_errors: List[Dict[str, str]] = []
    records: List[Dict[str, Any]] = []

    for store in stores:
        store_entry: Dict[str, Any] = {"db_path": str(store), "collections": []}
        try:
            client = chroma_client(store)
            collections = client.list_collections()
        except Exception as exc:
            scan_errors.append({"db_path": str(store), "collection": "", "error": str(exc)})
            scanned.append(store_entry)
            continue

        for col in collections:
            name = normalize_text(getattr(col, "name", ""))
            col_entry = {"name": name, "count": 0, "summary_count": 0, "recent_summary_count": 0}
            try:
                collection = client.get_collection(name=name)
                col_entry["count"] = int(collection.count())
                for doc_id, content, metadata in iter_collection_rows(collection):
                    ts = parse_timestamp(metadata)
                    if not is_summary_record(content, metadata):
                        continue
                    rec = build_record(
                        db_path=store,
                        collection_name=name,
                        doc_id=doc_id,
                        content=content,
                        metadata=metadata,
                        timestamp=ts,
                    )
                    records.append(rec)
                    col_entry["summary_count"] += 1
                    if ts and ts >= cutoff:
                        col_entry["recent_summary_count"] += 1
            except Exception as exc:
                scan_errors.append({"db_path": str(store), "collection": name, "error": str(exc)})
            store_entry["collections"].append(col_entry)
        scanned.append(store_entry)

    main_records = [
        rec
        for rec in records
        if rec["db_path"] == str(main_db) and rec["collection"] == main_collection
    ]
    main_recent_sigs = {
        rec["signature"]
        for rec in main_records
        if rec.get("timestamp_epoch") and rec["timestamp_epoch"] >= cutoff.timestamp()
    }

    recent_non_main = [
        rec
        for rec in records
        if not (rec["db_path"] == str(main_db) and rec["collection"] == main_collection)
        and rec.get("timestamp_epoch")
        and rec["timestamp_epoch"] >= cutoff.timestamp()
    ]

    missing_by_sig: Dict[str, Dict[str, Any]] = {}
    for rec in sorted(recent_non_main, key=lambda item: item.get("timestamp_epoch") or 0, reverse=True):
        sig = rec["signature"]
        if sig in main_recent_sigs:
            continue
        if sig in missing_by_sig:
            continue
        missing_by_sig[sig] = rec
    missing = list(missing_by_sig.values())

    migration: Dict[str, Any] = {
        "enabled": bool(args.migrate_missing),
        "attempted": len(missing),
        "inserted": 0,
        "failed": 0,
        "inserted_ids": [],
        "errors": [],
        "main_count_before": None,
        "main_count_after": None,
    }

    if args.migrate_missing and missing:
        client = chroma_client(main_db)
        main_col = client.get_or_create_collection(main_collection)
        migration["main_count_before"] = int(main_col.count())
        migrated_at = run_at.isoformat()

        for idx, rec in enumerate(missing, start=1):
            orig_meta = rec.get("metadata", {}) if isinstance(rec.get("metadata", {}), dict) else {}
            meta = sanitize_metadata(orig_meta)
            source_key = f"{Path(rec['db_path']).name}:{rec['collection']}"
            tags = parse_tags(meta)
            tags.append("migrated:recent-summary")
            tags.append(f"migrated_from:{source_key}")
            meta["tags"] = ",".join([item for item in tags if item])
            meta["migrated_from_db"] = rec["db_path"]
            meta["migrated_from_collection"] = rec["collection"]
            meta["migrated_from_id"] = rec["doc_id"]
            meta["migrated_at"] = migrated_at

            base_id = re.sub(r"[^a-zA-Z0-9_-]", "", normalize_text(rec["doc_id"]))[:40] or f"idx{idx}"
            target_id = f"migrated_{run_tag}_{idx}_{base_id}"
            try:
                main_col.upsert(ids=[target_id], documents=[rec["content"]], metadatas=[meta])
                verify = main_col.get(ids=[target_id], include=[])
                verify_ids = verify.get("ids") or []
                if target_id in verify_ids:
                    migration["inserted_ids"].append(target_id)
                    migration["inserted"] += 1
                else:
                    migration["failed"] += 1
                    migration["errors"].append(
                        {"target_id": target_id, "reason": "verify_miss", "source_id": rec["doc_id"]}
                    )
            except Exception as exc:
                migration["failed"] += 1
                migration["errors"].append(
                    {"target_id": target_id, "reason": str(exc), "source_id": rec["doc_id"]}
                )
        migration["main_count_after"] = int(main_col.count())
    elif args.migrate_missing:
        client = chroma_client(main_db)
        main_col = client.get_or_create_collection(main_collection)
        migration["main_count_before"] = int(main_col.count())
        migration["main_count_after"] = int(main_col.count())

    recent_distribution: Dict[str, int] = defaultdict(int)
    for rec in records:
        if rec.get("timestamp_epoch") and rec["timestamp_epoch"] >= cutoff.timestamp():
            key = f"{Path(rec['db_path']).name}:{rec['collection']}"
            recent_distribution[key] += 1

    report = {
        "run_at": run_at.isoformat(),
        "cutoff_days": int(args.days),
        "cutoff_iso": cutoff.isoformat(),
        "main_db": str(main_db),
        "main_collection": main_collection,
        "scanned_stores": scanned,
        "scan_errors": scan_errors,
        "summary_records_total": len(records),
        "summary_records_main": len(main_records),
        "recent_summary_distribution": dict(sorted(recent_distribution.items(), key=lambda item: item[0])),
        "recent_non_main_missing_candidates": len(missing),
        "missing_candidates_preview": [
            {
                "db_path": rec["db_path"],
                "collection": rec["collection"],
                "doc_id": rec["doc_id"],
                "title": rec["title"],
                "timestamp_iso": rec["timestamp_iso"],
            }
            for rec in missing[:50]
        ],
        "migration": migration,
        "rollback": {
            "available": bool(migration["inserted_ids"]),
            "rollback_script": "",
        },
    }

    report_json_path = report_dir / f"summary_audit_{run_tag}.json"
    report_md_path = report_dir / f"summary_audit_{run_tag}.md"
    rollback_path = report_dir / f"summary_audit_{run_tag}_rollback.sh"

    if migration["inserted_ids"]:
        generate_rollback_script(
            rollback_path,
            str(main_db),
            main_collection,
            list(migration["inserted_ids"]),
        )
        report["rollback"]["rollback_script"] = str(rollback_path)

    write_text(report_json_path, json.dumps(report, ensure_ascii=False, indent=2))

    md_lines = [
        f"# Summary Audit Report ({run_tag})",
        "",
        f"- run_at: `{run_at.isoformat()}`",
        f"- cutoff_days: `{args.days}`",
        f"- main_db: `{main_db}`",
        f"- main_collection: `{main_collection}`",
        f"- summary_records_total: `{len(records)}`",
        f"- summary_records_main: `{len(main_records)}`",
        f"- recent_non_main_missing_candidates: `{len(missing)}`",
        "",
        "## Recent Distribution",
    ]
    if recent_distribution:
        for key, count in sorted(recent_distribution.items(), key=lambda item: item[0]):
            md_lines.append(f"- `{key}`: `{count}`")
    else:
        md_lines.append("- (none)")

    md_lines.extend(
        [
            "",
            "## Migration",
            f"- enabled: `{bool(args.migrate_missing)}`",
            f"- attempted: `{migration['attempted']}`",
            f"- inserted: `{migration['inserted']}`",
            f"- failed: `{migration['failed']}`",
            f"- main_count_before: `{migration['main_count_before']}`",
            f"- main_count_after: `{migration['main_count_after']}`",
        ]
    )
    if report["rollback"]["rollback_script"]:
        md_lines.append(f"- rollback_script: `{report['rollback']['rollback_script']}`")

    if scan_errors:
        md_lines.extend(["", "## Scan Errors"])
        for item in scan_errors[:50]:
            md_lines.append(
                f"- `{item.get('db_path', '')}` / `{item.get('collection', '')}`: {item.get('error', '')}"
            )

    write_text(report_md_path, "\n".join(md_lines) + "\n")

    print(
        json.dumps(
            {
                "report_json": str(report_json_path),
                "report_md": str(report_md_path),
                "rollback_script": str(rollback_path) if rollback_path.exists() else "",
                "missing_candidates": len(missing),
                "migrated": migration["inserted"],
                "main_count_after": migration["main_count_after"],
                "scan_errors": len(scan_errors),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
