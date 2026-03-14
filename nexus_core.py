"""
Deep-Sea Nexus Core Module
封装向量检索和 RAG 召回功能
支持后台自动预热 + 智能触发
"""

import os
import sys
import gzip
import threading
import time
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache

# 添加 Deep-Sea Nexus 路径 (使用 venv-nexus 的 Python)
SKILL_ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(SKILL_ROOT)

# Ensure both import styles work:
# - package import: `from deepsea_nexus import ...`
# - legacy flat import: `from nexus_core import ...`
sys.path.insert(0, SKILLS_ROOT)
sys.path.insert(0, SKILL_ROOT)
sys.path.insert(0, os.path.join(SKILL_ROOT, "src", "retrieval"))
sys.path.insert(0, os.path.join(SKILL_ROOT, "vector_store"))


# Prefer plugin-based core when available (v3+).
def _plugin_active() -> bool:
    importers = (
        lambda: __import__("deepsea_nexus.core.plugin_system", fromlist=["get_plugin_registry", "PluginState"]),
        lambda: __import__("core.plugin_system", fromlist=["get_plugin_registry", "PluginState"]),
    )
    for load in importers:
        try:
            mod = load()
            registry = mod.get_plugin_registry()
            plugin = registry.get("nexus_core")
            return bool(plugin and plugin.state == mod.PluginState.ACTIVE)
        except Exception:
            continue
    return False

def _compat_call(fn_name: str, *args, **kwargs):
    modules = (
        "deepsea_nexus.compat",
        "compat",
    )
    for name in modules:
        try:
            _compat = __import__(name, fromlist=[fn_name])
        except Exception:
            continue
        func = getattr(_compat, fn_name, None)
        if not callable(func):
            continue
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
    return None

# 导入 Deep-Sea Nexus 核心模块
try:
    from semantic_recall import SemanticRecall, create_semantic_recall
    from init_chroma import create_vector_store
    from manager import create_manager
    NEXUS_AVAILABLE = True
except ImportError as e:
    NEXUS_AVAILABLE = False
    IMPORT_ERROR = str(e)

# ===================== 统一触发词检测（已移到 utils/triggers.py） =====================
try:
    # Try relative import (when used as package)
    from .utils.triggers import detect_trigger, extract_keywords, smart_parse
except ImportError:
    # Fall back to absolute import (when run directly)
    from utils.triggers import detect_trigger, extract_keywords, smart_parse

try:
    from .context_contract import export_typed_context, sanitize_typed_context_for_durable_write, typed_context_to_searchable_text
except ImportError:
    from context_contract import export_typed_context, sanitize_typed_context_for_durable_write, typed_context_to_searchable_text


# ===================== 自动预热 =====================
# 模块加载时自动启动后台预热
_nexus_instance = None

def _get_nexus_instance():
    """获取全局实例（懒加载）"""
    global _nexus_instance
    if _nexus_instance is None:
        _nexus_instance = NexusCore()
        # 自动后台预热
        _nexus_instance.start_background_warmup()
    return _nexus_instance


@dataclass
class RecallResult:
    """检索结果"""
    content: str
    source: str
    relevance: float
    metadata: Dict[str, Any] = None


class NexusCore:
    """Deep-Sea Nexus 核心类"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.recall = None
            self.manager = None
            self.store = None
            self._warming = False
            self._ready = False
            self._warmup_thread = None
            self._mem_v5 = None
            NexusCore._initialized = True

    def _get_mem_v5(self):
        if self._mem_v5 is not None:
            return self._mem_v5
        try:
            from memory_v5 import MemoryV5Service
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as fh:
                    config = json.load(fh)
            self._mem_v5 = MemoryV5Service(config)
            return self._mem_v5
        except Exception:
            self._mem_v5 = None
            return None
    
    def _background_warmup(self):
        """后台预热线程"""
        print("[Nexus Hook Debug] Triggering background warmup...") # Added print
        self._warming = True
        try:
            if not NEXUS_AVAILABLE:
                return
            
            # 初始化向量存储
            self.store = create_vector_store()
            
            # 创建管理器
            self.manager = create_manager(
                self.store.embedder,
                self.store.collection
            )
            
            # 创建语义检索
            self.recall = create_semantic_recall(self.manager)
            
            self._ready = True
            print(f"✓ Deep-Sea Nexus 预热完成 ({self.get_stats().get('total_documents', '?')} 文档)")
        except Exception as e:
            print(f"✗ 预热失败: {e}")
            self._warming = False
    
    def start_background_warmup(self):
        """启动后台预热（非阻塞）"""
        if self._ready or self._warming:
            return  # 已经在运行或已就绪
        
        self._warmup_thread = threading.Thread(target=self._background_warmup, daemon=True)
        self._warmup_thread.start()
        print("🔄 Deep-Sea Nexus 后台预热中...")
    
    def wait_for_ready(self, timeout: float = 120.0):
        """等待预热完成"""
        start = time.time()
        while not self._ready and not self.recall:
            if self._warmup_thread and not self._warmup_thread.is_alive() and not self._ready:
                break  # 线程已结束但失败了
            if time.time() - start > timeout:
                raise TimeoutError("预热超时")
            time.sleep(0.5)
    
    def init(self) -> bool:
        """同步初始化（阻塞）"""
        if not NEXUS_AVAILABLE:
            return False
        
        try:
            print("🔄 初始化 Deep-Sea Nexus...")
            
            # 初始化向量存储
            self.store = create_vector_store()
            
            # 创建管理器
            self.manager = create_manager(
                self.store.embedder,
                self.store.collection
            )
            
            # 创建语义检索
            self.recall = create_semantic_recall(self.manager)
            
            self._ready = True
            print(f"✓ Deep-Sea Nexus 已就绪")
            print(f"  📊 已索引: {self.get_stats().get('total_documents', 'N/A')} 条")
            
            return True
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            return False
    
    # ===================== 缓存层 =====================
    
    @lru_cache(maxsize=128)
    def _cached_search(self, query: str, n: int) -> tuple:
        """缓存搜索结果"""
        if self.recall is None:
            return ()
        
        try:
            results = self.recall.search(query, n_results=n)
            return tuple((r.content, r.metadata.get('title', r.doc_id), r.relevance_score) for r in results)
        except Exception:
            return ()
    
    def search_recall(self, query: str, n: int = 5, timeout: float = 120.0) -> List[RecallResult]:
        """语义检索（支持自动预热）"""
        # 启动后台预热（如果还没启动）
        if not self._ready and not self._warming:
            self.start_background_warmup()
        
        # 如果还没准备好，等待
        if not self._ready:
            try:
                self.wait_for_ready(timeout)
            except TimeoutError:
                return []
        
        if self.recall is None:
            return []
        
        try:
            # 使用缓存
            cached = self._cached_search(query, n)
            if cached:
                return [
                    RecallResult(
                        content=content,
                        source=source,
                        relevance=relevance,
                        metadata={}
                    )
                    for content, source, relevance in cached
                ]
            
            results = self.recall.search(query, n_results=n)
            out = [
                RecallResult(
                    content=r.content,
                    source=r.metadata.get('title', r.doc_id),
                    relevance=r.relevance_score,
                    metadata=r.metadata
                )
                for r in results
            ]

            mem_v5 = self._get_mem_v5()
            if mem_v5 is not None:
                try:
                    for hit in mem_v5.recall(query, limit=n):
                        out.append(
                            RecallResult(
                                content=hit.content,
                                source=f"🧠v5 {hit.title}",
                                relevance=hit.relevance,
                                metadata={"origin": hit.origin, **(hit.metadata or {})},
                            )
                        )
                except Exception:
                    pass

            # Deduplicate by content+source
            dedup = {}
            for item in out:
                key = f"{item.source}\n{item.content}".strip()
                if key not in dedup or item.relevance > dedup[key].relevance:
                    dedup[key] = item
            final = sorted(dedup.values(), key=lambda r: r.relevance, reverse=True)
            return final[:n]
        except Exception as e:
            print(f"检索错误: {e}")
            return []
    
    def search(self, query: str, n: int = 5) -> List[RecallResult]:
        """语义搜索"""
        return self.search_recall(query, n)
    
    # ===================== 增量索引 =====================
    
    def add_document(self, content: str, title: str = "", tags: str = "", 
                     note_id: str = None) -> Optional[str]:
        """
        添加单个文档到索引（增量索引）
        
        Args:
            content: 文档内容
            title: 文档标题
            tags: 标签（逗号分隔）
            note_id: 自定义文档ID（可选）
            
        Returns:
            str: 文档ID 或 None
        """
        if self.manager is None:
            if not self.init():
                return None
        
        try:
            metadata = {"title": title or "Untitled"}
            if tags:
                metadata["tags"] = [t.strip() for t in tags.split(",")]
            
            doc_id = self.manager.add_note(
                content=content,
                metadata=metadata,
                note_id=note_id  # 修复参数名
            )

            # Best-effort memory_v5 sync
            try:
                mem_v5 = self._get_mem_v5()
                if mem_v5 is not None:
                    mem_v5.ingest_document(
                        title=title or doc_id or "Untitled",
                        content=content,
                        tags=metadata.get("tags", []),
                        source_id=doc_id or "",
                    )
            except Exception:
                pass
            
            # 清除缓存以确保新文档可检索
            self._cached_search.cache_clear()
            
            return doc_id
        except Exception as e:
            print(f"添加文档失败: {e}")
            return None
    
    def add_documents(self, documents: List[Dict[str, str]], 
                      batch_size: int = 10) -> List[str]:
        """
        批量添加文档到索引
        
        Args:
            documents: 文档列表 [{content, title, tags, doc_id?}]
            batch_size: 批次大小
            
        Returns:
            List[str]: 成功添加的文档ID列表
        """
        results = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            for doc in batch:
                doc_id = self.add_document(
                    content=doc.get("content", ""),
                    title=doc.get("title", ""),
                    tags=doc.get("tags", ""),
                    doc_id=doc.get("doc_id")
                )
                
                if doc_id:
                    results.append(doc_id)
        
        # 清除缓存
        self._cached_search.cache_clear()
        
        return results
    
    def add(self, content: str, title: str, tags: str = "") -> Optional[str]:
        """添加笔记（别名）"""
        return self.add_document(content, title, tags)
    
    # ===================== 压缩归档 =====================
    
    def compress_session(self, session_path: str, compressed_path: str = None) -> str:
        """
        压缩会话文件
        
        Args:
            session_path: 原始会话文件路径
            compressed_path: 压缩文件路径（可选）
            
        Returns:
            str: 压缩文件路径
        """
        if compressed_path is None:
            compressed_path = session_path + ".gz"
        
        try:
            with open(session_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            return compressed_path
        except Exception as e:
            print(f"压缩失败: {e}")
            return ""
    
    def decompress_session(self, compressed_path: str, output_path: str = None) -> str:
        """
        解压会话文件
        
        Args:
            compressed_path: 压缩文件路径
            output_path: 输出路径（可选，默认覆盖原文件）
            
        Returns:
            str: 解压后的文件路径
        """
        if output_path is None:
            output_path = compressed_path.replace('.gz', '')
        
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            return output_path
        except Exception as e:
            print(f"解压失败: {e}")
            return ""
    
    def stats(self) -> Dict[str, Any]:
        """获取统计"""
        if self.manager is None:
            return {"total_documents": 0, "status": "未初始化"}
        
        try:
            stats = self.recall.get_recall_stats()
            return {
                "total_documents": stats.get("total_documents", 0),
                "collection_name": stats.get("collection_name", "N/A"),
                "status": "正常"
            }
        except Exception:
            return {"total_documents": 0, "status": "错误"}
    
    def health(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "available": NEXUS_AVAILABLE,
            "initialized": self.recall is not None,
            "documents": self.stats().get("total_documents", 0),
            "version": "2.0.0"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计（别名）"""
        return self.stats()


# ===================== 全局实例 =====================
_nexus = None


def _get_nexus() -> NexusCore:
    """获取全局实例"""
    global _nexus
    if _nexus is None:
        _nexus = NexusCore()
        # 自动后台预热
        _nexus.start_background_warmup()
    return _nexus


# ===================== 智能搜索 =====================
# AI 可以在每次对话前调用这些函数

def smart_search(user_input: str, n: int = 3) -> Dict[str, Any]:
    """
    智能搜索 - 根据用户输入自动搜索记忆
    
    1. 先检测触发词 ("还记得"、"上次提到" 等)
    2. 触发时执行精确搜索
    3. 非触发时提取关键词执行语义搜索
    
    Args:
        user_input: 用户的自然语言输入
        n: 返回结果数量
    
    Returns:
        Dict: {
            "triggered": bool,  # 是否触发
            "query": str,       # 搜索词
            "results": str,     # 格式化结果
            "context": str      # 可直接注入的上下文
        }
    """
    nexus = _get_nexus()
    
    # 如果还没准备好，返回空
    if not nexus._ready and not nexus.recall:
        return {"triggered": False, "query": "", "results": "", "context": ""}
    
    # 1. 检测触发词
    trigger = detect_trigger(user_input)
    
    if trigger:
        # 触发模式：使用原始查询词精确搜索
        query = trigger["query"]
        results = nexus.search_recall(query, n)
        
        return {
            "triggered": True,
            "query": query,
            "trigger_pattern": trigger["pattern"],
            "results": _format_results(results, query),
            "context": _build_context(results)
        }
    
    # 2. 非触发模式：提取关键词搜索
    keywords = extract_keywords(user_input, 3)
    
    if not keywords:
        return {"triggered": False, "query": "", "results": "", "context": ""}
    
    # 合并关键词搜索
    all_results = []
    seen = set()
    
    for kw in keywords:
        results = nexus.search_recall(kw, n)
        for r in results:
            if r.content[:100] not in seen:
                seen.add(r.content[:100])
                all_results.append(r)
    
    # 按相关性排序
    all_results.sort(key=lambda x: x.relevance, reverse=True)
    all_results = all_results[:n]
    
    return {
        "triggered": False,
        "query": " ".join(keywords),
        "keywords": keywords,
        "results": _format_results(all_results, user_input),
        "context": _build_context(all_results)
    }


def auto_search(user_input: str, n: int = 3) -> str:
    """
    自动搜索 - 返回格式化的记忆上下文
    
    Args:
        user_input: 用户输入
        n: 结果数量
    
    Returns:
        str: 格式化的记忆上下文（无结果返回空字符串）
    """
    result = smart_search(user_input, n)
    return result["context"]


def _format_results(results: List[RecallResult], query: str) -> str:
    """格式化搜索结果"""
    if not results:
        return f"🔍 未找到与 \"{query}\" 相关的记忆"
    
    lines = [f"🔍 找到 {len(results)} 条相关记忆:\n"]
    
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. [{r.relevance:.1%}] **{r.source}**")
        content = r.content[:150] + "..." if len(r.content) > 150 else r.content
        lines.append(f"   {content}")
        lines.append("")
    
    return "\n".join(lines)


def _build_context(results: List[RecallResult]) -> str:
    """构建可注入上下文的字符串"""
    if not results:
        return ""
    
    lines = ["**相关记忆：**\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.source}**")
        content = r.content[:200] + "..." if len(r.content) > 200 else r.content
        lines.append(f"   {content}")
        lines.append("")
    
    return "\n".join(lines)


def nexus_init(blocking: bool = False) -> bool:
    """初始化
    Args:
        blocking: 是否阻塞等待预热完成
    """
    print("[Nexus Hook Debug] Entering nexus_init...")  # Added print
    if _plugin_active():
        return True
    compat_ok = _compat_call("nexus_init")
    if compat_ok:
        return True
    nexus = _get_nexus()
    if blocking:
        return nexus.init()
    else:
        nexus.start_background_warmup()
        return True


def nexus_recall(query: str, n: int = 5) -> List[RecallResult]:
    """语义检索"""
    compat_results = _compat_call("nexus_recall", query, n)
    if compat_results is not None:
        return compat_results
    return _get_nexus().search_recall(query, n)


def nexus_search(query: str, n: int = 5) -> List[RecallResult]:
    """语义搜索"""
    compat_results = _compat_call("nexus_search", query, n)
    if compat_results is not None:
        return compat_results
    return _get_nexus().search(query, n)


def nexus_add(content: str, title: str, tags: str = "") -> Optional[str]:
    """添加笔记（兼容旧接口）。"""
    compat_result = _compat_call("nexus_add", content, title, tags)
    if compat_result is not None:
        return compat_result
    return _get_nexus().add(content, title, tags)


def nexus_write(
    content: str,
    title: str = "",
    *,
    priority: str = "P1",
    kind: str = "fact",
    source: str = "",
    tags: str = "",
) -> Optional[str]:
    """分层写入契约：统一 schema 写入入口（推荐）。

    - priority: P0/P1/P2/GOLD
    - kind: fact/decision/strategy/pitfall/code_pattern/summary/task
    - source: agent/channel/session identifier

    Note: 仍然复用底层 `nexus_add` 存储（tags 里编码结构），避免破坏兼容性。
    """

    pr = str(priority or "P1").strip().upper()
    if pr == "#GOLD":
        pr = "GOLD"
    if pr not in {"P0", "P1", "P2", "GOLD"}:
        pr = "P1"

    kd = str(kind or "fact").strip().lower()
    if kd not in {"fact", "decision", "strategy", "pitfall", "code_pattern", "summary", "task"}:
        kd = "fact"

    src = str(source or "").strip()

    tag_parts = []
    if tags:
        tag_parts.append(str(tags))
    tag_parts.append(f"priority:{pr}")
    tag_parts.append(f"kind:{kd}")
    if src:
        tag_parts.append(f"source:{src}")

    merged_tags = ",".join([p for p in tag_parts if p])
    return nexus_add(content, title or (kd + ":"), merged_tags)


def nexus_add_structured_summary(
    core_output: str,
    tech_points: List[str] = None,
    code_pattern: str = "",
    decision_context: str = "",
    pitfall_record: str = "",
    applicable_scene: str = "",
    search_keywords: List[str] = None,
    project关联: str = "",
    confidence: str = "medium",
    source: str = "",
    evidence_pointers: List[str] = None,
    replay_commands: List[str] = None,
) -> Dict[str, Any]:
    """
    添加结构化摘要（让第二大脑越来越聪明）
    
    Args:
        core_output: 本次核心产出
        tech_points: 技术要点列表
        code_pattern: 代码模式
        decision_context: 决策上下文
        pitfall_record: 避坑记录
        applicable_scene: 适用场景
        search_keywords: 搜索关键词
        project关联: 项目关联
        confidence: 置信度
        source: 来源标识
        
    Returns:
        Dict with stored doc IDs and summary data
    """
    nexus = _get_nexus()
    
    durable_payload = export_typed_context(
        sanitize_typed_context_for_durable_write(
            {
                "summary": core_output,
                "decisions": decision_context,
                "keywords": search_keywords or [],
                "project": project关联,
                "confidence": confidence,
                "tech_points": tech_points or [],
                "code_pattern": code_pattern,
                "pitfall_record": pitfall_record,
                "applicable_scene": applicable_scene,
                "evidence": evidence_pointers or [],
                "replay": replay_commands or [],
            }
        )
    )
    searchable_text = typed_context_to_searchable_text(durable_payload)
    
    # 构建标签
    tags_list = ["type:structured_summary", f"confidence:{confidence}"]
    if search_keywords:
        tags_list.extend(search_keywords)
    if source:
        tags_list.append(f"source:{source}")
    tags = ",".join(tags_list)
    
    results = {
        "stored_count": 0,
        "doc_ids": [],
        "summary_data": durable_payload,
    }
    
    try:
        # 1. 存储主摘要（可搜索）
        doc_id1 = nexus.add(
            content=searchable_text,
            title=f"结构化摘要 - {core_output[:50]}...",
            tags=tags
        )
        if doc_id1:
            results["stored_count"] += 1
            results["doc_ids"].append(doc_id1)
        
        # 2. 存储元数据（JSON 格式，保留结构）
        import json
        metadata_json = json.dumps(results["summary_data"], ensure_ascii=False)
        doc_id2 = nexus.add(
            content=metadata_json,
            title=f"摘要元数据 - {core_output[:50]}...",
            tags=f"type:summary_metadata,source:{source}"
        )
        if doc_id2:
            results["stored_count"] += 1
            results["doc_ids"].append(doc_id2)
        
        # 3. 关键词单独索引（提升检索精度）
        if search_keywords:
            keyword_text = " ".join(search_keywords)
            doc_id3 = nexus.add(
                content=keyword_text,
                title=f"关键词索引 - {core_output[:30]}...",
                tags=f"type:keywords,source:{source}"
            )
            if doc_id3:
                results["stored_count"] += 1
                results["doc_ids"].append(doc_id3)
        
    except Exception as e:
        print(f"存储结构化摘要失败: {e}")
        results["error"] = str(e)
    
    return results


def nexus_add_document(content: str, title: str = "", tags: str = "", 
                       note_id: str = None) -> Optional[str]:
    """添加文档（增量索引）"""
    compat_result = _compat_call("nexus_add_document", content, title, tags, note_id)
    if compat_result is not None:
        return compat_result
    return _get_nexus().add_document(content, title, tags, note_id)


def nexus_add_documents(documents: List[Dict[str, str]], 
                        batch_size: int = 10) -> List[str]:
    """批量添加文档"""
    compat_result = _compat_call("nexus_add_documents", documents, batch_size)
    if compat_result is not None:
        return compat_result
    return _get_nexus().add_documents(documents, batch_size)


def nexus_compress_session(session_path: str, compressed_path: str = None) -> str:
    """压缩会话文件"""
    return _get_nexus().compress_session(session_path, compressed_path)


def nexus_decompress_session(compressed_path: str, output_path: str = None) -> str:
    """解压会话文件"""
    return _get_nexus().decompress_session(compressed_path, output_path)


def nexus_stats() -> Dict[str, Any]:
    """获取统计"""
    compat_result = _compat_call("nexus_stats")
    if compat_result is not None:
        return compat_result
    return _get_nexus().stats()


def nexus_health() -> Dict[str, Any]:
    """健康检查"""
    compat_result = _compat_call("nexus_health")
    if compat_result is not None:
        return compat_result
    return _get_nexus().health()


# ======== 兼容性别名（避免 ImportError） ========
def get_stats() -> Dict[str, Any]:
    """兼容旧接口：get_stats()"""
    return nexus_stats()


def start_background_warmup() -> None:
    """兼容旧接口：start_background_warmup()"""
    _get_nexus().start_background_warmup()


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Deep-Sea Nexus CLI")
    parser.add_argument("command", choices=["init", "recall", "add", "stats", "health", "compress"])
    parser.add_argument("query", nargs="?", help="查询词")
    parser.add_argument("--n", type=int, default=5, help="结果数量")
    parser.add_argument("--title", help="笔记标题")
    parser.add_argument("--tags", help="标签")
    parser.add_argument("--input", help="输入文件路径")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    if args.command == "init":
        nexus_init()
    elif args.command == "recall":
        results = nexus_recall(args.query or "", args.n)
        for r in results:
            print(f"[{r.relevance:.2f}] {r.source}")
    elif args.command == "add":
        if args.title:
            import sys
            content = sys.stdin.read() if not args.query else args.query
            nexus_add(content, args.title, args.tags or "")
    elif args.command == "stats":
        print(nexus_stats())
    elif args.command == "health":
        print(nexus_health())
    elif args.command == "compress":
        if args.input:
            result = nexus_compress_session(args.input, args.output)
            print(f"✓ 压缩完成: {result}")
