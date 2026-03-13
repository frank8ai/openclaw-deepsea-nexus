"""
Shared NOW-manager helpers for SmartContext rescue flows.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from . import smart_context_rescue


NOWFactory = Callable[[], Any]


def _default_now_manager():
    from .now_manager import NOWManager

    return NOWManager()


def rescue_before_compress(
    conversation: str,
    *,
    rescue_gold: bool,
    rescue_decisions: bool,
    rescue_next_actions: bool,
    manager_factory: Optional[NOWFactory] = None,
) -> Dict[str, Any]:
    now = (manager_factory or _default_now_manager)()
    result = {
        "decisions_rescued": 0,
        "goals_rescued": 0,
        "questions_rescued": 0,
        "saved": False,
    }

    updates = smart_context_rescue.collect_rescue_updates(
        conversation,
        rescue_gold=bool(rescue_gold),
        rescue_decisions=bool(rescue_decisions),
        rescue_next_actions=bool(rescue_next_actions),
    )
    result.update(smart_context_rescue.apply_rescue_updates(now.state, updates))

    total = (
        int(result["decisions_rescued"])
        + int(result["goals_rescued"])
        + int(result["questions_rescued"])
    )
    if total > 0:
        now.save()
        result["saved"] = True
    return result


def get_rescue_context(manager_factory: Optional[NOWFactory] = None) -> str:
    return (manager_factory or _default_now_manager)().format_context()


def clear_rescue(manager_factory: Optional[NOWFactory] = None) -> None:
    (manager_factory or _default_now_manager)().clear()
