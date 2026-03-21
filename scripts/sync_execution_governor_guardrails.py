#!/usr/bin/env python3
"""Export Deep-Sea Nexus execution_guard config into execution-governor guardrails JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_guardrails_payload(config: Dict[str, Any]) -> Dict[str, Any]:
    guard = config.get("execution_guard", {}) if isinstance(config, dict) else {}
    thresholds = guard.get("thresholds", {}) if isinstance(guard.get("thresholds", {}), dict) else {}
    protected = guard.get("protected_targets", {}) if isinstance(guard.get("protected_targets", {}), dict) else {}
    report = guard.get("report", {}) if isinstance(guard.get("report", {}), dict) else {}
    return {
        "version": "2026-03-21.v1.4-guardrails",
        "source": "deepsea-nexus",
        "enabled": bool(guard.get("enabled", True)),
        "mode": str(guard.get("mode", "report_only") or "report_only"),
        "thresholds": {
            "ask_score": float(thresholds.get("ask_score", 0.7)),
            "block_score": float(thresholds.get("block_score", 0.9)),
        },
        "protected_targets": protected,
        "report": {
            "include_context_hint": bool(report.get("include_context_hint", True)),
        },
        "signals": [
            "tool_risk_decision",
            "tool_risk_score",
            "shell_obfuscation_signal",
            "secret_exposure_signal",
            "workspace_boundary_signal",
            "memory_asset_risk_signal",
        ],
    }


def write_guardrails(out_path: Path, payload: Dict[str, Any]) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync execution-governor guardrails from Deep-Sea Nexus config")
    parser.add_argument("--config", default=str(_repo_root() / "config.json"))
    parser.add_argument("--out", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    repo_root = _repo_root()

    if str(repo_root.parent) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(repo_root.parent))
    import deepsea_nexus  # type: ignore
    from deepsea_nexus.plugins.execution_guard_plugin import resolve_execution_governor_guardrails_path  # type: ignore

    config = _load_config(config_path)
    payload = build_guardrails_payload(config)
    out_path = Path(args.out).expanduser() if args.out else Path(resolve_execution_governor_guardrails_path(config)).expanduser()
    out_path = out_path.resolve()
    write_guardrails(out_path, payload)

    result = {"config": str(config_path), "out": str(out_path), "payload": payload}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[ok] wrote execution-governor guardrails to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
