# 🧠 Deep-Sea Nexus v5.0.0

AI agent 的本地长期记忆与上下文治理层。

[English](README_EN.md) | [简体中文](README.md)

**版本**: `5.0.0`
**状态**: 当前可用仓库版本
**更新**: `2026-03-14`

## 这是什么

Deep-Sea Nexus 是一个面向 agent 工作流的 `memory + context governance`
能力层，用来解决：

- 重要决策只存在当前上下文里，跨会话后丢失
- 长任务上下文越滚越大，成本和噪音失控
- 多个 agent / user 共用记忆时容易串数据
- 旧自动化迁移成本高，无法一次性重写
- 记忆链路是否真的工作，缺少 smoke / doctor / benchmark 证据

当前产品定位与范围边界请看：

- `docs/product/README.md`
- `docs/product/positioning.md`
- `docs/product/capabilities.md`

## 从哪里开始

### 1. 看产品

如果你想先理解这是什么产品、给谁用、当前承诺什么：

- `docs/product/README.md`
- `docs/product/positioning.md`
- `docs/product/users-and-use-cases.md`
- `docs/product/roadmap.md`

### 2. 做集成

如果你要接 API 或理解当前实现：

- `docs/API_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/sop/Context_Policy_v2_EventDriven.md`

### 3. 做部署和巡检

如果你要确认本地运行、部署、体检和 smoke：

- `docs/LOCAL_DEPLOY.md`
- `scripts/deploy_local_v5.sh`
- `scripts/nexus_doctor_local.sh`

### 4. 查历史

如果你在排查老脚本、旧设计或历史决策：

- `docs/README.md`
  - 其中 `Historical Or Reference-Only Docs` 已列出主要历史文档

## 当前稳定能力

- 兼容历史 sync API 的渐进接入
- async runtime + plugin lifecycle
- Memory v5 scoped memory（`agent_id / user_id` 隔离）
- recall / summary / inject 相关上下文治理
- 本地 deploy / doctor / smoke / benchmark 运维链路

## 三条主要使用路径

### Compatibility First

适合已有旧自动化、希望最小改动接入：

```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

nexus_init()
hits = nexus_recall("what did we decide?", n=5)
nexus_add("We kept FastAPI.", "Decision", "architecture")
```

### Runtime First

适合直接管理 app / plugin lifecycle：

```python
from deepsea_nexus import create_app

app = create_app()
await app.initialize()
await app.start()
hits = await app.plugins["nexus_core"].search_recall("decision", n=5)
await app.stop()
```

### Memory v5 First

适合作用域隔离和对象化记忆场景：

```python
from deepsea_nexus import MemoryScope, MemoryV5Service

service = MemoryV5Service({"memory_v5": {"enabled": True, "async_ingest": False}})
scope = MemoryScope(agent_id="main", user_id="default")
service.ingest_document(
    title="Decision",
    content="We kept FastAPI for the control plane.",
    tags=["architecture"],
    scope=scope,
)
```

## 最小验证路径

```bash
python3 tests/test_memory_v5.py -v
python3 run_tests.py
bash scripts/nexus_doctor_local.sh --check --skip-deploy
python3 scripts/memory_v5_smoke.py
```

更完整的部署与运行时验证说明：

- `docs/LOCAL_DEPLOY.md`
- `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## 当前文档分层

- 产品真源:
  - `docs/product/README.md`
  - `docs/product/positioning.md`
  - `docs/product/users-and-use-cases.md`
  - `docs/product/capabilities.md`
  - `docs/product/roadmap.md`
- 技术真源:
  - `docs/ARCHITECTURE_CURRENT.md`
  - `docs/API_CURRENT.md`
- 运维真源:
  - `docs/LOCAL_DEPLOY.md`
  - `docs/sop/Context_Policy_v2_EventDriven.md`
  - `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`
  - `docs/sop/SmartContext_Daily_Tuning_and_RCA_2026-02-28.md`
- 历史/参考:
  - `DOCUMENTATION.md`
  - `AUTO_SUMMARY_INTEGRATION.md`
  - `SOP_INDEX.md`
  - `CHANGELOG.md`
  - `benchmark.txt`
  - `docs/PRD.md`
  - `docs/USAGE_GUIDE.md`
  - `docs/architecture_v3.md`

## 仓库入口清单

- 文档总入口: `docs/README.md`
- 当前产品文档: `docs/product/README.md`
- 当前架构/API: `docs/ARCHITECTURE_CURRENT.md`, `docs/API_CURRENT.md`
- 当前部署入口: `scripts/deploy_local_v5.sh`
- 当前体检入口: `scripts/nexus_doctor_local.sh`
- 当前 smoke/benchmark:
  - `scripts/memory_v5_smoke.py`
  - `scripts/memory_v5_benchmark.py`

## 非目标

当前不要把这个仓库理解成：

- 通用 SaaS 知识库产品
- 团队协作内容平台
- 云托管多租户记忆服务
- 完整 BI / analytics 后台

## 历史说明

这个仓库保留了较多 v2/v3/v4 时代的兼容实现、运维脚本和文档。保留它们的目的是
降低迁移成本，不代表它们仍然是当前真源。

需要分辨当前与历史时，先看：

- `docs/README.md`
- `docs/product/README.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/API_CURRENT.md`
