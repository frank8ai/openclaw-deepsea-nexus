# Deep-Sea Nexus 产品定位

Last updated: 2026-03-13

## 一句话

Deep-Sea Nexus 是一个本地优先的 Agent Memory + Context Governance 层，
用来让 Codex、OpenClaw 及类似工作流中的 agent 在长任务、多轮对话、多
agent/多用户场景下保持可追溯、可隔离、可运营的长期记忆能力。

## 它解决什么问题

没有 Deep-Sea Nexus 时，agent 工作流常见问题是：

- 重要决策只存在聊天上下文里，跨会话后丢失
- 长任务上下文越滚越大，成本和噪音一起上升
- 多个 agent 或多个用户共用记忆时容易串数据
- 记忆是否真的被写入、召回、注入，缺少可验证证据
- 旧自动化脚本很多，重写成本高，迁移风险大

Deep-Sea Nexus 的目标不是“再做一个聊天记录器”，而是把记忆从隐式上下文
变成可管理的运行时能力。

## 目标用户

当前主要服务三类用户：

1. Agent 工作流维护者
   - 需要让本地 agent 系统稳定拥有长期记忆和上下文治理能力
2. 集成开发者
   - 需要在不打断旧脚本的前提下接入新记忆能力
3. 高强度个人用户
   - 需要让个人长期项目、决策、摘要和上下文跨会话延续

## 核心价值主张

- `可持续记忆`
  - 让重要决策、摘要、知识对象进入持久层，而不只存在于当前 prompt
- `可控上下文`
  - 让 recall / inject / summary 不只是“能用”，而是有预算、有策略、有观测
- `可演进接入`
  - 兼容历史 sync API，允许旧工作流渐进迁移
- `可隔离运营`
  - 通过 Memory v5 的 `agent_id / user_id` scope 做物理隔离
- `可验证运行`
  - 通过 smoke、doctor、benchmark、metrics 验证记忆链路是否真的工作

## 当前产品形态

当前 Deep-Sea Nexus 不是一个托管 SaaS，而是一个 repo-local /
workspace-local 的能力层，主要以以下方式存在：

- Python 包根 API
- OpenClaw/Codex 工作流中的本地记忆与上下文治理组件
- 运维脚本、巡检脚本、benchmark 与 smoke 工具集

## 当前不做什么

以下内容不应被当成当前产品承诺：

- 通用企业知识库或团队 Wiki 平台
- 云托管多租户记忆服务
- 完整 BI / analytics 平台
- 远程协作内容管理系统
- 与任意 agent 平台零配置即插即用的通用 SaaS 产品

## 与其他文档的关系

- 想知道当前产品能承诺什么：看 `capabilities.md`
- 想知道适合谁、怎么用：看 `users-and-use-cases.md`
- 想知道接下来怎么演进：看 `roadmap.md`
- 想知道当前实现细节：看 `../ARCHITECTURE_CURRENT.md`

