"""
Shared text extraction helpers for SmartContext summaries, keywords, and topics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List

try:
    from ..context_contract import normalize_typed_context
except ImportError:
    from context_contract import normalize_typed_context


STOP_WORDS = {
    "的",
    "了",
    "是",
    "在",
    "我",
    "你",
    "他",
    "这",
    "那",
    "和",
    "就",
    "都",
    "也",
    "会",
    "可以",
    "什么",
    "怎么",
    "如何",
    "有没有",
    "是不是",
    "能不能",
}

DECISION_KEYWORDS = ("决定", "选择", "采用", "使用", "结论", "方案", "策略", "切换", "改为")
TOPIC_HINT_KEYWORDS = ("主题", "话题", "模块", "子系统", "项目")


@dataclass
class SummaryResult:
    summary: str
    status: str


def _dedupe(items: List[str], limit: int) -> List[str]:
    seen = set()
    unique: List[str] = []
    for item in items:
        cleaned = (item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique


def extract_key_entities(text: str, limit: int = 5) -> List[str]:
    if not text:
        return []
    candidates: List[str] = []
    for match in re.findall(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)", text):
        candidates.append(match)
    for match in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\(\)", text):
        candidates.append(match)
    cleaned: List[str] = []
    for item in candidates:
        if len(item) < 4 or len(item) > 120:
            continue
        lowered = item.lower()
        if lowered.startswith(("sk-", "nvapi-", "ghp_")):
            continue
        if re.search(r"[A-Za-z0-9]{20,}", item):
            continue
        cleaned.append(item)
    return _dedupe(cleaned, max(1, int(limit)))


def append_entities(summary: str, entities: List[str], limit: int = 5) -> str:
    if not entities:
        return summary
    missing = [entity for entity in entities if entity not in summary]
    if not missing:
        return summary
    suffix = " 关键项: " + ", ".join(missing[: max(1, int(limit))])
    return (summary + suffix).strip()


def sanitize_summary(
    summary: str,
    fallback: str,
    *,
    min_summary_length: int = 50,
    fallback_max_chars: int = 200,
) -> SummaryResult:
    summary = (summary or "").strip()
    summary = re.sub(r"```[\s\S]*?```", "", summary).strip()
    if summary.endswith("...") and len(summary) < 10:
        summary = summary[:-3].strip()
    min_len = max(20, int(min_summary_length / 2))
    entities = extract_key_entities(fallback)
    if len(summary) >= min_len:
        return SummaryResult(summary=append_entities(summary, entities), status="ok")
    fallback_text = re.sub(r"```[\s\S]*?```", "", (fallback or "")).strip()
    if not fallback_text:
        return SummaryResult(summary=summary, status="short")
    rebuilt = (fallback_text[:fallback_max_chars] + ("..." if len(fallback_text) > fallback_max_chars else "")).strip()
    return SummaryResult(summary=append_entities(rebuilt, entities), status="fallback")


def extract_summary(
    text: str,
    *,
    min_summary_length: int = 50,
    fallback_max_chars: int = 200,
) -> SummaryResult:
    json_match = re.search(r"```json\s*\n([\s\S]*?)\n```", text or "")
    if json_match:
        try:
            data = normalize_typed_context(json.loads(json_match.group(1)))
            if data.get("summary"):
                return SummaryResult(
                    summary=append_entities(str(data.get("summary", "")), extract_key_entities(text)),
                    status="ok",
                )
            return sanitize_summary(
                data.get("summary", ""),
                text,
                min_summary_length=min_summary_length,
                fallback_max_chars=fallback_max_chars,
            )
        except json.JSONDecodeError:
            pass

    summary_match = re.search(r"## 📋 总结[^\n]*\n([\s\S]*?)(?=\n\n|$)", text or "")
    if summary_match:
        return sanitize_summary(
            summary_match.group(1).strip(),
            text,
            min_summary_length=min_summary_length,
            fallback_max_chars=fallback_max_chars,
        )

    default_summary = ((text or "")[:fallback_max_chars]).strip()
    return sanitize_summary(
        default_summary,
        text,
        min_summary_length=min_summary_length,
        fallback_max_chars=fallback_max_chars,
    )


def extract_keywords(text: str, limit: int = 5) -> List[str]:
    words = re.findall(r"\b\w+\b", (text or "").lower())
    keywords = [word for word in words if word not in STOP_WORDS and len(word) > 2]
    return _dedupe(keywords, max(1, int(limit)))


def extract_decision_blocks(text: str, max_items: int = 3) -> List[str]:
    if not text:
        return []
    blocks: List[str] = []
    text_without_code = re.sub(r"```[\s\S]*?```", "", text)

    json_match = re.search(r"```json\s*\n([\s\S]*?)\n```", text)
    if json_match:
        try:
            data = normalize_typed_context(json.loads(json_match.group(1)))
            if data.get("summary"):
                blocks.append(str(data["summary"]).strip())
            for value in data.get("decisions", []):
                if isinstance(value, str) and value.strip():
                    blocks.append(value.strip())
        except json.JSONDecodeError:
            pass

    for raw in text_without_code.splitlines():
        line = raw.strip(" \t-•")
        if not line:
            continue
        if "#GOLD" in line:
            line = re.sub(r".*#GOLD[:\s]*", "", line).strip()
        if any(keyword in line for keyword in DECISION_KEYWORDS) and len(line) >= 6:
            blocks.append(line)

    return _dedupe(blocks, max(1, int(max_items)))


def extract_actions(text: str, max_items: int = 5) -> List[str]:
    if not text:
        return []
    actions: List[str] = []
    for raw in text.splitlines():
        line = raw.strip(" \t-•")
        if not line:
            continue
        if line.lower().startswith(("todo", "next", "步骤")):
            actions.append(line)
            continue
        if "下一步" in line or "继续" in line:
            actions.append(line)
    return _dedupe(actions, max(1, int(max_items)))


def extract_questions(text: str, max_items: int = 5) -> List[str]:
    if not text:
        return []
    questions: List[str] = []
    for raw in text.splitlines():
        line = raw.strip(" \t-•")
        if not line:
            continue
        if "?" in line or "？" in line:
            questions.append(line)
    return _dedupe(questions, max(1, int(max_items)))


def extract_topics(
    text: str,
    *,
    topic_max: int = 3,
    topic_min_keywords: int = 2,
    keyword_limit: int = 5,
) -> List[str]:
    if not text:
        return []
    topics: List[str] = []
    for raw in text.splitlines():
        line = raw.strip(" \t-•")
        if not line:
            continue
        if line.startswith("## "):
            topics.append(line[3:].strip()[:60])
        if any(keyword in line for keyword in TOPIC_HINT_KEYWORDS) and len(line) <= 80:
            topics.append(line)
    keywords = extract_keywords(text, limit=max(1, int(keyword_limit)))
    if len(keywords) >= int(topic_min_keywords):
        topics.append(" / ".join(keywords[: int(topic_min_keywords) + 1]))
    return _dedupe(topics, max(1, int(topic_max)))
