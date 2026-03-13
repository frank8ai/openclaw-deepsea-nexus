"""
Shared graph/block storage helpers for SmartContext.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


GRAPH_PATTERNS = [
    (r"(使用|采用|选择|改为|切换到)\s*([\w\-./]+)", "uses"),
    (r"(依赖|基于)\s*([\w\-./]+)", "depends_on"),
    (r"(目标|目的)[:：]\s*([^，。]+)", "goal"),
    (r"(影响|导致)\s*([^，。]+)", "impacts"),
]


def extract_graph_edges(block: str, conversation_id: str, max_items: int) -> List[Dict[str, Any]]:
    if not block:
        return []
    subject = f"conversation:{conversation_id}" if conversation_id else "workspace"
    edges: List[Dict[str, Any]] = []
    for pattern, relation in GRAPH_PATTERNS:
        match = re.search(pattern, block)
        if not match:
            continue
        obj = match.group(2).strip()
        if not (2 <= len(obj) <= 80):
            continue
        edges.append(
            {
                "subj": subject,
                "rel": relation,
                "obj": obj,
                "weight": 1.0,
                "entity_types": {"subj": "conversation", "obj": "concept"},
            }
        )
    return edges[: max(1, int(max_items))]


def build_decision_block_operations(
    conversation_id: str,
    round_num: int,
    blocks: List[str],
    *,
    max_graph_edges: int,
) -> List[Dict[str, Any]]:
    operations: List[Dict[str, Any]] = []
    for index, block in enumerate(blocks or [], 1):
        operations.append(
            {
                "document": {
                    "content": block,
                    "title": f"决策块 {conversation_id} - 轮{round_num} ({index})",
                    "tags": f"type:decision_block,round:{round_num},conversation:{conversation_id}",
                },
                "graph_edges": [
                    {
                        **edge,
                        "source": f"decision_block:{conversation_id}",
                        "evidence_text": block,
                        "conversation_id": conversation_id,
                        "round_num": round_num,
                    }
                    for edge in extract_graph_edges(block, conversation_id, max_graph_edges)
                ],
            }
        )
    return operations


def build_topic_block_operations(
    conversation_id: str,
    round_num: int,
    topics: List[str],
) -> List[Dict[str, Any]]:
    operations: List[Dict[str, Any]] = []
    for index, topic in enumerate(topics or [], 1):
        operations.append(
            {
                "document": {
                    "content": topic,
                    "title": f"主题块 {conversation_id} - 轮{round_num} ({index})",
                    "tags": f"type:topic_block,round:{round_num},conversation:{conversation_id}",
                },
                "graph_edges": [
                    {
                        "subj": f"conversation:{conversation_id}",
                        "rel": "topic",
                        "obj": topic[:80],
                        "weight": 0.8,
                        "source": f"topic_block:{conversation_id}",
                        "evidence_text": topic,
                        "conversation_id": conversation_id,
                        "round_num": round_num,
                        "entity_types": {"subj": "conversation", "obj": "topic"},
                    }
                ],
            }
        )
    return operations
