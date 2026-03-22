#!/usr/bin/env python3
"""Run report-first capability autotune experiments for Deepsea-Nexus."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_autotune",
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


package = _load_local_package()
runtime_middleware = importlib.import_module(f"{package.__name__}.plugins.runtime_middleware_plugin")
autotune_plugin = importlib.import_module(f"{package.__name__}.plugins.capability_autotune_lab_plugin")
context_scorecard = importlib.import_module(f"{package.__name__}.scripts.context_recall_scorecard")
ToolEvent = runtime_middleware.ToolEvent
RtkTransformer = runtime_middleware.RtkTransformer

DEFAULT_GOLDEN_PATH = REPO_ROOT / "docs" / "evals" / "runtime_middleware_compression_golden_cases.json"


def load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Expected JSON object at {path}")


def _contains_text(payload: Any, needle: str) -> bool:
    text = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    return str(needle or "") in str(text or "")


def evaluate_case(case: Dict[str, Any], compression_cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event_payload = dict(case.get("event", {}) or {})
    expect = dict(case.get("expect", {}) or {})
    transformer = RtkTransformer(compression_cfg)
    compressed = transformer.transform(ToolEvent(**event_payload))
    checks: Dict[str, bool] = {}

    if expect.get("event_kind"):
        checks["event_kind"] = compressed.event_kind == str(expect["event_kind"])

    list_key = str(expect.get("structured_list_key", "") or "").strip()
    values: List[str] = []
    if list_key:
        raw_values = compressed.structured.get(list_key, [])
        if isinstance(raw_values, list):
            values = [str(item) for item in raw_values]

    summary_contains = list(expect.get("summary_contains", []) or [])
    if summary_contains:
        checks["summary_contains"] = all(str(part) in compressed.summary for part in summary_contains)

    structured_contains = list(expect.get("structured_contains", []) or [])
    if structured_contains:
        checks["structured_contains"] = all(any(part in value for value in values) for part in structured_contains)

    min_reduction_ratio = expect.get("min_reduction_ratio")
    if min_reduction_ratio is not None:
        checks["min_reduction_ratio"] = float(compressed.reduction_ratio) >= float(min_reduction_ratio)

    passed = bool(checks) and all(checks.values())
    return {
        "id": str(case.get("id", "") or "case"),
        "passed": passed,
        "checks": checks,
        "summary": compressed.summary,
        "event_kind": compressed.event_kind,
        "reduction_ratio": compressed.reduction_ratio,
        "token_before": compressed.token_before,
        "token_after": compressed.token_after,
        "structured": compressed.structured,
    }


def build_builtin_experiments(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    middleware_cfg = deepcopy(config.get("runtime_middleware", {}) if isinstance(config.get("runtime_middleware", {}), dict) else {})
    base_rules = deepcopy(middleware_cfg.get("compression", {}) if isinstance(middleware_cfg.get("compression", {}), dict) else {})
    return [
        {"id": "baseline", "description": "Current runtime_middleware compression profile", "compression": base_rules},
        {
            "id": "failure_focused",
            "description": "Favor concise failure previews and tighter generic signal limits",
            "compression": {
                **base_rules,
                "failure_preview_limit": max(2, int(base_rules.get("failure_preview_limit", 12)) - 4),
                "tail_preview_limit": max(3, int(base_rules.get("tail_preview_limit", 8)) - 2),
                "generic_signal_limit": max(4, int(base_rules.get("generic_signal_limit", 8)) - 2),
                "operational_signal_limit": max(4, int(base_rules.get("operational_signal_limit", 8)) - 2),
            },
        },
        {
            "id": "diff_focused",
            "description": "Favor diff and grep previews while keeping other limits stable",
            "compression": {
                **base_rules,
                "diff_preview_limit": int(base_rules.get("diff_preview_limit", 6)) + 2,
                "grep_match_limit": int(base_rules.get("grep_match_limit", 10)) + 2,
            },
        },
    ]


def evaluate_experiment(experiment: Dict[str, Any], cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    case_results = [evaluate_case(case, experiment.get("compression")) for case in cases]
    passed = sum(1 for row in case_results if row.get("passed"))
    token_before = sum(int(row.get("token_before", 0) or 0) for row in case_results)
    token_after = sum(int(row.get("token_after", 0) or 0) for row in case_results)
    saved_ratio = 0.0
    if token_before > 0:
        saved_ratio = round(max(0.0, (token_before - token_after) / float(token_before)), 3)
    return {
        "id": experiment["id"],
        "description": experiment["description"],
        "compression": experiment.get("compression", {}),
        "cases": len(case_results),
        "passed": passed,
        "pass_rate": round(passed / float(len(case_results)), 3) if case_results else 0.0,
        "token_before": token_before,
        "token_after": token_after,
        "saved_ratio": saved_ratio,
        "results": case_results,
    }


def choose_best(experiments: List[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(
        experiments,
        key=lambda row: (
            float(row.get("pass_rate", 0.0)),
            float(row.get("saved_ratio", 0.0)),
            -float(row.get("token_after", 0.0)),
        ),
        reverse=True,
    )
    return dict(ordered[0]) if ordered else {}


def render_markdown(payload: Dict[str, Any]) -> str:
    best = payload.get("best_experiment", {}) or {}
    baseline = payload.get("baseline_experiment", {}) or {}
    context_summary = payload.get("context_scorecard", {}) or {}
    lines = [
        "# Capability Autotune Lab Report",
        "",
        f"- Generated: `{payload.get('generated_at', '')}`",
        f"- Golden path: `{payload.get('golden_path', '')}`",
        f"- Recommended action: `{payload.get('recommended_action', '')}`",
        "",
        "## Baseline vs Best",
        "",
        f"- Baseline: `{baseline.get('id', '')}` pass_rate=`{baseline.get('pass_rate', 0.0)}` saved_ratio=`{baseline.get('saved_ratio', 0.0)}`",
        f"- Best: `{best.get('id', '')}` pass_rate=`{best.get('pass_rate', 0.0)}` saved_ratio=`{best.get('saved_ratio', 0.0)}`",
        "",
        "## Experiments",
        "",
    ]
    for experiment in payload.get("experiments", []) or []:
        lines.append(
            f"- `{experiment.get('id', '')}`: pass_rate=`{experiment.get('pass_rate', 0.0)}` saved_ratio=`{experiment.get('saved_ratio', 0.0)}`"
        )
    if context_summary:
        lines.extend(
            [
                "",
                "## Context Scorecard Guardrail",
                "",
                f"- cases=`{context_summary.get('cases', 0)}` pass_rate=`{context_summary.get('pass_rate', 0.0)}`",
            ]
        )
    return "\n".join(lines) + "\n"


def run(
    config_path: Optional[str] = None,
    golden_path: Optional[str | Path] = None,
    json_out: Optional[str | Path] = None,
    md_out: Optional[str | Path] = None,
) -> Dict[str, Any]:
    config_file = Path(config_path).resolve() if config_path else Path(package.resolve_default_config_path() or (REPO_ROOT / "config.json")).resolve()
    cfg = package.ConfigManager(str(config_file)).get_all()
    golden_file = Path(golden_path or DEFAULT_GOLDEN_PATH).resolve()
    golden = load_json(golden_file)
    cases = list(golden.get("cases", []) or [])
    experiments = [evaluate_experiment(item, cases) for item in build_builtin_experiments(cfg)]
    best = choose_best(experiments)
    baseline = next((row for row in experiments if row.get("id") == "baseline"), experiments[0] if experiments else {})
    context_payload = context_scorecard.run() if bool((cfg.get("capability_autotune_lab", {}) or {}).get("include_context_scorecard", True)) else {}
    context_summary = context_payload.get("summary", {}) if isinstance(context_payload, dict) else {}
    recommended_action = "discard"
    if best and baseline:
        if best.get("id") == baseline.get("id"):
            recommended_action = "keep_for_lab"
        elif float(best.get("pass_rate", 0.0)) >= float(baseline.get("pass_rate", 0.0)):
            recommended_action = "promote_recommended"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_file),
        "golden_path": str(golden_file),
        "recommended_action": recommended_action,
        "baseline_experiment": baseline,
        "best_experiment": best,
        "experiments": experiments,
        "recommended_runtime_middleware_compression": best.get("compression", {}) if best else {},
        "context_scorecard": context_summary,
    }

    resolved_json_out = Path(json_out).resolve() if json_out else None
    resolved_md_out = Path(md_out).resolve() if md_out else None
    if resolved_json_out is None:
        report_path = autotune_plugin.resolve_capability_autotune_report_path(cfg)
        resolved_json_out = Path(report_path).resolve() if report_path else None
    if resolved_json_out is not None:
        resolved_json_out.parent.mkdir(parents=True, exist_ok=True)
        resolved_json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if resolved_md_out is None and resolved_json_out is not None:
        resolved_md_out = resolved_json_out.with_suffix(".md")
    if resolved_md_out is not None:
        resolved_md_out.parent.mkdir(parents=True, exist_ok=True)
        resolved_md_out.write_text(render_markdown(payload), encoding="utf-8")
    if resolved_json_out is not None:
        payload["json_out"] = str(resolved_json_out)
    if resolved_md_out is not None:
        payload["md_out"] = str(resolved_md_out)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Deepsea capability autotune lab")
    parser.add_argument("--config", default=None, help="Optional Deepsea config path")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN_PATH), help="Compression eval pack path")
    parser.add_argument("--json-out", default=None, help="Optional JSON output path")
    parser.add_argument("--md-out", default=None, help="Optional Markdown output path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable payload")
    args = parser.parse_args()

    payload = run(
        config_path=args.config,
        golden_path=args.golden,
        json_out=args.json_out,
        md_out=args.md_out,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[autotune] recommended_action={payload.get('recommended_action')}")
        print(f"[autotune] best_experiment={payload.get('best_experiment', {}).get('id', '')}")
        if payload.get("json_out"):
            print(f"[autotune] json={payload['json_out']}")
        if payload.get("md_out"):
            print(f"[autotune] md={payload['md_out']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
