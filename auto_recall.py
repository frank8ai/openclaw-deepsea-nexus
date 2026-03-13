#!/usr/bin/env python3
"""
DeepSea Nexus Auto-Recall Integration
===================================
在 OpenClaw 对话中自动调用本地向量搜索

功能：
- 自动检测触发词 ("还记得"、"上次提到" 等)
- 自动提取关键词搜索
- 支持 Socket 快速模式和直接加载模式

使用方法：
1. 直接运行: python3 auto_recall.py "查询内容"
2. 导入调用: from auto_recall import AutoRecall

环境变量：
- NEXUS_AUTO_INJECT: 设为 "true" 自动注入到上下文
- NEXUS_MAX_RESULTS: 最大结果数（默认 5）
- NEXUS_SOCKET_PATH: Socket 路径（默认 /tmp/nexus_warmup.sock）
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ===================== 触发词配置 =====================
TRIGGER_PATTERNS = [
    (r'还记得(.+?)[吗?？]', "还记得...吗"),
    (r'上次.*提到(.+)', "上次提到"),
    (r'之前.*说过(.+)', "之前说过"),
    (r'之前.*讨论(.+)', "之前讨论"),
    (r'之前.*决定(.+)', "之前决定"),
    (r'前面.*内容(.+)', "前面内容"),
    (r'之前.*项目(.+)', "之前项目"),
    (r'上次.*对话(.+)', "上次对话"),
    (r'之前.*聊天(.+)', "之前聊天"),
]

STOP_WORDS = {'的', '了', '是', '在', '我', '你', '他', '她', '它', '这', '那', '和', '与', '或', '就', '都', '也', '会', '可以', '什么', '怎么', '如何'}

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get(
        "OPENCLAW_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"),
    )
).expanduser()


def detect_trigger(user_input: str) -> Optional[Dict[str, Any]]:
    """检测触发词"""
    for pattern, name in TRIGGER_PATTERNS:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            query = user_input[match.end():].strip().rstrip("吗?？")
            if not query:
                query = user_input[:match.start()].strip()
            return {
                "triggered": True,
                "pattern": name,
                "query": query or user_input,
                "original": user_input
            }
    return None


def extract_keywords(text: str, max_kw: int = 5) -> List[str]:
    """提取关键词"""
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    return list(dict.fromkeys(keywords))[:max_kw]


# ===================== Socket 模式 =====================
SOCKET_PATH = os.environ.get('NEXUS_SOCKET_PATH', '/tmp/nexus_warmup.sock')


def socket_search(query: str, n: int = 5) -> Optional[Dict]:
    """通过 Socket 搜索（快速模式）"""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        request = json.dumps({"query": query, "n": n})
        client.send(request.encode())
        response = client.recv(131072).decode()
        client.close()
        return json.loads(response)
    except Exception:
        return None


def _compat_search(query: str, n: int = 5) -> Optional[Dict]:
    """通过 compat API 搜索（无 socket 时的回退路径）"""
    try:
        from .compat import nexus_init, nexus_recall
    except Exception:
        try:
            from compat import nexus_init, nexus_recall
        except Exception:
            return None

    if not nexus_init():
        return None

    results = nexus_recall(query, n)
    if results is None:
        return None

    out = []
    for r in results:
        out.append({
            "content": getattr(r, "content", ""),
            "source": getattr(r, "source", ""),
            "relevance": getattr(r, "relevance", 0.0),
            "metadata": getattr(r, "metadata", {}) or {},
        })
    return {"query": query, "results": out}


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
    for candidate in [
        nexus_root,
        nexus_root / "vector_store",
        nexus_root / "src" / "retrieval",
    ]:
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


# ===================== 直接加载模式 =====================
NEXUS_ROOT = resolve_nexus_root()
NEXUS_PATH = str(NEXUS_ROOT)
VECTOR_STORE_PATH = str(NEXUS_ROOT / "vector_store")
RETRIEVAL_PATH = str(NEXUS_ROOT / "src" / "retrieval")
configure_import_paths(NEXUS_ROOT)


class AutoRecall:
    """自动回忆集成"""
    
    def __init__(
        self,
        use_socket: bool = True,
        nexus_root: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.use_socket = use_socket
        self.recall = None
        self.nexus_root = (
            Path(nexus_root).expanduser().resolve()
            if nexus_root
            else resolve_nexus_root()
        )
        configure_import_paths(self.nexus_root)
        self.vector_store_path = self.nexus_root / "vector_store"
        self.retrieval_path = self.nexus_root / "src" / "retrieval"
        self.config_path = str(
            resolve_config_path(config_path, nexus_root=self.nexus_root)
        )
    
    def init(self) -> bool:
        """初始化向量存储（直接加载模式）"""
        if self.recall is not None:
            return True
        
        try:
            import importlib.util
            
            spec = importlib.util.spec_from_file_location(
                "init_chroma",
                self.vector_store_path / "init_chroma.py",
            )
            init_chroma = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(init_chroma)
            
            spec2 = importlib.util.spec_from_file_location(
                "manager",
                self.vector_store_path / "manager.py",
            )
            manager_mod = importlib.util.module_from_spec(spec2)
            spec2.loader.exec_module(manager_mod)
            
            spec3 = importlib.util.spec_from_file_location(
                "semantic_recall",
                self.retrieval_path / "semantic_recall.py",
            )
            sr_mod = importlib.util.module_from_spec(spec3)
            spec3.loader.exec_module(sr_mod)
            
            store = init_chroma.create_vector_store(self.config_path)
            manager = manager_mod.create_manager(store.embedder, store.collection, self.config_path)
            self.recall = sr_mod.create_semantic_recall(manager, self.config_path)
            stats_getter = getattr(store, "get_collection_stats", None)
            if not callable(stats_getter):
                stats_getter = getattr(store, "get_stats", None)
            stats = stats_getter() if callable(stats_getter) else {}
            
            print(
                f"✓ AutoRecall 初始化成功 ({stats.get('total_documents', '?')} docs)",
                file=sys.stderr,
            )
            return True
            
        except Exception as e:
            print(f"✗ 初始化失败: {e}", file=sys.stderr)
            return False
    
    # ===================== 智能搜索 =====================
    
    def smart_search(self, user_input: str, n: int = 3) -> Dict[str, Any]:
        """
        智能搜索 - 自动触发 + 关键词
        
        Returns:
            {
                "triggered": bool,
                "query": str,
                "trigger_pattern": str,
                "keywords": List[str],
                "results": List[Dict],
                "context": str  # 可注入的上下文
            }
        """
        # 1. 尝试 Socket 模式
        if self.use_socket:
            result = self._smart_search_socket(user_input, n)
            if result:
                return result
        
        # 2. 回退到直接加载模式
        return self._smart_search_direct(user_input, n)
    
    def _smart_search_socket(self, user_input: str, n: int) -> Optional[Dict[str, Any]]:
        """Socket 模式智能搜索"""
        trigger = detect_trigger(user_input)
        
        if trigger:
            result = socket_search(trigger["query"], n)
            if result is None:
                result = _compat_search(trigger["query"], n)
            return {
                "triggered": True,
                "query": trigger["query"],
                "trigger_pattern": trigger["pattern"],
                "keywords": [],
                "results": result.get("results", []) if result else [],
                "context": self._build_context(result.get("results", []) if result else [])
            }
        
        keywords = extract_keywords(user_input, 3)
        if not keywords:
            return {"triggered": False, "query": "", "context": ""}
        
        all_results = []
        seen = set()
        
        for kw in keywords:
            result = socket_search(kw, n)
            if result is None:
                result = _compat_search(kw, n)
            if result and "results" in result:
                for r in result["results"]:
                    key = r["content"][:100]
                    if key not in seen:
                        seen.add(key)
                        all_results.append(r)
        
        all_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        all_results = all_results[:n]
        
        return {
            "triggered": False,
            "query": " ".join(keywords),
            "keywords": keywords,
            "results": all_results,
            "context": self._build_context(all_results)
        }
    
    def _smart_search_direct(self, user_input: str, n: int) -> Dict[str, Any]:
        """直接加载模式智能搜索"""
        if not self.init():
            return {"triggered": False, "query": "", "context": ""}
        
        trigger = detect_trigger(user_input)
        
        if trigger:
            results = self.recall.search(trigger["query"], n_results=n)
            formatted = self._format_results(results)
            return {
                "triggered": True,
                "query": trigger["query"],
                "trigger_pattern": trigger["pattern"],
                "keywords": [],
                "results": formatted,
                "context": self._build_context(formatted)
            }
        
        keywords = extract_keywords(user_input, 3)
        if not keywords:
            return {"triggered": False, "query": "", "context": ""}
        
        all_results = []
        seen = set()
        
        for kw in keywords:
            results = self.recall.search(kw, n_results=n)
            for r in results:
                key = r.content[:100]
                if key not in seen:
                    seen.add(key)
                    all_results.append(r)
        
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        all_results = all_results[:n]
        formatted = self._format_results(all_results)
        
        return {
            "triggered": False,
            "query": " ".join(keywords),
            "keywords": keywords,
            "results": formatted,
            "context": self._build_context(formatted)
        }
    
    # ===================== 格式化 =====================
    
    def _format_results(self, results) -> List[Dict]:
        """格式化搜索结果"""
        formatted = []
        for r in results:
            if hasattr(r, '__dict__'):  # 对象
                formatted.append({
                    "content": r.content,
                    "source": r.metadata.get('title', r.doc_id) if hasattr(r, 'metadata') else 'unknown',
                    "relevance": r.relevance_score if hasattr(r, 'relevance_score') else 0
                })
            else:  # 字典
                formatted.append(r)
        return formatted
    
    def _build_context(self, results: List[Dict]) -> str:
        """构建可注入的上下文"""
        if not results:
            return ""
        
        lines = ["**相关记忆：**\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['source']}**")
            content = r['content'][:200] + "..." if len(r['content']) > 200 else r['content']
            lines.append(f"   {content}")
            lines.append("")
        return "\n".join(lines)
    
    def recall_from_query(self, query: str, max_results: int = 5) -> list:
        """从查询中回忆相关内容（兼容旧接口）"""
        if self.use_socket:
            result = socket_search(query, max_results)
            if result is None:
                result = _compat_search(query, max_results)
            return result.get("results", []) if result else []
        else:
            if not self.init():
                return []
            results = self.recall.search(query, n_results=max_results)
            return self._format_results(results)
    
    def format_for_context(self, results: list, query: str) -> str:
        """格式化为上下文注入格式（兼容旧接口）"""
        if not results:
            return ""
        
        blocks = []
        blocks.append(f"<!-- 从向量库检索: \"{query}\" -->")
        blocks.append(f"<!-- 找到 {len(results)} 条相关记忆 -->")
        blocks.append("")
        
        for i, r in enumerate(results, 1):
            blocks.append(f"[来源: {r['source']} | 相关度: {r['relevance']:.1%}]")
            blocks.append(r['content'][:500] + ("..." if len(r['content']) > 500 else ""))
            blocks.append("")
        
        return "\n".join(blocks)


# ===================== CLI =====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='DeepSea Nexus Auto-Recall',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('query', nargs='?', help='搜索查询')
    parser.add_argument('--max-results', type=int, default=5, help='最大结果数')
    parser.add_argument('--format', choices=['json', 'context', 'brief', 'smart'], 
                       default='context', help='输出格式')
    parser.add_argument('--socket', action='store_true', help='强制使用 Socket 模式')
    parser.add_argument('--direct', action='store_true', help='强制使用直接加载模式')
    parser.add_argument('--quiet', action='store_true', help='安静模式')
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: python3 auto_recall.py \"查询内容\" [--max-results 5] [--format json|context|brief|smart]")
        print("\n触发词示例:")
        print('  python3 auto_recall.py "还记得上次说的Python吗?"')
        print('  python3 auto_recall.py "之前提到过的配置"')
        print('  python3 auto_recall.py "nightly build" --format smart')
        sys.exit(1)
    
    # 选择模式
    use_socket = not args.direct
    if args.socket:
        use_socket = True
    elif args.direct:
        use_socket = False
    else:
        # 默认优先 Socket
        use_socket = os.path.exists(SOCKET_PATH)
    
    auto_recall = AutoRecall(use_socket=use_socket)
    
    if args.format == 'smart':
        # 智能搜索
        result = auto_recall.smart_search(args.query, args.max_results)
        
        if result["triggered"]:
            print(f"✅ 触发: '{result['trigger_pattern']}' → {result['query']}")
        else:
            print(f"ℹ️ 关键词: {result.get('keywords', [])}")
        
        if result["context"]:
            print(f"\n{result['context']}")
        else:
            print("(无相关记忆)")
    
    elif args.format == 'json':
        result = auto_recall.smart_search(args.query, args.max_results)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        # 兼容旧接口
        results = auto_recall.recall_from_query(args.query, args.max_results)
        
        if args.format == 'context':
            context = auto_recall.format_for_context(results, args.query)
            if context:
                print(context)
            elif not args.quiet:
                print(f"<!-- 无相关记忆 -->", file=sys.stderr)
        elif args.format == 'brief':
            for r in results:
                print(f"[{r['relevance']:.2f}] {r['source']}: {r['content'][:80]}...")


if __name__ == '__main__':
    main()
