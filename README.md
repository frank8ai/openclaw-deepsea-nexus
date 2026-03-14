# 🧠 Deep-Sea Nexus v5.0.0

AI agent 的本地长期记忆与上下文治理层。

[English](README_EN.md) | [简体中文](README.md)

**版本**: `5.0.0`
**状态**: `v5.0.0` 正式版（official release）
**更新**: `2026-03-14`

## Comparison

**Beyond Context Management:** Deep-Sea Nexus 不是在重复做记忆框架，而是在补齐治理层（evidence gate、scope isolation、lifecycle governance、ops audit）。  
Read the technical manifesto: [`COMPARISON.md`](COMPARISON.md)

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

- `docs/releases/V5_0_0_OFFICIAL_2026-03-14.md`
- `docs/releases/V5_0_0_HOTFIX_1_2026-03-14.md`

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
- `scripts/nexus_doctor_local.sh`

## 当前稳定承诺

- 保持历史 sync API 的渐进兼容接入
- 提供 async runtime + plugin lifecycle
- 提供 Memory v5 scoped memory（`agent_id / user_id` 物理隔离 + `app_id / run_id / workspace` 记录级隔离）
- 提供 recall / inject / compress / rescue / replay 的上下文治理链路
- 提供本地 deploy / doctor / smoke / benchmark 运维路径

## 最小验证路径

```bash
python3 -m unittest tests.test_memory_v5 -v
python3 scripts/context_recall_scorecard.py --golden docs/evals/context_recall_golden_cases.json
python3 run_tests.py
bash scripts/nexus_doctor_local.sh --check --skip-deploy
python3 scripts/memory_v5_smoke.py
python3 scripts/memory_v5_maintenance.py --dry-run --write-report
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
  - `goal/status/constraints/blockers/decisions/next/questions/evidence/replay`
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
