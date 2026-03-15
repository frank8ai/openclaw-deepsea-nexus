#!/usr/bin/env python3
"""Batch backfill runner for memory_v5 archive_after_days defaults.

This script intentionally only applies archive-default backfill.
It does not execute archive moves.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SKILL_ROOT not in sys.path:
    sys.path.insert(0, SKILL_ROOT)
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from memory_v5 import MemoryScope, MemoryV5Service
import memory_v5_maintenance


def _scope_payload(scope: MemoryScope) -> Dict[str, str]:
    return {
        "agent_id": scope.agent_id,
        "user_id": scope.user_id,
        "app_id": scope.app_id,
        "run_id": scope.run_id,
        "workspace": scope.workspace,
    }


def _scope_label(payload: Dict[str, str]) -> str:
    agent = str(payload.get("agent_id") or "default")
    user = str(payload.get("user_id") or "default")
    qualifiers = []
    app = str(payload.get("app_id") or "")
    run = str(payload.get("run_id") or "")
    workspace = str(payload.get("workspace") or "")
    if app:
        qualifiers.append(f"app={app}")
    if run:
        qualifiers.append(f"run={run}")
    if workspace:
        qualifiers.append(f"workspace={workspace}")
    if qualifiers:
        return f"{agent}/{user} ({', '.join(qualifiers)})"
    return f"{agent}/{user}"


def default_report_dir() -> Path:
    return (Path(SKILL_ROOT).resolve() / "docs" / "reports").resolve()


def _build_default_report_paths(report_dir: str | Path, generated_at: str) -> tuple[Path, Path]:
    report_root = Path(os.path.expanduser(str(report_dir))).resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    tag = generated_at.replace("-", "").replace(":", "").replace("+00:00", "Z")
    tag = tag.replace(".", "_")
    base = report_root / f"memory_v5_backfill_{tag}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(payload: Dict[str, Any]) -> str:
    totals = payload.get("totals", {}) or {}
    lines = [
        "# Memory V5 Archive-Default Backfill",
        "",
        f"- Generated at: {payload.get('generated_at', '')}",
        f"- Apply mode: {payload.get('apply', False)}",
        f"- Batch size: {payload.get('batch_size', 0)}",
        f"- Max batches: {payload.get('max_batches', 0)}",
        f"- Scope count: {payload.get('scope_count', 0)}",
        "",
        "## Totals",
        f"- Matched: {totals.get('matched', 0)}",
        f"- Selected: {totals.get('selected', 0)}",
        f"- Updated: {totals.get('updated', 0)}",
        f"- Failed: {totals.get('failed', 0)}",
        f"- Batches run: {totals.get('batches_run', 0)}",
        f"- Remaining candidates: {totals.get('remaining', 0)}",
        "",
        "## Scopes",
    ]
    for scope_entry in payload.get("scopes", []) or []:
        scope = scope_entry.get("scope", {}) or {}
        scope_name = _scope_label(scope)
        summary = scope_entry.get("summary", {}) or {}
        lines.extend(
            [
                f"### {scope_name}",
                f"- Matched: {summary.get('matched', 0)}",
                f"- Selected: {summary.get('selected', 0)}",
                f"- Updated: {summary.get('updated', 0)}",
                f"- Failed: {summary.get('failed', 0)}",
                f"- Batches run: {summary.get('batches_run', 0)}",
                f"- Remaining candidates: {summary.get('remaining', 0)}",
            ]
        )
        for batch in scope_entry.get("batches", []) or []:
            lines.extend(
                [
                    f"- Batch {batch.get('batch', 0)} "
                    f"(matched_before={batch.get('matched_before', 0)}, "
                    f"selected={batch.get('selected', 0)}, "
                    f"updated={batch.get('updated', 0)}, "
                    f"failed={batch.get('failed', 0)})",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _resolve_scopes(service: MemoryV5Service, *, agent: str, user: str, all_agents: bool) -> List[MemoryScope]:
    scopes: List[MemoryScope] = [MemoryScope(agent_id=agent, user_id=user)]
    if all_agents:
        scopes = list(memory_v5_maintenance.iter_scopes(service.root)) or scopes
    return scopes


def _scope_backfill_batches(
    service: MemoryV5Service,
    *,
    scope: MemoryScope,
    now_ts: str,
    apply: bool,
    batch_size: int,
    max_batches: int,
    continue_on_failure: bool,
) -> Dict[str, Any]:
    batches: List[Dict[str, Any]] = []
    matched_total = 0
    selected_total = 0
    updated_total = 0
    failed_total = 0
    remaining = 0

    for idx in range(1, max_batches + 1):
        preview = service.backfill_archive_defaults(
            scope=scope,
            now_ts=now_ts,
            max_items=batch_size,
            dry_run=True,
        )
        matched_before = int(preview.get("matched", 0) or 0)
        selected = int(preview.get("selected", 0) or 0)
        candidate_ids = list(preview.get("candidate_ids", []) or [])

        if idx == 1:
            matched_total = matched_before
        if selected <= 0:
            remaining = matched_before
            break

        if not apply:
            selected_total += selected
            remaining = matched_before
            batches.append(
                {
                    "batch": idx,
                    "mode": "preview",
                    "matched_before": matched_before,
                    "selected": selected,
                    "updated": 0,
                    "failed": 0,
                    "candidate_ids": candidate_ids,
                    "updated_ids": [],
                    "failed_ids": [],
                }
            )
            break

        applied = service.backfill_archive_defaults(
            scope=scope,
            now_ts=now_ts,
            max_items=batch_size,
            dry_run=False,
        )
        updated = int(applied.get("updated", 0) or 0)
        failed = int(applied.get("failed", 0) or 0)
        updated_ids = list(applied.get("updated_ids", []) or [])
        failed_ids = list(applied.get("failed_ids", []) or [])

        selected_total += selected
        updated_total += updated
        failed_total += failed
        batches.append(
            {
                "batch": idx,
                "mode": "apply",
                "matched_before": matched_before,
                "selected": selected,
                "updated": updated,
                "failed": failed,
                "candidate_ids": candidate_ids,
                "updated_ids": updated_ids,
                "failed_ids": failed_ids,
            }
        )
        if failed > 0 and not continue_on_failure:
            remaining = max(0, matched_before - updated)
            break

        probe = service.backfill_archive_defaults(
            scope=scope,
            now_ts=now_ts,
            max_items=1,
            dry_run=True,
        )
        remaining = int(probe.get("matched", 0) or 0)
        if remaining <= 0:
            break

    return {
        "scope": _scope_payload(scope),
        "summary": {
            "matched": matched_total,
            "selected": selected_total,
            "updated": updated_total,
            "failed": failed_total,
            "batches_run": len(batches),
            "remaining": remaining,
        },
        "batches": batches,
    }


def run(
    *,
    config: Optional[dict] = None,
    agent: str = "default",
    user: str = "default",
    all_agents: bool = False,
    apply: bool = False,
    batch_size: int = 100,
    max_batches: int = 10,
    continue_on_failure: bool = False,
    now_ts: Optional[str] = None,
    json_out: Optional[str] = None,
    md_out: Optional[str] = None,
    write_report: bool = False,
    report_dir: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = config if isinstance(config, dict) else memory_v5_maintenance.load_config()
    if isinstance(cfg, dict):
        mem_cfg = cfg.get("memory_v5", {}) if isinstance(cfg.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        cfg["memory_v5"] = mem_cfg
    service = MemoryV5Service(cfg)
    scopes = _resolve_scopes(service, agent=agent, user=user, all_agents=all_agents)

    generated_at = now_ts or datetime.now(timezone.utc).isoformat()
    batch_size = max(1, int(batch_size))
    max_batches = max(1, int(max_batches))

    scope_results = [
        _scope_backfill_batches(
            service,
            scope=scope,
            now_ts=generated_at,
            apply=bool(apply),
            batch_size=batch_size,
            max_batches=max_batches,
            continue_on_failure=bool(continue_on_failure),
        )
        for scope in scopes
    ]

    totals = {
        "matched": sum(int((entry.get("summary", {}) or {}).get("matched", 0) or 0) for entry in scope_results),
        "selected": sum(int((entry.get("summary", {}) or {}).get("selected", 0) or 0) for entry in scope_results),
        "updated": sum(int((entry.get("summary", {}) or {}).get("updated", 0) or 0) for entry in scope_results),
        "failed": sum(int((entry.get("summary", {}) or {}).get("failed", 0) or 0) for entry in scope_results),
        "batches_run": sum(int((entry.get("summary", {}) or {}).get("batches_run", 0) or 0) for entry in scope_results),
        "remaining": sum(int((entry.get("summary", {}) or {}).get("remaining", 0) or 0) for entry in scope_results),
    }

    payload = {
        "generated_at": generated_at,
        "apply": bool(apply),
        "batch_size": batch_size,
        "max_batches": max_batches,
        "continue_on_failure": bool(continue_on_failure),
        "scope_count": len(scope_results),
        "totals": totals,
        "scopes": scope_results,
    }

    resolved_json_out = json_out
    resolved_md_out = md_out
    if write_report and not resolved_json_out and not resolved_md_out:
        json_path, md_path = _build_default_report_paths(report_dir or default_report_dir(), generated_at)
        resolved_json_out = str(json_path)
        resolved_md_out = str(md_path)

    artifacts: Dict[str, str] = {}
    if resolved_json_out:
        out_path = Path(os.path.expanduser(resolved_json_out)).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts["json"] = str(out_path)
    if resolved_md_out:
        out_path = Path(os.path.expanduser(resolved_md_out)).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_markdown(payload), encoding="utf-8")
        artifacts["markdown"] = str(out_path)
    if artifacts:
        payload["artifacts"] = artifacts
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run explicit memory_v5 archive-default backfill in bounded batches.",
    )
    parser.add_argument("--agent", default="default")
    parser.add_argument("--user", default="default")
    parser.add_argument("--all-agents", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--max-batches", type=int, default=10)
    parser.add_argument("--continue-on-failure", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-dir", default=str(default_report_dir()))
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--md-out", default=None)
    args = parser.parse_args()

    result = run(
        agent=args.agent,
        user=args.user,
        all_agents=bool(args.all_agents),
        apply=bool(args.apply),
        batch_size=args.batch_size,
        max_batches=args.max_batches,
        continue_on_failure=bool(args.continue_on_failure),
        write_report=bool(args.write_report),
        report_dir=args.report_dir,
        json_out=args.json_out,
        md_out=args.md_out,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
