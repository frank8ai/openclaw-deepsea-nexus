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
        rescue_modified_files=True,
        rescue_key_changes=True,
        rescue_verification=True,
        rescue_rollback=True,
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
    modified_files = rescue_updates.get("modified_files", [])[:6]
    change_scope = rescue_updates.get("change_scope", [])[:3]
    key_changes = rescue_updates.get("key_changes", [])[:4]
    decision_reversal_conditions = rescue_updates.get("decision_reversal_conditions", [])[:3]
    waiting_on = rescue_updates.get("waiting_on", [])[:3]
    assumptions = rescue_updates.get("assumptions", [])[:3]
    verification_subject = str(rescue_updates.get("verification_subject", "") or "").strip()
    verification_command = str(rescue_updates.get("verification_command", "") or "").strip()
    verification_result = str(rescue_updates.get("verification_result", "") or "").strip()
    verification_status = str(rescue_updates.get("verification_status", "") or "").strip()
    failure_fingerprint = str(rescue_updates.get("failure_fingerprint", "") or "").strip()
    rollback_notes = rescue_updates.get("rollback_notes", [])[:3]
    rollback_trigger = str(rescue_updates.get("rollback_trigger", "") or "").strip()
    rollback_target = str(rescue_updates.get("rollback_target", "") or "").strip()
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
        for item in decision_items[:3]:
            lines.append(f"Decision: {item}")
    if "decision_reversal_conditions" in fields and decision_reversal_conditions:
        lines.append(f"Decision Reversal: {'; '.join(decision_reversal_conditions[:3])}")
    if "waiting_on" in fields and waiting_on:
        lines.append(f"Waiting On: {'; '.join(waiting_on[:3])}")
    if "assumptions" in fields and assumptions:
        lines.append(f"Assumptions: {'; '.join(assumptions[:3])}")
    if "modified_files" in fields and modified_files:
        lines.append(f"Modified Files: {'; '.join(modified_files[:6])}")
    if "change_scope" in fields and change_scope:
        lines.append(f"Change Scope: {'; '.join(change_scope[:3])}")
    if "key_changes" in fields and key_changes:
        lines.append(f"Key Changes: {'; '.join(key_changes[:4])}")
    if "verification_subject" in fields and verification_subject:
        lines.append(f"Verification Subject: {verification_subject}")
    if "verification_command" in fields and verification_command:
        lines.append(f"Verification Command: {verification_command}")
    if "verification_result" in fields and verification_result:
        lines.append(f"Verification Result: {verification_result}")
    if "verification_status" in fields and verification_status:
        lines.append(f"Verification: {verification_status}")
    if "failure_fingerprint" in fields and failure_fingerprint:
        lines.append(f"Failure Fingerprint: {failure_fingerprint}")
    if "constraints" in fields and constraints:
        lines.append(f"Constraints: {'; '.join(constraints[:3])}")
    if "blockers" in fields and blockers:
        lines.append(f"Blockers: {'; '.join(blockers[:3])}")
    if "rollback_trigger" in fields and rollback_trigger:
        lines.append(f"Rollback Trigger: {rollback_trigger}")
    if "rollback_target" in fields and rollback_target:
        lines.append(f"Rollback Target: {rollback_target}")
    if "rollback_notes" in fields and rollback_notes:
        lines.append(f"Rollback: {'; '.join(rollback_notes[:3])}")
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
            "decision_reversal_conditions": decision_reversal_conditions,
            "waiting_on": waiting_on,
            "assumptions": assumptions,
            "constraints": constraints,
            "blockers": blockers,
            "next_actions": actions,
            "questions": questions,
            "evidence": evidence,
            "replay": replay_commands,
            "modified_files": modified_files,
            "change_scope": change_scope,
            "key_changes": key_changes,
            "verification_subject": verification_subject,
            "verification_command": verification_command,
            "verification_result": verification_result,
            "verification_status": verification_status,
            "failure_fingerprint": failure_fingerprint,
            "rollback_notes": rollback_notes,
            "rollback_trigger": rollback_trigger,
            "rollback_target": rollback_target,
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
