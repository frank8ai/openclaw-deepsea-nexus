#!/usr/bin/env python3
"""
Context Metrics Dashboard
汇总 smart_context + context_engine 指标，生成简洁报告
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


def _read_jsonl(path: str, limit: int = 2000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def _avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / max(1, len(values))


def build_report(base_path: str, window: int = 200) -> str:
    log_dir = os.path.join(base_path, "logs")
    smart_path = os.path.join(log_dir, "smart_context_metrics.log")
    engine_path = os.path.join(log_dir, "context_engine_metrics.log")

    smart_rows = _read_jsonl(smart_path, limit=5000)
    engine_rows = _read_jsonl(engine_path, limit=5000)

    smart_recent = smart_rows[-window:]
    engine_recent = engine_rows[-window:]

    inject_rows = [r for r in smart_recent if r.get("event") == "inject"]
    topic_rows = [r for r in smart_recent if r.get("event") == "topic_switch"]
    summary_rows = [r for r in smart_recent if r.get("event") == "turn_summary"]

    ratios = [float(r.get("ratio", 0.0)) for r in inject_rows]
    injected = [int(r.get("injected", 0)) for r in inject_rows]
    retrieved = [int(r.get("retrieved", 0)) for r in inject_rows]

    engine_tokens = [int(r.get("tokens", 0)) for r in engine_recent if r.get("event") == "context_build"]
    engine_items = [int(r.get("items_used", 0)) for r in engine_recent if r.get("event") == "context_build"]
    engine_lines = [int(r.get("lines", 0)) for r in engine_recent if r.get("event") == "context_build"]

    reasons = Counter([r.get("reason", "unknown") for r in inject_rows])

    lines = []
    lines.append("# Context Metrics Dashboard")
    lines.append("")
    lines.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Window (rows): {window}")
    lines.append("")
    lines.append("## SmartContext (Inject)")
    lines.append(f"- Inject events: {len(inject_rows)}")
    lines.append(f"- Avg inject ratio: {(_avg(ratios)):.3f}")
    lines.append(f"- Avg injected: {(_avg(injected)):.2f}")
    lines.append(f"- Avg retrieved: {(_avg(retrieved)):.2f}")
    lines.append(f"- Topic switches: {len(topic_rows)}")
    lines.append(f"- Turn summaries: {len(summary_rows)}")
    if reasons:
        lines.append(f"- Top reasons: {', '.join([f'{k}({v})' for k, v in reasons.most_common(5)])}")
    lines.append("")
    lines.append("## ContextEngine (Budget)")
    lines.append(f"- Context builds: {len(engine_tokens)}")
    lines.append(f"- Avg tokens: {(_avg(engine_tokens)):.1f}")
    lines.append(f"- Avg items: {(_avg(engine_items)):.2f}")
    lines.append(f"- Avg lines: {(_avg(engine_lines)):.1f}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=str(resolve_workspace_root()))
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    report = build_report(args.base, args.window)
    print(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)


if __name__ == "__main__":
    main()
