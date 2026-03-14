"""
Shared recall normalization and filtering helpers for SmartContext injection.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Tuple

try:
    from . import smart_context_text
except ImportError:
    import smart_context_text

TRACE_EVIDENCE_KEYS = (
    "evidence",
    "evidence_pointers",
    "replay",
    "replay_commands",
)

TRACE_SIGNAL_BY_KIND = {
    "decision": "decision",
    "constraint": "constraint",
    "blocker": "blocker",
    "summary": "summary",
    "topic": "topic",
    "evidence": "evidence",
    "replay": "replay",
    "graph_edge": "graph",
}

TRACE_KIND_BY_TAG = {
    "type:decision_block": "decision",
    "type:topic_block": "topic",
    "type:summary": "summary",
    "type:metadata": "metadata",
}

INTENT_HINTS = {
    "decision": ("决定", "决策", "方案", "选择", "采用", "结论", "decision", "decide", "adopt"),
    "constraint": ("约束", "限制", "边界", "兼容", "必须", "不能", "constraint", "limit", "must", "compat"),
    "blocker": (
        "阻塞",
        "卡住",
        "风险",
        "问题",
        "报错",
        "失败",
        "缺失",
        "blocker",
        "blocking",
        "blocked",
        "stuck",
        "risk",
        "error",
        "fail",
        "missing",
    ),
    "evidence": ("证据", "日志", "文件", "报告", "artifact", "evidence", "log", "logs", "file", "path", "report"),
    "replay": (
        "复现",
        "命令",
        "重跑",
        "恢复",
        "接续",
        "续跑",
        "replay",
        "command",
        "pytest",
        "run",
        "resume",
        "resumed",
    ),
    "topic": ("主题", "话题", "项目", "模块", "topic", "project", "module"),
    "summary": ("总结", "摘要", "概览", "overview", "summary"),
}

QUERY_REASON_DEFAULT_INTENTS = {
    "context_starved": ["summary"],
    "technical_term": ["topic"],
    "keyword": ["topic"],
}

FRESHNESS_QUERY_HINTS = (
    "current",
    "latest",
    "final",
    "still",
    "right now",
    "currently",
    "now",
    "today",
    "当前",
    "现在",
    "最新",
    "最终",
    "仍然",
    "还在",
)

CURRENT_ITEM_HINTS = (
    "current",
    "latest",
    "final",
    "active",
    "live",
    "now",
    "当前",
    "最新",
    "最终",
)

STALE_ITEM_HINTS = (
    "old",
    "legacy",
    "archive",
    "archived",
    "historical",
    "history",
    "prior",
    "previous",
    "stale",
    "旧",
    "历史",
    "归档",
    "过时",
)

RESUME_QUERY_HINTS = (
    "resume",
    "resumed",
    "恢复",
    "接续",
    "续跑",
)


def _read_result_field(result: Any, field: str, default: Any) -> Any:
    if isinstance(result, dict):
        return result.get(field, default)
    return getattr(result, field, default)


def _clean_text_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = [value]

    out: List[str] = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            text = (
                item.get("text")
                or item.get("path")
                or item.get("id")
                or item.get("value")
                or ""
            )
        else:
            text = item
        normalized = str(text or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _normalize_tags(metadata: Any, normalize_tags_fn: Callable[[Any], List[str]] | None) -> List[str]:
    if callable(normalize_tags_fn):
        try:
            return list(normalize_tags_fn(metadata) or [])
        except Exception:
            return []

    tags: List[str] = []
    if isinstance(metadata, dict):
        raw = metadata.get("tags") or []
        if isinstance(raw, list):
            tags.extend([str(tag).strip() for tag in raw if str(tag).strip()])
        elif isinstance(raw, str):
            tags.extend([tag.strip() for tag in raw.split(",") if tag.strip()])
    return tags


def _infer_origin(result: Any, metadata: Dict[str, Any]) -> str:
    origin = str(metadata.get("origin", "") or "").strip() if isinstance(metadata, dict) else ""
    if origin:
        return origin
    return str(_read_result_field(result, "origin", "") or "").strip()


def _infer_kind(tags: List[str], source: str, metadata: Dict[str, Any], origin: str) -> str:
    if isinstance(metadata, dict):
        metadata_kind = str(metadata.get("kind", "") or "").strip()
        if metadata_kind:
            return metadata_kind

    for tag in tags or []:
        mapped = TRACE_KIND_BY_TAG.get(str(tag).strip())
        if mapped:
            return mapped

    source_text = str(source or "").lower()
    if origin == "graph" or source_text == "graph":
        return "graph_edge"
    if "决策块" in str(source or ""):
        return "decision"
    if "主题块" in str(source or ""):
        return "topic"
    if "摘要" in str(source or ""):
        return "summary"
    return "note"


def _extract_evidence(
    result: Any,
    metadata: Dict[str, Any],
    *,
    kind: str,
    content: str,
) -> List[str]:
    evidence: List[str] = []
    evidence.extend(_clean_text_list(_read_result_field(result, "evidence", [])))
    for key in TRACE_EVIDENCE_KEYS:
        evidence.extend(_clean_text_list((metadata or {}).get(key)))
    if not evidence and kind in {"evidence", "replay"}:
        evidence.extend(_clean_text_list(content))
    deduped: List[str] = []
    seen = set()
    for item in evidence:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped[:3]


def _infer_signal(kind: str, tags: List[str], source: str, origin: str) -> str:
    signal = TRACE_SIGNAL_BY_KIND.get(str(kind).strip())
    if signal:
        return signal

    tag_set = {str(tag).strip() for tag in (tags or [])}
    if "type:decision_block" in tag_set or "决策块" in str(source or ""):
        return "decision"
    if "type:topic_block" in tag_set or "主题块" in str(source or ""):
        return "topic"
    if "type:summary" in tag_set or "摘要" in str(source or ""):
        return "summary"
    if origin == "graph":
        return "graph"
    return "semantic"


def _build_why(*, reason: str, signal: str, origin: str, evidence: List[str]) -> str:
    parts: List[str] = []
    if reason:
        parts.append(f"reason={reason}")
    if signal:
        parts.append(f"signal={signal}")
    if origin:
        parts.append(f"origin={origin}")
    if evidence:
        parts.append(f"evidence={len(evidence)}")
    return " | ".join(parts)


def _dedupe_strings(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _query_terms(query: str, *, keyword_limit: int) -> List[str]:
    terms: List[str] = []
    lowered = str(query or "").lower()
    terms.extend(smart_context_text.extract_keywords(lowered, limit=max(4, int(keyword_limit))))
    terms.extend([item.lower() for item in smart_context_text.extract_key_entities(query, limit=4)])
    for token in re.findall(r"[a-z0-9_./-]{3,}", lowered):
        terms.append(token)
        if "-" in token:
            terms.extend(part for part in token.split("-") if len(part) >= 3)
        if "/" in token:
            terms.extend(part for part in token.split("/") if len(part) >= 3)
    for token in re.findall(r"[\u4e00-\u9fff]{2,12}", str(query or "")):
        terms.append(token)
    return _dedupe_strings(terms)[: max(4, int(keyword_limit) * 2)]


def infer_query_profile(
    query: str,
    *,
    reason: str = "",
    keyword_limit: int = 8,
) -> Dict[str, Any]:
    lowered = str(query or "").lower()
    intents: List[str] = []
    for intent, hints in INTENT_HINTS.items():
        if any(hint.lower() in lowered for hint in hints):
            intents.append(intent)
    for intent in QUERY_REASON_DEFAULT_INTENTS.get(str(reason or "").strip(), []):
        if intent not in intents:
            intents.append(intent)

    scope_terms = _query_terms(query, keyword_limit=max(4, int(keyword_limit)))
    return {
        "query": str(query or "").strip(),
        "reason": str(reason or "").strip(),
        "intents": intents,
        "scope_terms": scope_terms,
        "freshness_required": any(hint.lower() in lowered for hint in FRESHNESS_QUERY_HINTS),
        "resume_requested": any(hint.lower() in lowered for hint in RESUME_QUERY_HINTS),
    }


def _score_scope_matches(item: Dict[str, Any], scope_terms: List[str]) -> Tuple[List[str], Dict[str, float]]:
    if not scope_terms:
        return [], {}

    metadata = item.get("metadata", {}) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    matches: List[str] = []
    breakdown: Dict[str, float] = {}
    match_specs = (
        ("project", 0.08),
        ("category", 0.06),
        ("source", 0.04),
    )
    for field, weight in match_specs:
        value = ""
        if field == "source":
            value = str(item.get("source", "") or "").strip()
        else:
            value = str(metadata.get(field, "") or "").strip()
        if not value:
            continue
        value_lower = value.lower()
        matched_terms = [term for term in scope_terms if term and term in value_lower]
        if matched_terms:
            matches.append(value)
            breakdown[f"scope_{field}"] = weight
            if len(matched_terms) > 1:
                breakdown[f"scope_{field}_overlap"] = min(0.04, 0.02 * float(len(matched_terms) - 1))
    return _dedupe_strings(matches)[:2], breakdown


def _score_freshness_matches(item: Dict[str, Any], *, freshness_required: bool) -> Tuple[List[str], Dict[str, float]]:
    if not freshness_required:
        return [], {}

    metadata = item.get("metadata", {}) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    haystack = " ".join(
        [
            str(item.get("source", "") or ""),
            str(metadata.get("project", "") or ""),
            str(metadata.get("category", "") or ""),
        ]
    ).lower()

    matches: List[str] = []
    breakdown: Dict[str, float] = {}
    if any(hint.lower() in haystack for hint in CURRENT_ITEM_HINTS):
        matches.append("current")
        breakdown["freshness_current"] = 0.08
    if any(hint.lower() in haystack for hint in STALE_ITEM_HINTS):
        matches.append("stale")
        breakdown["freshness_stale_penalty"] = -0.1
    return matches, breakdown


def _score_intent_matches(item: Dict[str, Any], intents: List[str], reason: str) -> Tuple[List[str], Dict[str, float]]:
    if not intents:
        return [], {}

    matched: List[str] = []
    breakdown: Dict[str, float] = {}
    kind = str(item.get("kind", "") or "").strip()
    signal = str(((item.get("trace") or {}) if isinstance(item.get("trace"), dict) else {}).get("signal", "") or "").strip()
    evidence = _clean_text_list(item.get("evidence", []))

    if kind in intents:
        matched.append(kind)
        breakdown["intent_kind"] = 0.18
    elif signal in intents:
        matched.append(signal)
        breakdown["intent_signal"] = 0.12

    if "decision" in intents and evidence:
        breakdown["evidence_support"] = max(breakdown.get("evidence_support", 0.0), 0.06)
    if "evidence" in intents and evidence:
        matched.append("evidence")
        breakdown["evidence_match"] = max(breakdown.get("evidence_match", 0.0), 0.12)
    if "replay" in intents and (
        kind == "replay"
        or any("pytest" in evidence_item.lower() or " " in evidence_item for evidence_item in evidence)
    ):
        matched.append("replay")
        breakdown["replay_match"] = max(breakdown.get("replay_match", 0.0), 0.12)
    if reason == "context_starved" and kind == "summary":
        matched.append("summary")
        breakdown["context_starved_summary"] = 0.08
    if reason in {"technical_term", "keyword"} and kind in {"topic", "summary"}:
        breakdown["typed_query_topic"] = 0.05

    return _dedupe_strings(matched)[:3], breakdown


def rerank_recall_candidates(
    items: List[Dict[str, Any]],
    *,
    query: str,
    reason: str = "",
    query_profile: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    profile = query_profile or infer_query_profile(query, reason=reason)
    intents = list(profile.get("intents", []) or [])
    scope_terms = list(profile.get("scope_terms", []) or [])
    freshness_required = bool(profile.get("freshness_required"))
    resume_requested = bool(profile.get("resume_requested"))
    available_signals = {
        str(item.get("kind", "") or "").strip()
        for item in items or []
        if str(item.get("kind", "") or "").strip()
    }
    for item in items or []:
        trace = item.get("trace", {}) if isinstance(item, dict) else {}
        if isinstance(trace, dict):
            signal = str(trace.get("signal", "") or "").strip()
            if signal:
                available_signals.add(signal)
    replay_available = "replay" in available_signals

    reranked: List[Dict[str, Any]] = []
    for raw_item in items or []:
        item = dict(raw_item or {})
        trace = item.get("trace", {})
        if not isinstance(trace, dict):
            trace = {}

        base_score = item_score(item)
        final_score = base_score
        score_breakdown: Dict[str, float] = {"base": round(base_score, 3)}

        matched_intents, intent_breakdown = _score_intent_matches(item, intents, reason)
        for key, value in intent_breakdown.items():
            final_score += value
            score_breakdown[key] = round(value, 3)

        scope_matches, scope_breakdown = _score_scope_matches(item, scope_terms)
        for key, value in scope_breakdown.items():
            final_score += value
            score_breakdown[key] = round(value, 3)

        freshness_matches, freshness_breakdown = _score_freshness_matches(
            item,
            freshness_required=freshness_required,
        )
        for key, value in freshness_breakdown.items():
            final_score += value
            score_breakdown[key] = round(value, 3)

        evidence = _clean_text_list(item.get("evidence", []))
        if evidence and "generic_evidence_bonus" not in score_breakdown:
            final_score += 0.02
            score_breakdown["generic_evidence_bonus"] = 0.02
        if reason == "context_starved" and scope_matches and str(item.get("kind", "") or "").strip() == "summary":
            final_score += 0.1
            score_breakdown["context_starved_scope"] = 0.1
        if resume_requested and not replay_available and str(item.get("kind", "") or "").strip() == "summary":
            final_score += 0.24
            score_breakdown["resume_without_replay_summary"] = 0.24

        final_score = max(0.0, min(1.75, final_score))
        item["score"] = round(final_score, 3)

        if matched_intents:
            trace["matched_intents"] = matched_intents
        if scope_matches:
            trace["scope_matches"] = scope_matches
        if freshness_matches:
            trace["freshness_matches"] = freshness_matches
        trace["score_breakdown"] = score_breakdown
        item["trace"] = trace

        why = str(item.get("why", "") or "").strip()
        extras: List[str] = []
        if matched_intents:
            extras.append(f"match={'/'.join(matched_intents[:2])}")
        if scope_matches:
            extras.append(f"scope={'/'.join(scope_matches[:2])}")
        if "current" in freshness_matches:
            extras.append("fresh=current")
        if "stale" in freshness_matches:
            extras.append("fresh=stale")
        if resume_requested and not replay_available and str(item.get("kind", "") or "").strip() == "summary":
            extras.append("fallback=summary")
        for extra in extras:
            if extra not in why:
                why = f"{why} | {extra}" if why else extra
        item["why"] = why
        reranked.append(item)

    return sorted(
        reranked,
        key=lambda item: (item_score(item), float(item.get("relevance", 0.0) or 0.0)),
        reverse=True,
    )


def normalize_recall_candidate(
    result: Any,
    *,
    reason: str = "",
    normalize_tags_fn: Callable[[Any], List[str]] | None = None,
    score_fn: Callable[[float, List[str], str], float] | None = None,
) -> Dict[str, Any]:
    content = str(_read_result_field(result, "content", "") or "")
    source = str(_read_result_field(result, "source", "") or "")
    metadata = _read_result_field(result, "metadata", {}) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    tags = _normalize_tags(metadata, normalize_tags_fn)
    try:
        relevance = float(_read_result_field(result, "relevance", 0.0) or 0.0)
    except Exception:
        relevance = 0.0

    if callable(score_fn):
        try:
            score = float(score_fn(relevance, tags, source))
        except Exception:
            score = relevance
    else:
        score = relevance

    origin = _infer_origin(result, metadata)
    kind = _infer_kind(tags, source, metadata, origin)
    evidence = _extract_evidence(result, metadata, kind=kind, content=content)
    signal = _infer_signal(kind, tags, source, origin)

    existing_trace = metadata.get("trace", {})
    if not isinstance(existing_trace, dict):
        existing_trace = {}

    why = str(
        _read_result_field(result, "why", "") or metadata.get("why", "") or _build_why(
            reason=reason,
            signal=signal,
            origin=origin,
            evidence=evidence,
        )
    ).strip()

    trace: Dict[str, Any] = dict(existing_trace)
    if reason and "reason" not in trace:
        trace["reason"] = reason
    if signal and "signal" not in trace:
        trace["signal"] = signal
    if origin and "origin" not in trace:
        trace["origin"] = origin
    if kind and "kind" not in trace:
        trace["kind"] = kind
    if source and "source" not in trace:
        trace["source"] = source
    if tags and "tags" not in trace:
        trace["tags"] = list(tags)
    if evidence and "evidence" not in trace:
        trace["evidence"] = list(evidence)
    for field in ("category", "project", "source_id"):
        value = str(metadata.get(field, "") or "").strip()
        if value and field not in trace:
            trace[field] = value

    return {
        "content": content,
        "source": source,
        "relevance": relevance,
        "score": score,
        "tags": tags,
        "metadata": metadata,
        "origin": origin,
        "kind": kind,
        "why": why,
        "evidence": evidence,
        "trace": trace,
    }


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
    reason: str = "",
    signature_fn: Callable[[str], str],
    normalize_tags_fn: Callable[[Any], List[str]],
    score_fn: Callable[[float, List[str], str], float],
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    seen_signatures = set()
    for result in results or []:
        content = str(_read_result_field(result, "content", "") or "")
        signature = signature_fn(content)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        items.append(
            normalize_recall_candidate(
                result,
                reason=reason,
                normalize_tags_fn=normalize_tags_fn,
                score_fn=score_fn,
            )
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
    top_item = filtered[0] if filtered else {}
    top_evidence = top_item.get("evidence") or []
    if not isinstance(top_evidence, list):
        top_evidence = _clean_text_list(top_evidence)
    top_trace = top_item.get("trace", {}) or {}
    if not isinstance(top_trace, dict):
        top_trace = {}
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
        "top_source": str(top_item.get("source", "") or ""),
        "top_why": str(top_item.get("why", "") or ""),
        "top_evidence_count": len(top_evidence),
        "top_matched_intents": list(top_trace.get("matched_intents", []) or []),
        "top_scope_matches": list(top_trace.get("scope_matches", []) or []),
        "top_score_breakdown": dict(top_trace.get("score_breakdown", {}) or {}),
    }
