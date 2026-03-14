# Deep-Sea Nexus v2.0 集成指南

> Archived reference: this file is a v2-era integration guide and is not the
> current source of truth for the `v5.0.0` release pack.
> Current docs:
> - `README.md`
> - `TECHNICAL_OVERVIEW_CURRENT.md`
> - `ARCHITECTURE_CURRENT.md`
> - `API_CURRENT.md`

> 说明：本文为 v2 兼容集成说明（历史文档），vNext 以插件方式运行，推荐使用 `config.json` + `OPENCLAW_WORKSPACE` 路径。
> 若插件已启动，调用 `nexus_core.py` 会自动走 compat 路径，无需手动切换。

## 概述

Deep-Sea Nexus v2.0 是一个专为 AI Agent 设计的长期记忆系统，与 OpenClaw 无缝集成。

## 启动规则

```
1. 启动时只读 `memory/90_Memory/YYYY-MM-DD/_INDEX.md`
2. 索引 < 300 tokens，无 Session 历史
3. 上下文立即就绪
```

## 对话规则

```
1. 用户提问
2. 调用 nexus.recall(query) 搜索索引
3. 加载相关内容 (< 500 tokens)
4. 生成回答
```

## 写入规则

```python
# 关键信息添加 #GOLD 标记
nexus.write_session(session_id, "关键决策", is_gold=True)

# 普通内容
nexus.write_session(session_id, "普通对话内容")
```

## Session 规则

| 规则 | 说明 |
|------|------|
| 格式 | `session_HHMM_Topic.md` |
| 每个话题 | 一个 Session |
| 自动 Flush | 每日凌晨 3 点 |

## 环境变量

```bash
# 兼容旧路径（v2），v3 插件系统优先使用 OPENCLAW_WORKSPACE
NEXUS_PATH=~/.openclaw/workspace/DEEP_SEA_NEXUS_V2
OPENCLAW_WORKSPACE=~/.openclaw/workspace
NEXUS_MEMORY=memory/90_Memory
NEXUS_FLUSH_TIME=03:00
```

## vNext Scorer（可选）

`brain.scorer_type` 支持 `keyword` / `hashed-vector` / `vector`，其中 `vector` 优先使用 sentence-transformers，未安装则自动回退。

## 示例工作流

```
用户: "继续昨天的 Python 学习"

Agent:
  1. recall("Python 学习")
  2. 加载相关 Session
  3. 恢复上下文
  4. 继续对话
```

## 性能指标

- 启动: < 1 秒
- 召回: < 100ms
- 索引: < 300 tokens
- 每轮: < 1000 tokens
