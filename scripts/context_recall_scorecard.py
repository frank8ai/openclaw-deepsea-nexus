#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from plugins import smart_context_inject
from plugins import smart_context_prompt
from plugins import smart_context_recall
from plugins.context_engine_runtime import ContextEngineRuntimeState

DEFAULT_GOLDEN_PATH = REPO_ROOT / "docs" / "evals" / "context_recall_golden_cases.json"


def load_golden_cases(path: str | Path) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"schema_version": "1.0", "cases": payload}
    if not isinstance(payload, dict):
        raise ValueError("Golden cases payload must be a JSON object or array.")
    payload.setdefault("schema_version", "1.0")
    payload.setdefault("cases", [])
    return payload


def _rate(hit: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(hit / float(total), 3)


def _contains_expected(values: List[str], expected: str) -> bool:
    target = str(expected or "").strip().lower()
    if not target:
        return False
    for value in values:
        normalized = str(value or "").strip().lower()
        if normalized == target or target in normalized:
            return True
    return False


def _normalize_candidate(candidate: Dict[str, Any], *, reason: str) -> Dict[str, Any]:
    payload = dict(candidate or {})
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    if payload.get("kind") and "kind" not in metadata:
        metadata["kind"] = payload["kind"]
    if payload.get("evidence") and "evidence" not in metadata:
        metadata["evidence"] = payload["evidence"]
    payload["metadata"] = metadata
    return smart_context_recall.normalize_recall_candidate(payload, reason=reason)


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = str(case.get("id", "") or "").strip() or "case"
    query = str(case.get("query", "") or "").strip()
    reason = str(case.get("reason", "") or "").strip()
    expected = case.get("expect", {}) or {}
    if not isinstance(expected, dict):
        expected = {}

    candidates = [
        _normalize_candidate(candidate, reason=reason)
        for candidate in list(case.get("candidates", []) or [])
    ]
    reranked = smart_context_recall.rerank_recall_candidates(
        candidates,
        query=query,
        reason=reason,
    )
    inject_cfg = case.get("inject", {}) or {}
    if not isinstance(inject_cfg, dict):
        inject_cfg = {}
    threshold = float(inject_cfg.get("threshold", 0.6))
    max_items = int(inject_cfg.get("max_items", 3))
    filtered, fallback_used, fallback_reason = smart_context_recall.select_injected_items(
        reranked,
        threshold=threshold,
    )
    injected_items = smart_context_inject.finalize_injected_items(
        filtered,
        [],
        topk_only=bool(inject_cfg.get("topk_only", True)),
        max_items=max_items,
        max_chars_per_item=int(inject_cfg.get("max_chars_per_item", 220)),
        max_lines_per_item=int(inject_cfg.get("max_lines_per_item", 8)),
        max_lines_total=int(inject_cfg.get("max_lines_total", 40)),
    )
    prompt = smart_context_prompt.build_context_prompt(
        injected_items,
        max_chars_per_item=int(inject_cfg.get("prompt_chars_per_item", inject_cfg.get("max_chars_per_item", 220))),
    )
    runtime = ContextEngineRuntimeState()
    prompt_tokens = runtime.estimate_tokens(prompt)
    prompt_lines = max(1, prompt.count("\n") + 1) if prompt else 0
    budget_tokens = int(inject_cfg.get("budget_tokens", 1000))
    prompt_max_lines = int(inject_cfg.get("prompt_max_lines", 60))
    token_ratio = round(prompt_tokens / float(budget_tokens), 3) if budget_tokens > 0 else 0.0
    line_ratio = round(prompt_lines / float(prompt_max_lines), 3) if prompt_max_lines > 0 else 0.0

    top = reranked[0] if reranked else {}
    top_trace = top.get("trace", {}) or {}
    if not isinstance(top_trace, dict):
        top_trace = {}

    checks: Dict[str, Optional[bool]] = {}
    if "top_kind" in expected:
        target_kind = str(expected.get("top_kind", "") or "")
        checks["top_kind"] = str(top.get("kind", "") or "") == target_kind
        checks["top3_kind"] = any(str(item.get("kind", "") or "") == target_kind for item in reranked[:3])
    if "top_matched_intent" in expected:
        checks["top_matched_intent"] = _contains_expected(
            list(top_trace.get("matched_intents", []) or []),
            str(expected.get("top_matched_intent", "") or ""),
        )
    if "top_scope_match" in expected:
        checks["top_scope_match"] = _contains_expected(
            list(top_trace.get("scope_matches", []) or []),
            str(expected.get("top_scope_match", "") or ""),
        )
    if "top_source_contains" in expected:
        checks["top_source_contains"] = str(expected.get("top_source_contains", "") or "").lower() in str(
            top.get("source", "") or ""
        ).lower()
    if "require_evidence" in expected:
        checks["require_evidence"] = bool(top.get("evidence")) == bool(expected.get("require_evidence"))
    inject_target_kind = str(
        expected.get("inject_contains_kind", "") or expected.get("top_kind", "") or ""
    ).strip()
    if inject_target_kind:
        checks["inject_contains_kind"] = any(
            str(item.get("kind", "") or "") == inject_target_kind
            for item in injected_items
        )
    if "prompt_contains" in expected:
        checks["prompt_contains"] = str(expected.get("prompt_contains", "") or "") in prompt
    if "max_budget_ratio" in expected:
        checks["max_budget_ratio"] = float(token_ratio) <= float(expected.get("max_budget_ratio", 1.0))
    if "max_line_ratio" in expected:
        checks["max_line_ratio"] = float(line_ratio) <= float(expected.get("max_line_ratio", 1.0))

    active_checks = {key: value for key, value in checks.items() if value is not None}
    passed = bool(active_checks) and all(active_checks.values())

    return {
        "id": case_id,
        "query": query,
        "reason": reason,
        "passed": passed,
        "checks": active_checks,
        "expected": expected,
        "top": {
            "kind": str(top.get("kind", "") or ""),
            "source": str(top.get("source", "") or ""),
            "score": float(top.get("score", 0.0) or 0.0),
            "relevance": float(top.get("relevance", 0.0) or 0.0),
            "why": str(top.get("why", "") or ""),
            "evidence": list(top.get("evidence", []) or []),
            "matched_intents": list(top_trace.get("matched_intents", []) or []),
            "scope_matches": list(top_trace.get("scope_matches", []) or []),
            "score_breakdown": dict(top_trace.get("score_breakdown", {}) or {}),
        },
        "inject": {
            "count": len(injected_items),
            "kinds": [str(item.get("kind", "") or "") for item in injected_items],
            "fallback_used": bool(fallback_used),
            "fallback_reason": fallback_reason,
            "prompt": prompt,
            "prompt_tokens": int(prompt_tokens),
            "prompt_lines": int(prompt_lines),
            "budget_tokens": int(budget_tokens),
            "prompt_max_lines": int(prompt_max_lines),
            "token_ratio": float(token_ratio),
            "line_ratio": float(line_ratio),
        },
        "ranked_kinds": [str(item.get("kind", "") or "") for item in reranked[:3]],
    }


def build_scorecard(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = {
        "cases": len(case_results),
        "passed": sum(1 for row in case_results if row.get("passed")),
        "top_kind": {"hit": 0, "total": 0},
        "top3_kind": {"hit": 0, "total": 0},
        "top_matched_intent": {"hit": 0, "total": 0},
        "top_scope_match": {"hit": 0, "total": 0},
        "require_evidence": {"hit": 0, "total": 0},
        "inject_contains_kind": {"hit": 0, "total": 0},
        "prompt_contains": {"hit": 0, "total": 0},
        "max_budget_ratio": {"hit": 0, "total": 0},
        "max_line_ratio": {"hit": 0, "total": 0},
    }

    total_top_score = 0.0
    total_with_top = 0
    total_token_ratio = 0.0
    total_line_ratio = 0.0
    total_inject_cases = 0
    for row in case_results:
        top = row.get("top", {}) or {}
        inject = row.get("inject", {}) or {}
        if top:
            total_top_score += float(top.get("score", 0.0) or 0.0)
            total_with_top += 1
        if inject:
            total_token_ratio += float(inject.get("token_ratio", 0.0) or 0.0)
            total_line_ratio += float(inject.get("line_ratio", 0.0) or 0.0)
            total_inject_cases += 1
        checks = row.get("checks", {}) or {}
        for key in (
            "top_kind",
            "top3_kind",
            "top_matched_intent",
            "top_scope_match",
            "require_evidence",
            "inject_contains_kind",
            "prompt_contains",
            "max_budget_ratio",
            "max_line_ratio",
        ):
            if key not in checks:
                continue
            metrics[key]["total"] += 1
            if checks.get(key):
                metrics[key]["hit"] += 1

    summary = {
        "cases": metrics["cases"],
        "passed": metrics["passed"],
        "pass_rate": _rate(metrics["passed"], metrics["cases"]),
        "avg_top_score": round(total_top_score / float(total_with_top), 3) if total_with_top else 0.0,
        "avg_prompt_token_ratio": round(total_token_ratio / float(total_inject_cases), 3) if total_inject_cases else 0.0,
        "avg_prompt_line_ratio": round(total_line_ratio / float(total_inject_cases), 3) if total_inject_cases else 0.0,
    }
    for key in (
        "top_kind",
        "top3_kind",
        "top_matched_intent",
        "top_scope_match",
        "require_evidence",
        "inject_contains_kind",
        "prompt_contains",
        "max_budget_ratio",
        "max_line_ratio",
    ):
        summary[key] = {
            "hit": metrics[key]["hit"],
            "total": metrics[key]["total"],
            "rate": _rate(metrics[key]["hit"], metrics[key]["total"]),
        }
    return summary


def render_markdown(payload: Dict[str, Any]) -> str:
    summary = payload.get("summary", {}) or {}
    lines = [
        "# Context Recall Scorecard",
        "",
        f"- Generated at: {payload.get('generated_at', '')}",
        f"- Golden path: `{payload.get('golden_path', '')}`",
        f"- Cases: {summary.get('cases', 0)}",
        f"- Pass rate: {summary.get('pass_rate', 0.0)}",
        f"- Avg top score: {summary.get('avg_top_score', 0.0)}",
        f"- Avg prompt token ratio: {summary.get('avg_prompt_token_ratio', 0.0)}",
        f"- Avg prompt line ratio: {summary.get('avg_prompt_line_ratio', 0.0)}",
        "",
        "## Metrics",
    ]
    for key in (
        "top_kind",
        "top3_kind",
        "top_matched_intent",
        "top_scope_match",
        "require_evidence",
        "inject_contains_kind",
        "prompt_contains",
        "max_budget_ratio",
        "max_line_ratio",
    ):
        metric = summary.get(key, {}) or {}
        lines.append(
            f"- {key}: {metric.get('hit', 0)}/{metric.get('total', 0)} ({metric.get('rate', 0.0)})"
        )
    lines.extend(["", "## Cases"])
    for case in payload.get("cases", []) or []:
        top = case.get("top", {}) or {}
        inject = case.get("inject", {}) or {}
        lines.extend(
            [
                f"### {case.get('id', 'case')}",
                f"- Passed: {case.get('passed', False)}",
                f"- Query: {case.get('query', '')}",
                f"- Top kind: {top.get('kind', '')}",
                f"- Top source: {top.get('source', '')}",
                f"- Top why: {top.get('why', '')}",
                f"- Top matched intents: {', '.join(top.get('matched_intents', []) or [])}",
                f"- Top scope matches: {', '.join(top.get('scope_matches', []) or [])}",
                f"- Inject kinds: {', '.join(inject.get('kinds', []) or [])}",
                f"- Prompt token ratio: {inject.get('token_ratio', 0.0)}",
                f"- Prompt line ratio: {inject.get('line_ratio', 0.0)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def run(
    *,
    golden_path: str | Path | None = None,
    json_out: str | Path | None = None,
    md_out: str | Path | None = None,
) -> Dict[str, Any]:
    resolved_golden = Path(golden_path or DEFAULT_GOLDEN_PATH).resolve()
    golden = load_golden_cases(resolved_golden)
    case_results = [evaluate_case(case) for case in list(golden.get("cases", []) or [])]
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "golden_path": str(resolved_golden),
        "summary": build_scorecard(case_results),
        "cases": case_results,
    }

    if json_out:
        json_path = Path(json_out).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if md_out:
        md_path = Path(md_out).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden recall/inject scorecard.")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN_PATH), help="Path to golden cases JSON.")
    parser.add_argument("--json-out", default=None, help="Optional path to write JSON scorecard.")
    parser.add_argument("--md-out", default=None, help="Optional path to write Markdown scorecard.")
    args = parser.parse_args()

    payload = run(
        golden_path=args.golden,
        json_out=args.json_out,
        md_out=args.md_out,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
