#!/usr/bin/env python3
"""Maintenance for memory_v5: archive expired items and refresh categories."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service, MemoryScope


def load_config() -> dict:
    config_path = os.path.join(SKILL_ROOT, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def parse_iso(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="default")
    parser.add_argument("--user", default="default")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all-agents", action="store_true")
    args = parser.parse_args()

    config = load_config()
    if isinstance(config, dict):
        mem_cfg = config.get("memory_v5", {}) if isinstance(config.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        config["memory_v5"] = mem_cfg
    service = MemoryV5Service(config)

    scopes = [MemoryScope(agent_id=args.agent, user_id=args.user)]
    if args.all_agents:
        scopes = iter_scopes(service.root) or scopes
    total_archived = 0
    total_checked = 0

    now = datetime.now(timezone.utc)
    for scope in scopes:
        items = service.index.list_all_items(scope, include_archived=False)
        archived = 0
        checked = 0

        for row in items:
            checked += 1
            ttl_days = int(row.get("ttl_days") or 0)
            updated_at = row.get("updated_at") or row.get("created_at")
            if not updated_at:
                continue
            try:
                age_days = max(0.0, (now - parse_iso(str(updated_at))).total_seconds() / 86400.0)
            except Exception:
                continue
            archive_after = int(service.archive_after_days or 0)
            expired = ttl_days > 0 and age_days > ttl_days
            aging_out = archive_after > 0 and age_days > archive_after
            if expired or aging_out:
                if args.dry_run:
                    archived += 1
                    continue
                if service.archive_item(str(row.get("id")), scope=scope):
                    archived += 1

        total_archived += archived
        total_checked += checked

    print(json.dumps({"checked": total_checked, "archived": total_archived, "dry_run": bool(args.dry_run)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
