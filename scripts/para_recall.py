#!/usr/bin/env python3
"""
PARA recall: directory-recursive retrieval with L0/L1/L2 minimization.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def load_config(repo_root: Path) -> dict:
    config_path = repo_root / "config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def resolve_obsidian_base(repo_root: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    config = load_config(repo_root)
    base = Path(config.get("paths", {}).get("base", repo_root)).expanduser().resolve()
    obsidian = config.get("paths", {}).get("obsidian", "Obsidian")
    obsidian_path = Path(obsidian)
    if not obsidian_path.is_absolute():
        obsidian_path = base / obsidian_path
    return obsidian_path


def tokenize(text: str) -> list[str]:
    tokens = re.split(r"[^0-9A-Za-z\\u4e00-\\u9fff]+", text.lower())
    return [t for t in tokens if t]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score_text(text: str, query_tokens: list[str]) -> float:
    if not text:
        return 0.0
    if not query_tokens:
        return 0.0
    lower = text.lower()
    score = 0.0
    for token in query_tokens:
        score += lower.count(token)
    normalized = score / max(1.0, len(query_tokens) * 4.0)
    return clamp(normalized)


def read_text(path: Path, max_chars: int = 800) -> str:
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8")
    return content[:max_chars]


def read_signal(project_dir: Path) -> dict:
    signal_path = project_dir / ".memory_signal.json"
    if not signal_path.exists():
        return {}
    try:
        payload = json.loads(signal_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def infer_importance(signal: dict, overview_text: str, warm_text: str) -> float:
    signal_importance = safe_float(signal.get("importance_score"), -1.0)
    if 0.0 <= signal_importance <= 1.0:
        return clamp(signal_importance)

    confidence = str(signal.get("confidence", "")).strip().lower()
    confidence_score = {"high": 1.0, "medium": 0.7, "low": 0.45, "高": 1.0, "中": 0.7, "低": 0.45}.get(
        confidence,
        0.7,
    )
    decisions = len(re.findall(r"^\s*[-*]\s+", overview_text, flags=re.MULTILINE))
    pitfalls = 1.0 if re.search(r"Pitfalls|避坑|风险", warm_text, flags=re.IGNORECASE) else 0.0
    heuristic = confidence_score * 0.6 + clamp(decisions / 6.0) * 0.25 + pitfalls * 0.15
    return clamp(heuristic)


def recency_score(last_touch_ts: float, half_life_days: float) -> float:
    if last_touch_ts <= 0:
        return 0.0
    half_life = max(0.5, half_life_days)
    days = max(0.0, (datetime.now().timestamp() - last_touch_ts) / 86400.0)
    return clamp(math.exp(-math.log(2.0) * days / half_life))


def project_score(
    project_dir: Path,
    query_tokens: list[str],
    relevance_weight: float,
    importance_weight: float,
    recency_weight: float,
    default_half_life_days: float,
) -> dict:
    abstract = read_text(project_dir / ".abstract.md", 300)
    overview = read_text(project_dir / ".overview.md", 1200)
    warm = read_text(project_dir / "Warm.md", 1600)
    relevance = clamp(
        score_text(abstract, query_tokens) * 0.55
        + score_text(overview, query_tokens) * 0.3
        + score_text(warm, query_tokens) * 0.15
    )

    signal = read_signal(project_dir)
    importance = infer_importance(signal, overview, warm)
    signal_half_life = safe_float(signal.get("decay_half_life_days"), default_half_life_days)
    mtime = max(
        (project_dir / ".abstract.md").stat().st_mtime if (project_dir / ".abstract.md").exists() else 0,
        (project_dir / ".overview.md").stat().st_mtime if (project_dir / ".overview.md").exists() else 0,
        (project_dir / "Warm.md").stat().st_mtime if (project_dir / "Warm.md").exists() else 0,
        (project_dir / ".memory_signal.json").stat().st_mtime if (project_dir / ".memory_signal.json").exists() else 0,
    )
    recency = recency_score(mtime, signal_half_life)
    final_score = clamp(
        relevance * relevance_weight
        + importance * importance_weight
        + recency * recency_weight
    )

    return {
        "project": project_dir.name,
        "score": final_score,
        "score_breakdown": {
            "relevance": round(relevance, 4),
            "importance": round(importance, 4),
            "recency": round(recency, 4),
            "weights": {
                "relevance": relevance_weight,
                "importance": importance_weight,
                "recency": recency_weight,
            },
        },
        "priority": signal.get("priority", ""),
        "importance_score": round(importance, 4),
        "decay_half_life_days": signal_half_life,
        "signal_updated_at": signal.get("updated_at", ""),
        "abstract": abstract.strip(),
        "overview": overview.strip(),
        "warm": warm.strip(),
        "path": str(project_dir),
    }


def collect_projects(projects_dir: Path) -> list[Path]:
    if not projects_dir.exists():
        return []
    return [p for p in projects_dir.iterdir() if p.is_dir()]


def write_trace(repo_root: Path, trace: dict[str, Any]) -> None:
    log_dir = repo_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    trace_path = log_dir / "para_recall_trace.jsonl"
    with trace_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trace, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]), help="Deep-Sea Nexus root")
    parser.add_argument("--obsidian", default=None, help="Obsidian vault path")
    parser.add_argument("--query", required=True, help="Query text")
    parser.add_argument("--top-projects", type=int, default=3)
    parser.add_argument("--max-warm-lines", type=int, default=18)
    parser.add_argument("--weight-relevance", type=float, default=0.6)
    parser.add_argument("--weight-importance", type=float, default=0.25)
    parser.add_argument("--weight-recency", type=float, default=0.15)
    parser.add_argument("--default-half-life-days", type=float, default=14.0)
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    obsidian_base = resolve_obsidian_base(repo_root, args.obsidian)
    projects_dir = obsidian_base / "10_Projects"
    query_tokens = tokenize(args.query)

    weight_relevance = max(0.0, float(args.weight_relevance))
    weight_importance = max(0.0, float(args.weight_importance))
    weight_recency = max(0.0, float(args.weight_recency))
    weight_sum = weight_relevance + weight_importance + weight_recency
    if weight_sum <= 0:
        weight_relevance, weight_importance, weight_recency = 0.6, 0.25, 0.15
        weight_sum = 1.0
    weight_relevance /= weight_sum
    weight_importance /= weight_sum
    weight_recency /= weight_sum

    projects = [
        project_score(
            p,
            query_tokens,
            weight_relevance,
            weight_importance,
            weight_recency,
            float(args.default_half_life_days),
        )
        for p in collect_projects(projects_dir)
    ]
    projects.sort(key=lambda x: x["score"], reverse=True)
    selected = projects[: args.top_projects]

    trace = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "query": args.query,
        "tokens": query_tokens,
        "weights": {
            "relevance": weight_relevance,
            "importance": weight_importance,
            "recency": weight_recency,
        },
        "candidates": [
            {k: v for k, v in item.items() if k in ("project", "score", "path", "importance_score", "priority", "score_breakdown")}
            for item in projects
        ],
        "selected": [
            {k: v for k, v in item.items() if k in ("project", "score", "path", "importance_score", "priority", "score_breakdown")}
            for item in selected
        ],
    }
    write_trace(repo_root, trace)

    if args.json:
        print(json.dumps({"query": args.query, "projects": selected}, ensure_ascii=False, indent=2))
        return

    lines = [f"# PARA Recall", f"Query: {args.query}", ""]
    for idx, item in enumerate(selected, 1):
        lines.append(f"{idx}. {item['project']} (score={item['score']:.2f})")
        lines.append(
            "   Score: "
            f"relevance={item['score_breakdown']['relevance']:.2f} "
            f"importance={item['score_breakdown']['importance']:.2f} "
            f"recency={item['score_breakdown']['recency']:.2f}"
        )
        if item.get("priority"):
            lines.append(f"   Priority: {item['priority']} | Importance={item['importance_score']:.2f}")
        if item["abstract"]:
            lines.append(f"   L0: {item['abstract']}")
        if item["overview"]:
            lines.append("   L1:")
            for ln in item["overview"].splitlines()[:6]:
                lines.append(f"     {ln}")
        if item["warm"]:
            lines.append("   Warm:")
            for ln in item["warm"].splitlines()[: args.max_warm_lines]:
                lines.append(f"     {ln}")
        lines.append(f"   Path: {item['path']}")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
