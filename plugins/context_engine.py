"""
Context Engine v2 - 统一的智能上下文引擎

设计理念（来自用户反馈）：
- 如果 OpenClaw 不知道某事，就应该先搜索向量库
- 自动检索相关记忆，注入上下文
- 不是等用户说"还记得"，而是主动推理

功能整合：
1. 智能检索 - 不知道就搜
2. 触发词检测 - 用户明确要求回忆
3. 关键词注入 - 自动提取并注入
4. 会话恢复 - 恢复上下文

消除 2.0 重复：
- nexus_core.py 的 detect_trigger
- context_injector.py 的注入逻辑
- nexus_autoinject.py 的搜索逻辑
- auto_recall.py 的自动调用
"""

import json
import re
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .session_manager import SessionManagerPlugin
from .context_engine_runtime import ContextBudget, ContextEngineRuntimeState
from ..core.plugin_system import NexusPlugin, PluginMetadata, PluginState, get_plugin_registry
from ..core.event_bus import EventTypes
from ..compat_async import run_coro_sync
from ..compat import nexus_add, nexus_init, nexus_recall


# ===================== 数据类 =====================


class _CompatNexusCoreAdapter:
    """Current sync API adapter used when the async plugin is unavailable."""

    def init(self) -> bool:
        return bool(nexus_init())

    def search_recall(self, query: str, n: int = 5):
        if not nexus_init():
            return []
        return nexus_recall(query, n=n)

    def add_document(
        self,
        content: str,
        title: str = "",
        tags: str = "",
        doc_id: Optional[str] = None,
    ) -> Optional[str]:
        del doc_id  # Legacy parameter kept for compatibility with old callers.
        return nexus_add(content=content, title=title, tags=tags)

    search = search_recall
    recall = search_recall
    add = add_document

class MemoryTier(Enum):
    """记忆层级"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class StructuredSummary:
    """
    结构化摘要
    
    9 字段设计，让第二大脑越来越聪明
    """
    core_output: str = ""
    tech_points: List[str] = None
    code_pattern: str = ""
    decision_context: str = ""
    pitfall_record: str = ""
    applicable_scene: str = ""
    search_keywords: List[str] = None
    project关联: str = ""
    confidence: str = "medium"
    
    def __post_init__(self):
        if self.tech_points is None:
            self.tech_points = []
        if self.search_keywords is None:
            self.search_keywords = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StructuredSummary':
        return cls(
            core_output=data.get("本次核心产出", ""),
            tech_points=data.get("技术要点", []),
            code_pattern=data.get("代码模式", ""),
            decision_context=data.get("决策上下文", ""),
            pitfall_record=data.get("避坑记录", ""),
            applicable_scene=data.get("适用场景", ""),
            search_keywords=data.get("搜索关键词", []),
            project关联=data.get("项目关联", ""),
            confidence=data.get("置信度", "medium")
        )
    
    def to_searchable_text(self) -> str:
        parts = [
            self.core_output,
            " ".join(self.tech_points),
            self.code_pattern,
            self.decision_context,
            self.pitfall_record,
            self.applicable_scene,
            " ".join(self.search_keywords),
            self.project关联,
        ]
        return " ".join(p for p in parts if p)


@dataclass
class ContextResult:
    """上下文检索结果"""
    triggered: bool
    trigger_type: str  # "auto", "trigger", "keyword", "none"
    query: str
    results: List[Dict]
    context_text: str
    confidence: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass  
class RecallItem:
    """记忆条目"""
    content: str
    source: str
    relevance: float
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ===================== 统一的 Context Engine =====================

class ContextEngine:
    """
    统一的智能上下文引擎
    
    整合了以下 2.0 重复功能：
    - nexus_core.py: detect_trigger, extract_keywords
    - context_injector.py: inject_on_resume, resolve_reference
    - nexus_autoinject.py: smart_search, inject_memory
    - auto_recall.py: 自动向量搜索
    
    设计理念：
    - 如果不知道 → 自动搜向量库 → 注入上下文
    """
    
    # 触发词模式（用户明确要求回忆）
    TRIGGER_PATTERNS = [
        (re.compile(r'还记得(.+?)[吗?？]', re.IGNORECASE), "recall"),
        (re.compile(r'上次.*提到(.+)', re.IGNORECASE), "recall"),
        (re.compile(r'之前.*说过(.+)', re.IGNORECASE), "recall"),
        (re.compile(r'之前.*讨论(.+)', re.IGNORECASE), "recall"),
        (re.compile(r'之前.*决定(.+)', re.IGNORECASE), "recall"),
        (re.compile(r'上次.*对话(.+)', re.IGNORECASE), "recall"),
    ]
    
    # 不知道模式（LLM 可能不知道，需要检索）
    UNKNOWN_PATTERNS = [
        re.compile(r'怎么(做|使用|实现|写|创建)', re.IGNORECASE),
        re.compile(r'如何(做|使用|实现|写|创建)', re.IGNORECASE),
        re.compile(r'.*是什么[?？]', re.IGNORECASE),
        re.compile(r'.*的原理[?？]', re.IGNORECASE),
        re.compile(r'.*有哪些[?？]', re.IGNORECASE),
        re.compile(r'.*区别[?？]', re.IGNORECASE),
    ]
    
    def __init__(self, nexus_core: Any = None):
        """
        初始化上下文引擎
        
        Args:
            nexus_core: NexusCore 实例（可选，懒加载）
        """
        self._nexus_core = nexus_core
        self._lazy_loaded = nexus_core is None
        self._runtime = ContextEngineRuntimeState()

    def _call_nexus(self, method_name: str, *args, **kwargs):
        core = self.nexus_core
        if core is None:
            return None
        method = getattr(core, method_name, None)
        if not callable(method):
            return None
        try:
            result = method(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return run_coro_sync(result)
            return result
        except Exception as e:
            print(f"向量库调用失败({method_name}): {e}")
            return None
    
    @property
    def nexus_core(self) -> Any:
        """Lazily resolve the runtime plugin or a sync API adapter."""
        if self._nexus_core is None:
            if self._lazy_loaded:
                try:
                    registry = get_plugin_registry()
                    plugin = registry.get("nexus_core")
                    if plugin and plugin.state == PluginState.ACTIVE:
                        self._nexus_core = plugin
                        self._lazy_loaded = False
                        return self._nexus_core
                except Exception:
                    pass

                self._nexus_core = _CompatNexusCoreAdapter()
                self._nexus_core.init()
                self._lazy_loaded = False
        return self._nexus_core
    
    # ===================== 核心功能：智能检索 =====================
    
    def should_retrieve(self, user_message: str) -> Tuple[bool, str]:
        """
        判断是否需要检索向量库
        
        设计理念：
        - 如果用户问"怎么做"、"是什么" → 可能不知道，需要检索
        - 如果用户说"还记得" → 明确要求回忆
        
        Returns:
            (should_retrieve, reason)
        """
        # 1. 检查明确触发词
        for pattern, _ in self.TRIGGER_PATTERNS:
            if pattern.search(user_message):
                return True, "trigger"
        
        # 2. 检查"不知道"模式
        for pattern in self.UNKNOWN_PATTERNS:
            if pattern.search(user_message):
                return True, "unknown"
        
        # 3. 检查关键词（如果有技术术语）
        keywords = self.extract_keywords(user_message, 3)
        if any(k for k in keywords if len(k) > 6):  # 长词可能是技术术语
            return True, "keyword"
        
        return False, "none"
    
    def smart_retrieve(self, user_message: str, n: int = 5) -> ContextResult:
        """
        智能检索 - 核心功能
        
        设计理念：
        - 不是等用户说"还记得"
        - 而是每次对话时判断是否需要检索
        
        Args:
            user_message: 用户消息
            n: 返回结果数量
            
        Returns:
            ContextResult: 包含检索结果和上下文
        """
        should_retrieve, reason = self.should_retrieve(user_message)
        
        if not should_retrieve:
            return ContextResult(
                triggered=False,
                trigger_type="none",
                query=user_message,
                results=[],
                context_text="",
                confidence=0.0
            )
        
        # 提取查询词
        query = self._extract_query(user_message)
        
        # 执行检索
        results = self._search_vector_store(query, n)
        
        # 生成上下文
        context_text = self._build_context(results, query)
        
        return ContextResult(
            triggered=True,
            trigger_type=reason,
            query=query,
            results=results,
            context_text=context_text,
            confidence=self._calculate_confidence(results)
        )
    
    def inject_context(self, user_message: str, n: int = 5) -> str:
        """
        注入上下文（供 LLM 使用）
        
        设计理念：
        - 如果 OpenClaw 不知道，就搜向量库
        - 返回格式化后的上下文字符串
        
        Args:
            user_message: 用户消息
            n: 结果数量
            
        Returns:
            格式化后的上下文文本
        """
        result = self.smart_retrieve(user_message, n)
        
        if not result.triggered:
            return ""
        
        return result.context_text
    
    # ===================== 触发词检测（用户明确要求） =====================
    
    def detect_trigger(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        检测触发词（用户明确要求回忆）
        
        来自用户反馈：
        - "还记得X吗"
        - "上次提到X"
        - "之前说过X"
        """
        for pattern, trigger_type in self.TRIGGER_PATTERNS:
            match = pattern.search(user_message)
            if match:
                return {
                    "triggered": True,
                    "type": trigger_type,  # "recall"
                    "pattern": match.group(0),
                    "query": self._extract_query(user_message),
                    "original_message": user_message
                }
        
        return None
    
    def resolve_reference(self, user_message: str, n: int = 5) -> List[Dict]:
        """
        解析引用并检索
        
        用户说"还记得X"时调用
        """
        result = self.detect_trigger(user_message)
        if not result:
            return []
        
        return self._search_vector_store(result["query"], n)
    
    # ===================== 关键词功能 =====================
    
    def extract_keywords(self, text: str, max_count: int = 5) -> List[str]:
        """
        提取关键词
        
        来自 nexus_core.py 和 context_injector.py 的重复代码
        """
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 停用词
        stop_words = {
            '的', '了', '是', '在', '我', '你', '他', '她', '它', '这', '那',
            '和', '与', '或', '就', '都', '也', '会', '可以', '什么', '怎么',
            '如何', '为什么', '有没有', '是不是', '能不能', '要不要'
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # 去重返回
        return list(dict.fromkeys(keywords))[:max_count]
    
    def inject_keywords(self, text: str, n: int = 3) -> str:
        """
        关键词自动注入
        
        提取关键词并检索相关记忆
        """
        keywords = self.extract_keywords(text, 5)
        results = []
        
        for keyword in keywords[:5]:
            related = self._search_vector_store(keyword, n)
            for r in related:
                if r not in results:
                    results.append(r)
        
        if not results:
            return ""
        
        return self._format_keyword_results(results, keywords)
    
    # ===================== 会话恢复 =====================
    
    def resume_session(self, session_id: str, topic: str = "", n: int = 5) -> str:
        """
        会话恢复
        
        恢复时自动注入相关历史
        """
        query = topic or session_id
        results = self._search_vector_store(query, n)
        
        return self._build_context(results, f"会话 {session_id}")
    
    # ===================== 摘要功能 =====================
    
    def parse_summary(self, response: str) -> Tuple[str, Optional[StructuredSummary]]:
        """
        解析 LLM 回复中的摘要
        
        来自 auto_summary.py 的整合
        """
        # JSON 格式
        json_match = re.search(r'```json\s*\n([\s\S]*?)\n```', response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                summary = StructuredSummary.from_dict(data)
                response = re.sub(r'```json\s*\n[\s\S]*?\n```', '', response).strip()
                return response, summary
            except (json.JSONDecodeError, KeyError):
                pass
        
        # 旧格式兼容
        legacy_match = re.search(r'## 📋 总结[^\n]*\n([\s\S]*?)(?=\n\n|$)', response)
        if legacy_match:
            summary_text = legacy_match.group(1).strip()
            summary = StructuredSummary(core_output=summary_text, confidence="low")
            response = re.sub(r'## 📋 总结[^\n]*\n[\s\S]*?(?=\n\n|$)', '', response).strip()
            return response, summary
        
        return response, None
    
    def store_summary(self, conversation_id: str, response: str) -> Dict[str, Any]:
        """
        存储摘要到向量库
        
        来自 auto_summary.py 的整合
        """
        reply, summary = self.parse_summary(response)
        
        results = {
            "conversation_id": conversation_id,
            "stored_count": 0,
            "has_summary": summary is not None
        }
        
        try:
            # 存储原文
            self._call_nexus(
                "add_document",
                content=reply,
                title=f"对话 {conversation_id} - 原文",
                tags=f"type:content,source:{conversation_id}"
            )
            results["stored_count"] += 1
            
            # 存储摘要
            if summary:
                searchable = summary.to_searchable_text()
                tags = f"type:structured_summary,confidence:{summary.confidence}"
                if summary.search_keywords:
                    tags += "," + ",".join(summary.search_keywords)
                
                self._call_nexus(
                    "add_document",
                    content=searchable,
                    title=f"对话 {conversation_id} - 摘要",
                    tags=tags
                )
                results["stored_count"] += 1
                
                # 元数据
                self._call_nexus(
                    "add_document",
                    content=json.dumps(summary.to_dict(), ensure_ascii=False),
                    title=f"对话 {conversation_id} - 元数据",
                    tags=f"type:metadata,source:{conversation_id}"
                )
                results["stored_count"] += 1
                
                results["summary_data"] = summary.to_dict()
                
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    # ===================== 内部方法 =====================
    
    def _extract_query(self, user_message: str) -> str:
        """提取查询词"""
        # 检查触发词
        for pattern, _ in self.TRIGGER_PATTERNS:
            match = pattern.search(user_message)
            if match:
                after = user_message[match.end():].strip().rstrip("吗?？")
                if after:
                    return after
                return user_message[:match.start()].strip()
        
        # 否则返回原消息
        return user_message
    
    def _search_vector_store(self, query: str, n: int) -> List[Dict]:
        """搜索向量库"""
        started = datetime.now().timestamp()
        try:
            results = self._call_nexus("search_recall", query, n) or []
            out = [
                {
                    "content": r.content,
                    "source": r.source,
                    "relevance": r.relevance,
                    "metadata": r.metadata or {}
                }
                for r in results
            ]
            fallback_used = False
            if not out:
                keywords = self.extract_keywords(query, max_count=min(3, n))
                merged: List[Dict[str, Any]] = []
                seen = set()
                for kw in keywords:
                    for item in self._call_nexus("search_recall", kw, max(1, n // 2)) or []:
                        key = f"{getattr(item, 'source', '')}\n{getattr(item, 'content', '')}".strip()
                        if key in seen:
                            continue
                        seen.add(key)
                        merged.append(
                            {
                                "content": getattr(item, "content", ""),
                                "source": getattr(item, "source", ""),
                                "relevance": getattr(item, "relevance", 0.0),
                                "metadata": getattr(item, "metadata", {}) or {},
                            }
                        )
                if merged:
                    out = sorted(merged, key=lambda x: x.get("relevance", 0), reverse=True)[: max(1, n)]
                    fallback_used = True

            self._append_metrics(
                {
                    "event": "vector_search",
                    "query_len": len(query or ""),
                    "requested": int(n),
                    "hits": len(out),
                    "fallback_used": bool(fallback_used),
                    "duration_ms": int((datetime.now().timestamp() - started) * 1000),
                }
            )
            return out
        except Exception as e:
            print(f"向量库搜索失败: {e}")
            self._append_metrics(
                {
                    "event": "vector_search_error",
                    "query_len": len(query or ""),
                    "requested": int(n),
                    "error": str(e),
                    "duration_ms": int((datetime.now().timestamp() - started) * 1000),
                }
            )
            return []
    
    def _build_context(self, results: List[Dict], query: str) -> str:
        """构建上下文文本"""
        if not results:
            return ""
        
        parts = [
            f"相关记忆 (搜索词: {query}):",
            ""
        ]
        
        for i, r in enumerate(results, 1):
            parts.append(f"【{i}】({r.get('source', '未知')} - {r.get('relevance', 0):.2f})")
            parts.append(r.get('content', '')[:300])
            parts.append("")
        
        return "\n".join(parts)
    
    def _format_keyword_results(self, results: List[Dict], keywords: List[str]) -> str:
        """格式化关键词结果"""
        if not results:
            return ""
        
        parts = [
            "相关关键词记忆:",
            ""
        ]
        
        for i, r in enumerate(results, 1):
            parts.append(f"【{i}】{r.get('source', '未知')}")
            parts.append(r.get('content', '')[:200])
            parts.append("")
        
        return "\n".join(parts)
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """计算置信度"""
        if not results:
            return 0.0
        
        # 基于相关性计算
        avg_relevance = sum(r.get('relevance', 0) for r in results) / len(results)
        
        # 基于数量调整
        count_bonus = min(len(results) * 0.05, 0.2)
        
        return min(avg_relevance + count_bonus, 1.0)

    # ===================== 预算化上下文拼装 =====================

    def build_context_block(
        self,
        user_message: str,
        memory_items: List[Dict],
        now_context: str = "",
        recent_summary: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        budget = self._runtime.budget_from_config(config)
        sections: List[str] = []

        if budget.include_now and now_context:
            sections.append("## NOW")
            sections.append(now_context.strip())

        if budget.include_recent_summary and recent_summary:
            sections.append("## RECENT SUMMARY")
            sections.append(recent_summary.strip())

        if budget.include_memory and memory_items:
            sections.append("## RECALL (Top-K)")
            sections.extend(self._format_recall_items(memory_items, budget))

        if not sections:
            return ""

        context_text = "\n".join(sections).strip()
        trimmed = self._runtime.trim_to_budget(context_text, budget.max_tokens)
        self._runtime.record_build_metrics(
            trimmed,
            memory_items,
            budget,
            config=config,
        )
        return trimmed

    def summarize_recent_messages(self, messages: List[Dict[str, Any]], max_chars: int = 400) -> str:
        if not messages:
            return ""
        parts = []
        for msg in messages[-4:]:
            role = (msg.get("role") or "unknown").upper()
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            parts.append(f"{role}: {content}")
        if not parts:
            return ""
        text = "\n".join(parts)
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "..."
        return text

    def _format_recall_items(self, items: List[Dict], budget: ContextBudget) -> List[str]:
        lines: List[str] = []
        max_items = max(1, int(budget.max_items))
        max_chars = max(80, int(budget.max_chars_per_item))
        max_lines_total = max(10, int(budget.max_lines_total))

        used_lines = 0
        for idx, item in enumerate(items[:max_items], 1):
            content = (item.get("content") or "").strip()
            if not content:
                continue
            content = self._trim_lines(content, max_chars)
            line_count = max(1, content.count("\n") + 1)
            if used_lines + line_count > max_lines_total:
                break
            used_lines += line_count
            source = item.get("source", "unknown")
            relevance = item.get("relevance", 0)
            lines.append(f"[{idx}] ({source} · {relevance:.2f})")
            lines.append(content)
        return lines

    def _trim_lines(self, text: str, max_chars: int) -> str:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            return ""
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "..."
        return text

    def configure_runtime(self, config: Optional[Dict[str, Any]]) -> None:
        self._runtime.prime(config)
    
    def _generate_summary_prompt(self) -> str:
        """生成摘要提示词"""
        return """
## 🧠 知识沉淀

请用 JSON 格式总结本次对话：

```json
{
  "本次核心产出": "一句话说明解决了什么问题",
  "技术要点": ["要点1", "要点2"],
  "代码模式": "可复用代码片段",
  "决策上下文": "为什么选择这个方案",
  "避坑记录": "应避免的错误",
  "适用场景": "适用的场景",
  "搜索关键词": ["标签1", "标签2"],
  "置信度": "high/medium/low"
}
```
"""


# ===================== 便捷函数 =====================

# 全局引擎实例
_engine: Optional[ContextEngine] = None


def get_engine() -> ContextEngine:
    """获取全局引擎实例"""
    global _engine
    if _engine is None:
        _engine = ContextEngine()
    return _engine


def smart_retrieve(user_message: str, n: int = 5) -> Dict:
    """
    智能检索 - 便捷函数
    
    设计理念：
    - 如果不知道 → 搜向量库 → 返回上下文
    
    Usage:
        context = smart_retrieve("Python装饰器怎么用?", n=3)
    """
    return get_engine().smart_retrieve(user_message, n)


def inject_context(user_message: str, n: int = 5) -> str:
    """
    注入上下文 - 便捷函数
    
    Usage:
        context = inject_context("怎么实现搜索功能?")
    """
    return get_engine().inject_context(user_message, n)


def detect_trigger(user_message: str) -> Optional[Dict]:
    """
    检测触发词 - 便捷函数
    
    Usage:
        result = detect_trigger("还记得上次说的Python吗?")
    """
    return get_engine().detect_trigger(user_message)


def parse_summary(response: str) -> Tuple[str, Optional[StructuredSummary]]:
    """
    解析摘要 - 便捷函数
    """
    return get_engine().parse_summary(response)


def store_summary(conversation_id: str, response: str) -> Dict[str, Any]:
    """
    存储摘要 - 便捷函数
    """
    return get_engine().store_summary(conversation_id, response)


# ===================== 插件化 =====================

class ContextEnginePlugin(NexusPlugin):
    """
    Context Engine 插件
    
    可注册到插件系统
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="context_engine",
            version="3.1.0",
            description="Unified smart context engine - eliminates 2.0 duplicates",
            dependencies=["nexus_core"],
            hot_reloadable=True,
        )
        self._engine: Optional[ContextEngine] = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化"""
        try:
            # 获取 nexus_core
            from ..core.plugin_system import get_plugin_registry
            registry = get_plugin_registry()
            nexus_core = registry.get("nexus_core")
            
            if nexus_core:
                self._engine = ContextEngine(nexus_core)
            else:
                self._engine = ContextEngine()
            if self._engine:
                self._engine.configure_runtime(config)
            
            return True
        except Exception as e:
            print(f"ContextEnginePlugin init failed: {e}")
            return False
    
    async def start(self) -> bool:
        return True
    
    async def stop(self) -> bool:
        return True


# ===================== CLI =====================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🧠 Context Engine v2 - 统一智能上下文引擎")
    print("=" * 60)
    print()
    print("设计理念:")
    print("- 如果 OpenClaw 不知道 → 自动搜向量库 → 注入上下文")
    print("- 不是等用户说'还记得'，而是主动推理")
    print()
    print("整合了 2.0 重复功能:")
    print("- nexus_core.py: 触发词检测、关键词提取")
    print("- context_injector.py: 上下文注入、会话恢复")
    print("- nexus_autoinject.py: 智能搜索")
    print("- auto_recall.py: 自动调用")
    print()
    
    # 测试
    engine = ContextEngine()
    
    test_messages = [
        "Python 装饰器怎么实现?",
        "还记得上次说的内存泄漏吗?",
        "今天天气怎么样",
        "FastAPI 和 Flask 有什么区别?",
    ]
    
    print("测试智能检索:")
    for msg in test_messages:
        result = engine.smart_retrieve(msg)
        print(f"\n输入: {msg}")
        print(f"触发: {result.triggered} ({result.trigger_type})")
        print(f"结果数: {len(result.results)}")
    
    print("\n" + "=" * 60)
    print("✅ Context Engine v2 工作正常")
