#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from knowledge_common import append_jsonl, emit_metric, ensure_pipeline_dirs, load_policy, make_trace_id


def _recent_file(path: Path, hours: int) -> bool:
    if not path.exists():
        return False
    threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
    dt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return dt >= threshold


def _check_cron_errors() -> dict[str, Any]:
    openclaw_bin = shutil.which("openclaw")
    if not openclaw_bin:
        return {"available": False, "errors": []}

    try:
        out = subprocess.check_output([openclaw_bin, "cron", "list", "--json"], text=True, timeout=20)
        data = json.loads(out)
        jobs = data.get("jobs", [])
        errors = []
        for job in jobs:
            state = job.get("state", {})
            last = state.get("lastStatus") or state.get("lastRunStatus")
            consecutive = int(state.get("consecutiveErrors", 0) or 0)
            if last == "error" or consecutive > 0:
                errors.append(
                    {
                        "id": job.get("id"),
                        "name": job.get("name"),
                        "agent": job.get("agentId"),
                        "last": last,
                        "consecutive": consecutive,
                    }
                )
        return {"available": True, "errors": errors, "job_count": len(jobs)}
    except Exception as e:
        return {"available": True, "errors": [], "error": str(e)}


def run(policy_path: str | None = None, stale_hours: int = 24) -> dict[str, Any]:
    started = time.time()
    trace_id = make_trace_id("doctor")

    policy = load_policy(policy_path)
    dirs = ensure_pipeline_dirs(policy)
    metrics_root = dirs["metrics_root"]

    checks: list[dict[str, Any]] = []

    required_paths = {
        "inbox_raw": dirs["inbox_raw"],
        "inbox_normalized": dirs["inbox_normalized"],
        "cards_root": dirs["cards_root"],
        "moc_root": dirs["moc_root"],
        "projects_reports": dirs["projects_reports"],
    }
    for name, path in required_paths.items():
        checks.append({"check": f"path:{name}", "ok": path.exists(), "detail": str(path)})

    collect_recent = _recent_file(metrics_root / "collect-run.jsonl", stale_hours)
    curate_recent = _recent_file(metrics_root / "curate-run.jsonl", stale_hours)
    metrics_recent = _recent_file(metrics_root / "metrics-run.jsonl", stale_hours)

    checks.extend(
        [
            {"check": "collect_recent", "ok": collect_recent, "detail": f"<= {stale_hours}h"},
            {"check": "curate_recent", "ok": curate_recent, "detail": f"<= {stale_hours}h"},
            {"check": "metrics_recent", "ok": metrics_recent, "detail": f"<= {stale_hours}h"},
        ]
    )

    cron = _check_cron_errors()
    cron_errors = cron.get("errors", [])
    checks.append({"check": "cron_errors", "ok": len(cron_errors) == 0, "detail": f"count={len(cron_errors)}"})

    ok_count = sum(1 for c in checks if c["ok"])
    total = len(checks)
    healthy = ok_count == total

    recommendations: list[str] = []
    if not collect_recent:
        recommendations.append("Run knowledge_collect.py and verify source inputs.")
    if not curate_recent:
        recommendations.append("Run knowledge_curate.py to keep cards/MOC fresh.")
    if cron_errors:
        recommendations.append("Inspect OpenClaw cron jobs with lastStatus=error and consecutiveErrors > 0.")
    if healthy:
        recommendations.append("No action required. Continue scheduled execution.")

    report_path = metrics_root / f"doctor-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    report_lines = [
        f"# Knowledge Pipeline Doctor {datetime.now(timezone.utc).date().isoformat()}",
        "",
        f"- Trace: `{trace_id}`",
        f"- Health: {'HEALTHY' if healthy else 'DEGRADED'} ({ok_count}/{total})",
        "",
        "## Checks",
    ]
    for c in checks:
        report_lines.append(f"- {'OK' if c['ok'] else 'FAIL'} {c['check']}: {c['detail']}")

    report_lines.extend(["", "## Cron Errors"])
    if cron_errors:
        for e in cron_errors:
            report_lines.append(
                f"- {e.get('name')} (agent={e.get('agent')}, last={e.get('last')}, consecutive={e.get('consecutive')})"
            )
    else:
        report_lines.append("- None")

    report_lines.extend(["", "## Recommendations"])
    for r in recommendations:
        report_lines.append(f"- {r}")

    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    duration_ms = int((time.time() - started) * 1000)
    emit_metric(
        metrics_root=metrics_root,
        stage="doctor",
        trace_id=trace_id,
        duration_ms=duration_ms,
        success=healthy,
        extras={"ok_count": ok_count, "total_checks": total, "cron_error_count": len(cron_errors)},
        error_class="doctor_degraded" if not healthy else "",
    )

    summary = {
        "trace_id": trace_id,
        "healthy": healthy,
        "ok_count": ok_count,
        "total_checks": total,
        "cron_errors": cron_errors,
        "recommendations": recommendations,
        "report": str(report_path),
        "duration_ms": duration_ms,
    }
    append_jsonl(
        metrics_root / "doctor-run.jsonl",
        {"ts": datetime.now(timezone.utc).isoformat(), **summary},
    )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Health doctor for knowledge pipeline")
    parser.add_argument("--policy", default=None, help="Path to knowledge pipeline policy JSON")
    parser.add_argument("--stale-hours", type=int, default=24, help="Freshness threshold for run logs")
    args = parser.parse_args()

    result = run(policy_path=args.policy, stale_hours=args.stale_hours)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
