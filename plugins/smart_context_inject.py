"""
Shared injection helpers for SmartContext scoring, trimming, and thresholds.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def finalize_injected_items(
    filtered: List[Dict[str, Any]],
    graph_items: List[Dict[str, Any]],
    *,
    topk_only: bool,
    max_items: int,
    max_chars_per_item: int,
    max_lines_per_item: int,
    max_lines_total: int,
) -> List[Dict[str, Any]]:
    final = list(filtered or []) + list(graph_items or [])
    if topk_only:
        final = sorted(
            final,
            key=lambda item: _item_score(item),
            reverse=True,
        )[: max(1, int(max_items))]
    return trim_injected_items(
        final,
        max_chars_per_item=max_chars_per_item,
        max_lines_per_item=max_lines_per_item,
        max_lines_total=max_lines_total,
    )


def trim_injected_items(
    items: List[Dict[str, Any]],
    *,
    max_chars_per_item: int,
    max_lines_per_item: int,
    max_lines_total: int,
) -> List[Dict[str, Any]]:
    if not items:
        return []
    max_chars = max(80, int(max_chars_per_item))
    max_lines_per = max(2, int(max_lines_per_item))
    max_lines_total = max(10, int(max_lines_total))

    trimmed: List[Dict[str, Any]] = []
    used_lines = 0
    for item in items:
        content = (item.get("content") or "").strip()
        if not content:
            continue
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) > max_lines_per:
            lines = lines[:max_lines_per]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "..."
        line_count = max(1, text.count("\n") + 1)
        if used_lines + line_count > max_lines_total:
            break
        used_lines += line_count
        normalized = dict(item)
        normalized["content"] = text
        trimmed.append(normalized)
    return trimmed


def _item_score(item: Dict[str, Any]) -> float:
    try:
        return float(item.get("score", item.get("relevance", 0.0)))
    except Exception:
        return 0.0


def normalize_tags(metadata: Any) -> List[str]:
    tags: List[str] = []
    if isinstance(metadata, dict):
        raw = metadata.get("tags") or []
        if isinstance(raw, list):
            tags.extend([str(tag).strip() for tag in raw if str(tag).strip()])
        elif isinstance(raw, str):
            tags.extend([tag.strip() for tag in raw.split(",") if tag.strip()])
    return tags


def score_injected_item(
    relevance: float,
    tags: List[str],
    source: str,
    *,
    decision_boost: float,
    topic_boost: float,
    summary_boost: float,
) -> float:
    score = float(relevance or 0.0)
    tag_str = ",".join(tags)
    if "type:decision_block" in tag_str or "决策块" in (source or ""):
        score += float(decision_boost)
    if "type:topic_block" in tag_str or "主题块" in (source or ""):
        score += float(topic_boost)
    if "type:summary" in tag_str or "摘要" in (source or ""):
        score += float(summary_boost)
    return min(1.5, score)


def has_signal_tag(tags: List[str], source: str) -> bool:
    if not tags and not source:
        return False
    tag_str = ",".join(tags)
    if "type:decision_block" in tag_str or "type:topic_block" in tag_str:
        return True
    if "决策块" in (source or "") or "主题块" in (source or ""):
        return True
    return False


def dynamic_inject_params(
    reason: str,
    items: List[Dict[str, Any]],
    *,
    max_items: int,
    threshold: float,
    inject_dynamic_enabled: bool,
    dynamic_max_items: int,
    dynamic_low_signal_penalty: int,
    dynamic_high_signal_bonus: int,
) -> Tuple[int, float]:
    max_items = int(max_items)
    threshold = float(threshold)

    if reason == "context_starved":
        max_items = max(1, min(2, max_items))
        threshold = max(0.0, min(1.0, threshold * 0.85))

    if not inject_dynamic_enabled:
        return max_items, threshold

    signal_hits = sum(1 for item in items if has_signal_tag(item.get("tags", []), item.get("source", "")))
    if signal_hits == 0:
        max_items = max(1, max_items - int(dynamic_low_signal_penalty))
        threshold = min(0.95, threshold + 0.05)
    elif signal_hits >= 2:
        max_items = min(int(dynamic_max_items), max_items + int(dynamic_high_signal_bonus))
        threshold = max(0.0, threshold - 0.05)

    return max_items, threshold
