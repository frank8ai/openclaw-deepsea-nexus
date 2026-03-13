"""
Shared round-state helpers for SmartContext.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_round_result(
    conversation_id: str,
    round_num: int,
    status: str,
    *,
    combined_text: str,
    summary: str = "",
    rescue_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "conversation_id": conversation_id,
        "round_num": round_num,
        "status": status,
        "stored": False,
    }
    if status == "full":
        result["content"] = combined_text
        result["compressed"] = False
        return result
    result["summary"] = summary
    result["compressed"] = status == "compressed"
    if rescue_result is not None:
        result["rescue"] = rescue_result
    return result


def build_rescue_metric_events(rescue_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = [
        {
            "event": "rescue_result",
            "saved": bool(rescue_result.get("saved")),
            "skipped": bool(rescue_result.get("skipped")),
            "reason": rescue_result.get("reason", ""),
            "decisions": rescue_result.get("decisions_rescued", 0),
            "goals": rescue_result.get("goals_rescued", 0),
            "questions": rescue_result.get("questions_rescued", 0),
        }
    ]
    if rescue_result.get("saved"):
        events.append(
            {
                "event": "rescue_saved",
                "decisions": rescue_result.get("decisions_rescued", 0),
                "goals": rescue_result.get("goals_rescued", 0),
                "questions": rescue_result.get("questions_rescued", 0),
            }
        )
    return events


def format_rescue_debug_line(rescue_result: Dict[str, Any]) -> str:
    return (
        "[SmartContext] RESCUE before compress "
        f"decisions={rescue_result.get('decisions_rescued', 0)} "
        f"goals={rescue_result.get('goals_rescued', 0)} "
        f"questions={rescue_result.get('questions_rescued', 0)}"
    )


def build_context_status_metric(
    status: str,
    reason: str,
    token_estimate: int,
    usage_snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "event": "context_status",
        "status": status,
        "reason": reason,
        "token_estimate": int(token_estimate),
        "full_tokens": int(usage_snapshot.get("full", 0)),
        "summary_tokens": int(usage_snapshot.get("summary", 0)),
        "compressed_tokens": int(usage_snapshot.get("compressed", 0)),
    }


def build_round_summary_document(
    conversation_id: str,
    round_num: int,
    content: str,
    *,
    topic_boundary: bool = False,
) -> Dict[str, str]:
    if topic_boundary:
        return {
            "content": content,
            "title": f"对话 {conversation_id} - 话题切换 (轮{round_num})",
            "tags": f"type:topic_boundary,round:{round_num},conversation:{conversation_id}",
        }
    return {
        "content": content,
        "title": f"对话 {conversation_id} - 轮{round_num} (摘要卡)",
        "tags": f"type:turn_summary,round:{round_num},conversation:{conversation_id}",
    }
