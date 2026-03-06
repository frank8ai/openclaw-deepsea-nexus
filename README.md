# 🧠 Deep-Sea Nexus v5.0.0

## AI Agent 长期记忆系统 - 热插拔架构

**版本**: 5.0.0  
**状态**: ✅ 生产就绪  
**更新**: 2026-03-01

---

## ✨ 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| 🔌 **热插拔架构** | 动态插件加载/卸载 | ✅ |
| 📡 **事件驱动** | 解耦模块通信 | ✅ |
| 📦 **统一压缩** | 消除代码重复 | ✅ |
| 🔄 **100% 向后兼容** | 零破坏性变更 | ✅ |
| ⚡ **异步优先** | 非阻塞操作 | ✅ |
| 🔧 **热重载配置** | 无需重启更新配置 | ✅ |
| 🚀 **v3.2 分层加载** | Token 优化，成本降低 89% | 🆕 [增强] |
| 🧠 **结构化摘要 v2.0** | 9字段知识沉淀，让大脑更聪明 | 🆕 v3.1 |
| 🧩 **v4.0 智能记忆** | 可选真向量 + 召回去重 + 使用度提升 | 🆕 v4.0 |
| 🧠 **v4.1 组块联想** | 决策块图谱 + 关系注入 + 自我修正 | 🆕 v4.1 |
| 📈 **v4.1.1 可观测性** | 注入/摘要/抢救指标 + 自愈调参落盘 | 🆕 v4.1.1 |
| 🧭 **v4.2 PARA 二脑** | L0/L1/L2 目录递归检索 + Warm 自动写入 | 🆕 v4.2 |
| 🛡️ **v4.3 稳态升级** | 缺依赖降级可用 + 混合召回 + 门禁稳定绿灯 | 🆕 v4.3 |
| 🧠 **v4.4.0 智能上下文升级** | Pack/Card 模板 + 字段检查 + 安全 digest cron + 指标 schema 统一 | 🆕 v4.4.0 |
| 🧪 **v4.4.1 记忆契约运营化** | 契约审计分组覆盖率 + PARA 三维评分 + Warm 信号晋升 | 🆕 v4.4.1 |
| 🧠 **v5.0 记忆操作层** | memU 风格三层记忆 + 记忆对象化 + 作用域隔离 + RRF 融合召回 | 🆕 v5.0 |

> v5.0 迭代详见：`docs/SECOND_BRAIN_V5_PLAN.md`（本次新增）。
> v4.4.1 迭代详见：`docs/SOP_MEMORY_GAP_ITERATION_2026-02-23.md`、`docs/reports/2026-02-23-contract-audit.md`。
> v4.4.0 使用与验收详见：`docs/SMART_CONTEXT_V4_4_0.md`、`docs/SECOND_BRAIN_PARA.md`、`docs/USAGE_GUIDE.md` 与 `docs/LOCAL_DEPLOY.md`。

---

## ✅ 生产核验清单（2026-02）

用于确认“主库对接正确且正在工作”，避免只看配置不看实测。

### 1) 主库契约（Single Source of Truth）

- `NEXUS_VECTOR_DB=/Users/yizhi/.openclaw/workspace/memory/.vector_db_restored`
- `NEXUS_COLLECTION=deepsea_nexus_restored`

### 2) 一条命令做体检

```bash
bash scripts/nexus_doctor_local.sh --check --skip-deploy
```

通过标准：
- `pass>0` 且 `fail=0`
- `hook ready: context-optimizer`
- `hook ready: deepsea-rag-recall`
- `vector DB count (deepsea_nexus_restored): <正整数>`

### 3) 一条命令做写读 smoke

```bash
/Users/yizhi/.openclaw/workspace/.venv-nexus/bin/python3 \
  /Users/yizhi/.openclaw/workspace/skills/evolution-loop/scripts/smoke_chroma.py
```

通过标准：
- `ok: true`
- `collection: deepsea_nexus_restored`
- `write_read_probe: true`

### 4) 计数口径说明（为什么会变）

`collection_count` 会因以下行为小幅波动（通常 +1 / +2）：
- smoke/probe 写入验证 marker
- 新会话摘要或巡查脚本写入

这是预期行为，不代表写错库。核验应以“路径+集合+可写可读”为主，而不是某个固定数字。

### 5) 关键运行日志

- `~/.openclaw/workspace/logs/nexus_core_metrics.log`
- `~/.openclaw/workspace/logs/smart_context_metrics.log`

---

## 🧠 v5 运维脚本（新增）

- Smoke: `python3 scripts/memory_v5_smoke.py`
- Maintenance: `python3 scripts/memory_v5_maintenance.py --all-agents`
- Benchmark: `python3 scripts/memory_v5_benchmark.py --cases docs/memory_v5_benchmark_sample.json --all-agents`

建议观察是否持续出现 `recall` / `add_document` 事件，确认召回与写入链路都在运行。

---

## 🎯 核心功能详解

### 1. 语义搜索与 RAG 召回

Deep-Sea Nexus 的核心功能，提供语义级别的记忆检索。

```python
from deepsea_nexus import nexus_recall

# 语义搜索
results = nexus_recall("Python 装饰器使用方法", n=5)

# 结果包含:
# - relevance: 相关性分数 (0-1)
# - content: 内容片段
# - source: 来源标识
# - metadata: 元数据
for r in results:
    print(f"[{r.relevance:.2f}] {r.source}")
    print(f"   {r.content[:100]}...")
```

**特性**:
- ✅ 语义相似度匹配
- ✅ 增量索引更新
- ✅ 智能分块处理
- ✅ 结果相关性排序
- ✅ 缓存优化
- ✅ `chromadb` 缺失时自动降级（lexical fallback），不中断主流程

---

### 2. 长期记忆管理

会话生命周期管理，自动跟踪和管理 AI 记忆。

```python
from deepsea_nexus import start_session, close_session, get_session_manager

# 创建会话
session_id = start_session("Python 学习会话")

# 获取会话信息
session = get_session_manager().get_session(session_id)
print(f"主题: {session.topic}")
print(f"状态: {session.status}")
print(f"片段数: {session.chunk_count}")
print(f"金句数: {session.gold_count}")

# 关闭会话
close_session(session_id)
```

**功能**:
- 📝 自动会话创建
- 📊 活动追踪
- 🏷️ 标签管理
- 📈 统计信息
- 🔄 自动归档

---

### 5. 运行观测与自愈调参（v4.1.1）

SmartContext 会持续写入运行指标，便于判断“记忆是否真正命中”与“摘要是否可靠”。

**指标日志位置**:
```
/Users/yizhi/.openclaw/workspace/logs/smart_context_metrics.log
```

**记录事件**:
- `inject` / `graph_inject` / `inject_stats` / `inject_ratio_alert`
- `inject_auto_tune`（命中率过低时自动调参）
- `summary_ok` / `summary_fallback` / `summary_short`
- `context_status`（summary/compress 触发原因与 token 估算）
- `rescue_saved`（压缩前抢救计数）

**自动调参落盘**:
当命中率持续偏低，系统会降低阈值并增加注入条数，并写回 `config.json`（默认 60 秒批量写入）。

**硬规则（摘要与注入）**:
- 每轮对话结束都会写入一张“摘要卡”，固定字段模板，避免长对话丢关键事实。
- 话题切换时自动落盘“话题边界摘要”，避免跨主题污染。
- 召回只取 Top-K，并对每条内容做行数/长度裁剪，防止整篇笔记塞进上下文。

**摘要模板默认字段**:
`Summary / Decisions / Next / Questions / Entities / Keywords`

**注入预算（默认）**:
- 单条最多 8 行或 360 字符
- 单轮注入总行数最多 40 行

---

### 6. Context Engine 预算化注入（v4.1.3）

ContextEngine 统一拼装注入上下文，严格控制 token 预算：
1. NOW.md 抢救上下文（当前目标/下一步）
2. Recent Summary（近几轮摘要）
3. Recall Top-K（来源/相关性标注 + 截断）

**默认预算**（`config.json` -> `context_engine`）:
- `max_tokens`: 1000
- `max_items`: 4
- `max_chars_per_item`: 360
- `max_lines_total`: 40

**价值**:
- 只注入最短、最精确的上下文块
- 避免“整篇历史”进入 prompt
- 稳定降低 token 成本，同时提升可控性

---

### 7. Context Engine 指标与自适应（v4.1.4）

ContextEngine 会记录每次注入的预算消耗，并按窗口自动调参：

**指标日志**:
`/Users/yizhi/.openclaw/workspace/logs/context_engine_metrics.log`

**记录字段**:
- `context_build`: tokens/lines/items_used
- `context_stats`: 窗口内均值
- `context_auto_tune`: 自动调参记录

**自适应默认**（`config.json` -> `context_engine`）:
- `auto_tune_enabled`: true
- `auto_tune_target_tokens`: 800
- `auto_tune_min_items`: 2
- `auto_tune_max_items`: 6
- `persist_interval_sec`: 60

**价值**:
- 自动稳定在目标 token 预算
- 高峰期减少注入条数，避免成本爆炸
- 低负载期允许更多 recall 提升准确性


---

### 3. 自动Flush与清理

智能管理存储空间，自动清理过期数据。

```python
from deepsea_nexus import manual_flush

# 预览（不执行）
preview = manual_flush(dry_run=True)
print(f"将归档: {len(preview['sessions_to_archive'])} 个会话")

# 执行清理
results = manual_flush(dry_run=False)
print(f"已归档: {results['archived']}")
print(f"已压缩: {results['compressed']}")
print(f"已跳过: {results['skipped']}")
```

**策略**:
- ⏰ 每日定时执行
- 📅 30天不活跃自动归档
- 📦 归档保留90天
- 🗜️ 自动压缩节省空间
- 🔥 手动触发清理

---

### 4. 统一压缩引擎

消除代码重复，提供统一的压缩接口，支持多种算法。

```python
from deepsea_nexus import CompressionManager

# 创建压缩管理器
cm = CompressionManager("zstd")  # gzip, zstd, lz4

# 压缩/解压数据
compressed = cm.compress(data)
decompressed = cm.decompress(compressed)

# 文件操作
cm.compress_file("data.txt")      # data.txt.gz
cm.decompress_file("data.txt.gz")  # data.txt
```

**算法对比**:

| 算法 | 压缩率 | 速度 | 依赖 |
|------|--------|------|------|
| **gzip** | ⭐⭐⭐ | ⭐⭐⭐ | 内置 |
| **zstd** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | zstandard |
| **lz4** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | lz4 |

---

### 5. 事件驱动架构

模块间通过事件进行解耦通信。

```python
from deepsea_nexus import get_event_bus

event_bus = get_event_bus()

# 订阅事件
def on_search_completed(event):
    print(f"搜索完成: {event.data['query']}")
    print(f"结果数: {len(event.data['results'])}")

event_bus.subscribe("nexus.search.completed", on_search_completed)

# 发布事件
event_bus.publish("my.custom.event", {
    "action": "update",
    "data": {"key": "value"}
})
```

**可用事件**:
- `nexus.search.completed` - 搜索完成
- `nexus.document_added` - 文档添加
- `session.created` - 会话创建
- `session.closed` - 会话关闭
- `flush.completed` - 清理完成

---

### 6. 配置热重载

无需重启即可更新配置。

```python
from deepsea_nexus import get_config_manager

config = get_config_manager()

# 获取配置
base_path = config.get("base_path", "./memory")
archive_days = config.get("session.auto_archive_days", 30)

# 设置配置
config.set("custom.setting", "value")

# 监听配置变化
config.add_listener("session.auto_archive_days", lambda old, new: 
    print(f"从 {old} 变为 {new}")
)
```

**支持**:
- 📄 YAML/JSON 配置文件
- 🔄 环境变量覆盖
- 👂 配置变更监听
- ✅ 配置验证

---

### 7. 插件系统

可扩展的插件架构，动态加载/卸载功能模块。

```python
from deepsea_nexus.core.plugin_system import NexusPlugin, PluginMetadata

class AnalyticsPlugin(NexusPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="analytics",
            version="1.0.0",
            dependencies=["nexus_core"],
            hot_reloadable=True,
        )
    
    async def initialize(self, config):
        # 初始化
        return True
    
    async def start(self):
        # 启动服务
        return True
    
    async def stop(self):
        # 清理资源
        return True
```

**特性**:
- 🔌 动态加载/卸载
- 🔗 依赖自动解析
- 🏃 生命周期管理
- 🔥 热重载支持
- 🛡️ 隔离保护

---

### 8. 向后兼容层

100% 兼容 v2.x API，无需修改现有代码。

```python
# v2.x 代码 - 完全不变
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

nexus_init()
results = nexus_recall("query", n=5)
doc_id = nexus_add("content", "title", "tags")
stats = nexus_stats()
health = nexus_health()
```

**兼容函数**:
| 函数 | 描述 |
|------|------|
| `nexus_init()` | 初始化 |
| `nexus_recall()` | 语义搜索 |
| `nexus_add()` | 添加文档 |
| `nexus_stats()` | 获取统计 |
| `nexus_health()` | 健康检查 |
| `start_session()` | 创建会话 |
| `close_session()` | 关闭会话 |
| `manual_flush()` | 手动清理 |
| `nexus_compress_session()` | 压缩会话 |

---

## 🚀 快速开始

### 安装（本地）
> 当前版本为 v4.4.0，未发布到 PyPI。请使用源码安装。
```bash
git clone https://github.com/frank8ai/deepsea-nexus.git
cd deepsea-nexus
python -m pip install -r requirements.txt
```

### 本地部署（v4.4.0）
```bash
cd ~/.openclaw/workspace/skills/deepsea-nexus
bash scripts/deploy_local_v4.sh --full
```

默认智能上下文规则：
- 最近 `8` 轮保留原文
- `9-20` 轮按摘要保留
- `35` 轮后进入压缩阶段（压缩前抢救决策/下一步/阻塞）

### 单一真源（推荐）
为避免 `OpenClaw Hook` 与 `deepsea-nexus` 参数漂移，v4.4.0 起建议启用单一真源同步：

```bash
cd ~/.openclaw/workspace/skills/deepsea-nexus
python3 scripts/sync_openclaw_context_optimizer.py --apply
```

同步策略：
- 以 `config.json -> smart_context` 为主
- 自动生成 `~/.openclaw/state/context-optimizer-single-source.json`
- 自动修复 `~/.openclaw/hooks/context-optimizer/handler.js` 漂移（例如升级后被覆盖）

参数映射：
- `smart_context.full_rounds -> preserveRecent`
- `smart_context.summary_rounds -> compressionThreshold`
- `smart_context.full_tokens_max -> tokenTriggerEstimate`

### OpenClaw Hook 快速接入（推荐）
```bash
# 推荐指定 Python（可选，不指定时会自动解析）
export NEXUS_PYTHON_PATH="$HOME/miniconda3/envs/openclaw-nexus/bin/python"

# 检查 Hook 状态
openclaw hooks list
openclaw hooks info context-optimizer
openclaw hooks info deepsea-rag-recall
```

建议的 OpenClaw 联动：
- 开启 `context-optimizer`（输入前做分层压缩）
- 开启 `deepsea-rag-recall`（统一管理入口，避免 legacy workspace hook 漂移）

### 运行指标看板（低成本可观测）
```bash
python3 scripts/context_metrics_dashboard.py --window 200 --output ~/.openclaw/workspace/logs/context_metrics_report.md
```

### Control UI 指标图表（网关内置 Canvas）
```bash
python3 scripts/context_metrics_export.py --window 200 --write-html
# 打开：
# http://127.0.0.1:18789/__openclaw__/canvas/context-metrics.html
```

### 自动刷新（每 5 分钟）
```bash
*/5 * * * * $HOME/.openclaw/workspace/.venv-nexus/bin/python3 \
  $HOME/.openclaw/workspace/skills/deepsea-nexus/scripts/context_metrics_export.py --window 200 --write-html
```

### 低成本模型路由（建议）
```bash
python3 scripts/model_router.py --text "这里是一段简单问题"
```

### 最小示例
```python
from deepsea_nexus import nexus_init, nexus_recall

# 初始化
nexus_init()

# 添加记忆
from deepsea_nexus import nexus_add
nexus_add("Python 装饰器是函数的高阶用法", "Python Decorator", "python,decorator")

# 搜索记忆
results = nexus_recall("Python 装饰器", n=3)
for r in results:
    print(f"[{r.relevance:.2f}] {r.content}")
```

### v4.0 新特性说明
- 可选真向量（sentence-transformers）与自动回退
- 使用度驱动的召回排序 + 去重
- 分层召回 + 新颖度闸门（防止历史噪声）
- 主题块/决策块优先级注入（信号更强、噪声更少）
- 动态 Top-K 门控（低信号自动降注入，高信号适度提升）

### 新 API 示例
```python
import asyncio
from deepsea_nexus import create_app

async def main():
    app = create_app()
    
    await app.initialize()
    await app.start()
    
    # 使用插件
    nexus = app.plugins["nexus_core"]
    
    # 添加文档
    await nexus.add_document(
        content="异步编程是 Python 的强大特性",
        title="Async Python",
        tags="python,async"
    )
    
    # 搜索
    results = await nexus.search_recall("Python 异步", n=5)
    
    await app.stop()

asyncio.run(main())
```

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| ⚡ **启动时间** | < 2s | 最小配置 |
| 🔍 **搜索延迟** | < 10ms | 缓存命中 |
| 📝 **添加速度** | 50+/秒 | 批量优化 |
| 🗜️ **压缩速度** | 300MB/s | LZ4 算法 |
| 💾 **内存占用** | -40% | 优化后 |
| 🔄 **并发操作** | 1000+ | 异步支持 |

---

## 📁 项目结构

```
deepsea-nexus/
├── 📄 __init__.py          # 统一入口
├── 📄 app.py               # 主应用
├── 📄 compat.py            # 兼容层
├── 📁 core/
│   ├── 📄 plugin_system.py # 插件系统
│   ├── 📄 event_bus.py     # 事件总线
│   └── 📄 config_manager.py # 配置管理
├── 📁 plugins/
│   ├── 📄 nexus_core.py    # 语义搜索
│   ├── 📄 session_manager.py # 会话管理
│   └── 📄 flush_manager.py  # 清理管理
├── 📁 storage/
│   ├── 📄 base.py          # 抽象基类
│   └── 📄 compression.py   # 统一压缩
├── 📁 tests/
│   ├── 📄 test_units.py    # 单元测试
│   ├── 📄 test_integration.py # 集成测试
│   └── 📄 test_performance.py # 性能测试
└── 📁 docs/
    ├── 📄 architecture_v3.md # 架构文档
    └── 📄 examples_v3.md    # 使用示例
```

---

## 🔧 配置示例

```yaml
# config.yaml
base_path: ./memory

nexus:
  vector_db_path: ./vector_db
  embedder_name: all-MiniLM-L6-v2

session:
  auto_archive_days: 30
  min_chunks_to_archive: 5

flush:
  enabled: true
  archive_time: "03:00"
  compress_enabled: true
  compress_algorithm: "zstd"
  keep_archived_days: 90

compression:
  default_algorithm: "zstd"
  supported_algorithms:
    - gzip
    - zstd
    - lz4
```

---

## 🚀 v3.2 分层加载增强 (Token 优化)

v3.2 是 v3.1 的功能增强版本，新增**分层加载架构**，在保证 100% 向后兼容的前提下，实现 Token 成本降低 89%。

### 性能对比

| 指标 | v3.1 | v3.2 增强 | 提升 |
|------|------|-----------|------|
| 启动 Token | 9,552 | 1,015 | **-89%** |
| 启动时间 | 200ms | 50ms | **-75%** |
| 内存占用 | 基准 | -60% | **显著降低** |
| 功能完整性 | 100% | 100% | **完全兼容** |

### 使用方式

**方式 1: 原有 API (继续兼容)**
```python
from deepsea_nexus import nexus_recall
results = nexus_recall("Python 装饰器")
```

**方式 2: v3.2 分层加载 (高频场景推荐)**
```python
from v3_2_enhancement.v3_2_core.nexus_v3 import Nexus
nexus = Nexus()  # 仅加载 1K tokens，启动更快
results = nexus.recall("Python 装饰器")  # 按需加载
```

### 运行测试

```bash
# 测试 v3.2 分层加载
python3 v3_2_enhancement/run.py --demo
```

查看完整文档: [v3_2_enhancement/README_V3_2.md](v3_2_enhancement/README_V3_2.md)

---

## 📝 更新日志

### v4.4.0 (2026-02-18)
- 新增 Deep Research Pack/Card 模板（`resources/sop/TEMPLATE.deep-research-*.md`）
- 新增工件严格校验脚本（`scripts/validate_research_artifacts.py`）
- 新增 Smart Context digest 报告脚本（`scripts/smart_context_digest.py`）
- 新增安全 cron 安装脚本（`scripts/install_safe_cron.sh`，仅报告与本地沉淀）
- 新增向量库维护脚本（快照/健康检查）：`scripts/vector_db_snapshot.py`、`scripts/vector_db_healthcheck.py`、`scripts/install_vector_db_maintenance_cron.sh`
- 指标 schema 统一到 4.4.0（`smart_context` / `context_engine` / `nexus_core`）

### v4.3.0 (2026-02-18)
- 缺少 `chromadb` 时，`nexus_core` 自动降级到可运行模式（不阻塞 `nexus_init`）
- 新增混合召回：向量召回不足时自动 lexical 补全（并保留 brain merge）
- `PluginRegistry` 兼容 Python 3.8 事件循环锁初始化路径
- `run_tests.py` 增加运行时能力探测与导入稳健化
- 新增本地部署脚本与部署文档（`scripts/deploy_local_v4.sh`、`docs/LOCAL_DEPLOY.md`）

### v4.1.0 (2026-02-16)
- Light knowledge graph for decision blocks (SQLite)
- Graph + vector hybrid recall injection
- Adaptive inject tuning (self-correcting threshold)

### v4.0.0 (2026-02-16)
- Optional real embeddings with safe fallback
- Usage-aware recall ranking + dedupe
- Tiered recall + novelty gate
- Async-core compat sync bridge

### v3.2.0 (2026-02-13)
**新增分层加载架构**:
- 🎯 System Prompt 分层加载（常驻层 + 按需层）
- 🔥 智能热加载 + LRU 缓存
- 📝 自研 SimpleYAML 解析器，零外部依赖
- 📊 Token 成本降低 89%（9.5K → 1K）
- ⚡ 启动时间减少 75%

### v3.1.0 (2026-02-13)

**架构升级**:
- 🔌 热插拔插件系统
- 📡 事件驱动通信
- 📦 统一压缩引擎
- 🔄 100% 向后兼容
- ⚡ 异步优先设计
- 🔧 配置热重载

**性能优化**:
- 2x 压缩速度提升
- 3x 事件处理提升
- 40% 内存降低
- 更好的并发支持

**新增功能**:
- 动态插件加载
- 高级压缩选项 (zstd, lz4)
- 改进会话管理
- 增强错误处理

---

## 📄 许可证

MIT License

---

## 👨‍💻 作者

Deep-Sea Nexus Team

---

## 🔗 链接

- 💻 **GitHub**: [frank8ai/deepsea-nexus](https://github.com/frank8ai/deepsea-nexus)
- 🐛 **Issues**: [Issues](https://github.com/frank8ai/deepsea-nexus/issues)

---

*让 AI 记住一切 - 智能、持久、可扩展*
