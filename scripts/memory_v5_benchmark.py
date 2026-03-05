#!/usr/bin/env python3
"""Simple benchmark for memory_v5 recall quality."""

import argparse
import json
import os
import sys

SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, SKILL_ROOT)

from memory_v5 import MemoryV5Service, MemoryScope


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


def iter_scopes(root: str):
    if not os.path.isdir(root):
        return []
    scopes = []
    for agent in os.listdir(root):
        agent_dir = os.path.join(root, agent)
        if not os.path.isdir(agent_dir):
            continue
        for user in os.listdir(agent_dir):
            user_dir = os.path.join(agent_dir, user)
            if not os.path.isdir(user_dir):
                continue
            scopes.append(MemoryScope(agent_id=agent, user_id=user))
    return scopes


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
        scopes = iter_scopes(service.root) or scopes

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
        scope_name = f"{scope.agent_id}/{scope.user_id}"
        per_scope.append(
            {
                "scope": scope_name,
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
