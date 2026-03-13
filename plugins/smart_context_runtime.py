"""
Runtime helpers for SmartContext metrics, inject auto-tune, and config writes.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from ..runtime_paths import resolve_log_path
except ImportError:
    from runtime_paths import resolve_log_path


class SmartContextRuntimeState:
    def __init__(self, config_path: Optional[str] = None):
        self._metrics_path: Optional[str] = None
        self._inject_ratio_streak = 0
        self._pending_config_updates: Dict[str, Any] = {}
        self._last_persist_ts = 0.0
        self._config_path = config_path or self.resolve_config_path()

    def prime(self, config: Optional[Dict[str, Any]]) -> None:
        if not self._metrics_path:
            self._metrics_path = self.resolve_metrics_path(config)

    def resolve_metrics_path(self, config: Optional[Dict[str, Any]]) -> Optional[str]:
        return resolve_log_path(config, "smart_context_metrics.log")

    def resolve_config_path(self) -> str:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_dir, "config.json")

    def append_metrics(self, payload: Dict[str, Any]) -> None:
        if not self._metrics_path:
            return
        try:
            payload.setdefault("schema_version", "4.4.0")
            payload.setdefault("component", "smart_context")
            payload.setdefault("event", "unknown")
            payload.setdefault("ts", datetime.now().isoformat())
            with open(self._metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            return

    def persist_config(self, updates: Dict[str, Any]) -> None:
        if not updates:
            return
        self._pending_config_updates.update(updates)

    def flush_pending_config_updates(self, config: Any) -> None:
        if not self._config_path or not self._pending_config_updates:
            return
        now_ts = datetime.now().timestamp()
        interval = max(10, int(getattr(config, "inject_persist_interval_sec", 60)))
        if now_ts - self._last_persist_ts < interval:
            return
        try:
            if not os.path.exists(self._config_path):
                return
            with open(self._config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            smart_cfg = data.get("smart_context", {})
            if not isinstance(smart_cfg, dict):
                smart_cfg = {}
            smart_cfg.update(self._pending_config_updates)
            data["smart_context"] = smart_cfg
            with open(self._config_path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(data, ensure_ascii=False, indent=2))
            self._pending_config_updates = {}
            self._last_persist_ts = now_ts
        except Exception:
            return

    def maybe_alert_inject_ratio(self, avg_ratio: float, window: int, config: Any) -> None:
        if not getattr(config, "inject_ratio_alert_enabled", True):
            return
        threshold = float(getattr(config, "inject_ratio_alert_threshold", 0.15))
        if avg_ratio < threshold:
            self._inject_ratio_streak += 1
        else:
            self._inject_ratio_streak = 0
        if self._inject_ratio_streak >= int(getattr(config, "inject_ratio_alert_streak", 2)):
            self.append_metrics(
                {
                    "event": "inject_ratio_alert",
                    "avg_ratio": round(avg_ratio, 3),
                    "threshold": round(threshold, 3),
                    "window": int(window),
                    "streak": int(self._inject_ratio_streak),
                }
            )
            if getattr(config, "inject_debug", False):
                print(
                    f"[SmartContext] ALERT inject ratio low avg={avg_ratio:.2f} "
                    f"threshold={threshold:.2f} window={window}"
                )
        if getattr(config, "inject_ratio_auto_tune", True):
            self.auto_tune_inject(avg_ratio, config)
        self.flush_pending_config_updates(config)

    def auto_tune_inject(self, avg_ratio: float, config: Any) -> None:
        step = float(getattr(config, "inject_ratio_auto_tune_step", 0.05))
        if avg_ratio <= 0 and step <= 0:
            return
        old_threshold = float(getattr(config, "inject_threshold", 0.6))
        new_threshold = max(float(getattr(config, "adaptive_min_threshold", 0.35)), old_threshold - step)
        if new_threshold != old_threshold:
            setattr(config, "inject_threshold", new_threshold)
        old_max_items = int(getattr(config, "inject_max_items", 3))
        max_cap = int(getattr(config, "inject_ratio_auto_tune_max_items", 6))
        new_max_items = min(max_cap, max(old_max_items, old_max_items + 1))
        if new_max_items != old_max_items:
            setattr(config, "inject_max_items", new_max_items)
        self.append_metrics(
            {
                "event": "inject_auto_tune",
                "avg_ratio": round(avg_ratio, 3),
                "threshold_before": round(old_threshold, 3),
                "threshold_after": round(float(getattr(config, "inject_threshold", old_threshold)), 3),
                "max_items_before": old_max_items,
                "max_items_after": int(getattr(config, "inject_max_items", old_max_items)),
            }
        )
        self.persist_config(
            {
                "inject_threshold": float(getattr(config, "inject_threshold", old_threshold)),
                "inject_max_items": int(getattr(config, "inject_max_items", old_max_items)),
            }
        )
        if getattr(config, "inject_debug", False):
            print(
                f"[SmartContext] AUTO_TUNE inject threshold {old_threshold:.2f}->{getattr(config, 'inject_threshold', old_threshold):.2f} "
                f"max_items {old_max_items}->{getattr(config, 'inject_max_items', old_max_items)}"
            )
