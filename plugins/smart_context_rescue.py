"""
Shared rescue helpers for SmartContext compression fallback.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


DEFAULT_DECISION_KEYWORDS = ["决定", "选择", "采用", "使用"]


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for item in items:
        cleaned = (item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def collect_rescue_updates(
    conversation: str,
    *,
    rescue_gold: bool,
    rescue_decisions: bool,
    rescue_next_actions: bool,
    decision_keywords: Optional[List[str]] = None,
    context_before: int = 30,
    context_after: int = 70,
    question_min_length: int = 6,
) -> Dict[str, List[str]]:
    conversation = conversation or ""
    updates = {
        "decisions": [],
        "next_actions": [],
        "open_questions": [],
    }

    if rescue_gold:
        gold_matches = re.findall(r"#GOLD[:\s]*(.+?)(?:\n|$)", conversation)
        updates["decisions"] = _dedupe(gold_matches)

    if rescue_decisions:
        for keyword in decision_keywords or DEFAULT_DECISION_KEYWORDS:
            if keyword not in conversation:
                continue
            idx = conversation.find(keyword)
            if idx == -1:
                continue
            context = conversation[max(0, idx - int(context_before)) : idx + int(context_after)].strip()
            if context:
                updates["next_actions"].append(context)
        updates["next_actions"] = _dedupe(updates["next_actions"])

    if rescue_next_actions:
        question_matches = re.findall(r"[?？](.+?)(?:\n|$)", conversation)
        updates["open_questions"] = _dedupe(
            [match.strip() for match in question_matches if len(match.strip()) >= int(question_min_length)]
        )

    return updates


def apply_rescue_updates(state: Dict[str, Any], updates: Dict[str, List[str]]) -> Dict[str, int]:
    state = state if isinstance(state, dict) else {}
    result = {
        "decisions_rescued": 0,
        "goals_rescued": 0,
        "questions_rescued": 0,
    }
    mapping = {
        "decisions": "decisions_rescued",
        "next_actions": "goals_rescued",
        "open_questions": "questions_rescued",
    }
    for key, count_key in mapping.items():
        bucket = state.setdefault(key, [])
        for item in updates.get(key, []):
            if item in bucket:
                continue
            bucket.append(item)
            result[count_key] += 1
    return result
