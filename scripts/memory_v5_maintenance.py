#!/usr/bin/env python3
"""Maintenance for memory_v5 lifecycle audit and explicit archive moves."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service, MemoryScope

_SCOPE_TABLES: Tuple[str, ...] = ("items", "resources", "categories", "edges")
_SCOPE_COLUMNS = {
    "scope_agent",
    "scope_user",
    "scope_app",
    "scope_run",
    "scope_workspace",
}


def load_config() -> dict:
    config_path = os.path.join(SKILL_ROOT, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def default_report_dir() -> Path:
    return (Path(SKILL_ROOT).resolve() / "docs" / "reports").resolve()


def _scope_sort_key(scope: MemoryScope) -> Tuple[str, str, str, str, str]:
    normalized = scope.normalized()
    return (
        normalized.agent_id,
        normalized.user_id,
        normalized.app_id,
        normalized.run_id,
        normalized.workspace,
    )


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


def _discover_scopes_from_index(index_path: str, fallback_scope: MemoryScope) -> List[MemoryScope]:
    if not os.path.exists(index_path):
        return []
    conn: Optional[sqlite3.Connection] = None
    discovered: Dict[str, MemoryScope] = {}
    try:
        conn = sqlite3.connect(f"file:{index_path}?mode=ro", uri=True)
        table_rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {str(row[0]) for row in table_rows if row and row[0]}
        for table in _SCOPE_TABLES:
            if table not in table_names:
                continue
            try:
                columns = {
                    str(row[1])
                    for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
                    if len(row) > 1
                }
            except sqlite3.DatabaseError:
                continue
            if not _SCOPE_COLUMNS.issubset(columns):
                continue
            try:
                rows = conn.execute(
                    f"""
                    SELECT DISTINCT
                        COALESCE(scope_agent, ''),
                        COALESCE(scope_user, ''),
                        COALESCE(scope_app, ''),
                        COALESCE(scope_run, ''),
                        COALESCE(scope_workspace, '')
                    FROM {table}
                    """
                ).fetchall()
            except sqlite3.DatabaseError:
                continue
            for row in rows:
                scope = MemoryScope(
                    agent_id=str(row[0] or fallback_scope.agent_id or "default"),
                    user_id=str(row[1] or fallback_scope.user_id or "default"),
                    app_id=str(row[2] or ""),
                    run_id=str(row[3] or ""),
                    workspace=str(row[4] or ""),
                ).normalized()
                discovered[scope.scope_key()] = scope
    except sqlite3.DatabaseError:
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return sorted(discovered.values(), key=_scope_sort_key)


def iter_scopes(root: str) -> List[MemoryScope]:
    if not os.path.isdir(root):
        return []
    scopes: Dict[str, MemoryScope] = {}
    for agent in sorted(os.listdir(root)):
        agent_dir = os.path.join(root, agent)
        if not os.path.isdir(agent_dir):
            continue
        for user in sorted(os.listdir(agent_dir)):
            user_dir = os.path.join(agent_dir, user)
            if not os.path.isdir(user_dir):
                continue
            fallback_scope = MemoryScope(agent_id=agent, user_id=user).normalized()
            index_path = os.path.join(user_dir, "index.sqlite3")
            discovered = _discover_scopes_from_index(index_path, fallback_scope)
            if discovered:
                for scope in discovered:
                    scopes[scope.scope_key()] = scope
                continue
            scopes[fallback_scope.scope_key()] = fallback_scope
    return sorted(scopes.values(), key=_scope_sort_key)


def _scope_payload(scope: MemoryScope) -> Dict[str, str]:
    return {
        "agent_id": scope.agent_id,
        "user_id": scope.user_id,
        "app_id": scope.app_id,
        "run_id": scope.run_id,
        "workspace": scope.workspace,
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    totals = payload.get("totals", {}) or {}
    lines = [
        "# Memory V5 Lifecycle Maintenance",
        "",
        f"- Generated at: {payload.get('generated_at', '')}",
        f"- Dry run: {payload.get('dry_run', False)}",
        f"- Include TTL expired: {payload.get('include_ttl_expired', False)}",
        f"- Apply archive backfill: {payload.get('apply_archive_backfill', False)}",
        f"- Scope count: {payload.get('scope_count', 0)}",
        f"- Checked: {payload.get('checked', 0)}",
        f"- Archived in run: {payload.get('archived', 0)}",
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
    for scope_entry in payload.get("scopes", []) or []:
        scope = scope_entry.get("scope", {}) or {}
        audit = scope_entry.get("audit", {}) or {}
        archive = scope_entry.get("archive", {}) or {}
        backfill = scope_entry.get("backfill", {}) or {}
        counts = audit.get("counts", {}) or {}
        scope_name = _scope_label(scope)
        lines.extend(
            [
                f"### {scope_name}",
                f"- Active: {counts.get('active', 0)}",
                f"- Existing archived: {counts.get('archived', 0)}",
                f"- TTL expired: {counts.get('ttl_expired', 0)}",
                f"- Archive due: {counts.get('archive_due', 0)}",
                f"- Decaying: {counts.get('decaying', 0)}",
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
) -> Dict[str, Any]:
    cfg = config if isinstance(config, dict) else load_config()
    if isinstance(cfg, dict):
        mem_cfg = cfg.get("memory_v5", {}) if isinstance(cfg.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        cfg["memory_v5"] = mem_cfg
    service = MemoryV5Service(cfg)

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
                "scope": _scope_payload(scope),
                "audit": audit,
                "archive": archive,
                "backfill": backfill,
            }
        )

    payload = {
        "generated_at": generated_at,
        "dry_run": bool(dry_run),
        "include_ttl_expired": bool(include_ttl_expired),
        "apply_archive_backfill": bool(apply_archive_backfill),
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
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
