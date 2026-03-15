# OpenClaw Deep-Sea Nexus 能力地图与范围边界

Last updated: 2026-03-15

## GitHub 介绍页能力展示（v5.1）

仓库根目录 README 需要对外统一展示以下主能力：

- `Evidence-Gated Durable Memory`
  - durable memory 写入必须可追溯到 evidence，不接受“无证据摘要”。
- `Scoped Isolation`
  - `agent_id/user_id` 物理隔离 + `app_id/run_id/workspace` 记录级隔离。
- `Lifecycle Governance`
  - lifecycle audit、archive maintenance、backfill 与 report-first 运维闭环。
- `Context Governance Pipeline`
  - `recall / inject / compress / rescue / replay` 一体化治理。
- `Runtime + Compatibility`
  - 兼容 sync API、async runtime/plugin lifecycle、Memory v5 三条接入路径。
- `Operator Tooling`
  - deploy/doctor/smoke/benchmark/maintenance 全链路本地运维工具。

## 能力地图

当前 release 的产品能力分成五层。

### 1. Capture

负责把内容写进可持续记忆层：

- 摘要写入
- 文档写入
- 会话生命周期中的记忆沉淀
- 对旧写入入口的兼容承接

当前对应能力：

- sync compatibility API
- SmartContext summary ingestion
- 兼容脚本与批量写入脚本

### 2. Recall

负责把历史信息找回来：

- 向量召回
- 词法 fallback
- Memory v5 scoped recall
- 融合排序与结果解释

当前对应能力：

- `nexus_recall`
- `nexus_search`
- Memory v5 recall

### 3. Scope

负责把记忆隔离成可运营对象：

- `agent_id / user_id` scope
- `resource / item / category` 结构
- TTL / decay / archive 的当前治理基础
- lifecycle audit 与显式 archive 维护

当前对应能力：

- Memory v5 scoped layout
- SQLite-backed index
- Memory v5 lifecycle audit / explicit archive maintenance
- thresholded lifecycle status / alerts / hot-scope summaries
- optional per-kind lifecycle defaults for narrower retention tuning
- explicit archive-default backfill for older zero-valued rows
- explicit extended-scope selectors (`app/run/workspace`) across maintenance / backfill / benchmark tools

### 4. Context Governance

负责控制什么进入上下文、何时进入、进入多少：

- SmartContext inject
- ContextEngine budgeting
- summary / rescue / replay / evidence discipline
- evidence-gated durable decisions
- 与 OpenClaw hook 和 execution-governor 的联动

当前规则真源：

- `../sop/Context_Policy_v2_EventDriven.md`

### 5. Operate

负责验证、部署、巡检和回归：

- local deploy
- doctor / health
- smoke / benchmark
- runtime maintenance
- 回归验证

## 当前稳定承诺

对当前仓库，可以稳定表达的内容是：

- 这是一个本地优先的 agent memory + context-governance 层
- 支持兼容 API、async runtime、Memory v5 三条使用路径
- 支持 Memory v5 作用域隔离
- 支持 context-governed recall / inject / compress / rescue
- 支持本地 deploy / doctor / smoke / benchmark
- 支持在旧工作流上做渐进迁移，而不是强制一次性重写

## 当前能力边界

### 产品层可以明确承诺

- 记忆链路是可验证的
- 上下文治理有固定规则与真源
- 记忆隔离是当前系统的重要能力，不是实验特性
- 兼容接入仍然是当前产品设计的一部分
- 默认调参策略是 report-first，不做静默运行时漂移

### 产品层不应过度承诺

- 通用 SaaS 化托管能力
- 团队协作产品面
- 成熟的多租户权限控制面
- 图谱可视化产品界面
- 完整 BI / admin console

## 当前 release 的能力表达方式

### 产品文档应该讲

- 用户问题
- 产品价值
- 能力边界
- 当前承诺

### 技术文档应该讲

- 模块边界
- 运行时结构
- public interface
- current vs compatibility

对应文档：

- `../TECHNICAL_OVERVIEW_CURRENT.md`
- `../ARCHITECTURE_CURRENT.md`
- `../API_CURRENT.md`

### 运维文档应该讲

- 部署
- 体检
- smoke
- benchmark
- 故障恢复

对应文档：

- `../LOCAL_DEPLOY.md`
- `../sop/Context_Policy_v2_EventDriven.md`
- `../sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## 当前最关键的边界语句

后续所有产品与技术文档，都应保持以下表述一致：

- OpenClaw Deep-Sea Nexus 的核心功能是上下文治理驱动的长期记忆
- 所有记忆都应先经过上下文处理，而不是旁路直接沉淀
- durable memory 不接受“无证据的随意摘要”
- 历史兼容能力存在，但不是当前产品叙事中心
