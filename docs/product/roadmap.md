# Deep-Sea Nexus 产品路线图

Last updated: 2026-03-13

这不是逐 commit 的工程任务单，而是产品层的 `Now / Next / Later` 视图。

## Now

当前可对齐的产品形态：

- 本地优先的 agent memory + context-governance 层
- 兼容旧 sync API 的渐进接入
- Memory v5 scoped memory
- SmartContext / ContextEngine 相关上下文治理
- 本地 deploy / doctor / smoke / benchmark 运维链路

当前阶段最重要的产品目标：

- 把“能用”变成“可验证、可运营、可迁移”
- 把产品叙事从历史版本堆叠里抽离出来

## Next

下一阶段建议聚焦四件事：

### 1. 产品文档收束

- 让 `docs/product/` 成为稳定产品层真源
- 把 root README 继续压缩成仓库入口而不是全量产品叙事
- 给剩余历史文档持续补 `reference-only` / `historical` 边界

### 2. 生命周期治理补齐

- 继续完善 Memory v5 的 TTL / archive / decay / audit 叙事
- 让“记忆对象化”不只停留在设计名词，而是成为产品承诺的一部分

### 3. 评测与证据产品化

- 把 benchmark、smoke、doctor 从工程脚本上升为标准采用路径
- 明确“用户如何知道记忆真的工作”

### 4. 上下文治理表达收束

- 把 SmartContext、ContextEngine、Execution Governor 的关系讲清楚
- 区分“当前稳定能力”和“仍在重构中的实现细节”

## Later

后续可以进入的方向：

- 更强的 category / graph explainability
- 更清晰的多 agent / 多用户运营视图
- 更成熟的 recall quality evaluation pack
- 更清晰的策略面与运行时面分层

## 明确延后

以下不应在当前产品文档里提前承诺：

- 云托管服务化
- 团队协作产品面
- 通用知识平台化包装
- 大规模商业化 pricing / packaging 体系

## 与工程计划的关系

- 产品路线图：看本文
- Memory v5 设计/落地节奏：看 `../SECOND_BRAIN_V5_PLAN.md`
- 当前实现状态：看 `../ARCHITECTURE_CURRENT.md`
- 当前 API 能力：看 `../API_CURRENT.md`

