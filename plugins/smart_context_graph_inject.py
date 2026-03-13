"""
Shared graph inject helpers for SmartContext.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

ALLOWED_GRAPH_REASONS = {"context_starved", "question", "technical_term", "keyword"}


def should_graph_inject(
    *,
    graph_enabled: bool,
    graph_inject_enabled: bool,
    reason: str,
) -> bool:
    if not (graph_enabled and graph_inject_enabled):
        return False
    return reason in ALLOWED_GRAPH_REASONS


def build_graph_injected_items(
    keywords: List[str],
    *,
    edge_lookup_fn: Callable[[str, int, int], List[Dict[str, Any]]],
    max_items: int,
    evidence_max_chars: int,
) -> List[Dict[str, Any]]:
    max_items = max(1, int(max_items))
    evidence_max = max(0, int(evidence_max_chars))
    out: List[Dict[str, Any]] = []
    for keyword in keywords[:max_items]:
        edges = edge_lookup_fn(keyword, max_items, 1)
        for edge in edges:
            evidence_text = ""
            evidence = edge.get("evidence") or []
            if evidence:
                evidence_text = (evidence[0].get("text") or "")[:evidence_max]
            content = f"{edge.get('subj')} {edge.get('rel')} {edge.get('obj')}"
            if evidence_text:
                content = f"{content} | 证据: {evidence_text}"
            out.append(
                {
                    "content": content,
                    "source": "graph",
                    "relevance": edge.get("weight", 1.0),
                }
            )
    return out[:max_items]
