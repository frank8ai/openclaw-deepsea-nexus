# SOP: SmartContext 每日调参与 RCA（2026-02-28）

> Archived reference: this is a historical RCA/tuning note from 2026-02-28 and
> not the current source of truth for v5 runtime defaults.
> Current docs:
> - `Context_Policy_v2_EventDriven.md`
> - `../README.md`
> - `../reports/2026-03-14-current-runtime-audit.md`

## 1. 目标
- 保证上下文压缩稳定触发（不漏压缩）
- 兼顾质量与成本（不影响工作流的前提下节省 tokens）
- 每日产出可执行参数建议：`full_rounds / summary_rounds / compress_after_rounds`

## 2. 本次根因与修复路径

### 2.1 根因
- `context-optimizer` 在部分 `before_prompt_build/agent:input` 事件中拿不到完整历史。
- 历史来源只读事件载荷，未回查 `sessionFile(jsonl)`，导致个别频道长期不触发压缩。

### 2.2 修复策略（最小影响）
- 保持事件历史优先。
- 仅在 `before_prompt_build` 和 `agent:input`：
  - 当事件历史不足时，通过 `sessionKey -> sessions.json -> sessionFile` 回填历史。
  - 只有回填历史严格更长时才替换。
- `before_agent_start` 不启用回填，避免副作用扩大。
- `hook_compaction` 指标增强：追加 `session_key/history_source/fallback_used/history_direct/history_resolved`。

### 2.3 验收信号
- `smart_context_metrics.log` 出现目标会话 `session_key` 的 `hook_compaction`。
- `openclaw status --json` 中对应会话 `smartContext` 非空。

## 3. Codex 与 OpenClaw 参数分层（当前）
- `Codex CLI`（本地 skill）：
  - `~/.codex/skills/deepsea-nexus/config.json`
  - `full_rounds=16`, `summary_rounds=40`, `compress_after_rounds=70`
- `OpenClaw`（运行时 hook）：
  - 优先：`~/.openclaw/state/context-optimizer-single-source.json`
  - 回退：`~/.openclaw/workspace/skills/deepsea-nexus/config.json`
  - 当前：`preserveRecent=8`（映射 `full_rounds=8`），`compressionThreshold=20`（映射 `summary_rounds=20`），`compress_after_rounds=35`

> 结论：Codex 16 轮与 OpenClaw 8 轮是“分运行时配置”，不是冲突。

## 4. 每日监控与调参闭环

### 4.1 报告脚本（report-only）
- 脚本：`skills/deepsea-nexus/scripts/smart_context_param_advisor.py`
- 输入：`~/.openclaw/workspace/logs/smart_context_metrics.log`
- 输出：
  - `~/.openclaw/workspace/logs/smart-context-advisor/YYYY-MM-DD/advisor-HHMMSS.md`
  - `~/.openclaw/workspace/logs/smart-context-advisor/YYYY-MM-DD/advisor-HHMMSS.json`
  - `~/.openclaw/workspace/logs/smart-context-advisor/latest.md|latest.json`
- 默认行为：只给建议，不自动改配置。

手动运行：
```bash
REPO_ROOT="${DEEPSEA_NEXUS_ROOT:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/skills/deepsea-nexus}"
cd "$REPO_ROOT"
python3 scripts/smart_context_param_advisor.py --lookback-hours 24 --min-events 8 --print-markdown
```

### 4.2 定时安装
- 安装脚本：`skills/deepsea-nexus/scripts/install_smart_context_param_advisor_cron.sh`
- 默认任务：每天 `09:20` 运行一次（本机 cron 时区）。

安装：
```bash
REPO_ROOT="${DEEPSEA_NEXUS_ROOT:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/skills/deepsea-nexus}"
bash "$REPO_ROOT/scripts/install_smart_context_param_advisor_cron.sh"
```

## 5. 调参规则（建议）
- 若 `token:hard-ratio` 占比持续偏高（例如 >=20%）或 `p90 rounds` 明显超过 `compress_after_rounds`：
  - 提前压缩（适当降低 `full/summary/compress`）。
- 若硬触发极低、平均节省很小且多数会话轮次远低于阈值：
  - 放宽参数（适当提高 `full/summary/compress`）。
- 样本不足时不改（先继续观察）。

建议执行纪律：
1. 连续观察至少 3 天再改参数。
2. 每次改动只改一档，避免大幅抖动。
3. 改后执行 `sync_openclaw_context_optimizer.py --apply` 并复验指标趋势。

## 6. 安全边界
- 禁止自动写配置（先报告后人工确认）。
- 优先修复“压缩是否触发”的可靠性，再讨论“压缩多早触发”。
- 频道/agent 独立参数尚未启用；当前是全局参数模式。
