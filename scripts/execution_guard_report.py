#!/usr/bin/env python3
"""Summarize execution_guard metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize execution_guard metrics")
    parser.add_argument("--metrics", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root()
    import sys

    if str(repo_root.parent) not in sys.path:
        sys.path.insert(0, str(repo_root.parent))
    import deepsea_nexus  # type: ignore
    from deepsea_nexus.plugins.execution_guard_plugin import read_execution_guard_metrics_summary  # type: ignore
    from deepsea_nexus.runtime_paths import resolve_log_path  # type: ignore

    config_path = deepsea_nexus.resolve_default_config_path()
    config = deepsea_nexus.ConfigManager(config_path).get_all()
    metrics_path = args.metrics or resolve_log_path(config, "execution_guard_metrics.log", allow_nexus_base=True)
    summary: Dict[str, Any] = read_execution_guard_metrics_summary(metrics_path)
    summary["metrics_path"] = metrics_path

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Metrics path: {metrics_path}")
        print(f"Processed: {summary.get('processed', 0)}")
        print(f"Allow: {summary.get('allow', 0)}")
        print(f"Context: {summary.get('context', 0)}")
        print(f"Ask: {summary.get('ask', 0)}")
        print(f"Block: {summary.get('block', 0)}")
        print(f"Top rules: {summary.get('top_rules', {})}")
        print(f"Top targets: {summary.get('top_targets', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
