#!/usr/bin/env python3
"""
会话记录导入脚本 - 将历史会话导入向量库
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

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


def resolve_config_path(
    config_path: Optional[str] = None,
    *,
    nexus_root: Optional[Path] = None,
) -> Path:
    if config_path:
        return Path(config_path).expanduser().resolve()

    root = Path(nexus_root or resolve_nexus_root()).resolve()
    candidates = [
        root / "config.json",
        root / "config.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def configure_import_paths(nexus_root: Path) -> None:
    candidates = [
        nexus_root,
        nexus_root / "vector_store",
        nexus_root / "src" / "retrieval",
    ]
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def load_dependencies(
    nexus_root: Optional[Path] = None,
) -> Tuple[Optional[Any], Optional[Any], Optional[str]]:
    root = Path(nexus_root or resolve_nexus_root()).resolve()
    configure_import_paths(root)

    try:
        from init_chroma import create_vector_store  # type: ignore
        from manager import create_manager  # type: ignore
    except ImportError as exc:
        return None, None, str(exc)

    return create_vector_store, create_manager, None


def load_config(
    config_path: Optional[str] = None,
    *,
    nexus_root: Optional[Path] = None,
) -> Tuple[Dict[str, Any], Path]:
    resolved = resolve_config_path(config_path, nexus_root=nexus_root)
    with open(resolved, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data, resolved


def parse_session_file(file_path: str) -> Dict[str, Any]:
    """解析会话文件"""
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    lines = content.split("\n")
    metadata: Dict[str, Any] = {}
    body: List[str] = []
    in_frontmatter = False
    in_body = False

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
            else:
                in_body = True
            continue

        if in_frontmatter and ":" in line:
            key = line.split(":")[0].strip()
            value = line.split(":", 1)[1].strip()
            if value.startswith("[") or value.startswith("{"):
                try:
                    parsed = yaml.safe_load(value)
                    if isinstance(parsed, (list, dict)):
                        value = parsed
                except Exception:
                    pass
            metadata[key] = value
        elif in_body:
            body.append(line)

    return {
        "title": metadata.get("title", Path(file_path).stem),
        "content": "\n".join(body),
        "uuid": metadata.get("uuid", ""),
        "created": metadata.get("created", ""),
        "tags": metadata.get("tags", []),
        "type": metadata.get("type", "session"),
        "source": file_path,
    }


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


def import_sessions(session_dir: str, store, _config: Dict[str, Any]) -> Dict[str, Any]:
    """导入会话目录下的所有会话"""
    session_files = glob.glob(os.path.join(session_dir, "session_*.md"))

    stats = {
        "total": len(session_files),
        "imported": 0,
        "failed": 0,
        "chunks": 0,
    }

    date_match = os.path.basename(session_dir)

    for file_path in session_files:
        try:
            session_data = parse_session_file(file_path)

            metadata = {
                "title": session_data["title"],
                "source_file": session_data["source"],
                "type": "session",
                "date": date_match,
                "uuid": session_data["uuid"],
                "created_at": session_data["created"],
                "tags": ",".join(session_data["tags"]) if session_data["tags"] else "session",
            }

            store.add_note(
                content=session_data["content"],
                metadata=metadata,
            )

            stats["imported"] += 1
            print(f"✅ 导入: {session_data['title']}")

        except Exception as exc:
            stats["failed"] += 1
            print(f"❌ 失败: {os.path.basename(file_path)} - {exc}")

    return stats


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入历史 session markdown 到当前向量库")
    parser.add_argument("--config-path", help="配置文件路径，默认自动解析 config.json/config.yaml")
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
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    """主函数"""
    args = _parse_args(argv)
    print("=" * 60)
    print("会话记录导入工具")
    print("=" * 60)

    nexus_root = resolve_nexus_root()
    workspace_root = (
        Path(args.workspace_root).expanduser().resolve()
        if args.workspace_root
        else DEFAULT_WORKSPACE_ROOT
    )

    create_vector_store, create_manager, import_error = load_dependencies(nexus_root)
    if import_error:
        print(f"❌ 缺少依赖或导入失败: {import_error}")
        return 1

    config, config_path = load_config(args.config_path, nexus_root=nexus_root)
    print(f"✅ 配置加载完成: {config_path}")

    store = create_vector_store(config_path=str(config_path))
    print(f"✅ 向量库连接成功: {store.collection.name}")

    manager = create_manager(store.embedder, store.collection, str(config_path))
    session_dirs = args.session_dirs or build_default_session_dirs(
        workspace_root=workspace_root,
        nexus_root=nexus_root,
    )

    if not session_dirs:
        print("⚠️ 未发现可导入的 session 目录，请使用 --session-dir 显式指定")
        return 0

    all_stats = {
        "total": 0,
        "imported": 0,
        "failed": 0,
        "chunks": 0,
    }

    for session_dir in session_dirs:
        resolved_dir = os.path.expanduser(session_dir)

        if os.path.exists(resolved_dir):
            print(f"\n📁 发现会话目录: {resolved_dir}")
            stats = import_sessions(resolved_dir, manager, config)

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
    print(f"  - 向量库文档数: {store.collection.count()}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
