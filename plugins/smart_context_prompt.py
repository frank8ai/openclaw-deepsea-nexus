"""
Shared prompt-formatting helpers for SmartContext injected memory.
"""

from __future__ import annotations

from typing import Any, Iterable


def _read_field(entry: Any, field: str, default: Any) -> Any:
    if isinstance(entry, dict):
        return entry.get(field, default)
    return getattr(entry, field, default)


def build_context_prompt(entries: Iterable[Any], *, max_chars_per_item: int = 200) -> str:
    items = list(entries or [])
    if not items:
        return ""

    parts = ["## 相关记忆", ""]
    for index, entry in enumerate(items, 1):
        source = str(_read_field(entry, "source", "未知") or "未知")
        relevance = _read_field(entry, "relevance", 0.0)
        try:
            relevance = float(relevance)
        except Exception:
            relevance = 0.0
        content = str(_read_field(entry, "content", "") or "")
        parts.append(f"【{index}】({source} - {relevance:.2f})")
        parts.append(content[: max(1, int(max_chars_per_item))])
        parts.append("")
    return "\n".join(parts)
