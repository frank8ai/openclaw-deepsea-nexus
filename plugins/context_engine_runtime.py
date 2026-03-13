"""
Runtime helpers for ContextEngine budget, trimming, and metrics state.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from ..runtime_paths import resolve_log_path
except ImportError:
    from runtime_paths import resolve_log_path


@dataclass
class ContextBudget:
    """上下文预算与拼装规则"""

    max_tokens: int = 1000
    max_items: int = 4
    max_chars_per_item: int = 360
    max_lines_total: int = 40
    include_now: bool = True
    include_recent_summary: bool = True
    include_memory: bool = True


class ContextEngineRuntimeState:
    def __init__(self, config_path: Optional[str] = None):
        self._metrics_path: Optional[str] = None
        self._build_stats: List[Dict[str, Any]] = []
        self._pending_config_updates: Dict[str, Any] = {}
        self._last_persist_ts = 0.0
        self._last_trim_reason = "none"
        self._last_trim_before_tokens = 0
        self._config_path = config_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "config.json")
        )

    @property
    def last_trim_reason(self) -> str:
        return self._last_trim_reason

    @property
    def last_trim_before_tokens(self) -> int:
        return int(self._last_trim_before_tokens)

    def budget_from_config(self, config: Optional[Dict[str, Any]]) -> ContextBudget:
        cfg = {}
        if isinstance(config, dict):
            cfg = config.get("context_engine", {}) or {}
        return ContextBudget(
            max_tokens=int(cfg.get("max_tokens", 1000)),
            max_items=int(cfg.get("max_items", 4)),
            max_chars_per_item=int(cfg.get("max_chars_per_item", 360)),
            max_lines_total=int(cfg.get("max_lines_total", 40)),
            include_now=bool(cfg.get("include_now", True)),
            include_recent_summary=bool(cfg.get("include_recent_summary", True)),
            include_memory=bool(cfg.get("include_memory", True)),
        )

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text) / 3))

    def trim_to_budget(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            self._last_trim_reason = "disabled"
            self._last_trim_before_tokens = 0
            return text
        est = self.estimate_tokens(text)
        self._last_trim_before_tokens = int(est)
        if est <= max_tokens:
            self._last_trim_reason = "none"
            return text
        ratio = max_tokens / float(max(est, 1))
        max_chars = max(200, int(len(text) * ratio))
        self._last_trim_reason = "token_budget"
        return text[:max_chars].rstrip() + "..."

    def prime(self, config: Optional[Dict[str, Any]]) -> None:
        if not self._metrics_path:
            self._metrics_path = self._resolve_metrics_path(config)

    def _resolve_metrics_path(self, config: Optional[Dict[str, Any]]) -> Optional[str]:
        return resolve_log_path(config, "context_engine_metrics.log")

    def _append_metrics(self, payload: Dict[str, Any]) -> None:
        if not self._metrics_path:
            return
        try:
            payload.setdefault("schema_version", "4.4.0")
            payload.setdefault("component", "context_engine")
            payload.setdefault("event", "unknown")
            payload.setdefault("ts", datetime.now().isoformat())
            with open(self._metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            return

    def record_build_metrics(
        self,
        context_text: str,
        memory_items: List[Dict[str, Any]],
        budget: ContextBudget,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._metrics_path:
            self._metrics_path = self._resolve_metrics_path(config)
        if not self._metrics_path:
            return
        cfg = config.get("context_engine", {}) if isinstance(config, dict) else {}
        if not cfg.get("metrics_enabled", True):
            return

        token_est = self.estimate_tokens(context_text)
        line_count = max(1, context_text.count("\n") + 1) if context_text else 0
        items_used = min(len(memory_items), int(budget.max_items))

        self._append_metrics(
            {
                "event": "context_build",
                "tokens": int(token_est),
                "lines": int(line_count),
                "items_used": int(items_used),
                "budget_tokens": int(budget.max_tokens),
                "budget_items": int(budget.max_items),
                "budget_lines": int(budget.max_lines_total),
                "trim_reason": self._last_trim_reason,
                "tokens_before_trim": int(self._last_trim_before_tokens),
            }
        )
        self._record_build_stats(token_est, items_used, config)

    def _record_build_stats(self, token_est: int, items_used: int, config: Optional[Dict[str, Any]]) -> None:
        cfg = config.get("context_engine", {}) if isinstance(config, dict) else {}
        window = int(cfg.get("metrics_window", 20))
        if window <= 0:
            return
        self._build_stats.append({"tokens": int(token_est), "items": int(items_used)})
        if len(self._build_stats) < window:
            return
        recent = self._build_stats[-window:]
        avg_tokens = sum(r["tokens"] for r in recent) / float(len(recent))
        avg_items = sum(r["items"] for r in recent) / float(len(recent))
        self._append_metrics(
            {
                "event": "context_stats",
                "window": len(recent),
                "avg_tokens": round(avg_tokens, 2),
                "avg_items": round(avg_items, 2),
            }
        )
        if cfg.get("auto_tune_enabled", False):
            self._auto_tune_budget(avg_tokens, avg_items, cfg)
        self._flush_pending_config_updates(config)

    def _auto_tune_budget(self, avg_tokens: float, avg_items: float, cfg: Dict[str, Any]) -> None:
        max_items = int(cfg.get("max_items", 4))
        min_items = int(cfg.get("auto_tune_min_items", 2))
        max_items_cap = int(cfg.get("auto_tune_max_items", 6))
        target_tokens = int(cfg.get("auto_tune_target_tokens", 800))

        new_items = max_items
        if avg_tokens > target_tokens and max_items > min_items:
            new_items = max(min_items, max_items - 1)
        elif avg_tokens < target_tokens * 0.7 and max_items < max_items_cap:
            new_items = min(max_items_cap, max_items + 1)

        if new_items != max_items:
            self._append_metrics(
                {
                    "event": "context_auto_tune",
                    "avg_tokens": round(avg_tokens, 2),
                    "items_before": max_items,
                    "items_after": new_items,
                }
            )
            self._pending_config_updates["max_items"] = int(new_items)

    def _flush_pending_config_updates(self, config: Optional[Dict[str, Any]]) -> None:
        if not self._pending_config_updates:
            return
        cfg = config.get("context_engine", {}) if isinstance(config, dict) else {}
        interval = max(10, int(cfg.get("persist_interval_sec", 60)))
        now_ts = datetime.now().timestamp()
        if now_ts - self._last_persist_ts < interval:
            return
        if not isinstance(config, dict):
            return
        try:
            if not os.path.exists(self._config_path):
                return
            with open(self._config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            data.setdefault("context_engine", {}).update(self._pending_config_updates)
            with open(self._config_path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(data, ensure_ascii=False, indent=2))
            self._pending_config_updates = {}
            self._last_persist_ts = now_ts
        except Exception:
            return
