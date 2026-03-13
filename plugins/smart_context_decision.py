"""
Shared decision helpers for SmartContext trigger and topic-switch rules.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from . import smart_context_text


QUESTION_PATTERNS = (
    r"怎么",
    r"如何",
    r"是什么",
    r"为什么",
    r"哪些",
    r"区别",
    r"实现",
    r"使用",
    r"解决",
)


def is_context_starved(user_message: str, min_chars: int) -> bool:
    message = (user_message or "").strip()
    if len(message) <= int(min_chars):
        return True
    for keyword in ("继续", "接着", "刚才", "上次", "之前", "延续", "帮我继续"):
        if keyword in message:
            return True
    return False


def should_inject(
    user_message: str,
    *,
    inject_enabled: bool,
    association_enabled: bool,
    context_starved_min_chars: int,
    inject_mode: str,
) -> Tuple[bool, str]:
    if not inject_enabled:
        return False, "disabled"

    if association_enabled and is_context_starved(user_message, context_starved_min_chars):
        return True, "context_starved"

    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, user_message or ""):
            return True, "question"

    keywords = smart_context_text.extract_keywords(user_message or "", limit=5)
    mode = (inject_mode or "balanced").strip().lower()
    if mode == "aggressive":
        if any(keyword for keyword in keywords if len(keyword) > 3):
            return True, "keyword"
    elif mode == "conservative":
        if any(keyword for keyword in keywords if len(keyword) > 8):
            return True, "technical_term"
    else:
        if any(keyword for keyword in keywords if len(keyword) > 6):
            return True, "technical_term"

    return False, "none"


def detect_topic_switch(
    user_message: str,
    *,
    topic_switch_enabled: bool,
    last_keywords: List[str],
    topic_switch_keywords_max: int,
    topic_switch_min_overlap_ratio: float,
) -> Tuple[bool, List[str]]:
    if not topic_switch_enabled:
        return False, []
    message = (user_message or "").strip()
    if any(keyword in message for keyword in ("换个话题", "另一个问题", "新话题", "顺便问", "另外")):
        return True, []

    keywords = smart_context_text.extract_keywords(message, limit=max(1, int(topic_switch_keywords_max)))
    if not keywords:
        return False, []
    if not last_keywords:
        return False, keywords

    overlap = len(set(keywords) & set(last_keywords))
    ratio = overlap / float(max(1, len(set(keywords))))
    return ratio <= float(topic_switch_min_overlap_ratio), keywords
