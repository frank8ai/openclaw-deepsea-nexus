"""
Shared prompt-formatting helpers for SmartContext injected memory.
"""

from __future__ import annotations

from typing import Any, Iterable, List


def _read_field(entry: Any, field: str, default: Any) -> Any:
    if isinstance(entry, dict):
        return entry.get(field, default)
    return getattr(entry, field, default)


def _normalize_text_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]
    out: List[str] = []
    for item in raw_items:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _read_trace_field(entry: Any, field: str, default: Any) -> Any:
    trace = _read_field(entry, "trace", {})
    if isinstance(trace, dict) and field in trace:
        return trace.get(field, default)
    return _read_field(entry, field, default)


def build_trace_lines(
    entry: Any,
    *,
    max_evidence_items: int = 2,
    max_evidence_chars: int = 80,
) -> List[str]:
    lines: List[str] = []
    why = str(_read_trace_field(entry, "why", "") or "").strip()
    if not why:
        reason = str(_read_trace_field(entry, "reason", "") or "").strip()
        signal = str(_read_trace_field(entry, "signal", "") or "").strip()
        origin = str(_read_trace_field(entry, "origin", "") or "").strip()
        evidence = _normalize_text_list(_read_trace_field(entry, "evidence", []))
        parts: List[str] = []
        if reason:
            parts.append(f"reason={reason}")
        if signal:
            parts.append(f"signal={signal}")
        if origin:
            parts.append(f"origin={origin}")
        if evidence:
            parts.append(f"evidence={len(evidence)}")
        why = " | ".join(parts)
    if why:
        lines.append(f"Why: {why}")

    evidence = _normalize_text_list(_read_trace_field(entry, "evidence", []))
    if evidence:
        trimmed: List[str] = []
        for item in evidence[: max(1, int(max_evidence_items))]:
            text = item
            if len(text) > int(max_evidence_chars):
                text = text[: int(max_evidence_chars)].rstrip() + "..."
            trimmed.append(text)
        lines.append(f"Evidence: {'; '.join(trimmed)}")
    return lines


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
        parts.extend(build_trace_lines(entry))
        parts.append("")
    return "\n".join(parts)
