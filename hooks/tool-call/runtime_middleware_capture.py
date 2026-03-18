#!/usr/bin/env python3
"""OpenClaw tool-call hook for Deep-Sea Nexus runtime middleware."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    context_raw = os.environ.get("NEXUS_HOOK_CONTEXT", "{}")
    try:
        context = json.loads(context_raw)
    except Exception:
        context = {}

    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root.parent) not in sys.path:
        sys.path.insert(0, str(repo_root.parent))

    try:
        import deepsea_nexus
    except Exception as exc:
        print(f"runtime_middleware hook import failed: {exc}")
        return 0

    if not deepsea_nexus.nexus_init():
        print("runtime_middleware hook init failed")
        return 0

    registry = deepsea_nexus.get_plugin_registry()
    plugin = registry.get("runtime_middleware")
    if plugin is None or not hasattr(plugin, "process_openclaw_context"):
        print("runtime_middleware plugin unavailable")
        return 0

    result = plugin.process_openclaw_context(context)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
