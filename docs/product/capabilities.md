# Deep-Sea Nexus 能力地图与范围边界

Last updated: 2026-03-13

## 能力地图

当前产品能力可以分成五层。

### 1. Capture

负责把内容写进可持续记忆层：

- 摘要写入
- 文档写入
- 会话生命周期内的记忆沉淀
- 对旧写入入口的兼容承接

当前对应能力：

- sync compatibility API
- SmartContext summary ingestion
- 兼容脚本与批量脚本

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
- item/resource/category 结构
- 后续 TTL / archive / decay 的基础

当前对应能力：

- Memory v5 scoped layout
- SQLite-backed index

### 4. Context Governance

负责控制什么进入上下文、何时进入、进入多少：

- SmartContext inject
- ContextEngine budgeting
- summary / rescue / graph / decision 相关策略
- 与 execution-governor 的联动

### 5. Operate

负责验证、部署、巡检和回归：

- smoke
- benchmark
- local deploy
- doctor / health
- runtime artifact cleanup

## 当前 release 可以稳定承诺的内容

对当前仓库，产品文档可以稳定表达：

- 这是一个本地优先的 agent memory + context-governance 层
- 支持兼容 API、async runtime、Memory v5 三条使用路径
- 支持作用域隔离的 Memory v5
- 支持本地部署、巡检、smoke、benchmark
- 支持在旧工作流上做渐进迁移，而不是强制一次性重写

## 当前不要对外过度承诺的内容

以下能力即使 repo 里有片段、实验或历史文档，也不应当作为当前产品主叙事：

- 通用 SaaS 化托管能力
- 面向团队协作的完整产品面
- 成熟的多租户权限控制面
- 大而全的知识图谱产品化界面
- 复杂 BI / analytics / admin console

## 当前文档表达规则

### 产品层

可以讲：

- 用户问题
- 产品价值
- 能力边界
- 采用路径

不应展开：

- 每个模块文件名
- 历史实现分叉
- 低层 refactor 细节

### 技术层

应该讲：

- 模块
- API
- runtime layers
- current source of truth

对应文档：

- `../ARCHITECTURE_CURRENT.md`
- `../API_CURRENT.md`

### 运维层

应该讲：

- 部署
- 体检
- smoke
- benchmark
- 故障恢复

对应文档：

- `../LOCAL_DEPLOY.md`
- `../sop/*.md`

## 文档重写建议

如果后续继续整理，优先顺序应是：

1. 保持本目录稳定，先把产品层定住
2. 继续把 `README.md` 压回仓库总览，而不是产品 PRD
3. 让 `PRD.md`、`USAGE_GUIDE.md`、`architecture_v3.md` 明确变成历史参考
4. 把版本迭代史从产品叙事里继续剥离到历史文档或 changelog

