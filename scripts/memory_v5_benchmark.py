#!/usr/bin/env python3
"""Simple benchmark for memory_v5 recall quality."""

import argparse
import json
import os
import sys

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SKILL_ROOT not in sys.path:
    sys.path.insert(0, SKILL_ROOT)
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from memory_v5 import MemoryV5Service, MemoryScope
import memory_v5_maintenance


def load_config() -> dict:
    config_path = os.path.join(SKILL_ROOT, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def load_cases(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else []


def match_hit(hit, expect_any):
    text = (hit.title + " " + hit.content).lower()
    return any(str(k).lower() in text for k in expect_any)


def _scope_payload(scope: MemoryScope):
    return {
        "agent_id": scope.agent_id,
        "user_id": scope.user_id,
        "app_id": scope.app_id,
        "run_id": scope.run_id,
        "workspace": scope.workspace,
    }


def _scope_label(scope: MemoryScope) -> str:
    payload = _scope_payload(scope)
    agent = str(payload.get("agent_id") or "default")
    user = str(payload.get("user_id") or "default")
    qualifiers = []
    app = str(payload.get("app_id") or "")
    run = str(payload.get("run_id") or "")
    workspace = str(payload.get("workspace") or "")
    if app:
        qualifiers.append(f"app={app}")
    if run:
        qualifiers.append(f"run={run}")
    if workspace:
        qualifiers.append(f"workspace={workspace}")
    if qualifiers:
        return f"{agent}/{user} ({', '.join(qualifiers)})"
    return f"{agent}/{user}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True, help="JSON list of {query, expect_any:[...]} cases")
    parser.add_argument("--agent", default="default")
    parser.add_argument("--user", default="default")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--all-agents", action="store_true")
    args = parser.parse_args()

    config = load_config()
    service = MemoryV5Service(config)
    scopes = [MemoryScope(agent_id=args.agent, user_id=args.user)]
    if args.all_agents:
        scopes = list(memory_v5_maintenance.iter_scopes(service.root)) or scopes

    cases = load_cases(args.cases)
    total_cases = len(cases)
    total_hit = 0
    total_runs = 0
    per_scope = []
    case_hit_by_any_scope = [False for _ in range(total_cases)]

    for scope in scopes:
        hit = 0
        for idx, case in enumerate(cases):
            query = str(case.get("query", "")).strip()
            expect_any = case.get("expect_any") or []
            if not query:
                continue
            hits = service.recall(query, limit=args.limit, scope=scope)
            ok = any(match_hit(h, expect_any) for h in hits) if expect_any else bool(hits)
            if ok:
                hit += 1
                case_hit_by_any_scope[idx] = True
        total_hit += hit
        total_runs += total_cases
        scope_name = _scope_label(scope)
        per_scope.append(
            {
                "scope": scope_name,
                "scope_fields": _scope_payload(scope),
                "total": total_cases,
                "hit": hit,
                "score": round(hit / total_cases, 4) if total_cases else 0.0,
            }
        )

    score = round(total_hit / total_runs, 4) if total_runs else 0.0
    any_scope_hit = sum(1 for ok in case_hit_by_any_scope if ok)
    any_scope_score = round(any_scope_hit / total_cases, 4) if total_cases else 0.0
    print(
        json.dumps(
            {
                "total": total_runs,
                "hit": total_hit,
                "score": score,
                "scope_count": len(scopes),
                "case_count": total_cases,
                "any_scope_hit": any_scope_hit,
                "any_scope_score": any_scope_score,
                "per_scope": per_scope,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
