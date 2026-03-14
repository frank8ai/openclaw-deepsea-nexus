# OpenClaw Deep-Sea Nexus 产品文档总览

Last updated: 2026-03-14

本目录是当前 `v5.0.1` release pack 的产品层真源。

当前发布状态：

- `v5.0.1` patch release
- 发布说明：
  - `../releases/V5_0_1_PATCH_2026-03-14.md`
  - `../releases/V5_0_0_OFFICIAL_2026-03-14.md`（official baseline）

它只回答四个问题：

- 这是什么产品
- 给谁用
- 当前稳定承诺什么
- 接下来往哪里演进

## 当前产品定义

OpenClaw Deep-Sea Nexus 是一个本地优先的 agent memory + context governance 层。

它的核心主张不是“无限保存原始上下文”，而是：

- 所有记忆都先经过上下文治理
- 只有重要且可追溯的信息进入 durable memory
- recall / inject / compress / rescue / replay 构成一个可验证闭环

## 阅读顺序

1. `positioning.md`
2. `capabilities.md`
3. `users-and-use-cases.md`
4. `roadmap.md`

## 产品文档与其他文档的边界

### 产品文档负责

- 产品定义
- 用户问题
- 能力边界
- 当前承诺
- 路线图

### 技术文档负责

- 当前系统如何组织
- public interface 是什么
- current runtime 与 compatibility/legacy 的边界

技术真源：

- `../TECHNICAL_OVERVIEW_CURRENT.md`
- `../ARCHITECTURE_CURRENT.md`
- `../API_CURRENT.md`

### 运行与治理文档负责

- 部署
- 巡检
- smoke / benchmark / doctor
- 上下文治理规则与运行联动

运维与治理真源：

- `../LOCAL_DEPLOY.md`
- `../sop/Context_Policy_v2_EventDriven.md`
- `../sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## 当前产品文档结构

- `positioning.md`
  - 一句话定位、核心命题、非目标
- `capabilities.md`
  - 能力地图、稳定承诺、当前边界
- `users-and-use-cases.md`
  - 主要用户、典型用例、采用路径
- `roadmap.md`
  - `Now / Next / Later`

## 英文文档策略

当前英文文档只保留最小入口，不作为详细真源：

- `README_EN.md`

如需详细 current docs，请回到中文主文档。

## 历史文档边界

以下文档保留归档/考古价值，但不是当前产品真源：

- `../PRD.md`
- `../SECOND_BRAIN_V5_PLAN.md`
- `../USAGE_GUIDE.md`
- `../SMART_CONTEXT_V4_4_0.md`

## 维护规则

- 产品定位或边界变化：先改本目录
- 当前系统结构变化：改 `../TECHNICAL_OVERVIEW_CURRENT.md` 和 `../ARCHITECTURE_CURRENT.md`
- public API 变化：改 `../API_CURRENT.md`
- 上下文治理规则变化：改 `../sop/Context_Policy_v2_EventDriven.md`
- 部署和运维路径变化：改 `../LOCAL_DEPLOY.md`
