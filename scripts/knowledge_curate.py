#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from knowledge_common import (
    append_jsonl,
    confidence_to_score,
    dump_frontmatter,
    emit_metric,
    ensure_pipeline_dirs,
    load_json,
    load_policy,
    make_trace_id,
    now_iso,
    read_markdown_frontmatter,
    render_tags,
    sanitize_slug,
    safe_title,
    stable_hash,
    write_json,
)


def _load_tag_whitelist(root: Path) -> dict[str, Any]:
    return load_json(root / "config" / "knowledge-pipeline" / "tag_whitelist.v1.json", {}) or {}


def _load_moc_map(root: Path) -> dict[str, Any]:
    return load_json(root / "config" / "knowledge-pipeline" / "moc_map.v1.json", {}) or {}


def _pick_status(confidence: Any) -> str:
    score = confidence_to_score(confidence)
    if score >= 0.85:
        return "validated"
    if score >= 0.55:
        return "draft"
    return "inbox"


def _pick_type(action: str) -> str:
    if action == "decide":
        return "decision"
    if action == "monitor":
        return "risk"
    if action == "execute":
        return "procedure"
    return "insight"


def _build_tags(item: dict[str, Any], whitelist: dict[str, Any], max_tags: int) -> list[str]:
    domain_allowed = set((whitelist.get("domain") or []))
    action_allowed = set((whitelist.get("action") or []))

    tags: list[str] = []
    domain = item.get("domain", "ops")
    action = item.get("action", "summarize")

    if domain in domain_allowed:
        tags.append(f"domain/{domain}")
    if action in action_allowed:
        tags.append(f"action/{action}")

    for tag in item.get("tags") or []:
        if not isinstance(tag, str):
            continue
        t = tag.strip()
        if not t or t in tags:
            continue
        if t.startswith("domain/"):
            if t.split("/", 1)[1] not in domain_allowed:
                continue
        if t.startswith("action/"):
            if t.split("/", 1)[1] not in action_allowed:
                continue
        tags.append(t)
        if len(tags) >= max_tags:
            break

    return tags[:max_tags]


def _render_card(item: dict[str, Any], card_id: str, tags: list[str], status: str, card_type: str) -> str:
    now = now_iso()
    created = item.get("captured_at") or now
    updated = now
    trace_id = item.get("trace_id", "")
    dedupe_key = item.get("dedupe_key", "")
    title = safe_title(item.get("title") or item.get("raw_text") or card_id)

    evidence_lines = [
        f"- Source: {item.get('source', '')}",
        f"- Trace: {trace_id}",
    ]

    body = [
        "## Claim",
        item.get("raw_text", "").strip() or "N/A",
        "",
        "## Why",
        "Captured via automated knowledge curation pipeline for future reuse.",
        "",
        "## Evidence",
        "\n".join(evidence_lines),
        "",
        "## Use Cases",
        "- Reuse in reports and strategy notes",
        "- Link to project execution context",
        "",
        "## Limits",
        "- May require manual validation for high-stakes decisions",
        "",
        "## Next Action",
        "- Review and promote status when evidence is sufficient",
    ]

    meta = {
        "id": card_id,
        "type": card_type,
        "domain": item.get("domain", "ops"),
        "status": status,
        "source": item.get("source", ""),
        "confidence": item.get("confidence", "medium"),
        "tags": tags,
        "created": created,
        "updated": updated,
        "trace_id": trace_id,
        "dedupe_key": dedupe_key,
    }

    return f"{dump_frontmatter(meta)}\n\n# {title}\n\n" + "\n".join(body).strip() + "\n"


def _write_or_update_moc(moc_file: Path, card_link: str, card_title: str, status: str, confidence: Any) -> bool:
    line = f"- {card_link} | {card_title} | status={status} | confidence={confidence}"
    if not moc_file.exists():
        content = "\n".join(
            [
                f"# MOC {moc_file.stem}",
                "",
                "## Scope",
                f"Domain knowledge map for {moc_file.stem}.",
                "",
                "## Cards",
                line,
                "",
                "## Relations",
                "- supports",
                "",
                "## Update Log",
                f"- {now_iso()} appended {card_link}",
                "",
            ]
        )
        moc_file.parent.mkdir(parents=True, exist_ok=True)
        moc_file.write_text(content, encoding="utf-8")
        return True

    content = moc_file.read_text(encoding="utf-8")
    if line in content:
        return False

    if "## Cards\n" in content:
        content = content.replace("## Cards\n", f"## Cards\n{line}\n", 1)
    else:
        content += f"\n## Cards\n{line}\n"

    if "## Update Log\n" in content:
        content = content.replace(
            "## Update Log\n",
            f"## Update Log\n- {now_iso()} appended {card_link}\n",
            1,
        )
    else:
        content += f"\n## Update Log\n- {now_iso()} appended {card_link}\n"

    moc_file.write_text(content, encoding="utf-8")
    return True


def _update_existing_card(card_path: Path, source: str) -> None:
    meta, body = read_markdown_frontmatter(card_path)
    meta["updated"] = now_iso()
    evidence_line = f"- Source: {source}"

    if "## Evidence" in body and evidence_line not in body:
        body = body.replace("## Evidence\n", f"## Evidence\n{evidence_line}\n", 1)

    content = f"{dump_frontmatter(meta)}\n\n{body.strip()}\n"
    card_path.write_text(content, encoding="utf-8")


def run(policy_path: str | None = None, max_items: int = 0, dry_run: bool = False) -> dict[str, Any]:
    started = time.time()
    trace_id = make_trace_id("curate")
    policy = load_policy(policy_path)
    dirs = ensure_pipeline_dirs(policy)
    root = Path(__file__).resolve().parents[3]
    metrics_root = dirs["metrics_root"]

    limits = policy.get("limits", {})
    max_tags = int(limits.get("max_tags_per_card", 4))

    state_path = metrics_root / "curate-state.json"
    dedupe_path = metrics_root / "card-dedupe-index.json"

    state = load_json(state_path, {"processed_item_ids": []})
    dedupe_index = load_json(dedupe_path, {})
    processed_set = set(state.get("processed_item_ids", []))

    whitelist = _load_tag_whitelist(root)
    moc_map = _load_moc_map(root).get("moc_by_domain", {})

    items = sorted(dirs["inbox_normalized"].glob("*.json"))
    created = 0
    updated = 0
    deduped = 0
    failed = 0
    moc_updates = 0

    processed_count = 0
    for item_file in items:
        if max_items and processed_count >= max_items:
            break
        try:
            item = json.loads(item_file.read_text(encoding="utf-8"))
            item_id = str(item.get("id", ""))
            if not item_id or item_id in processed_set:
                continue

            dedupe_key = item.get("dedupe_key") or stable_hash(item.get("raw_text", ""), length=24)
            existing = dedupe_index.get(dedupe_key)
            domain = sanitize_slug(item.get("domain", "ops"), fallback="ops")

            if existing:
                card_path = Path(existing.get("path", ""))
                if card_path.exists() and not dry_run:
                    _update_existing_card(card_path, item.get("source", ""))
                deduped += 1
                updated += 1
            else:
                card_id = f"card_{stable_hash(item.get('raw_text', ''), length=10)}"
                card_type = _pick_type(str(item.get("action", "summarize")))
                status = _pick_status(item.get("confidence"))
                tags = _build_tags(item, whitelist, max_tags)

                domain_dir = dirs["cards_root"] / domain
                card_path = domain_dir / f"{card_id}.md"
                card_content = _render_card(item, card_id, tags, status, card_type)
                card_title = safe_title(item.get("title") or item.get("raw_text") or card_id)

                if not dry_run:
                    domain_dir.mkdir(parents=True, exist_ok=True)
                    card_path.write_text(card_content, encoding="utf-8")

                dedupe_index[dedupe_key] = {
                    "card_id": card_id,
                    "path": str(card_path),
                    "updated": now_iso(),
                }
                created += 1

                moc_id = sanitize_slug(moc_map.get(domain, domain), fallback=domain)
                moc_file = dirs["moc_root"] / f"{moc_id}.md"
                card_link = f"[[10_Cards/{domain}/{card_id}|{card_id}]]"
                if not dry_run and _write_or_update_moc(
                    moc_file=moc_file,
                    card_link=card_link,
                    card_title=card_title,
                    status=status,
                    confidence=item.get("confidence", "medium"),
                ):
                    moc_updates += 1

            processed_set.add(item_id)
            processed_count += 1
        except Exception:
            failed += 1

    state["processed_item_ids"] = sorted(processed_set)
    if not dry_run:
        write_json(state_path, state)
        write_json(dedupe_path, dedupe_index)

    duration_ms = int((time.time() - started) * 1000)
    emit_metric(
        metrics_root=metrics_root,
        stage="curate",
        trace_id=trace_id,
        duration_ms=duration_ms,
        success=failed == 0,
        extras={
            "created": created,
            "updated": updated,
            "deduped": deduped,
            "failed": failed,
            "moc_updates": moc_updates,
        },
        error_class="curate_error" if failed else "",
    )

    run_log = {
        "ts": now_iso(),
        "trace_id": trace_id,
        "created": created,
        "updated": updated,
        "deduped": deduped,
        "failed": failed,
        "moc_updates": moc_updates,
        "duration_ms": duration_ms,
        "dry_run": dry_run,
    }
    if not dry_run:
        append_jsonl(metrics_root / "curate-run.jsonl", run_log)

    return run_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate normalized inbox items into cards and MOC")
    parser.add_argument("--policy", default=None, help="Path to knowledge pipeline policy JSON")
    parser.add_argument("--max-items", type=int, default=0, help="Optional max items to process")
    parser.add_argument("--dry-run", action="store_true", help="Do not write output files")
    args = parser.parse_args()

    result = run(policy_path=args.policy, max_items=args.max_items, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
