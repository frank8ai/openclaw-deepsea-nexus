"""
Capability autotune lab plugin for report-first offline optimization summaries.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..runtime_paths import resolve_log_path


def resolve_capability_autotune_report_path(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    cfg = config if isinstance(config, dict) else {}
    lab_cfg = cfg.get("capability_autotune_lab", {}) if isinstance(cfg.get("capability_autotune_lab", {}), dict) else {}
    override = str(lab_cfg.get("report_path") or "").strip()
    if override:
        return str(Path(override).expanduser())
    return resolve_log_path(
        cfg,
        "capability_autotune_latest.json",
        allow_nexus_base=True,
        default_base=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    )


def read_capability_autotune_report_summary(report_path: Optional[str]) -> Dict[str, Any]:
    path = str(report_path or "").strip()
    if not path or not os.path.exists(path):
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        "generated_at": payload.get("generated_at", ""),
        "best_experiment": payload.get("best_experiment", {}),
        "baseline_experiment": payload.get("baseline_experiment", {}),
        "recommended_action": payload.get("recommended_action", ""),
        "context_scorecard": payload.get("context_scorecard", {}),
    }


class CapabilityAutotuneLabPlugin(NexusPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = PluginMetadata(
            name="capability_autotune_lab",
            version="3.0.0",
            description="Report-first offline capability autotune lab summary",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self._enabled = True
        self._report_path: Optional[str] = None

    async def initialize(self, config: Dict[str, Any]) -> bool:
        cfg = config if isinstance(config, dict) else {}
        lab_cfg = cfg.get("capability_autotune_lab", {}) if isinstance(cfg.get("capability_autotune_lab", {}), dict) else {}
        self._enabled = bool(lab_cfg.get("enabled", True))
        self._report_path = resolve_capability_autotune_report_path(cfg)
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True

    def get_health_summary(self) -> Dict[str, Any]:
        return {
            "enabled": bool(self._enabled),
            "report_path": self._report_path or "",
            "last_report": read_capability_autotune_report_summary(self._report_path),
        }
