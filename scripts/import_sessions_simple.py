#!/usr/bin/env python3
"""
简单会话导入脚本 - 将历史会话导入向量库
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
from typing import Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get(
        "OPENCLAW_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"),
    )
).expanduser()

# 尝试导入 chromadb
try:
    import chromadb
    from chromadb.config import Settings

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️  警告: chromadb 未安装")


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


def resolve_persist_dir(
    persist_dir: Optional[str] = None,
    *,
    workspace_root: Optional[Path] = None,
) -> Path:
    if persist_dir:
        return Path(persist_dir).expanduser().resolve()

    workspace = Path(workspace_root or DEFAULT_WORKSPACE_ROOT).expanduser().resolve()
    return (workspace / "memory" / ".vector_db").resolve()


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
                value = value.strip("[]{}")
                metadata[key] = value
        elif found_opening and not in_frontmatter:
            body_lines.append(line)

    return metadata, "\n".join(body_lines)


def import_sessions(session_dir: str, collection) -> dict:
    """导入会话目录下的所有会话"""
    session_files = sorted(glob.glob(os.path.join(session_dir, "session_*.md")))

    stats = {
        "total": len(session_files),
        "imported": 0,
        "failed": 0,
    }

    date_match = Path(session_dir).name

    for file_path in session_files:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                content = handle.read()

            metadata, body = parse_frontmatter(content)

            title = metadata.get("title", Path(file_path).stem)
            tags = metadata.get("tags", "session")
            doc_id = f"session_{Path(file_path).stem}"

            collection.add(
                documents=[body],
                metadatas=[
                    {
                        "title": title,
                        "type": "session",
                        "date": date_match,
                        "source": file_path,
                        "tags": tags,
                        "uuid": metadata.get("uuid", ""),
                        "created": metadata.get("created", ""),
                    }
                ],
                ids=[doc_id],
            )

            stats["imported"] += 1
            print(f"✅ 导入: {title}")

        except Exception as exc:
            stats["failed"] += 1
            print(f"❌ 失败: {os.path.basename(file_path)} - {exc}")

    return stats


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将历史 session markdown 导入到 ChromaDB")
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
        "--persist-dir",
        help="覆盖 ChromaDB 持久化目录，默认使用 workspace/memory/.vector_db",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    """主函数"""
    args = _parse_args(argv)
    print("=" * 60)
    print("会话记录导入工具")
    print("=" * 60)

    if not DEPENDENCIES_AVAILABLE:
        print("❌ 缺少 chromadb，请先安装")
        return 1

    workspace_root = (
        Path(args.workspace_root).expanduser().resolve()
        if args.workspace_root
        else DEFAULT_WORKSPACE_ROOT
    )
    persist_dir = resolve_persist_dir(args.persist_dir, workspace_root=workspace_root)
    persist_dir.parent.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )

    collection = client.get_or_create_collection(name="deep_sea_nexus_sessions")
    print("✅ 向量库连接成功")

    session_dirs = args.session_dirs or build_default_session_dirs(
        workspace_root=workspace_root,
        nexus_root=resolve_nexus_root(),
    )

    if not session_dirs:
        print("⚠️ 未发现可导入的 session 目录，请使用 --session-dir 显式指定")
        return 0

    all_stats = {"total": 0, "imported": 0, "failed": 0}

    for session_dir in session_dirs:
        resolved_dir = os.path.expanduser(session_dir)
        if os.path.exists(resolved_dir):
            print(f"\n📁 发现会话目录: {resolved_dir}")
            stats = import_sessions(resolved_dir, collection)
            all_stats["total"] += stats["total"]
            all_stats["imported"] += stats["imported"]
            all_stats["failed"] += stats["failed"]
        else:
            print(f"⚠️ 目录不存在: {resolved_dir}")

    print("\n" + "=" * 60)
    print("导入完成!")
    print("📊 总计:")
    print(f"  - 发现会话: {all_stats['total']}")
    print(f"  - 成功导入: {all_stats['imported']}")
    print(f"  - 失败: {all_stats['failed']}")
    print(f"  - 向量库文档数: {collection.count()}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
