#!/usr/bin/env python

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import knowledge_collect  # type: ignore
import knowledge_curate  # type: ignore


def _policy_for_tmp(tmp_path: Path, summary_glob: str) -> Path:
    policy = {
        "paths": {
            "inbox_raw": str(tmp_path / "Obsidian" / "00_Inbox" / "raw"),
            "inbox_normalized": str(tmp_path / "Obsidian" / "00_Inbox" / "normalized"),
            "cards_root": str(tmp_path / "Obsidian" / "10_Cards"),
            "moc_root": str(tmp_path / "Obsidian" / "20_MOC"),
            "projects_reports": str(tmp_path / "Obsidian" / "30_Projects" / "_reports"),
            "playbooks_root": str(tmp_path / "Obsidian" / "40_Playbooks"),
            "archive_root": str(tmp_path / "Obsidian" / "90_Archive"),
            "metrics_root": str(tmp_path / "logs" / "knowledge-pipeline"),
            "summary_structured_glob": summary_glob,
        },
        "classification": {
            "default_domain": "ops",
            "default_action": "summarize",
            "domain_keywords": {
                "ops": ["ops", "incident", "告警"],
                "engineering": ["code", "bug", "代码"],
            },
            "action_keywords": {
                "summarize": ["summary", "总结"],
                "collect": ["collect", "采集"],
            },
        },
        "limits": {"max_tags_per_card": 4},
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2), encoding="utf-8")
    return policy_path


def test_collect_from_structured_summary(tmp_path: Path):
    summary_dir = tmp_path / "summaries"
    summary_dir.mkdir(parents=True)
    summary_file = summary_dir / "summary-1.json"
    summary_file.write_text(
        json.dumps(
            {
                "本次核心产出": "完成 incident summary 并输出 runbook 线索",
                "项目关联": "openclaw-ops",
                "置信度": "high",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    policy_path = _policy_for_tmp(tmp_path, str(summary_dir / "*.json"))

    result = knowledge_collect.run(policy_path=str(policy_path), dry_run=False)
    normalized_dir = tmp_path / "Obsidian" / "00_Inbox" / "normalized"

    assert result["created"] >= 1
    assert normalized_dir.exists()
    items = list(normalized_dir.glob("*.json"))
    assert len(items) >= 1


def test_curate_creates_card_and_moc(tmp_path: Path):
    policy_path = _policy_for_tmp(tmp_path, str(tmp_path / "empty" / "*.json"))

    normalized_dir = tmp_path / "Obsidian" / "00_Inbox" / "normalized"
    normalized_dir.mkdir(parents=True)
    item = {
        "id": "inbox_test_001",
        "source": "manual://test",
        "source_type": "manual_note",
        "captured_at": "2026-03-03T00:00:00+00:00",
        "raw_text": "ops summary about gateway stability and cost trend",
        "domain": "ops",
        "action": "summarize",
        "confidence": "medium",
        "trace_id": "tr_test_001",
        "dedupe_key": "dedupe_test_001",
        "tags": ["domain/ops", "action/summarize"],
    }
    (normalized_dir / "inbox_test_001.json").write_text(
        json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    result = knowledge_curate.run(policy_path=str(policy_path), dry_run=False)

    cards = list((tmp_path / "Obsidian" / "10_Cards" / "ops").glob("*.md"))
    moc_files = list((tmp_path / "Obsidian" / "20_MOC").glob("*.md"))

    assert result["created"] >= 1 or result["deduped"] >= 1
    assert cards, "expected curated card file"
    assert moc_files, "expected MOC file"
