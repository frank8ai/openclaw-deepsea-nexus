"""
智能摘要模块 v2.0 - 让第二大脑越来越聪明

功能：
- 从 LLM 回复中解析结构化摘要
- 混合存储摘要 + 原文到向量库
- 支持回溯到原始对话
- 结构化字段让检索更精准

核心设计理念：
- 每次对话都是知识沉淀的机会
- 摘要要有长期复用价值
- 避免"正确的废话"，只保留"未来能用到的"
"""

import json
import re
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class StructuredSummary:
    """
    结构化摘要数据类
    
    设计目标：让未来的检索更精准，让第二大脑越来越聪明
    """
    # 核心产出 - 必须填写
    core_output: str = ""           # 本次核心产出：一句话说明解决了什么问题
    
    # 技术要点 - 结构化知识
    tech_points: List[str] = None   # 技术要点：关键点列表
    
    # 代码模式 - 可复用资产
    code_pattern: str = ""          # 代码模式：提取的可复用代码
    
    # 决策上下文 - 理解"为什么"
    decision_context: str = ""       # 决策上下文：为什么选择这个方案
    
    # 避坑记录 - 避免重复犯错
    pitfall_record: str = ""         # 避坑记录：应避免的错误/弯路
    
    # 适用场景 - 避免滥用
    applicable_scene: str = ""       # 适用场景：这个方案适用的场景
    
    # 搜索关键词 - 精准检索
    search_keywords: List[str] = None # 搜索关键词：标签列表
    
    # 项目关联 - 项目连续性
    project关联: str = ""            # 项目关联：所属项目（可选）

    # 下一步与问题 - 计划与待澄清
    next_actions: str = ""           # 下一步：后续行动
    questions: str = ""              # 问题：待澄清问题

    # 实体 - 关键人/物/系统
    entities: List[str] = None       # 实体列表
    
    # 置信度 - 质量自检
    confidence: str = "medium"       # 置信度：high/medium/low
    
    def __post_init__(self):
        if self.tech_points is None:
            self.tech_points = []
        if self.search_keywords is None:
            self.search_keywords = []
        if self.entities is None:
            self.entities = []
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StructuredSummary':
        """从字典创建"""
        return cls(
            core_output=data.get("本次核心产出", ""),
            tech_points=data.get("技术要点", []),
            code_pattern=data.get("代码模式", ""),
            decision_context=data.get("决策上下文", ""),
            pitfall_record=data.get("避坑记录", ""),
            applicable_scene=data.get("适用场景", ""),
            search_keywords=data.get("搜索关键词", []),
            project关联=data.get("项目关联", ""),
            next_actions=data.get("下一步", data.get("next_actions", "")),
            questions=data.get("问题", data.get("questions", "")),
            entities=data.get("实体", data.get("entities", [])),
            confidence=data.get("置信度", "medium")
        )
    
    def to_searchable_text(self) -> str:
        """转换为可搜索的文本"""
        parts = [
            self.core_output,
            " ".join(self.tech_points),
            self.code_pattern,
            self.decision_context,
            self.pitfall_record,
            self.applicable_scene,
            " ".join(self.search_keywords),
            self.project关联,
            self.next_actions,
            self.questions,
            " ".join(self.entities),
        ]
        return " ".join(p for p in parts if p)
    
    def to_tags(self) -> str:
        """转换为标签字符串"""
        return ",".join(self.search_keywords)


class SummaryParser:
    """摘要解析器 v2.0"""
    
    # 新的结构化 JSON 格式
    JSON_PATTERN = re.compile(
        r'```json\s*\n([\s\S]*?)\n```',
        re.DOTALL
    )
    
    # 旧的简单格式（向后兼容）
    LEGACY_PATTERNS = [
        re.compile(r'## 📋 总结[^\n]*\n([\s\S]*?)(?=\n\n|$)', re.DOTALL),
        re.compile(r'---SUMMARY---\s*(.+?)\s*---END---', re.DOTALL | re.IGNORECASE),
    ]
    
    @classmethod
    def parse(cls, response: str) -> tuple:
        """
        解析 LLM 回复，提取摘要和原文
        
        Args:
            response: LLM 原始回复
            
        Returns:
            (reply, summary) 元组
            - reply: 主体回复内容
            - summary: 摘要内容，无摘要时为 None
        """
        summary = None
        
        # 优先尝试解析 JSON 格式
        json_match = cls.JSON_PATTERN.search(response)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                data = json.loads(json_str)
                # 转换为结构化摘要
                summary = StructuredSummary.from_dict(data)
                # 移除 JSON 块，得到原文
                response = cls.JSON_PATTERN.sub('', response).strip()
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"JSON 解析失败: {e}，尝试旧格式")
        
        # 如果没有 JSON，尝试旧格式（向后兼容）
        if summary is None:
            for pattern in cls.LEGACY_PATTERNS:
                match = pattern.search(response)
                if match:
                    summary_text = match.group(1).strip()
                    # 转换为简单的结构化摘要
                    summary = StructuredSummary(
                        core_output=summary_text,
                        confidence="low"  # 旧格式无法自评
                    )
                    # 移除摘要部分，得到原文
                    response = pattern.sub('', response).strip()
                    break
        
        return response, summary
    
    @classmethod
    def create_structured_summary_prompt(cls, conversation_history: str) -> str:
        """
        生成结构化摘要提示词
        
        Args:
            conversation_history: 对话历史
            
        Returns:
            包含结构化摘要要求的完整提示词
        """
        return f"""
{conversation_history}

---

## 🧠 知识沉淀（每次回复必须）

请用 JSON 格式总结本次对话要点，帮助未来的你快速理解这段对话的价值：

```json
{{
  "本次核心产出": "一句话说明这次解决了什么问题",
  "技术要点": ["关键点1", "关键点2"],
  "代码模式": "提取的可复用代码片段（如果有）",
  "决策上下文": "为什么选择这个方案",
  "避坑记录": "应避免的错误/弯路",
  "适用场景": "这个方案适用的场景",
  "下一步": "后续行动/下一步",
  "问题": "仍待澄清的问题",
  "实体": ["关键人/系统/组件"],
  "搜索关键词": ["标签1", "标签2"],
  "项目关联": "所属项目（可选）",
  "置信度": "high/medium/low"
}}
```

**填写指南**：
- 每个字段都要思考后填写
- 避免泛泛而谈，要具体可操作
- 重点突出"未来能用到"的信息
- 置信度：如果对摘要质量有信心选 high
"""


class HybridStorage:
    """混合存储管理器 v2.0"""
    
    def __init__(self, vector_store):
        """
        初始化混合存储
        
        Args:
            vector_store: 向量库实例（需有 add 和 search 方法）
        """
        self.vector_store = vector_store
        self.parser = SummaryParser()
        self._mem_v5 = None
        try:
            from memory_v5 import MemoryV5Service
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as fh:
                    config = json.load(fh)
            self._mem_v5 = MemoryV5Service(config)
        except Exception:
            self._mem_v5 = None
    
    def process_and_store(self, conversation_id: str, response: str, 
                          user_query: str = "") -> Dict[str, Any]:
        """
        处理 LLM 回复，解析并混合存储
        
        Args:
            conversation_id: 对话 ID
            response: LLM 原始回复
            user_query: 用户问题（可选，用于上下文）
            
        Returns:
            处理结果字典
        """
        # 1. 解析回复和摘要
        reply, summary = self.parser.parse(response)
        
        results = {
            "conversation_id": conversation_id,
            "reply": reply[:200] if reply else "",  # 截断显示
            "has_summary": summary is not None,
            "summary_type": type(summary).__name__ if summary else None,
            "stored_count": 0,
            "summary_data": None
        }
        
        # 2. 存储原文
        try:
            self.vector_store.add(
                content=reply,
                title=f"对话 {conversation_id} - 原文",
                tags=f"type:content,source:{conversation_id}"
            )
            results["stored_count"] += 1
        except Exception as e:
            print(f"存储原文失败: {e}")
        
        # 3. 如果有结构化摘要，存储结构化数据
        if summary:
            if isinstance(summary, StructuredSummary):
                # 结构化摘要 - 存储所有字段
                summary_text = summary.to_searchable_text()
                summary_tags = f"type:structured_summary,source:{conversation_id},confidence:{summary.confidence}"
                
                # 主存储：合并所有字段为可搜索文本
                self.vector_store.add(
                    content=summary_text,
                    title=f"对话 {conversation_id} - 结构化摘要",
                    tags=summary_tags
                )
                results["stored_count"] += 1
                
                # 元数据存储：保留原始结构
                self.vector_store.add(
                    content=json.dumps(summary.to_dict(), ensure_ascii=False),
                    title=f"对话 {conversation_id} - 摘要元数据",
                    tags=f"type:summary_metadata,source:{conversation_id}"
                )
                results["stored_count"] += 1
                
                # 关键词单独索引（提升检索精度）
                if summary.search_keywords:
                    keyword_text = " ".join(summary.search_keywords)
                    self.vector_store.add(
                        content=keyword_text,
                        title=f"对话 {conversation_id} - 关键词索引",
                        tags=f"type:keywords,source:{conversation_id}"
                    )
                    results["stored_count"] += 1
                
                results["summary_data"] = summary.to_dict()
                
            else:
                # 旧格式摘要（向后兼容）
                self.vector_store.add(
                    content=summary.core_output,
                    title=f"对话 {conversation_id} - 摘要",
                    tags=f"type:summary,source:{conversation_id}"
                )
                results["stored_count"] += 1
                results["summary_data"] = {"core_output": summary.core_output}

        # 4. Sync to memory_v5 (best-effort)
        if self._mem_v5 is not None:
            try:
                summary_payload = None
                if isinstance(summary, StructuredSummary):
                    summary_payload = summary.to_dict()
                elif summary is not None:
                    summary_payload = {"本次核心产出": getattr(summary, "core_output", str(summary))}
                self._mem_v5.ingest_summary(
                    conversation_id=conversation_id,
                    reply=reply or "",
                    summary=summary_payload,
                    user_query=user_query or "",
                )
            except Exception:
                pass
        
        return results
    
    def search_with_context(self, query: str, limit: int = 5) -> List[Dict]:
        """
        搜索并返回上下文信息
        
        Args:
            query: 搜索词
            limit: 返回数量
            
        Returns:
            搜索结果列表，包含类型标注
        """
        results = self.vector_store.search(query, limit=limit)
        
        # 添加类型标注
        for item in results:
            tags = item.get("metadata", {}).get("tags", "") or ""
            if "type:structured_summary" in tags:
                item["display_type"] = "结构化摘要"
            elif "type:summary_metadata" in tags:
                item["display_type"] = "摘要元数据"
            elif "type:keywords" in tags:
                item["display_type"] = "关键词"
            elif "type:summary" in tags:
                item["display_type"] = "摘要"
            else:
                item["display_type"] = "原文"
        
        return results


def create_summary_system_prompt() -> str:
    """
    创建系统提示词模板 v2.0
    
    Returns:
        包含结构化摘要生成指令的系统提示词
    """
    return """
你是一个 AI 助手。请在回复结束时，按以下格式添加知识沉淀：

[你的完整回复内容]

```json
{
  "本次核心产出": "一句话说明这次解决了什么问题",
  "技术要点": ["关键点1", "关键点2"],
  "代码模式": "提取的可复用代码片段（如果有）",
  "决策上下文": "为什么选择这个方案",
  "避坑记录": "应避免的错误/弯路",
  "适用场景": "这个方案适用的场景",
  "下一步": "后续行动/下一步",
  "问题": "仍待澄清的问题",
  "实体": ["关键人/系统/组件"],
  "搜索关键词": ["标签1", "标签2"],
  "项目关联": "所属项目（可选）",
  "置信度": "high/medium/low"
}
```

**填写指南**：
- 每个字段都要思考后填写
- 避免泛泛而谈，要具体可操作
- 重点突出"未来能用到"的信息
- 置信度：如果对摘要质量有信心选 high

要求：
- 摘要要简洁明了
- 包含关键决策、技术术语、重要信息
- 不要包含客套话
"""


if __name__ == "__main__":
    # 测试
    parser = SummaryParser()
    
    # 测试新格式
    test_response_v2 = """
Python 列表推导式是一种简洁的创建列表方式。

例如：[x for x in range(10) if x % 2 == 0]

```json
{
  "本次核心产出": "学习 Python 列表推导式的基本语法和用法",
  "技术要点": ["列表推导式语法", "条件过滤", "嵌套推导"],
  "代码模式": "[x for x in iterable if condition]",
  "决策上下文": "选择列表推导式是因为代码更简洁，运行效率相当",
  "避坑记录": "复杂条件应拆分为函数，否则可读性差",
  "适用场景": "数据过滤、转换、简单映射场景",
  "搜索关键词": ["python", "list-comprehension", "语法", "列表"],
  "项目关联": "Python 学习",
  "置信度": "high"
}
```
"""
    
    reply, summary = parser.parse(test_response_v2)
    print("=" * 60)
    print("Reply:", reply[:100], "...")
    print("=" * 60)
    if isinstance(summary, StructuredSummary):
        print("✅ 结构化摘要:")
        print(f"  核心产出: {summary.core_output}")
        print(f"  技术要点: {summary.tech_points}")
        print(f"  代码模式: {summary.code_pattern}")
        print(f"  置信度: {summary.confidence}")
    else:
        print("Summary:", summary)
    
    # 测试旧格式兼容
    print("\n" + "=" * 60)
    print("测试旧格式兼容:")
    test_response_old = """
这是旧格式的测试回复。

---SUMMARY---
学习 Python 列表推导式的基本语法和用法
---END---
"""
    
    reply2, summary2 = parser.parse(test_response_old)
    print("Reply:", reply2)
    print("Summary:", summary2)
