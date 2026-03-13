#!/usr/bin/env python3
"""
Helpers for maintenance scripts that still operate on the legacy filesystem
layout.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_PATH = Path("memory/90_Memory")


@dataclass(frozen=True)
class LegacyLayoutPaths:
    repo_root: Path
    workspace_root: Path
    memory_root: Path


def load_repo_config(repo_root: Path | None = None) -> dict:
    root = Path(repo_root or REPO_ROOT).expanduser().resolve()
    config_path = root / "config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def resolve_legacy_layout(
    repo_root: Path | None = None,
    config: dict | None = None,
) -> LegacyLayoutPaths:
    root = Path(repo_root or REPO_ROOT).expanduser().resolve()
    cfg = config if config is not None else load_repo_config(root)
    paths = cfg.get("paths", {}) if isinstance(cfg.get("paths", {}), dict) else {}

    workspace_root = Path(paths.get("base", root)).expanduser()
    if not workspace_root.is_absolute():
        workspace_root = (root / workspace_root).resolve()
    else:
        workspace_root = workspace_root.resolve()

    memory_root = Path(paths.get("memory", DEFAULT_MEMORY_PATH)).expanduser()
    if not memory_root.is_absolute():
        memory_root = (workspace_root / memory_root).resolve()
    else:
        memory_root = memory_root.resolve()

    return LegacyLayoutPaths(
        repo_root=root,
        workspace_root=workspace_root,
        memory_root=memory_root,
    )


def resolve_day_dir(date_str: str, layout: LegacyLayoutPaths | None = None) -> Path:
    paths = layout or resolve_legacy_layout()
    return paths.memory_root / date_str


def list_session_files(date_dir: Path) -> list[Path]:
    if not date_dir.exists():
        return []
    return sorted(
        [
            child
            for child in date_dir.iterdir()
            if child.is_file() and child.name.startswith("session_") and child.suffix == ".md"
        ]
    )


def iter_legacy_dates(
    layout: LegacyLayoutPaths | None = None,
    month: str | None = None,
) -> list[str]:
    paths = layout or resolve_legacy_layout()
    if not paths.memory_root.exists():
        return []

    prefix = f"{month}-" if month else None
    dates: list[str] = []
    for child in paths.memory_root.iterdir():
        if not child.is_dir():
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", child.name):
            continue
        if prefix and not child.name.startswith(prefix):
            continue
        dates.append(child.name)
    return sorted(dates)


def create_daily_index(index_file: Path, date_str: str) -> None:
    index_file.parent.mkdir(parents=True, exist_ok=True)
    content = f"""---
uuid: {datetime.now().strftime("%Y%m%d%H%M%S")}
type: daily-index
tags: [daily-index, {date_str}]
created: {date_str}
---

# {date_str} Daily Index

## Sessions (0)
_(no active sessions)_

## Gold Keys (0)
_(no gold keys)_

## Topics (0)
_(no topics)_
"""
    index_file.write_text(content, encoding="utf-8")


def daily_flush_legacy_layout(
    date_str: str | None = None,
    layout: LegacyLayoutPaths | None = None,
) -> dict:
    paths = layout or resolve_legacy_layout()
    flush_date = date_str or datetime.now().strftime("%Y-%m-%d")
    today_dir = resolve_day_dir(flush_date, paths)
    today_dir.mkdir(parents=True, exist_ok=True)

    sessions = list_session_files(today_dir)
    archive_dir = paths.memory_root / flush_date[:7]
    archive_dir.mkdir(parents=True, exist_ok=True)

    flushed = 0
    for session_file in sessions:
        session_file.rename(archive_dir / session_file.name)
        flushed += 1

    create_daily_index(today_dir / "_INDEX.md", flush_date)
    return {
        "date": flush_date,
        "flushed_count": flushed,
        "archive_dir": str(archive_dir),
    }
