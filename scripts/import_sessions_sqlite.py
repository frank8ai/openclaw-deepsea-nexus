#!/usr/bin/env python3
"""
会话导入脚本 - 使用系统 sqlite3
"""

from __future__ import annotations

import argparse
import glob
import os
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


def resolve_nexus_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return PROJECT_ROOT


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


def resolve_db_path(
    db_path: Optional[str] = None,
    *,
    workspace_root: Optional[Path] = None,
) -> Path:
    if db_path:
        return Path(db_path).expanduser().resolve()

    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    return (workspace / "memory" / "sessions.db").resolve()


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
    """初始化 SQLite 数据库"""
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
            embedding BLOB
        )
        """
    )
    conn.commit()
    return conn


def import_sessions(session_dir: str, conn) -> dict:
    """导入会话"""
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.md")))

    stats = {"total": len(session_files), "imported": 0, "failed": 0}
    date_match = Path(session_dir).name

    for file_path in session_files:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()

            metadata, body = parse_frontmatter(content)
            title = metadata.get("title", Path(file_path).stem)
            doc_id = f"session_{Path(file_path).stem}"

            conn.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, title, content, date, tags, uuid, created, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    title,
                    body,
                    date_match,
                    metadata.get("tags", "session"),
                    metadata.get("uuid", ""),
                    metadata.get("created", ""),
                    file_path,
                ),
            )

            stats["imported"] += 1
            print(f"✅ 导入: {title}")

        except Exception as exc:
            stats["failed"] += 1
            print(f"❌ 失败: {os.path.basename(file_path)} - {exc}")

    conn.commit()
    return stats


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将历史 session markdown 导入到 SQLite")
    parser.add_argument(
        "--session-dir",
        action="append",
        dest="session_dirs",
        help="显式指定要导入的 session 目录，可重复传入",
    )
    parser.add_argument(
        "--workspace-root",
        help="覆盖默认工作区根目录，用于发现 workspace/memory/90_Memory 下的会话目录",
    )
    parser.add_argument(
        "--db-path",
        help="覆盖 SQLite 数据库路径，默认使用 workspace/memory/sessions.db",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    print("=" * 60)
    print("会话记录导入工具 (SQLite)")
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
    if not session_dirs:
        print("⚠️ 未发现可导入的 session 目录，请使用 --session-dir 显式指定")
        conn.close()
        return 0

    all_stats = {"total": 0, "imported": 0, "failed": 0}
    for session_dir in session_dirs:
        resolved_dir = os.path.expanduser(session_dir)
        if os.path.exists(resolved_dir):
            print(f"\n📁 会话目录: {resolved_dir}")
            stats = import_sessions(resolved_dir, conn)
            all_stats["total"] += stats["total"]
            all_stats["imported"] += stats["imported"]
            all_stats["failed"] += stats["failed"]
        else:
            print(f"⚠️ 目录不存在: {resolved_dir}")

    print("\n" + "=" * 60)
    print("导入完成!")
    print(f"  - 发现: {all_stats['total']}")
    print(f"  - 成功: {all_stats['imported']}")
    print(f"  - 失败: {all_stats['failed']}")
    cursor = conn.execute("SELECT COUNT(*) FROM sessions")
    print(f"  - 数据库总数: {cursor.fetchone()[0]}")

    conn.close()
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
