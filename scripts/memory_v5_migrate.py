#!/usr/bin/env python3
"""Migrate existing markdown memory into memory_v5 (best-effort)."""

import argparse
import os
import json
import sys
from typing import Iterable

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service, MemoryScope


def iter_markdown(root: str) -> Iterable[str]:
    for base, _dirs, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".md"):
                yield os.path.join(base, name)


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    config_path = os.path.abspath(config_path)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Root path to scan markdown files")
    parser.add_argument("--agent", default="default", help="agent_id scope")
    parser.add_argument("--user", default="default", help="user_id scope")
    parser.add_argument("--max-chars", type=int, default=8000)
    args = parser.parse_args()

    config = load_config()
    if isinstance(config, dict):
        mem_cfg = config.get("memory_v5", {}) if isinstance(config.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        config["memory_v5"] = mem_cfg
    service = MemoryV5Service(config)
    scope = MemoryScope(agent_id=args.agent, user_id=args.user)

    count = 0
    for path in iter_markdown(args.path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            if args.max_chars and len(content) > args.max_chars:
                content = content[: args.max_chars]
            title = os.path.basename(path)
            service.ingest_document(
                title=title,
                content=content,
                tags=["migrated"],
                scope=scope,
                source_id=path,
            )
            count += 1
        except Exception:
            continue

    print(f"migrated_files={count}")


if __name__ == "__main__":
    main()
