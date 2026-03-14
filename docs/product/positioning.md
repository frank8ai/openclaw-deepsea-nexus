# OpenClaw Deep-Sea Nexus 产品定位

Last updated: 2026-03-14

## 一句话

OpenClaw Deep-Sea Nexus 是一个本地优先的 agent memory + context governance 层，
用于让 Codex、OpenClaw 及类似工作流中的 agent 在长任务、多轮对话、
多 agent / 多用户场景下保持可追溯、可隔离、可运营的记忆连续性。

## 核心命题

OpenClaw Deep-Sea Nexus 的核心命题是：

- 记忆不是“无限堆原始上下文”
- 记忆必须先经过上下文治理
- durable memory 必须带结构和证据，而不是随意摘要

因此，它要解决的不是“保存更多文本”，而是“让 agent 在长期工作中持续带着对
的背景继续工作”。

## 它解决什么问题

没有 OpenClaw Deep-Sea Nexus 时，agent 工作流常见问题是：

- 重要决策只存在聊天上下文里，跨会话后丢失
- 长任务上下文越滚越大，成本和噪音一起上升
- 多个 agent 或多个用户共用记忆时容易串数据
- 记忆是否真的被写入、召回、注入、压缩，缺少可验证证据
- 旧自动化脚本很多，重写成本高，迁移风险大

## 当前产品形态

当前 OpenClaw Deep-Sea Nexus 不是一个托管 SaaS，而是一个 repo-local /
workspace-local 的能力层，主要以以下形式存在：

- Python 包根 API
- async runtime + plugin lifecycle
- Memory v5 scoped memory
- SmartContext / ContextEngine / OpenClaw hook 集成
- doctor / smoke / benchmark / maintenance 工具链

## 目标用户

当前主要服务三类用户：

### 1. 工作流维护者

需要确保：

- 记忆链路真的工作
- 升级不打断旧自动化
- 多 agent / 多用户不串记忆
- 出问题时可巡检、可验证、可回退

### 2. 集成开发者

需要决定：

- 该接 sync API、async runtime，还是 Memory v5
- 新功能该接哪一层，避免绑死历史实现

### 3. 高强度个人用户

需要：

- 长任务和跨天项目能持续记住关键上下文
- 重要决策能被后续 agent 回忆出来
- 记忆按 agent / user 作用域隔离

## 核心价值主张

- `可持续记忆`
  - 让重要决策、摘要、知识对象进入持久层，而不只存在于当前 prompt
- `可控上下文`
  - 让 recall / inject / compress / rescue 有预算、有规则、有观测
- `可演进接入`
  - 兼容历史 sync API，允许旧工作流渐进迁移
- `可隔离运营`
  - 通过 Memory v5 的 `agent_id / user_id` scope 做物理隔离
- `可验证运行`
  - 通过 doctor、smoke、benchmark、metrics 验证记忆链路是否真的工作

## 当前不做什么

以下内容不应被当成当前产品承诺：

- 通用企业知识库或团队 Wiki 平台
- 云托管多租户记忆服务
- 远程协作内容管理系统
- 完整 BI / analytics / admin 产品面
- 面向任意 agent 平台的零配置 SaaS 服务

## 关系图

- 想知道当前承诺什么：看 `capabilities.md`
- 想知道适合谁、怎么用：看 `users-and-use-cases.md`
- 想知道接下来怎么演进：看 `roadmap.md`
- 想知道当前技术结构：看 `../TECHNICAL_OVERVIEW_CURRENT.md`
