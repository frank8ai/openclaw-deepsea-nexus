#!/usr/bin/env python3
"""
批量导入会话和重要笔记到数据库
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get(
        "OPENCLAW_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"),
    )
).expanduser()
DAILY_NOTE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def resolve_nexus_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return PROJECT_ROOT


def resolve_db_path(
    db_path: Optional[str] = None,
    *,
    workspace_root: Optional[Path] = None,
) -> Path:
    if db_path:
        return Path(db_path).expanduser().resolve()

    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    return (workspace / "memory" / "sessions.db").resolve()


def _collect_session_dirs(root: Path) -> List[Path]:
    if not root.exists():
        return []

    directories: List[Path] = []
    if any(root.glob("session_*.md")):
        directories.append(root)

    for child in sorted(root.iterdir()):
        if child.is_dir() and any(child.glob("session_*.md")):
            directories.append(child)
    return directories


def build_default_session_dirs(
    *,
    workspace_root: Optional[Path] = None,
    nexus_root: Optional[Path] = None,
) -> List[str]:
    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    root = Path(nexus_root or resolve_nexus_root()).resolve()
    search_roots = [
        root / "memory" / "90_Memory",
        workspace / "memory" / "90_Memory",
    ]

    seen = set()
    session_dirs: List[str] = []
    for search_root in search_roots:
        for directory in _collect_session_dirs(search_root):
            directory_str = str(directory)
            if directory_str not in seen:
                seen.add(directory_str)
                session_dirs.append(directory_str)
    return session_dirs


def build_default_rescue_dirs(
    *,
    workspace_root: Optional[Path] = None,
    nexus_root: Optional[Path] = None,
) -> List[str]:
    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    root = Path(nexus_root or resolve_nexus_root()).resolve()
    search_roots = [
        root / "Obsidian" / "90_Memory",
        workspace / "Obsidian" / "90_Memory",
    ]

    seen = set()
    rescue_dirs: List[str] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for child in sorted(search_root.iterdir()):
            if child.is_dir() and child.name.endswith("-Rescue") and any(child.glob("SESSION_*.md")):
                child_str = str(child.resolve())
                if child_str not in seen:
                    seen.add(child_str)
                    rescue_dirs.append(child_str)
    return rescue_dirs


def build_default_daily_files(
    *,
    workspace_root: Optional[Path] = None,
    nexus_root: Optional[Path] = None,
) -> List[str]:
    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    root = Path(nexus_root or resolve_nexus_root()).resolve()
    search_roots = [
        root / "memory",
        workspace / "memory",
    ]

    seen = set()
    daily_files: List[str] = []
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for child in sorted(search_root.iterdir()):
            if child.is_file() and DAILY_NOTE_RE.match(child.name):
                child_str = str(child.resolve())
                if child_str not in seen:
                    seen.add(child_str)
                    daily_files.append(child_str)
    return daily_files


def parse_frontmatter(content: str) -> tuple:
    """解析 markdown frontmatter"""
    lines = content.split("\n")
    metadata = {}
    body_lines = []
    in_frontmatter = False
    found_opening = False

    for line in lines:
        if line.strip() == "---":
            if not found_opening:
                found_opening = True
                in_frontmatter = True
                continue
            in_frontmatter = False
            continue

        if in_frontmatter and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                metadata[key] = value
        elif found_opening and not in_frontmatter:
            body_lines.append(line)

    return metadata, "\n".join(body_lines)


def init_db(db_path: str):
    """初始化数据库"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            content TEXT,
            date TEXT,
            tags TEXT,
            uuid TEXT,
            created TEXT,
            source TEXT,
            doc_type TEXT
        )
        """
    )
    conn.commit()
    return conn


def import_file(file_path: str, conn, doc_type: str = "session") -> bool:
    """导入单个文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()

        metadata, body = parse_frontmatter(content)
        title = metadata.get("title", Path(file_path).stem)
        doc_id = f"{doc_type}_{Path(file_path).stem}"

        conn.execute(
            """
            INSERT OR REPLACE INTO sessions
            (id, title, content, date, tags, uuid, created, source, doc_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                title,
                body,
                metadata.get("created", "")[:10] if metadata.get("created") else "",
                metadata.get("tags", doc_type),
                metadata.get("uuid", ""),
                metadata.get("created", ""),
                file_path,
                doc_type,
            ),
        )

        print(f"✅ 导入 [{doc_type}]: {title}")
        return True

    except Exception as exc:
        print(f"❌ 失败: {os.path.basename(file_path)} - {exc}")
        return False


def import_directory(
    session_dir: str,
    conn,
    pattern: str = "*.md",
    doc_type: str = "session",
) -> dict:
    """导入目录下所有匹配的文件"""
    files = sorted(glob.glob(os.path.join(session_dir, pattern)))
    stats = {"total": len(files), "imported": 0, "failed": 0}

    for file_path in files:
        if import_file(file_path, conn, doc_type):
            stats["imported"] += 1
        else:
            stats["failed"] += 1

    conn.commit()
    return stats


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量导入 session、rescue 和 daily notes 到 SQLite")
    parser.add_argument(
        "--session-dir",
        action="append",
        dest="session_dirs",
        help="显式指定 session 目录，可重复传入",
    )
    parser.add_argument(
        "--rescue-dir",
        action="append",
        dest="rescue_dirs",
        help="显式指定 rescue 目录，可重复传入",
    )
    parser.add_argument(
        "--daily-file",
        action="append",
        dest="daily_files",
        help="显式指定 daily note 文件，可重复传入",
    )
    parser.add_argument(
        "--workspace-root",
        help="覆盖默认工作区根目录，用于发现 workspace 下的数据",
    )
    parser.add_argument(
        "--db-path",
        help="覆盖 SQLite 数据库路径，默认使用 workspace/memory/sessions.db",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    print("=" * 60)
    print("批量导入工具 - 会话和笔记")
    print("=" * 60)

    workspace_root = (
        Path(args.workspace_root).expanduser().resolve()
        if args.workspace_root
        else DEFAULT_WORKSPACE_ROOT
    )
    db_path = resolve_db_path(args.db_path, workspace_root=workspace_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = init_db(str(db_path))
    print(f"✅ 数据库: {db_path}")

    session_dirs = args.session_dirs or build_default_session_dirs(
        workspace_root=workspace_root,
        nexus_root=resolve_nexus_root(),
    )
    rescue_dirs = args.rescue_dirs or build_default_rescue_dirs(
        workspace_root=workspace_root,
        nexus_root=resolve_nexus_root(),
    )
    daily_files = args.daily_files or build_default_daily_files(
        workspace_root=workspace_root,
        nexus_root=resolve_nexus_root(),
    )

    all_stats = {"total": 0, "imported": 0, "failed": 0}

    for session_dir in session_dirs:
        resolved_dir = os.path.expanduser(session_dir)
        if os.path.exists(resolved_dir):
            print(f"\n📁 导入会话: {resolved_dir}")
            stats = import_directory(resolved_dir, conn, "session_*.md", "session")
            all_stats["total"] += stats["total"]
            all_stats["imported"] += stats["imported"]
            all_stats["failed"] += stats["failed"]

    for rescue_dir in rescue_dirs:
        resolved_dir = os.path.expanduser(rescue_dir)
        if os.path.exists(resolved_dir):
            print(f"\n📁 导入 Rescue 会话: {resolved_dir}")
            stats = import_directory(resolved_dir, conn, "SESSION_*.md", "rescue-session")
            all_stats["total"] += stats["total"]
            all_stats["imported"] += stats["imported"]
            all_stats["failed"] += stats["failed"]

    for daily_file in daily_files:
        resolved_file = os.path.expanduser(daily_file)
        if os.path.exists(resolved_file):
            print(f"\n📄 导入每日笔记: {Path(resolved_file).stem}")
            if import_file(resolved_file, conn, "daily-note"):
                all_stats["imported"] += 1
                all_stats["total"] += 1
            else:
                all_stats["failed"] += 1
                all_stats["total"] += 1

    if not (session_dirs or rescue_dirs or daily_files):
        print("⚠️ 未发现可导入的数据，请使用显式参数指定")
        conn.close()
        return 0

    print("\n" + "=" * 60)
    print("导入完成!")
    print(f"  - 处理: {all_stats['total']}")
    print(f"  - 成功: {all_stats['imported']}")
    print(f"  - 失败: {all_stats['failed']}")

    cursor = conn.execute("SELECT COUNT(*), doc_type FROM sessions GROUP BY doc_type")
    print("\n📊 按类型统计:")
    for row in cursor.fetchall():
        print(f"  - {row[1]}: {row[0]}")

    conn.close()
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
