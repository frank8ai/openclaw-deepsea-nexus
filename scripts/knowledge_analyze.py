#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from knowledge_common import (
    append_jsonl,
    emit_metric,
    ensure_pipeline_dirs,
    load_policy,
    make_trace_id,
    parse_iso_week,
    read_markdown_frontmatter,
    safe_title,
)


def _extract_section(body: str, section: str) -> str:
    pattern = rf"## {re.escape(section)}\n([\s\S]*?)(\n## |$)"
    m = re.search(pattern, body)
    if not m:
        return ""
    return m.group(1).strip()


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def run(policy_path: str | None = None) -> dict[str, Any]:
    started = time.time()
    trace_id = make_trace_id("analyze")

    policy = load_policy(policy_path)
    dirs = ensure_pipeline_dirs(policy)
    cards_root = dirs["cards_root"]
    reports_root = dirs["projects_reports"]
    metrics_root = dirs["metrics_root"]

    cards: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    for card_path in sorted(cards_root.rglob("*.md")):
        try:
            meta, body = read_markdown_frontmatter(card_path)
            updated_dt = _parse_dt(str(meta.get("updated", ""))) or now
            cards.append(
                {
                    "path": card_path,
                    "meta": meta,
                    "body": body,
                    "updated": updated_dt,
                    "is_recent": updated_dt >= cutoff,
                    "next_action": _extract_section(body, "Next Action"),
                    "limits": _extract_section(body, "Limits"),
                }
            )
        except Exception:
            continue

    if not cards:
        reports_root.mkdir(parents=True, exist_ok=True)
        empty_path = reports_root / f"weekly-{now.strftime('%Y-W%V')}.md"
        empty_path.write_text(
            "# Weekly Knowledge Report\n\nNo cards available yet.\n",
            encoding="utf-8",
        )
        duration_ms = int((time.time() - started) * 1000)
        emit_metric(metrics_root, "analyze", trace_id, duration_ms, True, extras={"cards": 0})
        return {
            "trace_id": trace_id,
            "cards": 0,
            "weekly_report": str(empty_path),
            "topic_brief": "",
            "duration_ms": duration_ms,
        }

    recent = [c for c in cards if c["is_recent"]]
    source_set = recent if recent else cards

    by_domain = Counter(str(c["meta"].get("domain", "unknown")) for c in source_set)
    by_status = Counter(str(c["meta"].get("status", "unknown")) for c in source_set)

    scored: list[tuple[int, dict[str, Any]]] = []
    for c in source_set:
        status = str(c["meta"].get("status", ""))
        base = {"evergreen": 4, "validated": 3, "draft": 2, "inbox": 1, "archived": 0}.get(status, 1)
        if c["next_action"]:
            base += 1
        scored.append((base, c))

    top_cards = [c for _, c in sorted(scored, key=lambda x: x[0], reverse=True)[:10]]

    # Topic candidates from domains and tags
    topic_pool: dict[str, list[str]] = defaultdict(list)
    for c in top_cards:
        meta = c["meta"]
        domain = str(meta.get("domain", "unknown"))
        card_id = str(meta.get("id", c["path"].stem))
        topic_pool[domain].append(card_id)

    year, week = parse_iso_week(now)
    week_label = f"{year}-W{week:02d}"
    weekly_path = reports_root / f"weekly-{week_label}.md"
    topic_path = reports_root / f"topic-{now.strftime('%Y-%m-%d')}.md"
    reports_root.mkdir(parents=True, exist_ok=True)

    domain_lines = [f"- {k}: {v}" for k, v in by_domain.most_common()]
    status_lines = [f"- {k}: {v}" for k, v in by_status.most_common()]

    top_lines = []
    for c in top_cards:
        meta = c["meta"]
        card_id = str(meta.get("id", c["path"].stem))
        domain = str(meta.get("domain", "unknown"))
        status = str(meta.get("status", "unknown"))
        confidence = str(meta.get("confidence", "medium"))
        title = safe_title(str(c["path"].stem).replace("_", " "), max_len=60)
        link = f"[[10_Cards/{domain}/{card_id}|{title}]]"
        top_lines.append(f"- {link} | status={status} | confidence={confidence}")

    risk_lines = []
    for c in top_cards:
        limits = c["limits"]
        if limits:
            risk_lines.append(f"- {limits.splitlines()[0]}")
    if not risk_lines:
        risk_lines.append("- No explicit risk notes found in sampled cards.")

    next_actions = []
    for c in top_cards:
        nxt = c["next_action"]
        if nxt:
            next_actions.append(f"- {nxt.splitlines()[0]}")
    if not next_actions:
        next_actions.append("- Promote high-confidence cards to validated status.")

    weekly_content = "\n".join(
        [
            f"# Weekly Knowledge Report {week_label}",
            "",
            "## Summary",
            f"- Cards scanned: {len(cards)}",
            f"- Recent cards: {len(recent)}",
            f"- Domains touched: {len(by_domain)}",
            "",
            "## Domain Breakdown",
            "\n".join(domain_lines) if domain_lines else "- N/A",
            "",
            "## Status Breakdown",
            "\n".join(status_lines) if status_lines else "- N/A",
            "",
            "## Top Cards",
            "\n".join(top_lines) if top_lines else "- N/A",
            "",
            "## Risks and Uncertainty",
            "\n".join(risk_lines),
            "",
            "## Next Actions",
            "\n".join(next_actions),
            "",
            f"_Generated at {datetime.now(timezone.utc).isoformat()} (trace: {trace_id})_",
            "",
        ]
    )

    topic_lines = []
    for domain, card_ids in sorted(topic_pool.items(), key=lambda kv: len(kv[1]), reverse=True):
        topic_lines.append(f"- {domain}: {', '.join(card_ids[:5])}")

    topic_content = "\n".join(
        [
            f"# Topic Brief {now.strftime('%Y-%m-%d')}",
            "",
            "## Selected Topics",
            "\n".join(topic_lines) if topic_lines else "- N/A",
            "",
            "## Evidence Links",
            "\n".join(top_lines[:8]) if top_lines else "- N/A",
            "",
            "## Suggested Actions",
            "\n".join(next_actions[:8]),
            "",
            f"_Generated at {datetime.now(timezone.utc).isoformat()} (trace: {trace_id})_",
            "",
        ]
    )

    weekly_path.write_text(weekly_content, encoding="utf-8")
    topic_path.write_text(topic_content, encoding="utf-8")

    duration_ms = int((time.time() - started) * 1000)
    emit_metric(
        metrics_root=metrics_root,
        stage="analyze",
        trace_id=trace_id,
        duration_ms=duration_ms,
        success=True,
        extras={"cards": len(cards), "recent": len(recent), "top_cards": len(top_cards)},
    )
    append_jsonl(
        metrics_root / "analyze-run.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "cards": len(cards),
            "recent": len(recent),
            "top_cards": len(top_cards),
            "weekly_report": str(weekly_path),
            "topic_brief": str(topic_path),
            "duration_ms": duration_ms,
        },
    )

    return {
        "trace_id": trace_id,
        "cards": len(cards),
        "recent": len(recent),
        "weekly_report": str(weekly_path),
        "topic_brief": str(topic_path),
        "duration_ms": duration_ms,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze curated cards into weekly reports and topic briefs")
    parser.add_argument("--policy", default=None, help="Path to knowledge pipeline policy JSON")
    args = parser.parse_args()

    result = run(policy_path=args.policy)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
