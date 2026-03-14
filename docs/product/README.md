# Deep-Sea Nexus 产品文档总览

Last updated: 2026-03-14

本目录是当前仓库的产品层文档真源，回答四个问题：

- 这是什么产品
- 给谁用
- 当前能稳定承诺什么
- 接下来怎么演进

英文入口：

- `README_EN.md`

如果你要理解 Deep-Sea Nexus 的产品形态，请先读这里，而不是从历史 PRD
或单个技术实现文档开始。

## 推荐阅读顺序

1. `positioning.md`
2. `users-and-use-cases.md`
3. `capabilities.md`
4. `roadmap.md`

## 文档边界

产品文档负责回答：

- `what`: 产品是什么
- `why`: 为什么存在
- `who`: 目标用户是谁
- `scope`: 当前承诺与非目标

技术文档负责回答：

- `how`: 当前实现与接口如何工作
- `where`: 当前运行时入口、模块、配置与验证方式

对应技术真源：

- `../ARCHITECTURE_CURRENT.md`
- `../API_CURRENT.md`

运维文档负责回答：

- 如何部署
- 如何巡检
- 如何验证运行时健康

对应运维真源：

- `../LOCAL_DEPLOY.md`
- `../sop/Context_Policy_v2_EventDriven.md`
- `../sop/Execution_Governor_Context_Management_v1.3_Integration.md`
- `../sop/SmartContext_Daily_Tuning_and_RCA_2026-02-28.md`

## 当前产品文档结构

- `positioning.md`
  - 一句话定位、目标用户、价值主张、非目标
- `users-and-use-cases.md`
  - 典型用户、核心任务、采用路径
- `capabilities.md`
  - 能力地图、当前 release scope、对外表达边界
- `roadmap.md`
  - `Now / Next / Later` 演进路线

## 旧文档映射

- `../README.md`
  - 仓库总览与入口，不再承担完整产品叙事
- `../README_EN.md`
  - 英文仓库总览，不再承担完整产品叙事
- `../PRD.md`
  - v2 历史 PRD，保留归档价值，不是当前产品真源
- `../SECOND_BRAIN_V5_PLAN.md`
  - Memory v5 设计/实现计划，不是完整产品文档
- `../USAGE_GUIDE.md`
  - 历史兼容用法文档，不是当前产品叙事

## 维护规则

- 产品定位、目标用户、范围边界变化时，优先更新本目录
- 接口变化，优先更新 `../API_CURRENT.md`
- 运行时实现变化，优先更新 `../ARCHITECTURE_CURRENT.md`
- 上下文治理规则变化，优先更新 `../sop/Context_Policy_v2_EventDriven.md`
- 巡检/部署流程变化，优先更新 `../LOCAL_DEPLOY.md`
