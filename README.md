# 🧠 OpenClaw Deep-Sea Nexus v5.5.0

AI agent 的本地长期记忆与上下文治理层。

[English](README_EN.md) | [简体中文](README.md)

**版本**: `5.5.0`
**状态**: `v5.5.0` feature release
**更新**: `2026-03-22`

## Comparison

**Beyond Context Management:** Deep-Sea Nexus 不是在重复做记忆框架，而是在补齐治理层（evidence gate、scope isolation、lifecycle governance、ops audit）。
Read the technical manifesto: [`COMPARISON.md`](COMPARISON.md)

## 主要功能总览

面向 GitHub 评审与开发接入，当前版本的产品主能力如下：

- `Evidence-Gated Durable Memory`：记忆沉淀要求证据链，不接受“无证据随意摘要”。
- `Scoped Isolation`：`agent_id/user_id` 物理隔离 + `app_id/run_id/workspace` 记录级隔离，降低串扰与污染风险。
- `Lifecycle Governance`：支持 lifecycle audit、archive maintenance、backfill 和 report-first 运维策略。
- `Context Governance Pipeline`：围绕 `recall / inject / compress / rescue / replay` 构建可验证治理闭环。
- `Runtime + Compatibility`：同时支持兼容 sync API、async runtime plugin lifecycle、Memory v5 first 三条接入路径。
- `Operator Tooling`：提供 deploy/doctor/smoke/benchmark/maintenance 一整套本地运维链路。

功能详解与边界请看：[`docs/product/capabilities.md`](docs/product/capabilities.md)
## 项目定义

Deep-Sea Nexus 的目标不是“无限保存原始聊天记录”，而是通过上下文治理实现
长期、可追溯、可隔离、可运营的记忆连续性。

它解决的核心问题是：

- 重要决策只存在当前上下文，跨会话后丢失
- 长任务上下文不断膨胀，成本和噪音一起失控
- 多 agent / 多用户记忆容易串扰
- 记忆写入、召回、注入、压缩缺少明确策略和验证证据
- 旧自动化太多，无法接受一次性重写迁移

## Current Release Pack

这套 release 的当前真源文档分成三层：

- 产品真源：
  - `docs/product/README.md`
  - `docs/product/positioning.md`
  - `docs/product/capabilities.md`
  - `docs/product/users-and-use-cases.md`
  - `docs/product/roadmap.md`
- 技术真源：
  - `docs/TECHNICAL_OVERVIEW_CURRENT.md`
  - `docs/ARCHITECTURE_CURRENT.md`
  - `docs/API_CURRENT.md`
- 运行与治理真源：
  - `docs/LOCAL_DEPLOY.md`
  - `docs/sop/Context_Policy_v2_EventDriven.md`
  - `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`

正式发布说明：

- `docs/releases/V5_5_0_RELEASE_2026-03-22.md`
- `docs/releases/V5_5_0_RELEASE_2026-03-22_ZH.md`
- `docs/releases/V5_4_0_RELEASE_2026-03-22.md`
- `docs/releases/V5_4_0_RELEASE_2026-03-22_ZH.md`
- `docs/releases/V5_3_0_RELEASE_2026-03-21.md`
- `docs/releases/V5_3_0_RELEASE_2026-03-21_ZH.md`
- `docs/releases/V5_2_0_RELEASE_2026-03-18.md`
- `docs/releases/V5_2_0_RELEASE_2026-03-18_ZH.md`
- `docs/releases/V5_0_1_PATCH_2026-03-14.md`
- `docs/releases/V5_0_0_OFFICIAL_2026-03-14.md`
- `docs/releases/V5_0_0_HOTFIX_1_2026-03-14.md`
- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`

## 读者入口

### 1. 内部维护者

如果你要理解“这个系统当前到底是什么、边界在哪里、哪些算历史负债”：

- `docs/README.md`
- `docs/product/README.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/sop/Context_Policy_v2_EventDriven.md`

### 2. 集成开发者

如果你要决定该接 sync API、async runtime 还是 Memory v5：

- `docs/API_CURRENT.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`

### 3. 运维/工作流操作者

如果你要部署、体检、巡检、跑 smoke / benchmark：

- `docs/LOCAL_DEPLOY.md`
- `docs/sop/Context_Policy_v2_EventDriven.md`
- `scripts/deploy_local_v5.sh`
- `scripts/deploy_local_v5.cmd`
- `scripts/nexus_doctor_local.sh`

## 当前稳定承诺

- 保持历史 sync API 的渐进兼容接入
- 提供 async runtime + plugin lifecycle
- 提供 Memory v5 scoped memory（`agent_id / user_id` 物理隔离 + `app_id / run_id / workspace` 记录级隔离）
- 提供 recall / inject / compress / rescue / replay 的上下文治理链路
- 提供 RTK 风格 `runtime_middleware`，在 tool output 进入 capture 前执行压缩、结构化与 token 估算
- 提供零侵入 `codex_periodic_ingest`，离线扫描 `~/.codex` 会话与历史并自动写入 Memory v5
- 提供带 `status / alerts / hot scopes / recommendations` 的 lifecycle operator 输出
- 提供本地 deploy / doctor / smoke / benchmark 运维路径

## v5.5.0 发布重点

- 保留 `v5.4.0` 的 runtime middleware / execution guard / capability autotune 基线
- 新增内部 `execution_guard` 插件：
  - `allow / ask / block / context` 风险决策
  - `workspace_safe / workspace_sensitive / outside_workspace / system_sensitive / credential_sensitive / second_brain_sensitive` 路径敏感级别
  - report-only 默认执行模式
  - `GuardDecision / GuardFinding` 结构化输出
- 将 `nah` 的安全判定思路融入 execution-governor 融合面：
  - secrets / credential search 风险识别
  - obfuscated shell / curl-pipe-shell / powershell encoded execution 识别
  - 工作区越界写删风险识别
  - 第二大脑关键资产访问风险识别
- 新增 guardrails 与报告入口：
  - `scripts/sync_execution_governor_guardrails.py`
  - `scripts/execution_guard_report.py`
- 新增内部 `capability_autotune_lab`：
  - 离线压缩规则 golden eval
  - baseline / candidate compression profile 对比
  - report-first 推荐 `keep_for_lab / promote_recommended / discard`
  - `health --json` / `paths --json` 暴露最近 autotune 报告
- `runtime_middleware` 现在支持 config-driven compression rules，而不是完全硬编码
- 新增内部 `codex_periodic_ingest`：
  - 不改 Codex 启动方式，不依赖 OpenClaw hook
  - 扫描 `~/.codex/sessions/**/*.jsonl` 与 `~/.codex/history.jsonl`
  - 增量提取会话摘要与历史摘要写入 Memory v5
  - 默认支持每小时离线运行，可通过 Windows 计划任务安装脚本接入

## Runtime Middleware

`runtime_middleware` 是当前 release 中新增的内部 runtime 层，用来在工具输出进入 capture 之前先做：

- event kind 分类（`git_diff / grep / test / lint / build / container / network / shell`）
- RTK 风格压缩与结构化
- token 估算
- token-aware capture gate
- evidence snapshot 持久化

当前 v1 边界：

- 不新增 public API
- 默认通过内部插件启用
- 当前同时保留 OpenClaw `tool-call` adapter 与 Codex periodic ingest adapter
- 压缩结果不能绕过现有 evidence gate
- 压缩规则可通过 `runtime_middleware.compression.*` 离线实验与手工推广

运行态产物：

- metrics：`<workspace>/logs/runtime_middleware_metrics.log`
- evidence snapshots：`<workspace>/logs/runtime_middleware_evidence/`
- `Memory v5` item kind：`tool_event`

## Execution Guard

`execution_guard` 是当前 release 中新增的内部安全判定层，用来在工具事件进入 execution-governor 联动面之前先做：

- 风险 taxonomy 分类
- 路径敏感级别识别
- secrets / credential 命中识别
- shell obfuscation / network bootstrap 风险识别
- `allow / ask / block / context` 决策与 recommendation 产出

当前 v1 边界：

- 默认 `report_only`
- 不直接阻断宿主执行
- 当前只交付最小 OpenClaw 适配入口
- 风险结果会附着到 `tool_event.metadata.guard`

## Codex Periodic Ingest

`codex_periodic_ingest` 是当前 release 中新增的内部零侵入接入层，用来在**不改 Codex 启动方式、不依赖 OpenClaw**的前提下，把本机 Codex 使用痕迹增量沉淀到 Deep-Sea Nexus：

- 扫描 `~/.codex/sessions/**/*.jsonl`
- 扫描 `~/.codex/history.jsonl`
- 只做增量 ingest，避免重复写入
- 默认将扫描结果写入 `~/.codex/deepsea-nexus-workspace/memory/95_MemoryV5`
- `health --json` / `paths --json` 暴露最近一轮扫描状态与路径
- 提供 `scripts/codex_periodic_ingest.py` 手动运行入口
- 提供 `scripts/install_codex_periodic_ingest_task.py` Windows 每小时计划任务安装入口

当前 v1 边界：

- 内部插件，不是 public API
- 默认是离线周期扫描，不是实时 hook
- 当前只接 `sessions` + `history`
- 当前不反向修改 Codex 配置，也不把记忆直接注回活跃对话

## Capability Autotune Lab

`capability_autotune_lab` 是当前 release 中新增的内部离线能力优化层，用来在**不修改生产记忆链路**的前提下，对第二大脑的记忆/上下文/压缩规则做 golden-case 评测：

- 比较 baseline 与候选 compression profile
- 校验 failure / diff / grep 关键证据是否在压缩后保留
- 输出推荐的 `runtime_middleware.compression` 覆盖项
- 使用现有 `context_recall_scorecard` 作为 recall guardrail

当前 v1 边界：

- 默认 report-first
- 不自动改线上 config
- 不自动写 durable memory
- 当前重点是 `runtime_middleware` 压缩规则，而不是直接自修改 Memory v5 内核
## 最小验证路径

```bash
python3 -m unittest tests.test_memory_v5 -v
python3 scripts/context_recall_scorecard.py --golden docs/evals/context_recall_golden_cases.json
python3 run_tests.py
bash scripts/nexus_doctor_local.sh --check --skip-deploy
python3 scripts/memory_v5_smoke.py
python3 scripts/memory_v5_maintenance.py --dry-run --write-report
python3 scripts/runtime_middleware_report.py --json
python3 scripts/capability_autotune_lab.py --json
python3 scripts/codex_periodic_ingest.py --json
```

## 三个关键模型

### 1. 三层记忆模型

- `Working Context`
  - 当前目标、状态、约束、阻塞、下一步、开放问题
- `Durable Decision`
  - 带 evidence pointer 的稳定决策
- `Evidence Store`
  - 原始日志、文件、命令、artifact、报告

### 2. 三条接入路径

- Compatibility First
  - `nexus_init / nexus_recall / nexus_add`
- Runtime First
  - `create_app()` + plugin lifecycle
- Memory v5 First
  - `MemoryScope / MemoryV5Service`

### 3. 上下文治理规则

- 所有记忆先经过 context pipeline，再决定是否进入 durable memory
- 固定轮次基线：
  - `8 / 20 / 35`
- 压缩前先保留 typed state：
  - `goal/status/decisions/decision_reversal_conditions/waiting_on/assumptions/constraints/blockers/modified_files/change_scope/key_changes/verification_subject/verification_command/verification_result/verification_status/failure_fingerprint/rollback_trigger/rollback_target/rollback_notes/next/questions/evidence/replay`
- 当前压缩保留优先级：
  - 架构决策按独立 `Decision:` 行保留，不混成一句摘要
  - 执行续跑必需信息单独保留：等待项、关键假设、变更范围、验证对象/命令/结果
  - 已修改文件、关键变更、回滚触发/目标/笔记进入 typed context
  - 工具原始输出不直接写入压缩记忆正文：成功只留 `PASS/FAIL`，失败额外保留失败指纹
- 规则真源：
  - `docs/sop/Context_Policy_v2_EventDriven.md`

## 非目标

当前不要把这个仓库理解成：

- 通用 SaaS 知识库产品
- 团队协作内容平台
- 云托管多租户记忆服务
- 完整 BI / admin / analytics 后台

## 历史说明

仓库仍保留较多 v2/v3/v4 时代文档和兼容实现，用于迁移与考古。
它们默认不是当前真源。

判断 current vs archive 时，先看：

- `docs/README.md`
- `docs/product/README.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/API_CURRENT.md`
