#!/usr/bin/env python3
"""Print deepsea-nexus SmartContext runtime config and in-memory counters.

Runs within the deepsea-nexus package so relative imports work.
"""

import asyncio
import json
import os
import sys

# Ensure repo root is importable when running as a script
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _to_jsonable(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


async def main() -> int:
    # Import via the repo root package name (this repo is a package via __init__.py)
    from core.plugin_system import get_plugin_registry  # type: ignore
    from plugins.smart_context import SmartContextPlugin  # type: ignore

    # Initialize plugin registry + SmartContext
    registry = get_plugin_registry()
    plugin = SmartContextPlugin()
    ok = await plugin.initialize({})

    # Register it so we can introspect similarly to runtime
    try:
        registry.register(plugin)
    except Exception:
        # If already registered, ignore
        pass

    cfg = plugin.config

    state = {
        "init_ok": ok,
        "config": {
            "full_rounds": cfg.full_rounds,
            "summary_rounds": cfg.summary_rounds,
            "compress_after_rounds": cfg.compress_after_rounds,
            "full_tokens_max": cfg.full_tokens_max,
            "summary_tokens_max": cfg.summary_tokens_max,
            "compressed_tokens_max": cfg.compressed_tokens_max,
            "trigger_soft_ratio": cfg.trigger_soft_ratio,
            "trigger_hard_ratio": cfg.trigger_hard_ratio,
            "store_summary_enabled": cfg.store_summary_enabled,
            "summary_on_each_turn": cfg.summary_on_each_turn,
            "summary_template_fields": list(cfg.summary_template_fields),
            "rescue_enabled": cfg.rescue_enabled,
            "rescue_gold": cfg.rescue_gold,
            "rescue_decisions": cfg.rescue_decisions,
            "rescue_next_actions": cfg.rescue_next_actions,
            "inject_enabled": cfg.inject_enabled,
            "inject_threshold": cfg.inject_threshold,
            "inject_max_items": cfg.inject_max_items,
            "inject_max_chars_per_item": cfg.inject_max_chars_per_item,
            "inject_max_lines_per_item": cfg.inject_max_lines_per_item,
            "inject_max_lines_total": cfg.inject_max_lines_total,
            "graph_inject_enabled": cfg.graph_inject_enabled,
            "graph_max_items": cfg.graph_max_items,
        },
        "runtime_counters": {
            "current_round": getattr(plugin, "_current_round", None),
            "context_history_len": len(getattr(plugin, "_context_history", []) or []),
            "inject_history_len": len(getattr(plugin, "_inject_history", []) or []),
            "inject_stats_len": len(getattr(plugin, "_inject_stats", []) or []),
            "graph_enabled": getattr(plugin, "_graph_enabled", None),
            "last_keywords": _to_jsonable(getattr(plugin, "_last_keywords", None)),
        },
        "note": "These runtime counters reflect a freshly initialized SmartContextPlugin instance in this process; they are not the live OpenClaw agent session state.",
    }

    print(json.dumps(state, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
