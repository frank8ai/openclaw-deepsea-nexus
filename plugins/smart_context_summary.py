"""
Shared turn-summary helpers for SmartContext.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from . import smart_context_text


@dataclass(frozen=True)
class TurnSummaryBuildResult:
    summary_result: smart_context_text.SummaryResult
    text: str


def build_turn_summary(
    user_message: str,
    ai_response: str,
    decisions: List[str],
    *,
    summary_template_enabled: bool,
    summary_template_fields: Iterable[str],
    summary_min_length: int,
    topic_max: int,
    topic_min_keywords: int,
    keyword_limit: int = 5,
    entity_limit: int = 5,
    action_limit: int = 5,
    question_limit: int = 5,
) -> TurnSummaryBuildResult:
    combined_text = f"{user_message}\n{ai_response}"
    summary_result = smart_context_text.sanitize_summary(
        ai_response,
        ai_response,
        min_summary_length=int(summary_min_length),
        fallback_max_chars=200,
    )
    if not summary_template_enabled:
        return TurnSummaryBuildResult(summary_result=summary_result, text=summary_result.summary)

    actions = smart_context_text.extract_actions(ai_response, max_items=max(1, int(action_limit)))
    questions = smart_context_text.extract_questions(combined_text, max_items=max(1, int(question_limit)))
    entities = smart_context_text.extract_key_entities(combined_text, limit=max(1, int(entity_limit)))
    keywords = smart_context_text.extract_keywords(
        f"{user_message} {ai_response}",
        limit=max(1, int(keyword_limit)),
    )
    topics = smart_context_text.extract_topics(
        combined_text,
        topic_max=max(1, int(topic_max)),
        topic_min_keywords=int(topic_min_keywords),
        keyword_limit=max(1, int(keyword_limit)),
    )

    fields = set(summary_template_fields or ())
    lines: List[str] = []
    if "summary" in fields:
        lines.append(f"Summary: {summary_result.summary}")
    if "decisions" in fields and decisions:
        lines.append(f"Decisions: {'; '.join(decisions[:3])}")
    if "topics" in fields and topics:
        lines.append(f"Topics: {', '.join(topics[:4])}")
    if "next_actions" in fields and actions:
        lines.append(f"Next: {'; '.join(actions[:3])}")
    if "questions" in fields and questions:
        lines.append(f"Questions: {'; '.join(questions[:3])}")
    if "entities" in fields and entities:
        lines.append(f"Entities: {', '.join(entities[:5])}")
    if "keywords" in fields and keywords:
        lines.append(f"Keywords: {', '.join(keywords[:6])}")

    return TurnSummaryBuildResult(
        summary_result=summary_result,
        text="\n".join(lines).strip(),
    )
