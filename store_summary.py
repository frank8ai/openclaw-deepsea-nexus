#!/usr/bin/env python3
"""
智能摘要存储脚本

用法：
    python3 store_summary.py "对话ID" "LLM回复内容" "用户问题(可选)"

示例：
    python3 store_summary.py "session_001" "回复内容... ---SUMMARY--- 摘要 ---END---"

或交互式使用：
    python3 store_summary.py
    # 然后输入对话ID和回复内容
"""

import sys
import json
import importlib.util
from pathlib import Path

from auto_summary import HybridStorage, SummaryParser


def _load_local_package():
    repo_root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_store_summary",
        repo_root / "__init__.py",
        submodule_search_locations=[str(repo_root)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
nexus_init = deepsea_nexus.nexus_init
nexus_add = deepsea_nexus.nexus_add


class _SummaryStoreAdapter:
    """Minimal vector-store shape expected by HybridStorage."""

    def add(self, content: str, title: str = "", tags: str = "") -> str:
        return nexus_add(content=content, title=title, tags=tags) or ""


def main():
    if not nexus_init():
        print("✗ 初始化失败")
        sys.exit(1)
    
    storage = HybridStorage(_SummaryStoreAdapter())
    
    if len(sys.argv) >= 3:
        # 命令行参数
        conversation_id = sys.argv[1]
        response = sys.argv[2]
        user_query = sys.argv[3] if len(sys.argv) > 3 else ""
    else:
        # 交互式输入
        print("=== 智能摘要存储 ===")
        conversation_id = input("对话ID: ").strip()
        print("请粘贴 LLM 回复内容 (Ctrl+D 完成):")
        response = sys.stdin.read().strip()
        user_query = input("用户问题 (可选): ").strip()
    
    # 解析
    reply, summary = SummaryParser.parse(response)
    
    print(f"\n✓ 解析成功")
    print(f"  原文: {reply[:50]}...")
    print(f"  摘要: {summary}")
    
    # 存储
    result = storage.process_and_store(
        conversation_id=conversation_id,
        response=response,
        user_query=user_query
    )
    
    print(f"\n✓ 存储完成")
    print(f"  存储数量: {result['stored_count']} 条")
    print(f"  对话ID: {result['conversation_id']}")


if __name__ == "__main__":
    main()
