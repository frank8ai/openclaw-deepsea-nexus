"""
Smart Context - 第二大脑核心子功能

功能：
1. 对话摘要存储 - 根据规则保留原文+摘要（已压缩）
2. 记忆库注入 - 提取记忆库关键信息注入上下文
3. 上下文压缩规则 - 根据对话轮数压缩
4. 压缩前抢救 - NOW.md 抢救机制

设计理念：
- 和第二大脑一起启动
- 每次对话后 → 存储摘要
- 每次对话前 → 注入上下文
- 压缩前 → 抢救关键信息

集成位置：
- plugins/smart_context.py
- 和 nexus_core、session_manager 一起启动
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from . import smart_context_decision
from . import smart_context_adaptive
from . import smart_context_conversation
from . import smart_context_graph
from . import smart_context_graph_inject
from . import smart_context_inject
from . import smart_context_now
from . import smart_context_prompt
from . import smart_context_recall
from . import smart_context_round
from . import smart_context_storage
from . import smart_context_summary
from . import smart_context_text
from .session_manager import SessionManagerPlugin
from .smart_context_runtime import SmartContextRuntimeState
from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..core.event_bus import EventTypes
from ..compat_async import run_coro_sync
from ..brain.graph_api import configure_graph, graph_add_edge, graph_related_with_evidence


# ===================== 配置 =====================

@dataclass
class ContextCompressionConfig:
    """
    上下文压缩配置
    
    规则配置：
    - 什么时候存储摘要
    - 什么时候注入上下文
    - 根据对话轮数压缩
    - 压缩前抢救关键信息
    """
    # 对话轮数规则 - 编程任务优化配置
    full_rounds: int = 8          # 完整保留最近 8 轮 (编程需要更多上下文)
    summary_rounds: int = 20      # 超过 20 轮只保留摘要 (保留关键决策)
    compress_after_rounds: int = 35  # 超过 35 轮压缩 (长任务归档)
    # token 规则（估算值，非模型真实 token）
    full_tokens_max: int = 8000
    summary_tokens_max: int = 3000
    compressed_tokens_max: int = 2000
    trigger_soft_ratio: float = 0.6
    trigger_hard_ratio: float = 0.85
    
    # 摘要存储规则
    store_summary_enabled: bool = True
    summary_min_length: int = 50
    compress_on_store: bool = True
    summary_on_each_turn: bool = True
    summary_template_enabled: bool = True
    summary_template_fields: Tuple[str, ...] = (
        "summary",
        "decisions",
        "next_actions",
        "questions",
        "entities",
        "keywords",
    )
    topic_switch_enabled: bool = True
    topic_switch_min_overlap_ratio: float = 0.2
    topic_switch_keywords_max: int = 8
    
    # 上下文注入规则
    inject_enabled: bool = True
    inject_threshold: float = 0.6
    inject_max_items: int = 3
    inject_topk_only: bool = True
    inject_max_chars_per_item: int = 360
    inject_max_lines_per_item: int = 8
    inject_max_lines_total: int = 40
    inject_debug: bool = False
    inject_debug_max_chars: int = 200
    inject_mode: str = "balanced"  # conservative | balanced | aggressive
    association_enabled: bool = True
    context_starved_min_chars: int = 16
    decision_block_enabled: bool = True
    decision_block_max: int = 3
    topic_block_enabled: bool = True
    topic_block_max: int = 3
    topic_block_min_keywords: int = 2
    graph_inject_enabled: bool = True
    graph_max_items: int = 3
    graph_evidence_max_chars: int = 120
    adaptive_enabled: bool = True
    adaptive_min_threshold: float = 0.35
    adaptive_max_threshold: float = 0.75
    adaptive_step: float = 0.03
    adaptive_window: int = 40

    # 注入统计
    inject_stats_enabled: bool = True
    inject_stats_window: int = 50
    inject_ratio_alert_enabled: bool = True
    inject_ratio_alert_threshold: float = 0.15
    inject_ratio_alert_streak: int = 2
    inject_ratio_auto_tune: bool = True
    inject_ratio_auto_tune_step: float = 0.05
    inject_ratio_auto_tune_max_items: int = 6
    inject_persist_interval_sec: int = 60

    # 注入信号增强与动态门控
    inject_signal_boost_decision: float = 0.12
    inject_signal_boost_topic: float = 0.08
    inject_signal_boost_summary: float = 0.05
    inject_dynamic_enabled: bool = True
    inject_dynamic_max_items: int = 5
    inject_dynamic_low_signal_penalty: int = 1
    inject_dynamic_high_signal_bonus: int = 1
    
    # 抢救规则 (NOW.md)
    rescue_enabled: bool = True       # 启用压缩前抢救
    rescue_gold: bool = True        # 抢救 #GOLD 标记
    rescue_decisions: bool = True     # 抢救关键决策
    rescue_next_actions: bool = True # 抢救下一步行动


@dataclass
class ConversationContext:
    """
    对话上下文
    
    记录每轮对话的上下文状态
    """
    round_num: int
    status: str  # "full", "summary", "compressed"
    content: str
    created_at: str
    summary: str = ""
    compressed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ===================== Smart Context 核心 =====================

class SmartContextPlugin(NexusPlugin):
    def _content_signature(self, content: str) -> str:
        """Stable signature for de-dup.

        Aim: keep semantically same content stable even if it contains timestamps,
        ids, or minor formatting differences.
        """
        try:
            s = (content or "").strip().lower()
            if not s:
                return ""
            # Strip fenced code blocks markers while keeping the code body.
            s = re.sub(r"```[a-z0-9_-]*", "```", s)
            # Normalize numbers that are often volatile (timestamps, ids).
            s = re.sub(r"\b\d{4}-\d{2}-\d{2}[ t]\d{2}:\d{2}(:\d{2})?\b", "<ts>", s)
            s = re.sub(r"\b\d{10,}\b", "<num>", s)
            s = re.sub(r"\b[0-9a-f]{8,}\b", "<hex>", s)
            # Collapse whitespace.
            s = re.sub(r"\s+", " ", s)
            # Focus on a prefix to keep it cheap.
            return s[:400]
        except Exception:
            return (content or "")[:120].strip().lower()

    """
    Smart Context 插件
    
    第二大脑核心子功能：
    1. 存储对话摘要（根据规则）
    2. 注入记忆库上下文
    3. 根据对话轮数压缩上下文
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="smart_context",
            version="3.1.0",
            description="Smart context - summary storage, memory injection, context compression",
            dependencies=["nexus_core", "session_manager"],
            hot_reloadable=True,
        )
        self.config = ContextCompressionConfig()
        self._nexus_core = None
        self._session_manager = None
        self._context_history: List[ConversationContext] = []
        self._current_round = 0
        self._graph_enabled = False
        self._inject_history: List[Dict[str, Any]] = []
        self._inject_stats: List[Dict[str, Any]] = []
        self._runtime = SmartContextRuntimeState()
        self._last_keywords: List[str] = []
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化"""
        try:
            from ..core.plugin_system import get_plugin_registry
            registry = get_plugin_registry()
            self._nexus_core = registry.get("nexus_core")
            self._session_manager = registry.get("session_manager")
            
            if not self._nexus_core:
                print("⚠️ SmartContext: nexus_core 未就绪")
            
            # 加载配置
            if config.get("smart_context"):
                smart_cfg = config["smart_context"]
                self.config = ContextCompressionConfig(
                    full_rounds=smart_cfg.get("full_rounds", 8),
                    summary_rounds=smart_cfg.get("summary_rounds", 20),
                    compress_after_rounds=smart_cfg.get("compress_after_rounds", 35),
                    full_tokens_max=smart_cfg.get("full_tokens_max", 8000),
                    summary_tokens_max=smart_cfg.get("summary_tokens_max", 3000),
                    compressed_tokens_max=smart_cfg.get("compressed_tokens_max", 2000),
                    trigger_soft_ratio=smart_cfg.get("trigger_soft_ratio", 0.6),
                    trigger_hard_ratio=smart_cfg.get("trigger_hard_ratio", 0.85),
                    store_summary_enabled=smart_cfg.get("store_summary_enabled", True),
                    summary_on_each_turn=smart_cfg.get("summary_on_each_turn", True),
                    summary_template_enabled=smart_cfg.get("summary_template_enabled", True),
                    summary_template_fields=tuple(
                        smart_cfg.get(
                            "summary_template_fields",
                            [
                                "summary",
                                "decisions",
                                "next_actions",
                                "questions",
                                "entities",
                                "keywords",
                            ],
                        )
                    ),
                    topic_switch_enabled=smart_cfg.get("topic_switch_enabled", True),
                    topic_switch_min_overlap_ratio=smart_cfg.get("topic_switch_min_overlap_ratio", 0.2),
                    topic_switch_keywords_max=smart_cfg.get("topic_switch_keywords_max", 8),
                    inject_enabled=smart_cfg.get("inject_enabled", True),
                    inject_threshold=smart_cfg.get("inject_threshold", 0.6),
                    inject_max_items=smart_cfg.get("inject_max_items", 3),
                    inject_topk_only=smart_cfg.get("inject_topk_only", True),
                    inject_max_chars_per_item=smart_cfg.get("inject_max_chars_per_item", 360),
                    inject_max_lines_per_item=smart_cfg.get("inject_max_lines_per_item", 8),
                    inject_max_lines_total=smart_cfg.get("inject_max_lines_total", 40),
                    inject_debug=smart_cfg.get("inject_debug", False),
                    inject_debug_max_chars=smart_cfg.get("inject_debug_max_chars", 200),
                    inject_mode=smart_cfg.get("inject_mode", "balanced"),
                    association_enabled=smart_cfg.get("association_enabled", True),
                    context_starved_min_chars=smart_cfg.get("context_starved_min_chars", 16),
                    decision_block_enabled=smart_cfg.get("decision_block_enabled", True),
                    decision_block_max=smart_cfg.get("decision_block_max", 3),
                    topic_block_enabled=smart_cfg.get("topic_block_enabled", True),
                    topic_block_max=smart_cfg.get("topic_block_max", 3),
                    topic_block_min_keywords=smart_cfg.get("topic_block_min_keywords", 2),
                    graph_inject_enabled=smart_cfg.get("graph_inject_enabled", True),
                    graph_max_items=smart_cfg.get("graph_max_items", 3),
                    graph_evidence_max_chars=smart_cfg.get("graph_evidence_max_chars", 120),
                    adaptive_enabled=smart_cfg.get("adaptive_enabled", True),
                    adaptive_min_threshold=smart_cfg.get("adaptive_min_threshold", 0.35),
                    adaptive_max_threshold=smart_cfg.get("adaptive_max_threshold", 0.75),
                    adaptive_step=smart_cfg.get("adaptive_step", 0.03),
                    adaptive_window=smart_cfg.get("adaptive_window", 40),
                    inject_stats_enabled=smart_cfg.get("inject_stats_enabled", True),
                    inject_stats_window=smart_cfg.get("inject_stats_window", 50),
                    inject_ratio_alert_enabled=smart_cfg.get("inject_ratio_alert_enabled", True),
                    inject_ratio_alert_threshold=smart_cfg.get("inject_ratio_alert_threshold", 0.15),
                    inject_ratio_alert_streak=smart_cfg.get("inject_ratio_alert_streak", 2),
                    inject_ratio_auto_tune=smart_cfg.get("inject_ratio_auto_tune", True),
                    inject_ratio_auto_tune_step=smart_cfg.get("inject_ratio_auto_tune_step", 0.05),
                    inject_ratio_auto_tune_max_items=smart_cfg.get("inject_ratio_auto_tune_max_items", 6),
                    inject_persist_interval_sec=smart_cfg.get("inject_persist_interval_sec", 60),
                    inject_signal_boost_decision=smart_cfg.get("inject_signal_boost_decision", 0.12),
                    inject_signal_boost_topic=smart_cfg.get("inject_signal_boost_topic", 0.08),
                    inject_signal_boost_summary=smart_cfg.get("inject_signal_boost_summary", 0.05),
                    inject_dynamic_enabled=smart_cfg.get("inject_dynamic_enabled", True),
                    inject_dynamic_max_items=smart_cfg.get("inject_dynamic_max_items", 5),
                    inject_dynamic_low_signal_penalty=smart_cfg.get("inject_dynamic_low_signal_penalty", 1),
                    inject_dynamic_high_signal_bonus=smart_cfg.get("inject_dynamic_high_signal_bonus", 1),
                    rescue_enabled=smart_cfg.get("rescue_enabled", True),
                    rescue_gold=smart_cfg.get("rescue_gold", True),
                    rescue_decisions=smart_cfg.get("rescue_decisions", True),
                    rescue_next_actions=smart_cfg.get("rescue_next_actions", True),
                )
            graph_cfg = config.get("graph", {}) if isinstance(config.get("graph", {}), dict) else {}
            self._graph_enabled = bool(graph_cfg.get("enabled", False))
            if self._graph_enabled:
                configure_graph(
                    enabled=True,
                    base_path=config.get("paths", {}).get("base", "."),
                    db_path=graph_cfg.get("db_path"),
                )
            self._runtime.prime(config)
            self._append_metrics(
                {
                    "event": "smart_context_init",
                    "inject_enabled": bool(self.config.inject_enabled),
                    "adaptive_enabled": bool(self.config.adaptive_enabled),
                    "graph_enabled": bool(self._graph_enabled),
                }
            )
            
            print(f"✅ SmartContext 初始化完成 (规则: {self.config.full_rounds}轮完整/{self.config.summary_rounds}轮摘要/{self.config.compress_after_rounds}轮压缩)")
            return True
            
        except Exception as e:
            print(f"❌ SmartContext 初始化失败: {e}")
            return False
    
    async def start(self) -> bool:
        """启动"""
        print("✅ SmartContext 启动")
        return True
    
    async def stop(self) -> bool:
        """停止"""
        print("✅ SmartContext 停止")
        return True
    
    # ===================== 对话轮数管理 =====================
    
    def get_current_round(self, conversation_id: str) -> int:
        """
        获取当前对话轮数
        
        从会话管理器获取当前轮数
        """
        if self._session_manager and conversation_id:
            try:
                session = self._session_manager.get_session(conversation_id)
                if session and getattr(session, "chunk_count", 0) > 0:
                    return int(session.chunk_count)
            except Exception:
                pass
        return self._current_round
    
    def should_compress(self, round_num: int) -> Tuple[bool, str]:
        """
        判断是否应该压缩
        
        Returns:
            (should_compress, reason)
        """
        if round_num <= self.config.full_rounds:
            return False, "full"  # 最近 N 轮完整保留

        if round_num <= self.config.summary_rounds:
            return True, "summary"  # 中间的轮数只保留摘要

        return True, "compress"  # 更早的轮数压缩

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text) / 3))

    def _context_token_usage(self) -> Dict[str, int]:
        usage = {"full": 0, "summary": 0, "compressed": 0}
        for ctx in self._context_history:
            content = ctx.content or ""
            if ctx.status == "summary":
                content = ctx.summary or content
            elif ctx.status == "compressed":
                content = ctx.summary or content
            usage[ctx.status] = usage.get(ctx.status, 0) + self._estimate_tokens(content)
        return usage

    def _decide_status_with_tokens(self, round_num: int, token_estimate: int) -> Tuple[str, str]:
        should_compress, reason = self.should_compress(round_num)
        status = "summary" if should_compress and reason == "summary" else "compress" if should_compress else "full"

        usage = self._context_token_usage()
        budget_total = self.config.full_tokens_max + self.config.summary_tokens_max + self.config.compressed_tokens_max
        current_total = sum(usage.values()) + token_estimate

        if budget_total > 0:
            if current_total >= budget_total * float(self.config.trigger_hard_ratio):
                status = "compress"
                reason = "token_hard"
            elif current_total >= budget_total * float(self.config.trigger_soft_ratio) and round_num > self.config.full_rounds:
                status = "summary"
                reason = "token_soft"

        if status == "full" and usage["full"] + token_estimate > int(self.config.full_tokens_max):
            status = "summary"
            reason = "full_tokens_max"

        if status == "summary" and usage["summary"] + token_estimate > int(self.config.summary_tokens_max):
            status = "compress"
            reason = "summary_tokens_max"

        return status, reason
    
    # ===================== 上下文处理 =====================
    
    def process_round(self, 
                     conversation_id: str,
                     round_num: int,
                     user_message: str,
                     ai_response: str) -> Dict[str, Any]:
        """
        处理单轮对话
        
        根据轮数决定处理方式：
        - 0-8 轮：完整保留
        - 9-30 轮：只保留摘要
        - 30+ 轮：压缩/归档
        
        Args:
            conversation_id: 对话 ID
            round_num: 当前轮数
            user_message: 用户消息
            ai_response: AI 回复
            
        Returns:
            处理结果
        """
        combined_text = f"{user_message}\n{ai_response}"
        token_estimate = self._estimate_tokens(combined_text)
        status, reason = self._decide_status_with_tokens(round_num, token_estimate)
        usage_snapshot = self._context_token_usage()
        artifacts = smart_context_round.build_round_process_artifacts(
            conversation_id,
            round_num,
            status,
            combined_text=combined_text,
            ai_response=ai_response,
            extract_summary_fn=self._extract_summary,
            rescue_before_compress_fn=self.rescue_before_compress,
        )
        result = artifacts.result
        for event in artifacts.metric_events:
            self._append_metrics(event)
        if artifacts.rescue_debug_line:
            print(artifacts.rescue_debug_line)
        self._append_metrics(
            smart_context_round.build_context_status_metric(
                status,
                reason,
                token_estimate,
                usage_snapshot,
            )
        )
        
        blocks: List[str] = []
        if self.config.decision_block_enabled:
            blocks = self._extract_decision_blocks(combined_text)

        if self.config.summary_on_each_turn:
            turn_summary = self._build_turn_summary(
                user_message,
                ai_response,
                blocks if self.config.decision_block_enabled else [],
            )
            if turn_summary:
                if self._nexus_core:
                    self._call_nexus("add_document", **smart_context_round.build_round_summary_document(
                        conversation_id,
                        round_num,
                        turn_summary,
                    ))
                    result["stored"] = True
                self._append_metrics({"event": "turn_summary", "len": len(turn_summary)})

        if self._detect_topic_switch(user_message):
            topic_summary = self._build_turn_summary(
                user_message,
                ai_response,
                blocks if self.config.decision_block_enabled else [],
            )
            if topic_summary:
                if self._nexus_core:
                    self._call_nexus("add_document", **smart_context_round.build_round_summary_document(
                        conversation_id,
                        round_num,
                        topic_summary,
                        topic_boundary=True,
                    ))
                    result["stored"] = True
                self._append_metrics({"event": "topic_switch", "round": round_num})

        # 存储
        if self._nexus_core:
            self._store_context(conversation_id, round_num, result)
            if blocks:
                self._store_decision_blocks(conversation_id, round_num, blocks)
            if self.config.topic_block_enabled:
                topics = self._extract_topics(combined_text)
                if topics:
                    self._store_topic_blocks(conversation_id, round_num, topics)
            result["stored"] = True
        
        # 更新历史
        self._current_round = round_num
        self._context_history.append(
            ConversationContext(
                **smart_context_round.build_context_history_entry(
                    round_num,
                    result,
                    created_at=datetime.now().isoformat(),
                )
            )
        )
        
        return result

    def _call_nexus(self, method_name: str, *args, **kwargs):
        if not self._nexus_core:
            return None
        method = getattr(self._nexus_core, method_name, None)
        if not callable(method):
            return None
        try:
            result = method(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return run_coro_sync(result)
            return result
        except Exception as e:
            print(f"⚠️ SmartContext: 调用 nexus_core.{method_name} 失败: {e}")
            return None

    def _resolve_metrics_path(self, config: Dict[str, Any]) -> str:
        return self._runtime.resolve_metrics_path(config) or ""

    def _resolve_config_path(self) -> str:
        return self._runtime.resolve_config_path()

    def _append_metrics(self, payload: Dict[str, Any]) -> None:
        self._runtime.append_metrics(payload)

    def _persist_smart_context_config(self, updates: Dict[str, Any]) -> None:
        self._runtime.persist_config(updates)

    def _flush_pending_config_updates(self) -> None:
        self._runtime.flush_pending_config_updates(self.config)
    
    def _extract_summary(self, response: str) -> str:
        result = smart_context_text.extract_summary(
            response,
            min_summary_length=self.config.summary_min_length,
            fallback_max_chars=200,
        )
        self._record_summary_metrics(result)
        return result.summary

    def _record_summary_metrics(self, result: smart_context_text.SummaryResult) -> None:
        event_by_status = {
            "ok": "summary_ok",
            "short": "summary_short",
            "fallback": "summary_fallback",
        }
        event = event_by_status.get(result.status)
        if not event:
            return
        self._append_metrics({"event": event, "len": len(result.summary)})

    def _store_context(self, conversation_id: str, round_num: int, context: Dict):
        """
        存储上下文到向量库
        """
        try:
            self._call_nexus(
                "add_document",
                **smart_context_storage.build_round_context_document(
                    conversation_id,
                    round_num,
                    context,
                ),
            )
        except Exception as e:
            print(f"⚠️ 存储上下文失败: {e}")
    
    # ===================== 功能 1: 摘要存储 =====================
    
    def should_store_summary(self, response: str) -> bool:
        """判断是否应该存储摘要"""
        if not self.config.store_summary_enabled:
            return False
        
        if len(response) < self.config.summary_min_length:
            return False
        
        return True
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        return smart_context_text.extract_keywords(text, limit=5)

    def _is_context_starved(self, user_message: str) -> bool:
        return smart_context_decision.is_context_starved(
            user_message,
            int(self.config.context_starved_min_chars),
        )

    def _extract_decision_blocks(self, text: str) -> List[str]:
        return smart_context_text.extract_decision_blocks(
            text,
            max_items=max(1, int(self.config.decision_block_max)),
        )

    def _build_turn_summary(
        self,
        user_message: str,
        ai_response: str,
        decisions: List[str],
    ) -> str:
        result = smart_context_summary.build_turn_summary(
            user_message,
            ai_response,
            decisions,
            summary_template_enabled=bool(self.config.summary_template_enabled),
            summary_template_fields=self.config.summary_template_fields or (),
            summary_min_length=int(self.config.summary_min_length),
            topic_max=int(self.config.topic_block_max),
            topic_min_keywords=int(self.config.topic_block_min_keywords),
            keyword_limit=5,
            entity_limit=5,
            action_limit=5,
            question_limit=5,
        )
        self._record_summary_metrics(result.summary_result)
        return result.text

    def _extract_topics(self, text: str) -> List[str]:
        return smart_context_text.extract_topics(
            text,
            topic_max=max(1, int(self.config.topic_block_max)),
            topic_min_keywords=int(self.config.topic_block_min_keywords),
            keyword_limit=5,
        )

    def _detect_topic_switch(self, user_message: str) -> bool:
        switched, keywords = smart_context_decision.detect_topic_switch(
            user_message,
            topic_switch_enabled=bool(self.config.topic_switch_enabled),
            last_keywords=self._last_keywords,
            topic_switch_keywords_max=int(self.config.topic_switch_keywords_max),
            topic_switch_min_overlap_ratio=float(self.config.topic_switch_min_overlap_ratio),
        )
        if keywords:
            self._last_keywords = keywords
        return switched

    def _trim_injected_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return smart_context_inject.trim_injected_items(
            items,
            max_chars_per_item=int(self.config.inject_max_chars_per_item),
            max_lines_per_item=int(self.config.inject_max_lines_per_item),
            max_lines_total=int(self.config.inject_max_lines_total),
        )

    def _normalize_tags(self, metadata: Any) -> List[str]:
        return smart_context_inject.normalize_tags(metadata)

    def _score_injected_item(self, relevance: float, tags: List[str], source: str) -> float:
        return smart_context_inject.score_injected_item(
            relevance,
            tags,
            source,
            decision_boost=float(self.config.inject_signal_boost_decision),
            topic_boost=float(self.config.inject_signal_boost_topic),
            summary_boost=float(self.config.inject_signal_boost_summary),
        )

    def _has_signal_tag(self, tags: List[str], source: str) -> bool:
        return smart_context_inject.has_signal_tag(tags, source)

    def _dynamic_inject_params(self, reason: str, items: List[Dict[str, Any]]) -> Tuple[int, float]:
        return smart_context_inject.dynamic_inject_params(
            reason,
            items,
            max_items=int(self.config.inject_max_items),
            threshold=float(self.config.inject_threshold),
            inject_dynamic_enabled=bool(self.config.inject_dynamic_enabled),
            dynamic_max_items=int(self.config.inject_dynamic_max_items),
            dynamic_low_signal_penalty=int(self.config.inject_dynamic_low_signal_penalty),
            dynamic_high_signal_bonus=int(self.config.inject_dynamic_high_signal_bonus),
        )

    def _extract_graph_edges(self, block: str, conversation_id: str) -> List[Dict[str, Any]]:
        return smart_context_graph.extract_graph_edges(
            block,
            conversation_id,
            int(self.config.decision_block_max),
        )

    def _store_decision_blocks(self, conversation_id: str, round_num: int, blocks: List[str]) -> None:
        for operation in smart_context_graph.build_decision_block_operations(
            conversation_id,
            round_num,
            blocks,
            max_graph_edges=int(self.config.decision_block_max),
        ):
            self._call_nexus("add_document", **operation["document"])
            if self._graph_enabled:
                for edge in operation["graph_edges"]:
                    graph_add_edge(**edge)

    def _store_topic_blocks(self, conversation_id: str, round_num: int, topics: List[str]) -> None:
        for operation in smart_context_graph.build_topic_block_operations(
            conversation_id,
            round_num,
            topics,
        ):
            self._call_nexus("add_document", **operation["document"])
            if self._graph_enabled:
                for edge in operation["graph_edges"]:
                    graph_add_edge(**edge)
    
    def store_conversation(self, 
                          conversation_id: str,
                          user_message: str,
                          ai_response: str) -> Dict[str, Any]:
        """
        存储对话摘要（兼容旧 API）
        """
        result = {
            "conversation_id": conversation_id,
            "stored": False,
        }
        
        if not self.should_store_summary(ai_response):
            return result
        
        if not self._nexus_core:
            return result
        
        try:
            summary = self._extract_summary(ai_response)
            data = smart_context_conversation.build_conversation_store_data(
                user_message,
                ai_response,
                summary=summary,
                keyword_limit=5,
                decision_max=int(self.config.decision_block_max),
                topic_max=int(self.config.topic_block_max),
                topic_min_keywords=int(self.config.topic_block_min_keywords),
            )
            blocks = data.decisions if self.config.decision_block_enabled else []
            topics = data.topics if self.config.topic_block_enabled else []

            for entry in smart_context_storage.build_conversation_store_entries(
                conversation_id,
                ai_response=ai_response,
                summary=data.summary,
                keywords=data.keywords,
                decisions=[],
                topics=[],
            ):
                self._call_nexus(
                    "add_document",
                    content=entry["content"],
                    title=entry["title"],
                    tags=entry["tags"],
                )
                result["stored"] = True

            if self.config.decision_block_enabled and blocks:
                self._store_decision_blocks(conversation_id, 0, blocks)

            if self.config.topic_block_enabled and topics:
                self._store_topic_blocks(conversation_id, 0, topics)
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    # ===================== 功能 2: 上下文注入 =====================
    
    def should_inject(self, user_message: str) -> Tuple[bool, str]:
        """
        判断是否需要注入上下文
        """
        return smart_context_decision.should_inject(
            user_message,
            inject_enabled=bool(self.config.inject_enabled),
            association_enabled=bool(self.config.association_enabled),
            context_starved_min_chars=int(self.config.context_starved_min_chars),
            inject_mode=str(self.config.inject_mode),
        )
    
    def inject_memory(self, user_message: str) -> List[Dict]:
        """
        注入记忆库上下文
        """
        should_inject, reason = self.should_inject(user_message)
        
        if not should_inject:
            if self.config.inject_debug:
                print(f"[SmartContext] INJECT skip reason={reason}")
            return []
        
        if not self._nexus_core:
            if self.config.inject_debug:
                print("[SmartContext] INJECT skip nexus_core=missing")
            self._append_metrics(
                {
                    "event": "inject_skip",
                    "reason": "nexus_core_missing",
                }
            )
            return []
        
        try:
            max_items = int(self.config.inject_max_items)
            threshold = float(self.config.inject_threshold)

            fetch_n = smart_context_recall.calculate_fetch_n(
                max_items,
                inject_dynamic_enabled=bool(self.config.inject_dynamic_enabled),
                inject_dynamic_max_items=int(self.config.inject_dynamic_max_items),
            )
            results = self._call_nexus("search_recall", user_message, fetch_n) or []
            if not results:
                self._append_metrics(
                    {
                        "event": "inject_empty",
                        "reason": reason,
                        "query_len": len(user_message or ""),
                    }
                )
            items = smart_context_recall.build_inject_candidates(
                results,
                signature_fn=self._content_signature,
                normalize_tags_fn=self._normalize_tags,
                score_fn=self._score_injected_item,
            )

            max_items, threshold = self._dynamic_inject_params(reason, items)

            filtered, fallback_used, fallback_reason = smart_context_recall.select_injected_items(
                items,
                threshold=threshold,
            )

            if self.config.inject_debug:
                sources = [r.get("source", "unknown") for r in filtered]
                sample = (filtered[0]["content"][: self.config.inject_debug_max_chars] if filtered else "")
                print(
                    f"[SmartContext] INJECT ok reason={reason} topk={len(filtered)}/{len(results)} "
                    f"threshold={threshold} sources={sources} sample={sample!r}"
                )

            retrieved = len(results)
            injected = len(filtered)
            self._append_metrics(
                smart_context_recall.build_inject_metric_payload(
                    reason=reason,
                    retrieved=retrieved,
                    filtered=filtered,
                    threshold=threshold,
                    max_items=max_items,
                    fallback_used=fallback_used,
                    fallback_reason=fallback_reason,
                )
            )

            graph_items = self._inject_graph_associations(user_message, reason)
            final = smart_context_inject.finalize_injected_items(
                filtered,
                graph_items,
                topk_only=bool(self.config.inject_topk_only),
                max_items=max_items,
                max_chars_per_item=int(self.config.inject_max_chars_per_item),
                max_lines_per_item=int(self.config.inject_max_lines_per_item),
                max_lines_total=int(self.config.inject_max_lines_total),
            )
            graph_ratio = (len(graph_items) / injected) if injected else 0.0
            self._append_metrics(
                {
                    "event": "graph_inject",
                    "reason": reason,
                    "graph_injected": len(graph_items),
                    "graph_ratio": round(graph_ratio, 3),
                }
            )
            self._record_inject_event(reason, len(final))
            self._record_inject_stats(reason, len(results), len(filtered), len(graph_items), threshold)
            return final
            
        except Exception as e:
            print(f"⚠️ 记忆注入失败: {e}")
            return []

    def _record_inject_event(self, reason: str, injected_count: int) -> None:
        if not self.config.adaptive_enabled:
            return
        self._inject_history.append(
            {
                "reason": reason,
                "count": int(injected_count),
            }
        )
        if len(self._inject_history) >= int(self.config.adaptive_window):
            self._tune_adaptive()

    def _record_inject_stats(
        self,
        reason: str,
        retrieved: int,
        injected: int,
        graph_injected: int,
        threshold: float,
    ) -> None:
        if not self.config.inject_stats_enabled:
            return
        self._inject_stats.append(
            smart_context_adaptive.build_inject_stats_entry(
                reason,
                retrieved,
                injected,
                graph_injected,
                threshold,
            )
        )
        summary = smart_context_adaptive.summarize_inject_stats(
            self._inject_stats,
            int(self.config.inject_stats_window),
        )
        if not summary:
            return
        self._append_metrics(
            {
                "event": "inject_stats",
                **summary,
            }
        )
        self._maybe_alert_inject_ratio(float(summary["avg_ratio"]), int(summary["window"]))

    def _maybe_alert_inject_ratio(self, avg_ratio: float, window: int) -> None:
        self._runtime.maybe_alert_inject_ratio(avg_ratio, window, self.config)

    def _auto_tune_inject(self, avg_ratio: float) -> None:
        self._runtime.auto_tune_inject(avg_ratio, self.config)

    def _tune_adaptive(self) -> None:
        adaptive = smart_context_adaptive.compute_adaptive_threshold(
            self._inject_history,
            adaptive_window=int(self.config.adaptive_window),
            current_threshold=float(self.config.inject_threshold),
            adaptive_min_threshold=float(self.config.adaptive_min_threshold),
            adaptive_max_threshold=float(self.config.adaptive_max_threshold),
            adaptive_step=float(self.config.adaptive_step),
        )
        if not adaptive:
            return
        new_threshold = float(adaptive["new_threshold"])
        if new_threshold != self.config.inject_threshold:
            if self.config.inject_debug:
                print(
                    f"[SmartContext] ADAPT threshold {self.config.inject_threshold:.2f} -> {new_threshold:.2f} "
                    f"(ratio={float(adaptive['ratio']):.2f}, window={int(adaptive['window'])})"
                )
            self.config.inject_threshold = new_threshold

    def _inject_graph_associations(self, user_message: str, reason: str) -> List[Dict]:
        if not smart_context_graph_inject.should_graph_inject(
            graph_enabled=bool(self._graph_enabled),
            graph_inject_enabled=bool(self.config.graph_inject_enabled),
            reason=reason,
        ):
            return []

        keywords = self.extract_keywords(user_message)
        if not keywords:
            return []

        max_items = max(1, int(self.config.graph_max_items))
        out = smart_context_graph_inject.build_graph_injected_items(
            keywords,
            edge_lookup_fn=lambda keyword, limit, evidence_limit: graph_related_with_evidence(
                keyword,
                limit=limit,
                evidence_limit=evidence_limit,
            ),
            max_items=max_items,
            evidence_max_chars=int(self.config.graph_evidence_max_chars),
        )
        if self.config.inject_debug and out:
            print(f"[SmartContext] GRAPH inject count={len(out)} keywords={keywords[:max_items]}")
        return out[: max_items]
    
    def generate_context_prompt(self, user_message: str) -> str:
        """
        生成上下文提示词
        """
        results = self.inject_memory(user_message)
        return smart_context_prompt.build_context_prompt(results, max_chars_per_item=200)
    
    # ===================== 功能 3: 压缩前抢救 (NOW.md) =====================
    
    def rescue_before_compress(self, conversation: str) -> Dict[str, Any]:
        """
        压缩前抢救
        
        从对话中提取关键信息并保存到 NOW.md
        """
        if not self.config.rescue_enabled:
            return {"skipped": True, "reason": "rescue_disabled"}
        
        try:
            return smart_context_now.rescue_before_compress(
                conversation,
                rescue_gold=bool(self.config.rescue_gold),
                rescue_decisions=bool(self.config.rescue_decisions),
                rescue_next_actions=bool(self.config.rescue_next_actions),
            )
        except Exception as e:
            return {
                "decisions_rescued": 0,
                "goals_rescued": 0,
                "questions_rescued": 0,
                "saved": False,
                "error": str(e),
            }
    
    def get_rescue_context(self) -> str:
        """获取抢救上下文"""
        try:
            return smart_context_now.get_rescue_context()
        except:
            return ""
    
    def clear_rescue(self):
        """清空抢救状态"""
        try:
            smart_context_now.clear_rescue()
        except:
            pass
    
    # ===================== 便捷函数 =====================

def store_conversation(conversation_id: str, user_message: str, ai_response: str) -> Dict:
    """存储对话摘要（便捷函数）"""
    from ..compat import nexus_init, nexus_write

    if not nexus_init():
        return {"error": "nexus init failed", "stored": False}
    data = smart_context_conversation.build_conversation_store_data(
        user_message,
        ai_response,
        summary_min_length=50,
        summary_fallback_max_chars=100,
        keyword_limit=5,
        decision_max=3,
        topic_max=3,
        topic_min_keywords=2,
    )
    for entry in smart_context_storage.build_conversation_store_entries(
        conversation_id,
        ai_response=ai_response,
        summary=data.summary,
        keywords=data.keywords,
        decisions=data.decisions,
        topics=data.topics,
    ):
        compat = entry["compat"]
        nexus_write(
            entry["content"],
            entry["title"],
            priority=compat["priority"],
            kind=compat["kind"],
            source=compat["source"],
            tags=compat["tags"],
        )

    return {"stored": True, "conversation_id": conversation_id}


def inject_memory_context(user_message: str) -> str:
    """注入记忆上下文（便捷函数）"""
    from ..compat import nexus_init, nexus_recall

    if not nexus_init():
        return ""

    results = nexus_recall(user_message, n=3)
    return smart_context_prompt.build_context_prompt(results, max_chars_per_item=200)


# ===================== 向后兼容 =====================

__all__ = [
    "SmartContextPlugin",
    "ContextCompressionConfig",
    "ConversationContext",
    "store_conversation",
    "inject_memory_context",
]
