"""
Shared adaptive stats helpers for SmartContext injection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_inject_stats_entry(
    reason: str,
    retrieved: int,
    injected: int,
    graph_injected: int,
    threshold: float,
) -> Dict[str, Any]:
    return {
        "reason": reason,
        "retrieved": int(retrieved),
        "injected": int(injected),
        "graph": int(graph_injected),
        "ratio": round((injected / retrieved), 3) if retrieved else 0.0,
        "threshold": round(float(threshold), 3),
    }


def summarize_inject_stats(entries: List[Dict[str, Any]], window: int) -> Optional[Dict[str, Any]]:
    window = int(window)
    if window <= 0 or len(entries) < window:
        return None
    recent = entries[-window:]
    count = len(recent)
    total_retrieved = sum(item.get("retrieved", 0) for item in recent)
    total_injected = sum(item.get("injected", 0) for item in recent)
    total_graph = sum(item.get("graph", 0) for item in recent)
    avg_ratio = (total_injected / total_retrieved) if total_retrieved else 0.0
    return {
        "window": count,
        "retrieved": total_retrieved,
        "injected": total_injected,
        "graph_injected": total_graph,
        "avg_ratio": round(avg_ratio, 3),
    }


def compute_adaptive_threshold(
    inject_history: List[Dict[str, Any]],
    *,
    adaptive_window: int,
    current_threshold: float,
    adaptive_min_threshold: float,
    adaptive_max_threshold: float,
    adaptive_step: float,
) -> Optional[Dict[str, Any]]:
    window = int(adaptive_window)
    if window <= 0 or not inject_history:
        return None
    recent = inject_history[-window:]
    success = sum(1 for item in recent if item.get("count", 0) > 0)
    ratio = success / float(len(recent))

    new_threshold = float(current_threshold)
    if ratio < 0.35:
        new_threshold = min(float(adaptive_max_threshold), float(current_threshold) + float(adaptive_step))
    elif ratio > 0.7:
        new_threshold = max(float(adaptive_min_threshold), float(current_threshold) - float(adaptive_step))

    return {
        "ratio": ratio,
        "window": len(recent),
        "new_threshold": new_threshold,
    }
