"""
Shared NOW-manager helpers for SmartContext rescue flows.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from . import smart_context_rescue


NOWFactory = Callable[[], Any]
UNIQUE_RESCUE_COUNT_KEYS = (
    "decisions_rescued",
    "goal_rescued",
    "status_rescued",
    "constraints_rescued",
    "blockers_rescued",
    "next_actions_rescued",
    "open_questions_rescued",
    "evidence_rescued",
    "replay_rescued",
)


def _default_now_manager():
    from .now_manager import NOWManager

    return NOWManager()


def rescue_before_compress(
    conversation: str,
    *,
    rescue_gold: bool,
    rescue_decisions: bool,
    rescue_next_actions: bool,
    rescue_goal: bool = True,
    rescue_status: bool = True,
    rescue_constraints: bool = True,
    rescue_blockers: bool = True,
    rescue_evidence: bool = True,
    rescue_replay: bool = True,
    manager_factory: Optional[NOWFactory] = None,
) -> Dict[str, Any]:
    now = (manager_factory or _default_now_manager)()
    result = {
        "decisions_rescued": 0,
        "goal_rescued": 0,
        "status_rescued": 0,
        "constraints_rescued": 0,
        "blockers_rescued": 0,
        "next_actions_rescued": 0,
        "goals_rescued": 0,
        "open_questions_rescued": 0,
        "questions_rescued": 0,
        "evidence_rescued": 0,
        "replay_rescued": 0,
        "saved": False,
    }

    updates = smart_context_rescue.collect_rescue_updates(
        conversation,
        rescue_gold=bool(rescue_gold),
        rescue_decisions=bool(rescue_decisions),
        rescue_next_actions=bool(rescue_next_actions),
        rescue_goal=bool(rescue_goal),
        rescue_status=bool(rescue_status),
        rescue_constraints=bool(rescue_constraints),
        rescue_blockers=bool(rescue_blockers),
        rescue_evidence=bool(rescue_evidence),
        rescue_replay=bool(rescue_replay),
    )
    result.update(smart_context_rescue.apply_rescue_updates(now.state, updates))

    total = sum(int(result.get(key, 0)) for key in UNIQUE_RESCUE_COUNT_KEYS)
    if total > 0:
        now.save()
        result["saved"] = True
    return result


def get_rescue_context(manager_factory: Optional[NOWFactory] = None) -> str:
    return (manager_factory or _default_now_manager)().format_context()


def clear_rescue(manager_factory: Optional[NOWFactory] = None) -> None:
    (manager_factory or _default_now_manager)().clear()
