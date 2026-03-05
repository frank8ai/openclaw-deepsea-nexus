#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_common import (
    append_jsonl,
    classify_text,
    confidence_to_score,
    emit_metric,
    ensure_pipeline_dirs,
    load_json,
    load_policy,
    make_trace_id,
    normalize_text,
    now_iso,
    resolve_path,
    safe_title,
    score_to_confidence_label,
    stable_hash,
    write_json,
)


def _extract_text_from_summary(data: dict[str, Any]) -> str:
    fields = [
        data.get("本次核心产出"),
        data.get("summary"),
        data.get("core_output"),
        data.get("output"),
        data.get("assistant"),
        data.get("full_response"),
        data.get("response"),
    ]
    for value in fields:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return json.dumps(data, ensure_ascii=False)


def _extract_confidence(data: dict[str, Any]) -> str:
    score = confidence_to_score(data.get("confidence") or data.get("置信度") or "medium")
    return score_to_confidence_label(score)


def _collect_summary_files(pattern: str) -> list[Path]:
    expanded = str(Path(pattern).expanduser())
    return sorted([Path(p).expanduser() for p in glob.glob(expanded)])


def _collect_manual_files(raw_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for ext in ("*.md", "*.txt", "*.json"):
        paths.extend(raw_dir.rglob(ext))
    return sorted(paths)


def _fingerprint(path: Path) -> str:
    st = path.stat()
    return stable_hash(f"{path}:{st.st_mtime_ns}:{st.st_size}", length=40)


def _make_item_id(source: str, raw_text: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    h = stable_hash(source + "::" + normalize_text(raw_text), length=8)
    return f"inbox_{ts}_{h}"


def _build_item(
    source_file: Path,
    source_type: str,
    raw_text: str,
    domain: str,
    action: str,
    confidence: str,
    trace_id: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_text(raw_text)
    dedupe_key = stable_hash(f"{domain}:{action}:{normalized[:1200]}", length=24)
    item_id = _make_item_id(str(source_file), raw_text)
    payload = {
        "id": item_id,
        "source": str(source_file),
        "source_type": source_type,
        "captured_at": now_iso(),
        "raw_text": raw_text.strip(),
        "domain": domain,
        "action": action,
        "confidence": confidence,
        "trace_id": trace_id,
        "dedupe_key": dedupe_key,
        "tags": [f"domain/{domain}", f"action/{action}"],
        "title": safe_title(raw_text),
    }
    if extra:
        payload.update(extra)
    return payload


def _parse_manual_file(path: Path) -> str:
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                text = data.get("raw_text") or data.get("content") or data.get("text")
                if isinstance(text, str) and text.strip():
                    return text
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return path.read_text(encoding="utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def run(policy_path: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    started = time.time()
    trace_id = make_trace_id("collect")
    policy = load_policy(policy_path)
    dirs = ensure_pipeline_dirs(policy)
    metrics_root = dirs["metrics_root"]

    state_path = metrics_root / "collect-state.json"
    state = load_json(state_path, {"processed": {}})
    processed: dict[str, Any] = state.get("processed", {})

    summary_pattern = policy.get("paths", {}).get(
        "summary_structured_glob", "~/.openclaw/logs/summaries/structured/*.json"
    )

    summary_files = _collect_summary_files(summary_pattern)
    manual_files = _collect_manual_files(dirs["inbox_raw"])

    created = 0
    skipped = 0
    failed = 0

    # Structured summaries
    for source_file in summary_files:
        try:
            fp = _fingerprint(source_file)
            source_key = str(source_file)
            if processed.get(source_key, {}).get("fingerprint") == fp:
                skipped += 1
                continue

            data = json.loads(source_file.read_text(encoding="utf-8"))
            raw_text = _extract_text_from_summary(data)
            domain, action, _ = classify_text(raw_text + " " + json.dumps(data, ensure_ascii=False), policy)
            confidence = _extract_confidence(data)
            extra = {
                "project": data.get("project")
                or data.get("project_name")
                or data.get("项目关联")
                or "",
                "links": [v for v in [data.get("url"), data.get("source_url")] if isinstance(v, str) and v],
            }
            item = _build_item(source_file, "structured_summary", raw_text, domain, action, confidence, trace_id, extra)

            if not dry_run:
                target = dirs["inbox_normalized"] / f"{item['id']}.json"
                write_json(target, item)
                processed[source_key] = {
                    "fingerprint": fp,
                    "item_id": item["id"],
                    "updated": now_iso(),
                }
            created += 1
        except Exception:
            failed += 1

    # Manual notes
    for source_file in manual_files:
        try:
            fp = _fingerprint(source_file)
            source_key = str(source_file)
            if processed.get(source_key, {}).get("fingerprint") == fp:
                skipped += 1
                continue

            raw_text = _parse_manual_file(source_file)
            if not raw_text.strip():
                skipped += 1
                continue

            domain, action, _ = classify_text(raw_text, policy)
            confidence = "medium"
            item = _build_item(source_file, "manual_note", raw_text, domain, action, confidence, trace_id)

            if not dry_run:
                target = dirs["inbox_normalized"] / f"{item['id']}.json"
                write_json(target, item)
                processed[source_key] = {
                    "fingerprint": fp,
                    "item_id": item["id"],
                    "updated": now_iso(),
                }
            created += 1
        except Exception:
            failed += 1

    state["processed"] = processed
    if not dry_run:
        write_json(state_path, state)

    duration_ms = int((time.time() - started) * 1000)
    emit_metric(
        metrics_root=metrics_root,
        stage="collect",
        trace_id=trace_id,
        duration_ms=duration_ms,
        success=failed == 0,
        extras={
            "created": created,
            "skipped": skipped,
            "failed": failed,
            "sources_summary": len(summary_files),
            "sources_manual": len(manual_files),
        },
        error_class="collect_error" if failed else "",
    )

    run_log = {
        "ts": now_iso(),
        "trace_id": trace_id,
        "created": created,
        "skipped": skipped,
        "failed": failed,
        "sources_summary": len(summary_files),
        "sources_manual": len(manual_files),
        "duration_ms": duration_ms,
        "dry_run": dry_run,
    }
    if not dry_run:
        append_jsonl(metrics_root / "collect-run.jsonl", run_log)

    return run_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize inbox items from summaries and manual notes")
    parser.add_argument("--policy", default=None, help="Path to knowledge pipeline policy JSON")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    args = parser.parse_args()

    result = run(policy_path=args.policy, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
