# Deep-Sea Nexus 用户与用例

Last updated: 2026-03-14

## 主要用户画像

### 1. 工作流维护者

关心的问题：

- 当前记忆链路是否真的写入、召回、注入成功
- 升级后会不会打断现有自动化
- 多个 agent 是否会互相污染记忆
- 出问题时能不能快速巡检与回退

他们最常走的路径：

- `README.md`
- `docs/README.md`
- `docs/LOCAL_DEPLOY.md`
- `scripts/nexus_doctor_local.sh`

### 2. 集成开发者

关心的问题：

- 我应该接 sync API、async app，还是 Memory v5
- 旧代码是否还能继续工作
- 新功能应该接哪一层，避免绑定历史实现

他们最常走的路径：

- `docs/API_CURRENT.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`

### 3. 高强度个人用户 / 操作者

关心的问题：

- 长任务和跨天项目能否持续记住关键上下文
- 重要决策是否能被后续 agent 回忆出来
- 记忆是否能按 agent / user 作用域隔离

他们最常走的路径：

- `docs/product/positioning.md`
- `docs/product/capabilities.md`
- `docs/LOCAL_DEPLOY.md`

## 核心用例

### 用例 A: 为现有 agent 工作流补长期记忆

目标：

- 不重写旧脚本
- 先接入兼容 API
- 验证 recall / write / health 是否稳定

推荐入口：

- `nexus_init`
- `nexus_recall`
- `nexus_add`
- `manual_flush`
- `docs/API_CURRENT.md`

### 用例 B: 为多 agent / 多用户场景做记忆隔离

目标：

- 把不同 agent / user 的记忆物理隔离
- 降低跨会话、跨任务污染

推荐入口：

- `MemoryV5Service`
- `MemoryScope`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `scripts/memory_v5_smoke.py`

### 用例 C: 为长任务做上下文治理

目标：

- 控制上下文膨胀
- 让摘要、注入、召回有证据可追
- 把 recall 与 context policy 串成一个闭环

推荐入口：

- `docs/sop/Context_Policy_v2_EventDriven.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`

### 用例 D: 为本地工作区建立可运营记忆层

目标：

- 有 doctor / smoke / benchmark
- 有运维脚本
- 有 current source of truth 与 archive 的清晰分层

推荐入口：

- `docs/LOCAL_DEPLOY.md`
- `scripts/deploy_local_v5.sh`
- `scripts/nexus_doctor_local.sh`
- `scripts/memory_v5_benchmark.py`

## 采用路径

### 路径 1: Compatibility First

适合：

- 已有旧自动化
- 需要最小改动上线

从这里开始：

- `docs/API_CURRENT.md`
- `docs/LOCAL_DEPLOY.md`

### 路径 2: Runtime First

适合：

- 直接管理 app / plugin lifecycle
- 需要对 runtime 做更细粒度控制

从这里开始：

- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/API_CURRENT.md`

### 路径 3: Memory v5 First

适合：

- 重点是作用域隔离、对象化记忆、后续生命周期治理

从这里开始：

- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/API_CURRENT.md`
- `docs/product/capabilities.md`

设计补充参考：

- `docs/SECOND_BRAIN_V5_PLAN.md`（archive reference）

## 非目标用例

以下需求当前不适合用 Deep-Sea Nexus 作为主解：

- 团队级文档协作平台
- 远程托管知识服务
- 非本地、非 agent 工作流为中心的通用内容平台
