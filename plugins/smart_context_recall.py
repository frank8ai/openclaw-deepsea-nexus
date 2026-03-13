"""
Shared recall normalization and filtering helpers for SmartContext injection.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple


def item_score(item: Dict[str, Any]) -> float:
    try:
        return float(item.get("score", item.get("relevance", 0.0)))
    except Exception:
        return 0.0


def calculate_fetch_n(
    max_items: int,
    *,
    inject_dynamic_enabled: bool,
    inject_dynamic_max_items: int,
) -> int:
    fetch_n = int(max_items)
    if inject_dynamic_enabled:
        fetch_n = max(fetch_n, int(inject_dynamic_max_items))
    return fetch_n


def build_inject_candidates(
    results: List[Any],
    *,
    signature_fn: Callable[[str], str],
    normalize_tags_fn: Callable[[Any], List[str]],
    score_fn: Callable[[float, List[str], str], float],
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen_signatures = set()
    for result in results or []:
        content = getattr(result, "content", "")
        signature = signature_fn(content)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        metadata = getattr(result, "metadata", {}) or {}
        tags = normalize_tags_fn(metadata)
        source = getattr(result, "source", "")
        relevance = float(getattr(result, "relevance", 0.0) or 0.0)
        items.append(
            {
                "content": content,
                "source": source,
                "relevance": relevance,
                "score": score_fn(relevance, tags, source),
                "tags": tags,
            }
        )
    return items


def select_injected_items(
    items: List[Dict[str, Any]],
    *,
    threshold: float,
) -> Tuple[List[Dict[str, Any]], bool, str]:
    filtered = [item for item in items if item_score(item) >= float(threshold)]
    if items and not filtered:
        return [max(items, key=item_score)], True, "fallback_top1"
    return filtered, False, ""


def build_inject_metric_payload(
    *,
    reason: str,
    retrieved: int,
    filtered: List[Dict[str, Any]],
    threshold: float,
    max_items: int,
    fallback_used: bool,
    fallback_reason: str,
) -> Dict[str, Any]:
    injected = len(filtered)
    ratio = (injected / int(retrieved)) if retrieved else 0.0
    return {
        "event": "inject",
        "reason": reason,
        "retrieved": int(retrieved),
        "injected": injected,
        "ratio": round(ratio, 3),
        "threshold": round(float(threshold), 3),
        "max_items": int(max_items),
        "fallback": bool(fallback_used),
        "fallback_reason": fallback_reason,
        "top_score": round(item_score(filtered[0]), 3) if filtered else 0.0,
    }
