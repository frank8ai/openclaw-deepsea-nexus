#!/usr/bin/env python3
"""Maintenance for memory_v5 lifecycle audit and explicit archive moves."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service, MemoryScope


DEFAULT_LIFECYCLE_ALERTS = {
    "enabled": True,
    "archive_due_warn": 1,
    "archive_due_critical": 10,
    "ttl_expired_warn": 1,
    "ttl_expired_critical": 10,
    "archive_backfill_candidates_warn": 1,
    "archive_backfill_candidates_critical": 100,
    "decaying_ratio_warn": 0.6,
    "decaying_ratio_critical": 0.85,
    "archive_failed_warn": 1,
    "archive_failed_critical": 1,
    "backfill_failed_warn": 1,
    "backfill_failed_critical": 1,
}

SEVERITY_RANK = {
    "healthy": 0,
    "warn": 1,
    "critical": 2,
}


def load_config() -> dict:
    config_path = os.path.join(SKILL_ROOT, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def default_report_dir() -> Path:
    return (Path(SKILL_ROOT).resolve() / "docs" / "reports").resolve()


def iter_scopes(root: str):
    if not os.path.isdir(root):
        return []
    scopes = []
    for agent in os.listdir(root):
        agent_dir = os.path.join(root, agent)
        if not os.path.isdir(agent_dir):
            continue
        for user in os.listdir(agent_dir):
            user_dir = os.path.join(agent_dir, user)
            if not os.path.isdir(user_dir):
                continue
            scopes.append(MemoryScope(agent_id=agent, user_id=user))
    return scopes


def _scope_payload(scope: MemoryScope) -> Dict[str, str]:
    return {
        "agent_id": scope.agent_id,
        "user_id": scope.user_id,
        "app_id": scope.app_id,
        "run_id": scope.run_id,
        "workspace": scope.workspace,
    }


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _scope_name(scope_payload: Dict[str, Any]) -> str:
    return f"{scope_payload.get('agent_id', 'default')}/{scope_payload.get('user_id', 'default')}"


def _resolve_lifecycle_alerts(config: Optional[dict], enable_alerts: Optional[bool] = None) -> Dict[str, Any]:
    resolved = dict(DEFAULT_LIFECYCLE_ALERTS)
    memory_cfg = {}
    if isinstance(config, dict):
        raw_memory_cfg = config.get("memory_v5", {})
        if isinstance(raw_memory_cfg, dict):
            memory_cfg = raw_memory_cfg
    raw = memory_cfg.get("lifecycle_alerts", {})
    if isinstance(raw, dict):
        for key in DEFAULT_LIFECYCLE_ALERTS:
            if key in raw:
                if key == "enabled":
                    resolved[key] = bool(raw[key])
                elif "ratio" in key:
                    resolved[key] = _safe_float(raw[key], resolved[key])
                else:
                    resolved[key] = _safe_int(raw[key], resolved[key])
    if enable_alerts is not None:
        resolved["enabled"] = bool(enable_alerts)
    return resolved


def _sample_briefs(audit: Dict[str, Any], bucket: str, limit: int = 3) -> List[Dict[str, Any]]:
    rows = (audit.get("samples", {}) or {}).get(bucket, []) or []
    briefs = []
    for row in rows[:limit]:
        briefs.append(
            {
                "id": str(row.get("id", "")),
                "title": str(row.get("title", "")),
                "kind": str(row.get("kind", "")),
                "age_days": round(_safe_float(row.get("age_days", 0.0), 0.0), 3),
            }
        )
    return briefs


def _severity_for_metric(actual: float, warn: float, critical: float) -> Optional[str]:
    critical = max(float(critical), float(warn))
    if actual >= critical:
        return "critical"
    if actual >= warn:
        return "warn"
    return None


def _make_alert(
    *,
    scope: Dict[str, Any],
    metric: str,
    severity: str,
    actual: float,
    warn_threshold: float,
    critical_threshold: float,
    message: str,
) -> Dict[str, Any]:
    return {
        "scope": scope,
        "scope_name": _scope_name(scope),
        "metric": metric,
        "severity": severity,
        "actual": actual,
        "warn_threshold": warn_threshold,
        "critical_threshold": critical_threshold,
        "message": message,
    }


def _build_recommendations(alerts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    actions: Dict[str, Dict[str, str]] = {}
    for alert in alerts:
        metric = str(alert.get("metric", ""))
        if metric in {"archive_due", "ttl_expired"}:
            actions.setdefault(
                "explicit_archive",
                {
                    "kind": "explicit_archive",
                    "message": "Review archive-due / TTL-expired candidates, then rerun maintenance without --dry-run for the affected scopes.",
                    "command": "python3 scripts/memory_v5_maintenance.py --write-report",
                },
            )
        elif metric == "archive_backfill_candidates":
            actions.setdefault(
                "archive_backfill",
                {
                    "kind": "archive_backfill",
                    "message": "Older rows still have unresolved archive defaults; run the dedicated backfill batches before expecting archive_due counts to settle.",
                    "command": "python3 scripts/memory_v5_backfill_batches.py --batch-size 100 --max-batches 5 --write-report",
                },
            )
        elif metric == "decaying_ratio":
            actions.setdefault(
                "decay_review",
                {
                    "kind": "decay_review",
                    "message": "Inspect decaying samples for stale decisions or overdue summaries; this scope is drifting toward weak recall quality.",
                    "command": "python3 scripts/memory_v5_maintenance.py --dry-run --write-report",
                },
            )
        elif metric in {"archive_failed", "backfill_failed"}:
            actions.setdefault(
                "investigate_failures",
                {
                    "kind": "investigate_failures",
                    "message": "Maintenance writes failed; inspect item paths, permissions, and SQLite/index consistency before retrying.",
                    "command": "python3 scripts/memory_v5_maintenance.py --dry-run --write-report",
                },
            )
    return list(actions.values())


def _evaluate_scope_health(
    scope_payload: Dict[str, Any],
    audit: Dict[str, Any],
    archive: Dict[str, Any],
    backfill: Dict[str, Any],
    thresholds: Dict[str, Any],
) -> Dict[str, Any]:
    counts = audit.get("counts", {}) or {}
    total = max(
        0,
        _safe_int(counts.get("active", 0), 0)
        + _safe_int(counts.get("ttl_expired", 0), 0)
        + _safe_int(counts.get("archive_due", 0), 0),
    )
    if total <= 0:
        total = max(
            0,
            _safe_int(counts.get("total", 0), 0) - _safe_int(counts.get("archived", 0), 0),
        )
    decaying_ratio = (
        _safe_float(counts.get("decaying", 0), 0.0) / float(total)
        if total > 0
        else 0.0
    )

    alerts: List[Dict[str, Any]] = []
    if thresholds.get("enabled", True):
        metric_specs = [
            (
                "archive_due",
                float(_safe_int(counts.get("archive_due", 0), 0)),
                float(_safe_int(thresholds.get("archive_due_warn", 1), 1)),
                float(_safe_int(thresholds.get("archive_due_critical", 10), 10)),
                lambda actual: f"{_scope_name(scope_payload)} has {int(actual)} archive-due items waiting for explicit archive.",
            ),
            (
                "ttl_expired",
                float(_safe_int(counts.get("ttl_expired", 0), 0)),
                float(_safe_int(thresholds.get("ttl_expired_warn", 1), 1)),
                float(_safe_int(thresholds.get("ttl_expired_critical", 10), 10)),
                lambda actual: f"{_scope_name(scope_payload)} has {int(actual)} TTL-expired items still in active storage.",
            ),
            (
                "archive_backfill_candidates",
                float(_safe_int(counts.get("archive_backfill_candidates", 0), 0)),
                float(_safe_int(thresholds.get("archive_backfill_candidates_warn", 1), 1)),
                float(_safe_int(thresholds.get("archive_backfill_candidates_critical", 100), 100)),
                lambda actual: f"{_scope_name(scope_payload)} has {int(actual)} rows with unresolved archive defaults.",
            ),
            (
                "decaying_ratio",
                decaying_ratio,
                float(_safe_float(thresholds.get("decaying_ratio_warn", 0.6), 0.6)),
                float(_safe_float(thresholds.get("decaying_ratio_critical", 0.85), 0.85)),
                lambda actual: f"{_scope_name(scope_payload)} has {actual:.1%} decaying live memory.",
            ),
            (
                "archive_failed",
                float(_safe_int(archive.get("failed", 0), 0)),
                float(_safe_int(thresholds.get("archive_failed_warn", 1), 1)),
                float(_safe_int(thresholds.get("archive_failed_critical", 1), 1)),
                lambda actual: f"{_scope_name(scope_payload)} had {int(actual)} failed archive moves in this run.",
            ),
            (
                "backfill_failed",
                float(_safe_int(backfill.get("failed", 0), 0)),
                float(_safe_int(thresholds.get("backfill_failed_warn", 1), 1)),
                float(_safe_int(thresholds.get("backfill_failed_critical", 1), 1)),
                lambda actual: f"{_scope_name(scope_payload)} had {int(actual)} failed archive-default backfills in this run.",
            ),
        ]
        for metric, actual, warn_threshold, critical_threshold, message_fn in metric_specs:
            severity = _severity_for_metric(actual, warn_threshold, critical_threshold)
            if severity:
                alerts.append(
                    _make_alert(
                        scope=scope_payload,
                        metric=metric,
                        severity=severity,
                        actual=actual,
                        warn_threshold=warn_threshold,
                        critical_threshold=critical_threshold,
                        message=message_fn(actual),
                    )
                )

    level = "healthy"
    for alert in alerts:
        if SEVERITY_RANK[str(alert["severity"])] > SEVERITY_RANK[level]:
            level = str(alert["severity"])
    return {
        "level": level,
        "decaying_ratio": round(decaying_ratio, 4),
        "alerts": alerts,
        "samples": {
            "archive_due": _sample_briefs(audit, "archive_due"),
            "ttl_expired": _sample_briefs(audit, "ttl_expired"),
            "decaying": _sample_briefs(audit, "decaying"),
            "archive_backfill_candidates": _sample_briefs(audit, "archive_backfill_candidates"),
        },
    }


def _format_sample_line(label: str, rows: List[Dict[str, Any]]) -> Optional[str]:
    if not rows:
        return None
    rendered = ", ".join(
        f"{row.get('title') or row.get('id')} ({row.get('id')}, {row.get('age_days', 0)}d)"
        for row in rows
    )
    return f"- {label}: {rendered}"


def render_markdown(payload: Dict[str, Any]) -> str:
    totals = payload.get("totals", {}) or {}
    status = payload.get("status", {}) or {}
    scope_status_counts = payload.get("scope_status_counts", {}) or {}
    lines = [
        "# Memory V5 Lifecycle Maintenance",
        "",
        f"- Generated at: {payload.get('generated_at', '')}",
        f"- Dry run: {payload.get('dry_run', False)}",
        f"- Include TTL expired: {payload.get('include_ttl_expired', False)}",
        f"- Apply archive backfill: {payload.get('apply_archive_backfill', False)}",
        f"- Alerts enabled: {payload.get('alerts_enabled', True)}",
        f"- Overall status: {str(status.get('level', 'healthy')).upper()}",
        f"- Scope count: {payload.get('scope_count', 0)}",
        f"- Checked: {payload.get('checked', 0)}",
        f"- Archived in run: {payload.get('archived', 0)}",
        "",
        "## Status Summary",
        f"- Healthy scopes: {scope_status_counts.get('healthy', 0)}",
        f"- Warn scopes: {scope_status_counts.get('warn', 0)}",
        f"- Critical scopes: {scope_status_counts.get('critical', 0)}",
        "",
        "## Alerts",
    ]
    alerts = payload.get("alerts", []) or []
    if alerts:
        for alert in alerts:
            actual = alert.get("actual", 0)
            if str(alert.get("metric", "")) == "decaying_ratio":
                actual_repr = f"{float(actual):.1%}"
            else:
                actual_repr = str(int(actual))
            lines.append(
                f"- {str(alert.get('severity', 'warn')).upper()} {alert.get('scope_name', '')} "
                f"{alert.get('metric', '')}={actual_repr}: {alert.get('message', '')}"
            )
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Hot Scopes",
        ]
    )
    hot_scopes = payload.get("hot_scopes", []) or []
    if hot_scopes:
        for scope_entry in hot_scopes:
            lines.extend(
                [
                    f"### {scope_entry.get('scope_name', '')}",
                    f"- Status: {str(scope_entry.get('status', 'healthy')).upper()}",
                    f"- Archive due: {scope_entry.get('counts', {}).get('archive_due', 0)}",
                    f"- TTL expired: {scope_entry.get('counts', {}).get('ttl_expired', 0)}",
                    f"- Decaying ratio: {float(scope_entry.get('decaying_ratio', 0.0)):.1%}",
                    f"- Archive backfill candidates: {scope_entry.get('counts', {}).get('archive_backfill_candidates', 0)}",
                ]
            )
            for label, key in (
                ("Archive due samples", "archive_due"),
                ("TTL expired samples", "ttl_expired"),
                ("Decaying samples", "decaying"),
                ("Backfill samples", "archive_backfill_candidates"),
            ):
                sample_line = _format_sample_line(label, (scope_entry.get("samples", {}) or {}).get(key, []) or [])
                if sample_line:
                    lines.append(sample_line)
            lines.append("")
    else:
        lines.extend(["- None", ""])
    lines.extend(
        [
            "## Recommended Actions",
        ]
    )
    recommendations = payload.get("recommendations", []) or []
    if recommendations:
        for action in recommendations:
            lines.append(f"- {action.get('message', '')}")
            lines.append(f"  - Command: `{action.get('command', '')}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
        "## Totals",
        f"- Active: {totals.get('active', 0)}",
        f"- Existing archived: {totals.get('archived_existing', 0)}",
        f"- TTL expired: {totals.get('ttl_expired', 0)}",
        f"- Archive due: {totals.get('archive_due', 0)}",
        f"- Decaying: {totals.get('decaying', 0)}",
        f"- Archive backfill candidates: {totals.get('archive_backfill_candidates', 0)}",
        f"- Matched candidates: {totals.get('matched', 0)}",
        f"- Selected candidates: {totals.get('selected', 0)}",
        f"- Failed archive moves: {totals.get('failed', 0)}",
        f"- Backfill matched: {totals.get('backfill_matched', 0)}",
        f"- Backfilled in run: {totals.get('backfill_updated', 0)}",
        f"- Failed backfill moves: {totals.get('backfill_failed', 0)}",
        "",
        "## Scopes",
        ]
    )
    for scope_entry in payload.get("scopes", []) or []:
        scope = scope_entry.get("scope", {}) or {}
        audit = scope_entry.get("audit", {}) or {}
        archive = scope_entry.get("archive", {}) or {}
        backfill = scope_entry.get("backfill", {}) or {}
        counts = audit.get("counts", {}) or {}
        scope_name = f"{scope.get('agent_id', 'default')}/{scope.get('user_id', 'default')}"
        health = scope_entry.get("health", {}) or {}
        lines.extend(
            [
                f"### {scope_name}",
                f"- Status: {str(health.get('level', 'healthy')).upper()}",
                f"- Active: {counts.get('active', 0)}",
                f"- Existing archived: {counts.get('archived', 0)}",
                f"- TTL expired: {counts.get('ttl_expired', 0)}",
                f"- Archive due: {counts.get('archive_due', 0)}",
                f"- Decaying: {counts.get('decaying', 0)}",
                f"- Decaying ratio: {float(health.get('decaying_ratio', 0.0)):.1%}",
                f"- Archive backfill candidates: {counts.get('archive_backfill_candidates', 0)}",
                f"- Matched candidates: {archive.get('matched', 0)}",
                f"- Archived in run: {archive.get('archived', 0)}",
                f"- Backfill matched: {backfill.get('matched', 0)}",
                f"- Backfilled in run: {backfill.get('updated', 0)}",
            ]
        )
        candidate_ids = list(archive.get("candidate_ids", []) or [])
        if candidate_ids:
            lines.append(f"- Candidate ids: {', '.join(candidate_ids)}")
        backfill_ids = list(backfill.get("candidate_ids", []) or [])
        if backfill_ids:
            lines.append(f"- Backfill candidate ids: {', '.join(backfill_ids)}")
        for label, key in (
            ("Archive due samples", "archive_due"),
            ("TTL expired samples", "ttl_expired"),
            ("Decaying samples", "decaying"),
            ("Backfill samples", "archive_backfill_candidates"),
        ):
            sample_line = _format_sample_line(label, (health.get("samples", {}) or {}).get(key, []) or [])
            if sample_line:
                lines.append(sample_line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _build_default_report_paths(report_dir: str | Path, generated_at: str) -> tuple[Path, Path]:
    report_root = Path(os.path.expanduser(str(report_dir))).resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    tag = generated_at.replace("-", "").replace(":", "").replace("+00:00", "Z")
    tag = tag.replace(".", "_")
    base = report_root / f"memory_v5_lifecycle_{tag}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def run(
    *,
    config: Optional[dict] = None,
    agent: str = "default",
    user: str = "default",
    all_agents: bool = False,
    dry_run: bool = True,
    max_items: int = 100,
    sample_limit: int = 5,
    include_ttl_expired: bool = True,
    apply_archive_backfill: bool = False,
    now_ts: Optional[str] = None,
    json_out: Optional[str] = None,
    md_out: Optional[str] = None,
    write_report: bool = False,
    report_dir: Optional[str] = None,
    enable_alerts: Optional[bool] = None,
) -> Dict[str, Any]:
    cfg = config if isinstance(config, dict) else load_config()
    if isinstance(cfg, dict):
        mem_cfg = cfg.get("memory_v5", {}) if isinstance(cfg.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        cfg["memory_v5"] = mem_cfg
    service = MemoryV5Service(cfg)
    thresholds = _resolve_lifecycle_alerts(cfg, enable_alerts=enable_alerts)

    scopes: List[MemoryScope] = [MemoryScope(agent_id=agent, user_id=user)]
    if all_agents:
        scopes = iter_scopes(service.root) or scopes

    generated_at = now_ts
    if not generated_at:
        generated_at = datetime.now(timezone.utc).isoformat()

    results = []
    totals = {
        "checked": 0,
        "active": 0,
        "archived_existing": 0,
        "ttl_expired": 0,
        "archive_due": 0,
        "decaying": 0,
        "archive_backfill_candidates": 0,
        "matched": 0,
        "selected": 0,
        "archived": 0,
        "failed": 0,
        "backfill_matched": 0,
        "backfill_selected": 0,
        "backfill_updated": 0,
        "backfill_failed": 0,
    }
    for scope in scopes:
        audit = service.audit_lifecycle(scope=scope, now_ts=generated_at, sample_limit=sample_limit)
        archive = service.archive_due_items(
            scope=scope,
            now_ts=generated_at,
            max_items=max_items,
            dry_run=dry_run,
            include_ttl_expired=include_ttl_expired,
        )
        backfill = service.backfill_archive_defaults(
            scope=scope,
            now_ts=generated_at,
            max_items=max_items,
            dry_run=bool(dry_run or not apply_archive_backfill),
        )
        scope_payload = _scope_payload(scope)
        health = _evaluate_scope_health(scope_payload, audit, archive, backfill, thresholds)
        counts = audit.get("counts", {}) or {}
        totals["checked"] += int(counts.get("total", 0) or 0)
        totals["active"] += int(counts.get("active", 0) or 0)
        totals["archived_existing"] += int(counts.get("archived", 0) or 0)
        totals["ttl_expired"] += int(counts.get("ttl_expired", 0) or 0)
        totals["archive_due"] += int(counts.get("archive_due", 0) or 0)
        totals["decaying"] += int(counts.get("decaying", 0) or 0)
        totals["archive_backfill_candidates"] += int(counts.get("archive_backfill_candidates", 0) or 0)
        totals["matched"] += int(archive.get("matched", 0) or 0)
        totals["selected"] += int(archive.get("selected", 0) or 0)
        totals["archived"] += int(archive.get("archived", 0) or 0)
        totals["failed"] += int(archive.get("failed", 0) or 0)
        totals["backfill_matched"] += int(backfill.get("matched", 0) or 0)
        totals["backfill_selected"] += int(backfill.get("selected", 0) or 0)
        totals["backfill_updated"] += int(backfill.get("updated", 0) or 0)
        totals["backfill_failed"] += int(backfill.get("failed", 0) or 0)
        results.append(
            {
                "scope": scope_payload,
                "audit": audit,
                "archive": archive,
                "backfill": backfill,
                "health": health,
            }
        )

    alerts = []
    scope_status_counts = {"healthy": 0, "warn": 0, "critical": 0}
    hot_scopes = []
    overall_level = "healthy"
    for entry in results:
        health = entry.get("health", {}) or {}
        level = str(health.get("level", "healthy"))
        scope_status_counts[level] = scope_status_counts.get(level, 0) + 1
        if SEVERITY_RANK.get(level, 0) > SEVERITY_RANK.get(overall_level, 0):
            overall_level = level
        scope_alerts = list(health.get("alerts", []) or [])
        alerts.extend(scope_alerts)
        if level != "healthy":
            counts = (entry.get("audit", {}) or {}).get("counts", {}) or {}
            scope_payload = entry.get("scope", {}) or {}
            hot_scopes.append(
                {
                    "scope": scope_payload,
                    "scope_name": _scope_name(scope_payload),
                    "status": level,
                    "counts": {
                        "active": _safe_int(counts.get("active", 0), 0),
                        "ttl_expired": _safe_int(counts.get("ttl_expired", 0), 0),
                        "archive_due": _safe_int(counts.get("archive_due", 0), 0),
                        "archive_backfill_candidates": _safe_int(counts.get("archive_backfill_candidates", 0), 0),
                    },
                    "decaying_ratio": health.get("decaying_ratio", 0.0),
                    "alerts": scope_alerts,
                    "samples": health.get("samples", {}) or {},
                }
            )
    hot_scopes.sort(
        key=lambda item: (
            -SEVERITY_RANK.get(str(item.get("status", "healthy")), 0),
            -_safe_int((item.get("counts", {}) or {}).get("archive_due", 0), 0),
            -_safe_int((item.get("counts", {}) or {}).get("ttl_expired", 0), 0),
            -_safe_int((item.get("counts", {}) or {}).get("archive_backfill_candidates", 0), 0),
        )
    )
    recommendations = _build_recommendations(alerts)
    payload = {
        "generated_at": generated_at,
        "dry_run": bool(dry_run),
        "include_ttl_expired": bool(include_ttl_expired),
        "apply_archive_backfill": bool(apply_archive_backfill),
        "alerts_enabled": bool(thresholds.get("enabled", True)),
        "status": {
            "level": overall_level,
        },
        "alerts": alerts,
        "scope_status_counts": scope_status_counts,
        "hot_scopes": hot_scopes,
        "recommendations": recommendations,
        "scope_count": len(scopes),
        "checked": totals["checked"],
        "archived": totals["archived"],
        "totals": totals,
        "scopes": results,
    }
    resolved_json_out = json_out
    resolved_md_out = md_out
    if write_report and not resolved_json_out and not resolved_md_out:
        json_path, md_path = _build_default_report_paths(report_dir or default_report_dir(), generated_at)
        resolved_json_out = str(json_path)
        resolved_md_out = str(md_path)
    artifacts: Dict[str, str] = {}
    if resolved_json_out:
        json_path = Path(os.path.expanduser(resolved_json_out)).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts["json"] = str(json_path)
    if resolved_md_out:
        md_path = Path(os.path.expanduser(resolved_md_out)).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        artifacts["markdown"] = str(md_path)
    if artifacts:
        payload["artifacts"] = artifacts
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Memory v5 lifecycle state and optionally archive explicit candidates.")
    parser.add_argument("--agent", default="default")
    parser.add_argument("--user", default="default")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all-agents", action="store_true")
    parser.add_argument("--max-items", type=int, default=100)
    parser.add_argument("--sample-limit", type=int, default=5)
    parser.add_argument("--exclude-ttl-expired", action="store_true")
    parser.add_argument("--apply-archive-backfill", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--report-dir", default=str(default_report_dir()))
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--md-out", default=None)
    parser.add_argument("--no-alerts", action="store_true")
    args = parser.parse_args()

    result = run(
        agent=args.agent,
        user=args.user,
        all_agents=bool(args.all_agents),
        dry_run=bool(args.dry_run),
        max_items=args.max_items,
        sample_limit=args.sample_limit,
        include_ttl_expired=not bool(args.exclude_ttl_expired),
        apply_archive_backfill=bool(args.apply_archive_backfill),
        write_report=bool(args.write_report),
        report_dir=args.report_dir,
        json_out=args.json_out,
        md_out=args.md_out,
        enable_alerts=(False if args.no_alerts else None),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
