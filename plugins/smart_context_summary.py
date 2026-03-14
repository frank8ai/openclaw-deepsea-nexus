"""
Shared turn-summary helpers for SmartContext.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from . import smart_context_rescue
from . import smart_context_text

try:
    from ..context_contract import normalize_typed_context
except ImportError:
    from context_contract import normalize_typed_context


@dataclass(frozen=True)
class TurnSummaryBuildResult:
    summary_result: smart_context_text.SummaryResult
    text: str
    typed_context: Dict[str, Any]


def _merge_items(primary: List[str], secondary: List[str], *, limit: int, prefixes: tuple[str, ...] = ()) -> List[str]:
    seen = set()
    merged: List[str] = []
    for item in (primary or []) + (secondary or []):
        cleaned = smart_context_rescue._canonical_item(item, prefixes)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        merged.append(cleaned)
        if len(merged) >= max(1, int(limit)):
            break
    return merged


def _is_explicit_evidence_pointer(item: str) -> bool:
    cleaned = (item or "").strip()
    if not cleaned:
        return False
    if "/" in cleaned or "\\" in cleaned:
        return True
    if "#L" in cleaned or ":" in cleaned:
        return True
    lowered = cleaned.lower()
    return any(token in lowered for token in (".log", "artifact", "hash", "report"))


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
        return TurnSummaryBuildResult(
            summary_result=summary_result,
            text=summary_result.summary,
            typed_context=normalize_typed_context({"summary": summary_result.summary}),
        )

    rescue_updates = smart_context_rescue.collect_rescue_updates(
        combined_text,
        rescue_gold=True,
        rescue_decisions=True,
        rescue_next_actions=True,
        rescue_goal=True,
        rescue_status=True,
        rescue_constraints=True,
        rescue_blockers=True,
        rescue_evidence=True,
        rescue_replay=True,
    )
    actions = _merge_items(
        rescue_updates.get("next_actions", []),
        smart_context_text.extract_actions(ai_response, max_items=max(1, int(action_limit))),
        limit=max(1, int(action_limit)),
        prefixes=smart_context_rescue.NEXT_PREFIXES,
    )
    questions = _merge_items(
        smart_context_text.extract_questions(combined_text, max_items=max(1, int(question_limit))),
        rescue_updates.get("open_questions", []),
        limit=max(1, int(question_limit)),
    )
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

    constraints = rescue_updates.get("constraints", [])[:3]
    blockers = rescue_updates.get("blockers", [])[:3]
    evidence = [
        item
        for item in (rescue_updates.get("evidence_pointers", []) or [])
        if _is_explicit_evidence_pointer(item)
    ][:3]
    replay_commands = rescue_updates.get("replay_commands", [])[:1]
    has_decision_evidence = bool(evidence or replay_commands)
    decision_items = _merge_items(decisions, rescue_updates.get("decisions", []), limit=3) if has_decision_evidence else []
    goal = str(rescue_updates.get("current_goal", "") or "").strip()
    status = str(rescue_updates.get("current_status", "") or "").strip()

    fields = set(summary_template_fields or ())
    lines: List[str] = []
    if "summary" in fields:
        lines.append(f"Summary: {summary_result.summary}")
    if "goal" in fields and goal:
        lines.append(f"Goal: {goal}")
    if "status" in fields and status:
        lines.append(f"Status: {status}")
    if "decisions" in fields and decision_items:
        lines.append(f"Decisions: {'; '.join(decision_items[:3])}")
    if "constraints" in fields and constraints:
        lines.append(f"Constraints: {'; '.join(constraints[:3])}")
    if "blockers" in fields and blockers:
        lines.append(f"Blockers: {'; '.join(blockers[:3])}")
    if "topics" in fields and topics:
        lines.append(f"Topics: {', '.join(topics[:4])}")
    if "next_actions" in fields and actions:
        lines.append(f"Next: {'; '.join(actions[:3])}")
    if "questions" in fields and questions:
        lines.append(f"Questions: {'; '.join(questions[:3])}")
    if "evidence" in fields and evidence:
        lines.append(f"Evidence: {'; '.join(evidence[:3])}")
    if "replay" in fields and replay_commands:
        lines.append(f"Replay: {replay_commands[0]}")
    if "entities" in fields and entities:
        lines.append(f"Entities: {', '.join(entities[:5])}")
    if "keywords" in fields and keywords:
        lines.append(f"Keywords: {', '.join(keywords[:6])}")

    typed_context = normalize_typed_context(
        {
            "summary": summary_result.summary,
            "goal": goal,
            "status": status,
            "decisions": decision_items,
            "constraints": constraints,
            "blockers": blockers,
            "next_actions": actions,
            "questions": questions,
            "evidence": evidence,
            "replay": replay_commands,
            "topics": topics,
            "keywords": keywords,
            "entities": entities,
        }
    )

    return TurnSummaryBuildResult(
        summary_result=summary_result,
        text="\n".join(lines).strip(),
        typed_context=typed_context,
    )
