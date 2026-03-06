#!/usr/bin/env python3
"""Quick smoke test for memory_v5."""

import os
import json
import sys

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    config_path = os.path.abspath(config_path)
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def main():
    config = load_config()
    if isinstance(config, dict):
        mem_cfg = config.get("memory_v5", {}) if isinstance(config.get("memory_v5", {}), dict) else {}
        mem_cfg["async_ingest"] = False
        config["memory_v5"] = mem_cfg
    service = MemoryV5Service(config)
    service.ingest_document(title="SmokeTest", content="mem v5 smoke test content", tags=["smoke"])
    hits = service.recall("smoke test", limit=3)
    ok = bool(hits)
    print(json.dumps({"ok": ok, "hits": len(hits)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
