# v3.1 清理 2.0 重复代码

> Archived reference: this file records an earlier v3.1 duplicate-cleanup pass
> and is not the current source of truth for the `v5.0.0` release pack.

## 问题分析

### 2.0 版本功能重复

| 功能 | nexus_core.py | context_injector.py | nexus_autoinject.py | auto_recall.py |
|------|---------------|---------------------|---------------------|----------------|
| 触发词检测 | ✅ | ✅ | ✅ | ❌ |
| 关键词提取 | ✅ | ✅ | ✅ | ❌ |
| 语义搜索 | ✅ | ❌ | ✅ | ✅ |
| 上下文注入 | ❌ | ✅ | ✅ | ❌ |
| 自动调用 | ❌ | ❌ | ✅ | ✅ |

---

## 3.0 解决方案

### 统一 Context Engine

```
v2.0 (重复)
├── nexus_core.py        → 保留（兼容入口，优先走插件/compat）
├── context_injector.py  → 保留（兼容回退）
├── nexus_autoinject.py  → 保留（无 socket 时走 compat）
├── auto_recall.py       → 保留（无 socket 时走 compat）
└── layered_storage.py   → 保留（可能有用）

v3.0 (统一)
└── plugins/context_engine.py  ← 单一入口
```

### 核心设计理念

**来自用户反馈**：
> "如果 OpenClaw 不知道，就应该先搜索向量库的记忆，找到相关 token 注入上下文"

不是等用户说"还记得"才触发，而是：
1. 每次对话时判断是否需要检索
2. 如果用户问"怎么做"、"是什么" → 可能不知道，检索
3. 自动注入相关上下文

---

## 删除的文件

| 文件 | 移动到 | 原因 |
|------|--------|------|
| `nexus_core.py` (部分) | `plugins/context_engine.py` | 触发词检测、关键词提取 |
| `context_injector.py` (全部) | `plugins/context_engine.py` | 上下文注入、会话恢复 |
| `nexus_autoinject.py` (全部) | `plugins/context_engine.py` | 智能搜索 |
| `auto_recall.py` (全部) | `plugins/context_engine.py` | 自动调用 |

---

## 保留的文件

| 文件 | 保留原因 |
|------|----------|
| `nexus_core.py` | 保留核心语义搜索功能 |
| `session_manager.py` | 会话管理独立功能 |
| `flush_manager.py` | 清理功能独立 |
| `auto_summary.py` | 向后兼容，用户可能直接引用 |
| `layered_storage.py` | 保留，可能有其他用途 |

---

## 新 API 设计

### 便捷函数

```python
from deepsea_nexus import (
    # 智能检索（核心功能）
    smart_retrieve,     # 智能检索判断
    inject_context,     # 注入上下文
    
    # 触发词检测
    detect_trigger,     # 检测"还记得"
    
    # 摘要功能
    parse_summary,      # 解析摘要
    store_summary,      # 存储摘要
    
    # 引擎
    ContextEngine,      # 引擎类
    get_engine,        # 获取引擎实例
)
```

### 使用示例

```python
from deepsea_nexus import smart_retrieve, inject_context

# 智能检索（自动判断是否需要）
result = smart_retrieve("Python 装饰器怎么实现?")
# 返回: {"triggered": True, "trigger_type": "unknown", ...}

# 注入上下文
context = inject_context("怎么实现搜索功能?")
# 返回: "相关记忆:\n【1】..."

# 检测触发词
result = detect_trigger("还记得上次说的X吗?")
# 返回: {"triggered": True, "query": "X", ...}
```

---

## 向后兼容

### 保留的旧 API

```python
# 仍然可以工作
from deepsea_nexus import nexus_init, nexus_recall, nexus_add
```

### 迁移指南

| 旧 API | 新 API | 备注 |
|--------|--------|------|
| `nexus_core.detect_trigger()` | `detect_trigger()` | 函数名相同 |
| `nexus_core.extract_keywords()` | `extract_keywords()` | 已整合到引擎 |
| `context_injector.inject_on_resume()` | `resume_session()` | 新方法名 |
| `nexus_autoinject.smart_search()` | `smart_retrieve()` | 功能相同 |

---

## 清理步骤

### 步骤 1: 确认新代码工作

```bash
cd deepsea-nexus
python3 -c "
from deepsea_nexus import smart_retrieve, inject_context, detect_trigger
print('✅ 新 API 导入成功')
"
```

### 步骤 2: 更新引用

如果有代码引用以下模块，需要更新：

| 旧引用 | 新引用 |
|--------|--------|
| `from nexus_core import detect_trigger` | `from deepsea_nexus import detect_trigger` |
| `from context_injector import ContextInjector` | `from deepsea_nexus import ContextEngine` |
| `from nexus_autoinject import smart_search` | `from deepsea_nexus import smart_retrieve` |

### 步骤 3: 删除重复文件（可选）

确认所有引用更新后，可以删除：

```bash
# 如需瘦身，可在确认无旧入口依赖后删除（当前建议保留以兼容）
# rm nexus_core.py
# rm context_injector.py
# rm nexus_autoinject.py
# rm auto_recall.py
```

**注意**: 目前默认保留上述文件以兼容旧入口，并已具备 compat 回退。

---

## 测试验证

```bash
# 运行清理后的测试
python3 plugins/context_engine.py

# 应该输出：
# ✅ Context Engine v2 工作正常
```

---

## 总结

| 项目 | 状态 |
|------|------|
| 消除重复代码 | ✅ 完成 |
| 统一 API | ✅ 完成 |
| 向后兼容 | ✅ 保持 |
| 智能上下文 | ✅ 新增 |

---

*版本: 3.1.0 | 日期: 2026-02-13*
