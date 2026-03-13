"""
Shared conversation-analysis helpers for SmartContext storage flows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from . import smart_context_text


@dataclass(frozen=True)
class ConversationStoreData:
    combined_text: str
    summary: str
    keywords: List[str]
    decisions: List[str]
    topics: List[str]


def build_conversation_store_data(
    user_message: str,
    ai_response: str,
    *,
    summary: Optional[str] = None,
    summary_min_length: int = 50,
    summary_fallback_max_chars: int = 100,
    keyword_limit: int = 5,
    decision_max: int = 3,
    topic_max: int = 3,
    topic_min_keywords: int = 2,
) -> ConversationStoreData:
    combined_text = f"{user_message}\n{ai_response}"
    if summary is None:
        summary = smart_context_text.extract_summary(
            ai_response,
            min_summary_length=int(summary_min_length),
            fallback_max_chars=int(summary_fallback_max_chars),
        ).summary

    return ConversationStoreData(
        combined_text=combined_text,
        summary=summary,
        keywords=smart_context_text.extract_keywords(
            f"{user_message} {ai_response}",
            limit=max(1, int(keyword_limit)),
        ),
        decisions=smart_context_text.extract_decision_blocks(
            combined_text,
            max_items=max(1, int(decision_max)),
        ),
        topics=smart_context_text.extract_topics(
            combined_text,
            topic_max=max(1, int(topic_max)),
            topic_min_keywords=int(topic_min_keywords),
            keyword_limit=max(1, int(keyword_limit)),
        ),
    )
