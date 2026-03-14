# Deep-Sea Nexus 产品路线图

Last updated: 2026-03-14

这不是逐 commit 的工程任务单，而是当前产品层的 `Now / Next / Later`
视图。

## Now

当前已经成型的产品形态：

- 本地优先的 agent memory + context-governance 层
- 兼容旧 sync API 的渐进接入
- Memory v5 scoped memory
- SmartContext / ContextEngine / hook 联动的上下文治理
- 本地 deploy / doctor / smoke / benchmark 运维链路

当前阶段最重要的目标：

- 把“能用”变成“可验证、可运营、可迁移”
- 把产品叙事、技术真源、运行治理真源分层稳定下来
- 把历史方案文档从 current narrative 中剥离出去

## Next

下一阶段建议聚焦四件事：

当前执行入口：

- `../exec-plans/2026-03-14-core-context-governance-polish.md`

### 1. 生命周期治理补齐

- 继续完善 Memory v5 的 TTL / decay / archive / audit 叙事
- 让“记忆对象化”从设计概念变成更明确的产品承诺
- 把 lifecycle audit / backfill / explicit archive 收束成稳定巡检入口，而不是散落脚本

### 2. 评测与证据产品化

- 把 benchmark、smoke、doctor 从工程脚本提升为标准采用路径
- 明确“用户如何知道记忆真的工作”
- 当前仓库内已具备 22-case recall/inject golden scorecard
  - 已覆盖 freshness conflict、cross-session drift、evidence-vs-replay conflict、
    contradictory constraints、no-scope recovery fallback
  - 现阶段还需要继续把 repo-local eval 扩成更完整的长会话生命周期评测

### 3. 上下文治理闭环继续收紧

- 持续强化 evidence-driven durable decision 规则
- 继续收束 SmartContext、ContextEngine、execution-governor 的边界
- 让 replay / rescue / evidence 指针更一致

### 4. 多作用域运维能力增强

- 更清晰的多 agent / 多用户视图
- 更可控的维护、巡检、审计路径

## Later

后续可以进入的方向：

- 更强的 category / graph explainability
- 更完整的 recall quality evaluation pack
  - current baseline now has a repo-local 22-case scorecard plus prompt budget metrics
- 更清晰的策略面与运行时面分层
- 更成熟的多 agent 运营视图

## 明确延后

以下内容不应在当前产品文档里提前承诺：

- 云托管服务化
- 团队协作产品面
- 通用知识平台化包装
- 大规模商业化 pricing / packaging 体系

## 与技术/历史文档的关系

- 当前系统结构：看 `../TECHNICAL_OVERVIEW_CURRENT.md`
- 当前实现细节：看 `../ARCHITECTURE_CURRENT.md`
- 当前 public API：看 `../API_CURRENT.md`
- Memory v5 历史设计节奏：看 `../SECOND_BRAIN_V5_PLAN.md`（archive reference）
