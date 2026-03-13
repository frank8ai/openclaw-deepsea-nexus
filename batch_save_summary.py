#!/usr/bin/env python3
"""
批量保存摘要到向量库（历史兼容脚本）

Reference-only compatibility helper for older manual workflows.
Current v5 summary/runtime docs:
- docs/README.md
- docs/API_CURRENT.md
- docs/LOCAL_DEPLOY.md
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent
OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser()
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get("OPENCLAW_WORKSPACE", OPENCLAW_HOME / "workspace")
).expanduser()


def resolve_nexus_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return REPO_ROOT.resolve()


def resolve_memory_dir() -> Path:
    override = os.environ.get("NEXUS_MEMORY_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (DEFAULT_WORKSPACE_ROOT / "memory").resolve()


NEXUS_PATH = str(resolve_nexus_root())
sys.path.insert(0, NEXUS_PATH)

def extract_summary_from_text(text: str) -> tuple:
    """
    从文本中提取摘要部分
    返回 (正文, 摘要) 元组
    """
    # 匹配 ## 📋 总结 格式
    pattern = r'##\s*📋\s*总结\s*\n\s*([\s\S]*?)(?=\n\n##|\n\n---|$)'
    match = re.search(pattern, text)
    
    if match:
        summary = match.group(1).strip()
        # 移除摘要部分得到正文
        main_text = re.sub(pattern, '', text).strip()
        return main_text, summary
    
    return text, None


def save_summary_direct(text: str, source: str = "manual", tags: list = None):
    """
    直接保存摘要到向量库
    """
    try:
        from vector_store.init_chroma import create_vector_store
        from vector_store.manager import create_manager
        
        # 初始化向量存储
        vs = create_vector_store()
        vs.initialize_all()
        store = create_manager(vs.embedder, vs.collection)
        
        # 提取摘要
        main_text, summary = extract_summary_from_text(text)
        
        if summary:
            # 保存摘要（带标记）
            summary_id = store.add_note(
                content=summary,
                metadata={
                    "title": f"摘要 - {source}",
                    "tags": tags or ["summary", "auto-extracted"],
                    "is_summary": True,
                    "source": source,
                    "timestamp": datetime.now().isoformat(),
                    "has_summary": True
                }
            )
            print(f"✅ 摘要已保存: {summary_id}")
        
        # 保存正文
        if main_text:
            content_id = store.add_note(
                content=main_text,
                metadata={
                    "title": f"对话 - {source}",
                    "tags": tags or ["conversation"],
                    "is_summary": False,
                    "source": source,
                    "timestamp": datetime.now().isoformat()
                }
            )
            print(f"✅ 正文已保存: {content_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_save_from_memory_files(memory_dir: Optional[str] = None):
    """
    从 memory 文件批量导入历史对话
    """
    memory_dir_path = (
        Path(memory_dir).expanduser().resolve()
        if memory_dir
        else resolve_memory_dir()
    )
    
    if not memory_dir_path.exists():
        print(f"⚠️ 目录不存在: {memory_dir_path}")
        return
    
    count = 0
    for filename in os.listdir(memory_dir_path):
        if filename.endswith('.md'):
            filepath = memory_dir_path / filename
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含摘要格式
                if "## 📋 总结" in content:
                    if save_summary_direct(content, source=f"memory:{filename}"):
                        count += 1
                        print(f"  → 已导入: {filename}")
            except Exception as e:
                print(f"❌ 读取失败 {filename}: {e}")
    
    print(f"\n📊 批量导入完成: {count} 个文件")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='批量保存摘要')
    parser.add_argument('--memory', action='store_true', help='从memory文件批量导入')
    parser.add_argument('--memory-dir', type=str, default=str(resolve_memory_dir()), help='memory 目录路径')
    parser.add_argument('--text', type=str, help='直接保存指定文本')
    parser.add_argument('--source', type=str, default="manual", help='来源标识')
    
    args = parser.parse_args()
    
    if args.memory:
        batch_save_from_memory_files(args.memory_dir)
    elif args.text:
        save_summary_direct(args.text, source=args.source)
    else:
        # 默认：显示帮助
        parser.print_help()
        print("\n💡 示例:")
        print("  python3 batch_save_summary.py --memory")
