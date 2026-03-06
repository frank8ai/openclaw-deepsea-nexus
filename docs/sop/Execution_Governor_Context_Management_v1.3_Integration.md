# SOP: Execution Governor v1.3 与 Deep-Sea Nexus 上下文治理联动（2026-03-06）

## 目标

把 `SmartContext`（摘要/注入/压缩）与 `execution-governor` v1.3（上下文压力/缓存效率/provider 原生能力信号）打通，形成可观测、可调参、可回滚的上下文治理闭环。

## 适用场景

- 长会话 token 持续偏高，历史膨胀影响稳定性。
- Provider 请求成本偏高，疑似缓存命中率偏低。
- 需要判断“该压缩了没”和“压缩是否真正生效”。

## 运行面依赖

- 运行策略：`~/.openclaw/state/execution-governor-policy.json`（v1.3）
- 策略源：`~/.openclaw/workspace/config/execution-governor/policy.v1.3.json`
- apply 脚本：`~/.openclaw/workspace/scripts/apply_execution_governor.sh`
- 报告脚本：`~/.openclaw/workspace/scripts/execution_governor_report.py`
- smoke 脚本：`~/.openclaw/workspace/scripts/execution_governor_context_smoke.js`

## 一键应用

```bash
bash ~/.openclaw/workspace/scripts/apply_execution_governor.sh
jq -r '.version,.context_management.enabled' ~/.openclaw/state/execution-governor-policy.json
```

期望：

- `version=2026-03-05.v1.3`
- `context_management.enabled=true`

## 联动验收

```bash
# 1) 扩展逻辑与事件烟测
node ~/.openclaw/workspace/scripts/execution_governor_context_smoke.js

# 2) 运行报表（看缓存与上下文压力）
python3 ~/.openclaw/workspace/scripts/execution_governor_report.py --tail 2000

# 3) 事件抽样（关键新增事件）
rg "provider_native_context_capability|context_pressure|cache_efficiency|context_compaction_signal" \
  ~/.openclaw/logs/execution-governor.log | tail -n 80
```

## 关键信号解释（与 Deep-Sea Nexus 的关系）

- `context_pressure`:
  - `soft`: 建议收敛输出，减少历史复述。
  - `hard`: 必须触发更强压缩策略；若持续出现，优先检查 `smart_context` 阈值与无效长 prompt。
- `context_compaction_signal`:
  - 用于校验“应压缩”判断是否出现。
  - 应与 `smart_context_metrics.log` 中 `hook_compaction` 趋势相互印证。
- `cache_efficiency`:
  - 表示 provider 缓存读命中状态；低命中通常意味着上下文抖动大或提示词不稳定。
- `cache_efficiency_low_streak`:
  - 连续低命中告警；优先做模板稳定化、减少不必要上下文噪音。
- `provider_native_context_capability`:
  - 给出 provider 家族对 `conversation_state/prompt_cache/server_compaction` 的能力画像，作为路由与成本策略依据。

## 日常巡检建议（每天 1-2 次）

```bash
python3 ~/.openclaw/workspace/scripts/execution_governor_report.py --tail 3000 --json
```

重点看：

- `cache_efficiency_by_task`
- `context_pressure_by_task`
- `context_compaction_signal_by_task`
- `provider_native_capability_by_family`

## 回滚

```bash
# 快速禁用 execution-governor
bash ~/.openclaw/workspace/scripts/rollback_execution_governor.sh

# 或回到 v1.2
POLICY_SOURCE_OVERRIDE=~/.openclaw/workspace/config/execution-governor/policy.v1.2.json \
bash ~/.openclaw/workspace/scripts/apply_execution_governor.sh
```

## 当前主机注意事项

- 若 `apply_execution_governor.sh --restart` 提示 LaunchAgent 不可用，说明自动重载失败。
- 这不影响策略文件落盘；但实时流量生效需等待下一次成功的 gateway 进程重载/重启。

