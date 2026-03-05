---
name: nexus-auto-save
description: "Deep-Sea Nexus 自动保存：在消息发送后解析摘要并写入向量库"
metadata:
  openclaw:
    emoji: "💾"
    events:
      - message:sent
    requires:
      bins:
        - python3
    always: true
---

# Nexus Auto Save Hook

- 触发时机：`message:sent`
- 作用：将回复内容与可用摘要写入 Deep-Sea Nexus（向量库 + memory_v5）
- 摘要来源（按优先级）：
  - 回复中内嵌摘要（`## 📋 总结` / JSON）
  - Context Policy v2 摘要提示（`summary_hint`）
  - 无结构化摘要时仍保存原文（保证记忆不断流）
- 写入路径：`hooks/post-response/auto_save_summary.py` 统一使用 `nexus_core.nexus_write`（原文 + 结构化摘要 + 摘要元数据），不再依赖脆弱的 `create_vector_store` 快路径
- 失败处理：
  - Hook Python 进程返回非零时视为保存失败（不会写入 dedupe 状态）
  - 自动写入备用文件：`~/.openclaw/logs/summaries/*.json`
  - 调试日志：`/tmp/nexus-auto-save-debug.jsonl`（包含 hook stdout/stderr 片段）
