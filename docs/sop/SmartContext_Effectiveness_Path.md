# SOP: SmartContext (8/20/35) 规则生效与底层路径 (2026-02-27)

## 1. 现象描述
- 会话 Context 占用高（86%+），但 `Compactions: 0`。
- `smart_context_metrics.log` 只有 `init` 事件，没有 `process_round` 或 `rescue_saved` 事件。
- 状态卡显示 `Runtime: direct`。

## 2. 底层生效路径 (The "Hidden" Pipeline)
在 OpenClaw 2026.2.25+ 版本中，SmartContext 的生效依赖以下三级链路，缺一不可：

### A. 消息路由 (Routing)
- **机制**：Discord Channel 必须通过 `openclaw.json` 的 `bindings` 明确绑定到对应的 Agent（如 `researcher`）。
- **经验**：如果 Channel 未绑定，即使在卡片里看到了 Agent 标识，它也可能没走 Hook 流水线。
- **配置标准**：优先使用 `guildId` 全量绑定，确保服务器内所有频道一致性。

### B. Hook 桥接 (Workspace Bridge)
- **机制**：OpenClaw 内核不内置 SmartContext 逻辑。它通过 `loadInternalHooks` 从 `workspace/hooks` 目录加载脚本。
- **入口文件**：
  - `workspace/hooks/context-optimizer.json`: 定义事件订阅 (`agent:input`, `before_prompt_build`)。
  - `workspace/hooks/context-optimizer.js`: 桥接代码，直接调用 Deep-Sea Nexus 的单一路径 handler：`skills/deepsea-nexus/resources/openclaw/context-optimizer/handler.single-source.js`。
- **关键日志**：`gateway.log` 中必须出现 `Registered hook: context-optimizer -> ...`。
- **验收信号**：`~/.openclaw/workspace/logs/smart_context_metrics.log` 出现 `event: "hook_compaction"`（这是 hook 实际执行的唯一可靠证据）。

### C. 规则同步 (Single Source of Truth)
- **机制**：通过 `sync_openclaw_context_optimizer.py --apply` 将 Deep-Sea Nexus 的 8/20/35 配置物理写入 `~/.openclaw/state/context-optimizer-single-source.json`。
- **优先级**：此文件的内容具有最高优先级，会覆盖 `openclaw.json` 中的 `contextPruning` 设置。

## 3. 运维与防漂移指令
- **重同步命令**：`python3 /Users/yizhi/.openclaw/workspace/skills/deepsea-nexus/scripts/sync_openclaw_context_optimizer.py --apply`
- **查看执行指标**：`tail -f /Users/yizhi/.openclaw/workspace/logs/smart_context_metrics.log`（寻找 `process_round` 事件）。
- **确认 Hook 状态**：`rg "Registered hook: context-optimizer" /Users/yizhi/.openclaw/logs/gateway.log`。

## 4. 关键避坑记录
- **Runtime direct 误区**：`Runtime: direct` 是显示状态，不代表 Hook 不工作。不要尝试去改 runtimeMode。
- **配置漂移**：不要手动在 `openclaw.json` 里修改 `contextPruning`，那些修改在同步时会被覆盖。
