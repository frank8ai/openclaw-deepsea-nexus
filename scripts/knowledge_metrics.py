#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from knowledge_common import append_jsonl, emit_metric, ensure_pipeline_dirs, load_json, load_policy, make_trace_id


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _collect_metric_rows(metrics_root: Path, lookback_days: int) -> list[dict[str, Any]]:
    threshold = date.today() - timedelta(days=max(0, lookback_days - 1))
    rows: list[dict[str, Any]] = []
    for file in sorted(metrics_root.glob("metrics-*.jsonl")):
        try:
            d = date.fromisoformat(file.stem.replace("metrics-", ""))
        except Exception:
            continue
        if d < threshold:
            continue
        rows.extend(_load_jsonl(file))
    return rows


def run(policy_path: str | None = None, lookback_days: int = 7) -> dict[str, Any]:
    started = time.time()
    trace_id = make_trace_id("metrics")

    policy = load_policy(policy_path)
    dirs = ensure_pipeline_dirs(policy)
    metrics_root = dirs["metrics_root"]

    rows = _collect_metric_rows(metrics_root, lookback_days=lookback_days)
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("stage", "unknown"))].append(row)

    summary: dict[str, Any] = {
        "trace_id": trace_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": lookback_days,
        "events": len(rows),
        "stages": {},
    }

    for stage, stage_rows in by_stage.items():
        success_count = sum(1 for r in stage_rows if r.get("success") is True)
        fail_count = sum(1 for r in stage_rows if r.get("success") is False)
        duration_values = [int(r.get("duration_ms", 0)) for r in stage_rows if isinstance(r.get("duration_ms"), (int, float))]
        token_values = [int(r.get("tokens", 0)) for r in stage_rows if isinstance(r.get("tokens"), (int, float))]
        avg_duration = int(sum(duration_values) / len(duration_values)) if duration_values else 0
        p95_duration = sorted(duration_values)[int(len(duration_values) * 0.95) - 1] if len(duration_values) > 1 else (duration_values[0] if duration_values else 0)
        summary["stages"][stage] = {
            "events": len(stage_rows),
            "success": success_count,
            "failed": fail_count,
            "success_rate": round((success_count / len(stage_rows)) * 100, 2) if stage_rows else 0.0,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": max(0, p95_duration),
            "tokens_total": sum(token_values),
        }

    collect_runs = _load_jsonl(metrics_root / "collect-run.jsonl")
    curate_runs = _load_jsonl(metrics_root / "curate-run.jsonl")
    analyze_runs = _load_jsonl(metrics_root / "analyze-run.jsonl")

    collect_recent = collect_runs[-14:]
    curate_recent = curate_runs[-14:]
    analyze_recent = analyze_runs[-8:]

    collect_seen = sum(int(r.get("created", 0)) + int(r.get("skipped", 0)) + int(r.get("failed", 0)) for r in collect_recent)
    collect_ok = sum(int(r.get("created", 0)) + int(r.get("skipped", 0)) for r in collect_recent)
    collect_success_rate = round((collect_ok / collect_seen) * 100, 2) if collect_seen else 0.0

    total_curated = sum(int(r.get("created", 0)) + int(r.get("deduped", 0)) for r in curate_recent)
    total_deduped = sum(int(r.get("deduped", 0)) for r in curate_recent)
    card_reuse_rate = round((total_deduped / total_curated) * 100, 2) if total_curated else 0.0

    avg_weekly_report_ms = 0
    if analyze_recent:
        avg_weekly_report_ms = int(
            sum(int(r.get("duration_ms", 0)) for r in analyze_recent) / len(analyze_recent)
        )

    summary["kpi"] = {
        "collect_success_rate": collect_success_rate,
        "card_reuse_rate": card_reuse_rate,
        "weekly_report_avg_duration_ms": avg_weekly_report_ms,
        "collect_runs": len(collect_recent),
        "curate_runs": len(curate_recent),
        "analyze_runs": len(analyze_recent),
    }

    dashboard_json = metrics_root / f"dashboard-{date.today().isoformat()}.json"
    dashboard_md = metrics_root / f"dashboard-{date.today().isoformat()}.md"

    dashboard_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# Knowledge Pipeline Dashboard {date.today().isoformat()}",
        "",
        f"- Trace: `{trace_id}`",
        f"- Lookback: {lookback_days} days",
        f"- Events: {summary['events']}",
        "",
        "## KPI",
        f"- Collect success rate: {collect_success_rate}%",
        f"- Card reuse rate: {card_reuse_rate}%",
        f"- Weekly report average duration: {avg_weekly_report_ms} ms",
        "",
        "## Stage Metrics",
    ]

    for stage, data in summary["stages"].items():
        md_lines.extend(
            [
                f"### {stage}",
                f"- Events: {data['events']}",
                f"- Success rate: {data['success_rate']}%",
                f"- Avg duration: {data['avg_duration_ms']} ms",
                f"- P95 duration: {data['p95_duration_ms']} ms",
                f"- Tokens total: {data['tokens_total']}",
                "",
            ]
        )

    dashboard_md.write_text("\n".join(md_lines), encoding="utf-8")

    duration_ms = int((time.time() - started) * 1000)
    emit_metric(
        metrics_root=metrics_root,
        stage="metrics",
        trace_id=trace_id,
        duration_ms=duration_ms,
        success=True,
        extras={
            "lookback_days": lookback_days,
            "collect_success_rate": collect_success_rate,
            "card_reuse_rate": card_reuse_rate,
            "weekly_report_avg_duration_ms": avg_weekly_report_ms,
        },
    )
    append_jsonl(
        metrics_root / "metrics-run.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "dashboard_json": str(dashboard_json),
            "dashboard_md": str(dashboard_md),
            "duration_ms": duration_ms,
            "lookback_days": lookback_days,
        },
    )

    return {
        "trace_id": trace_id,
        "dashboard_json": str(dashboard_json),
        "dashboard_md": str(dashboard_md),
        "duration_ms": duration_ms,
        "kpi": summary["kpi"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate knowledge pipeline metrics")
    parser.add_argument("--policy", default=None, help="Path to knowledge pipeline policy JSON")
    parser.add_argument("--lookback-days", type=int, default=7, help="Number of days to aggregate")
    args = parser.parse_args()

    result = run(policy_path=args.policy, lookback_days=args.lookback_days)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
