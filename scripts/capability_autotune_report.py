#!/usr/bin/env python3
"""Summarize capability autotune lab reports."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_autotune_report",
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


package = _load_local_package()
autotune_plugin = importlib.import_module(f"{package.__name__}.plugins.capability_autotune_lab_plugin")


def build_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    best = payload.get("best_experiment", {}) if isinstance(payload.get("best_experiment", {}), dict) else {}
    baseline = payload.get("baseline_experiment", {}) if isinstance(payload.get("baseline_experiment", {}), dict) else {}
    context = payload.get("context_scorecard", {}) if isinstance(payload.get("context_scorecard", {}), dict) else {}
    return {
        "generated_at": payload.get("generated_at", ""),
        "recommended_action": payload.get("recommended_action", ""),
        "best_experiment": {
            "id": best.get("id", ""),
            "pass_rate": best.get("pass_rate", 0.0),
            "saved_ratio": best.get("saved_ratio", 0.0),
        },
        "baseline_experiment": {
            "id": baseline.get("id", ""),
            "pass_rate": baseline.get("pass_rate", 0.0),
            "saved_ratio": baseline.get("saved_ratio", 0.0),
        },
        "context_scorecard": {
            "cases": context.get("cases", 0),
            "pass_rate": context.get("pass_rate", 0.0),
        },
    }


def resolve_report_path(config_path: str | None = None, report_path: str | None = None) -> Path:
    if report_path:
        return Path(report_path).expanduser().resolve()
    config_file = (
        Path(config_path).resolve()
        if config_path
        else Path(package.resolve_default_config_path() or (REPO_ROOT / "config.json")).resolve()
    )
    cfg = package.ConfigManager(str(config_file)).get_all()
    resolved = autotune_plugin.resolve_capability_autotune_report_path(cfg)
    if resolved:
        return Path(resolved).expanduser().resolve()
    return (REPO_ROOT / "logs" / "capability_autotune_latest.json").resolve()


def run(config_path: str | None = None, report_path: str | None = None) -> Dict[str, Any]:
    path = resolve_report_path(config_path=config_path, report_path=report_path)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    summary = build_summary(payload if isinstance(payload, dict) else {})
    summary["report_path"] = str(path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize capability autotune lab report")
    parser.add_argument("report_path", nargs="?", default=None)
    parser.add_argument("--config", default=None, help="Optional Deepsea config path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary = run(config_path=args.config, report_path=args.report_path)
    path = Path(summary["report_path"])

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Report path: {path}")
        print(f"Recommended action: {summary['recommended_action']}")
        print(f"Best experiment: {summary['best_experiment']}")
        print(f"Baseline experiment: {summary['baseline_experiment']}")
        print(f"Context scorecard: {summary['context_scorecard']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
