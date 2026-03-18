#!/usr/bin/env python3
"""Summarize runtime middleware metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    stored = [row for row in rows if row.get("event") == "tool_event_stored"]
    skipped = sum(1 for row in rows if row.get("event") == "tool_event_skipped")
    aggregated = sum(1 for row in rows if row.get("event") == "tool_event_aggregated")
    token_before = sum(int(row.get("token_before", 0) or 0) for row in stored)
    token_after = sum(int(row.get("token_after", 0) or 0) for row in stored)
    saved_ratio = 0.0
    if token_before > 0:
        saved_ratio = round(max(0.0, (token_before - token_after) / float(token_before)), 3)
    by_kind: Dict[str, int] = {}
    for row in stored:
        key = str(row.get("event_kind") or "unknown")
        by_kind[key] = by_kind.get(key, 0) + 1
    return {
        "stored": len(stored),
        "skipped": skipped,
        "aggregated": aggregated,
        "token_before": token_before,
        "token_after": token_after,
        "saved_ratio": saved_ratio,
        "by_kind": by_kind,
        "last_event": stored[-1] if stored else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize runtime middleware metrics")
    parser.add_argument("metrics_path", nargs="?", default="logs/runtime_middleware_metrics.log")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.metrics_path).expanduser().resolve()
    summary = build_summary(load_rows(path))
    summary["metrics_path"] = str(path)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Metrics path: {path}")
        print(f"Stored: {summary['stored']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Aggregated: {summary['aggregated']}")
        print(f"Token before: {summary['token_before']}")
        print(f"Token after: {summary['token_after']}")
        print(f"Saved ratio: {summary['saved_ratio']}")
        print(f"By kind: {summary['by_kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
