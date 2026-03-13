"""
Shared storage payload helpers for SmartContext document writes.
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_round_context_document(
    conversation_id: str,
    round_num: int,
    context: Dict[str, Any],
) -> Dict[str, str]:
    status = context.get("status", "unknown")
    if status == "full":
        return {
            "content": context.get("content", ""),
            "title": f"对话 {conversation_id} - 轮{round_num} (完整)",
            "tags": f"type:full,round:{round_num},conversation:{conversation_id}",
        }
    if status == "summary":
        return {
            "content": f"[摘要] {context.get('summary', '')}",
            "title": f"对话 {conversation_id} - 轮{round_num} (摘要)",
            "tags": f"type:summary,round:{round_num},conversation:{conversation_id}",
        }
    return {
        "content": f"[已压缩] {context.get('summary', '')}",
        "title": f"对话 {conversation_id} - 轮{round_num} (已压缩)",
        "tags": f"type:compressed,round:{round_num},conversation:{conversation_id}",
    }


def build_conversation_store_entries(
    conversation_id: str,
    *,
    ai_response: str,
    summary: str,
    keywords: List[str],
    decisions: List[str],
    topics: List[str],
) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = [
        {
            "content": ai_response,
            "title": f"对话 {conversation_id} - 原文",
            "tags": f"type:content,source:{conversation_id}",
            "compat": {
                "priority": "P2",
                "kind": "summary",
                "source": str(conversation_id),
                "tags": "type:content",
            },
        }
    ]
    if summary:
        entries.append(
            {
                "content": f"[摘要] {summary}",
                "title": f"对话 {conversation_id} - 摘要",
                "tags": f"type:summary,source:{conversation_id}",
                "compat": {
                    "priority": "P1",
                    "kind": "summary",
                    "source": str(conversation_id),
                    "tags": "type:summary",
                },
            }
        )
    if keywords:
        entries.append(
            {
                "content": " ".join(keywords),
                "title": f"对话 {conversation_id} - 关键词",
                "tags": f"type:keywords,source:{conversation_id}",
                "compat": {
                    "priority": "P2",
                    "kind": "fact",
                    "source": str(conversation_id),
                    "tags": "type:keywords",
                },
            }
        )
    for index, block in enumerate(decisions or [], 1):
        entries.append(
            {
                "content": block,
                "title": f"决策块 {conversation_id} - ({index})",
                "tags": f"type:decision_block,source:{conversation_id}",
                "compat": {
                    "priority": "P0",
                    "kind": "decision",
                    "source": str(conversation_id),
                    "tags": "type:decision_block",
                },
            }
        )
    for index, topic in enumerate(topics or [], 1):
        entries.append(
            {
                "content": topic,
                "title": f"主题块 {conversation_id} - ({index})",
                "tags": f"type:topic_block,source:{conversation_id}",
                "compat": {
                    "priority": "P1",
                    "kind": "strategy",
                    "source": str(conversation_id),
                    "tags": "type:topic_block",
                },
            }
        )
    return entries
