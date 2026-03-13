# Deep-Sea Nexus 使用指南（历史兼容版）

> 状态：本文保留较多 v2/v4 时代的兼容说明，已不再是 v5 当前真源。
> 当前文档请优先看：`README.md`、`README_EN.md`、`docs/ARCHITECTURE_CURRENT.md`、`docs/API_CURRENT.md`。
> 本地部署流程见：`docs/LOCAL_DEPLOY.md`。

## 目录

- [系统概述](#系统概述)
- [安装步骤](#安装步骤)
- [使用方法](#使用方法)
- [API 用法示例](#api-用法示例)
- [常见问题](#常见问题)

---

## 系统概述

Deep-Sea Nexus v2.0 是一个专为 AI Agent 设计的长期记忆系统，采用向量存储和语义搜索技术。

### 核心特性

| 特性 | 指标 | 说明 |
|------|------|------|
| 启动加载 | < 300 tokens | 只读索引 |
| 每轮对话 | < 1000 tokens | 按需加载 |
| 召回延迟 | < 100ms | 关键词搜索 |
| 零依赖 | 纯 Python | 核心标准库实现（可选组件自动降级） |

### 技术架构

- **向量数据库**: ChromaDB (本地持久化)
- **嵌入模型**: sentence-transformers/all-MiniLM-L6-v2
- **文本切片**: 智能语义分块 (chunk_size=1000, overlap=100)
- **搜索方式**: 余弦相似度检索

---

## 安装步骤

### 1. 环境要求

```bash
Python 3.8+
pip3
```

### 2. 安装依赖

```bash
cd ~/.openclaw/workspace/skills/deepsea-nexus
pip3 install -r requirements.txt
```

> 说明：`DEEP_SEA_NEXUS_V2` 为历史目录名，当前项目位于 `~/.openclaw/workspace/skills/deepsea-nexus`；插件系统优先使用 `OPENCLAW_WORKSPACE`。

### 3. 依赖列表

```txt
chromadb>=0.4.0
sentence-transformers>=2.2.0
python-dotenv>=1.0.0
pyyaml>=6.0
tqdm>=4.65.0
```

### 4. 配置说明

编辑 `config.json`（推荐）或 `config.yaml`（legacy）：

```json
{
  "vector_store": {
    "persist_directory": "../memory/.vector_db",
    "collection_name": "deep_sea_nexus_notes",
    "distance_metric": "cosine"
  },
  "embedding": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384
  },
  "brain": {
    "scorer_type": "keyword"
  },
  "chunking": {
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "min_chunk_size": 10
  },
  "rag": {
    "top_k": 5,
    "similarity_threshold": 0.5
  }
}
```

---

## 使用方法

### CLI 命令

当前推荐 CLI 入口：

```bash
python3 __main__.py version --json
python3 __main__.py health --json
python3 __main__.py recall "列表" -n 5 --json
```

维护旧文件布局时，继续使用脚本入口：

```bash
python3 scripts/daily_flush.py --once
python3 scripts/index_rebuild.py --all
python3 scripts/session_split.py --scan
```

> `src/nexus_core.py` 现仅保留为历史实现快照，不建议新接入继续依赖。

### 批量索引工具

#### 索引 Obsidian 笔记

```bash
cd scripts
python batch_chunk.py ../Obsidian --chunk-size 1000 --overlap 100 --strategy hybrid
```

#### 索引单个文件

```bash
python batch_chunk.py /path/to/file.md --strategy hybrid
```

#### 重置索引

```bash
python batch_chunk.py ../Obsidian --reset
```

#### 查看索引统计

```bash
python batch_chunk.py --stats
```

---

## 第二大脑 PARA（v4.4.0）

### 初始化 PARA 目录

```bash
python scripts/para_init.py --obsidian ~/Obsidian
```

### 会话摘要写入 Warm

```bash
python scripts/warm_writer.py --from ~/.openclaw/logs/summaries/xxx.json
```

### 目录递归检索（项目优先）

```bash
python scripts/para_recall.py --query "故障转移系统" --top-projects 3
```

### OpenClaw Compaction 审计（系统级）

```bash
python scripts/openclaw_compaction_audit.py
```

### Smart Context 工件模板与检查（v4.4.0）

```bash
# 1) 拷贝模板
cp resources/sop/TEMPLATE.deep-research-pack.md SOP/research/$(date +%F)/<topic>-deep-research-pack.md
cp resources/sop/TEMPLATE.deep-research-card.md 90_Memory/$(date +%F)/<topic>-deep-research-card.md

# 2) 严格检查
python scripts/validate_research_artifacts.py \
  --pack SOP/research/$(date +%F)/<topic>-deep-research-pack.md \
  --card 90_Memory/$(date +%F)/<topic>-deep-research-card.md \
  --strict
```

### Smart Context Digest 与安全 Cron（v4.4.0）

```bash
# 手动生成报告（仅报告，不危险动作）
python scripts/smart_context_digest.py --mode morning
python scripts/smart_context_digest.py --mode progress
python scripts/smart_context_digest.py --mode nightly

# 安装/移除 cron
bash scripts/install_safe_cron.sh --install
bash scripts/install_safe_cron.sh --remove
```

### 一键验收（OpenViking 风格链路）

```bash
TMP_OBS=/tmp/obsidian_para_smoke
python scripts/para_init.py --obsidian "$TMP_OBS"
cat > /tmp/para_smoke_summary.json <<'JSON'
{
  "core_output": "PARA 二脑 smoke",
  "project": "SmokeProject",
  "tech_points": ["para_recall", "warm_writer"],
  "decision_context": "验证项目优先召回",
  "next_actions": ["run tests", "update docs"]
}
JSON
python scripts/warm_writer.py --from /tmp/para_smoke_summary.json --obsidian "$TMP_OBS"
python scripts/para_validate.py --project SmokeProject --obsidian "$TMP_OBS" --max-age-minutes 999999
python scripts/para_recall.py --query "PARA 二脑" --obsidian "$TMP_OBS" --top-projects 1
```


### 其他工具脚本

```bash
# 分割大文件
python scripts/session_split.py --scan

# 重建索引
python scripts/index_rebuild.py --all

# 迁移 v1.0
python scripts/migrate.py --source /path/to/v1 --verify
```

---

## API 用法示例

### Python API

```python
from deepsea_nexus import nexus_add, nexus_init, nexus_recall

# 初始化
nexus_init()
nexus_add(
    content="今天学习列表推导式，过滤条件写在尾部更易读。",
    title="Python学习",
    tags="python,list-comprehension",
)

# 召回记忆
results = nexus_recall("列表", n=5)
for r in results:
    print(f"[{r.relevance:.2f}] {r.source}")
```

### 向量存储 API

```python
from vector_store.init_chroma import create_vector_store
from vector_store.manager import create_manager

# 初始化向量存储
store = create_vector_store()
manager = create_manager(store.embedder, store.collection)

# 添加笔记
note_id = manager.add_note(
    content="这是一个测试笔记",
    metadata={"title": "测试", "tags": "test"}
)

# 搜索
results = manager.search("测试内容", n_results=5)
for doc, dist in zip(results['documents'][0], results['distances'][0]):
    print(f"[{dist:.3f}] {doc[:100]}...")

# 获取统计
stats = manager.get_stats()
print(f"总文档数: {stats['total_documents']}")
```

---

## vNext Brain (Optional)

> Optional brain layer with pluggable scoring and safe fallbacks.

### Enable brain in config.json

```json
{
  "brain": {
    "enabled": true,
    "base_path": "/Users/yizhi/.openclaw/workspace",
    "mode": "facts",
    "min_score": 0.2,
    "merge": "append",
    "scorer_type": "keyword",
    "max_snapshots": 20,
    "backfill_on_start": false,
    "backfill_limit": 0,
    "dedupe_on_write": false,
    "dedupe_recent_max": 5000,
    "track_usage": true,
    "decay_on_checkpoint_days": 14,
    "decay_floor": 0.1,
    "decay_step": 0.05,
    "tiered_recall": false,
    "tiered_order": ["P0", "P1", "P2"],
    "tiered_limits": [3, 2, 1],
    "dedupe_on_recall": true
  }
}
```

Supported `scorer_type` values:
- `keyword` (default, dependency-free)
- `vector` (sentence-transformers if available; falls back safely)
- `hashed-vector` (dependency-free hashed embedding)

### Embedding write-back

When `scorer_type` enables real sentence-transformers embeddings, brain writes will
precompute and store embeddings in record metadata for fast recall. If the model
is not available, the system falls back to hashed embeddings without breaking.

### Brain API

```python
from deepsea_nexus.brain import configure_brain, brain_write, brain_retrieve, checkpoint, rollback, list_versions

configure_brain(enabled=True, base_path="/Users/yizhi/.openclaw/workspace", scorer_type="vector")
brain_write({"id": "1", "kind": "fact", "source": "demo", "content": "JSONL is append-only"})
results = brain_retrieve("append-only", mode="facts", limit=3)
stats = checkpoint()
versions = list_versions()
rollback(stats["version"])
```

### Backfill embeddings (optional)

```python
from deepsea_nexus.brain import backfill_embeddings

# Backfill stored records when sentence-transformers is available
stats = backfill_embeddings(limit=0)  # limit=0 means no limit
print(stats)
```

### Brain lifecycle helpers

Use these to keep the brain store compact and auditable.

```python
from deepsea_nexus.brain.api import checkpoint, list_versions, rollback

# Compact write-ahead log into a snapshot
stats = checkpoint()
print(stats)  # {"version": "...", "snapshot_count": N, "compacted_from": M}

# List available snapshots
versions = list_versions()
print(versions[:3])

# Roll back to a specific snapshot
ok = rollback(versions[0])
print(ok)
```

### 文本切片 API

```python
from chunking.text_splitter import create_splitter

# 创建分块器
splitter = create_splitter()

# 智能分块
chunks = splitter.smart_split(text, strategy="hybrid")

# 文档分块（带 metadata）
doc_chunks = splitter.chunk_document(
    text,
    {"title": "文档标题", "type": "note"},
    strategy="hybrid"
)
```

---

## 常见问题

### Q1: 索引速度慢？

首次运行需要下载嵌入模型（约90MB），后续会缓存。索引105个文件约需1-2分钟。

### Q2: 如何调整分块大小？

修改 `config.yaml` 中的 `chunking` 配置：

```yaml
chunking:
  chunk_size: 1000    # 增大可减少块数量
  chunk_overlap: 100   # 增大可提高召回率
```

### Q3: 搜索结果不准确？

1. 降低 `similarity_threshold` (默认 0.5)
2. 增加 `top_k` 获取更多结果
3. 尝试不同的 `strategy` (hybrid/sentence/paragraph/fixed)

### Q4: 如何备份/恢复？

```bash
# 备份向量库
cp -r memory/.vector_db backup/.vector_db

# 恢复
cp -r backup/.vector_db memory/.vector_db
```

### Q5: 如何集成到 OpenClaw？

修改 `~/.openclaw/workspace/AGENTS.md`：

```markdown
# Deep-Sea Nexus v2.0 集成

## 启动规则
1. 启动时只读 `_DAILY_INDEX.md`
2. 不加载任何 Session 历史

## 对话规则
1. 用户提问时调用 `nexus_recall(query)` 或通过当前 SmartContext 注入
2. 只加载相关内容 (< 500 tokens)
3. 不注入完整上下文

## 写入规则
1. 关键信息添加 `#GOLD` 标记
2. 每次交互后调用 `nexus_add()` / `nexus_write()`
```

### Q6: 报错 "client" 属性不存在？

这是 `VectorStoreManager.reset_collection()` 的已知问题。索引操作不受影响，后续版本会修复。

---

## 目录结构

```
DEEP_SEA_NEXUS_V2/
├── src/
│   ├── nexus_core.py       # 核心引擎
│   ├── config.py           # 配置管理
│   ├── data_structures.py  # 数据结构
│   ├── exceptions.py       # 异常定义
│   ├── lock.py             # 文件锁
│   └── logger.py           # 日志系统
├── scripts/
│   ├── batch_chunk.py      # 批量索引 ⭐
│   ├── session_split.py    # 会话分割
│   ├── index_rebuild.py    # 索引重建
│   └── migrate.py          # v1.0 迁移
├── chunking/
│   └── text_splitter.py    # 文本分块
├── vector_store/
│   ├── init_chroma.py      # ChromaDB 初始化
│   └── manager.py          # 向量存储管理
├── tests/
│   ├── test_core.py        # 单元测试
│   └── test_units.py       # 组件测试
├── docs/
│   └── USAGE_GUIDE.md      # 本文档
├── memory/
│   └── 90_Memory/          # 记忆存储
├── config.yaml             # 配置文件
└── requirements.txt        # 依赖列表
```

---

## 性能基准

| 场景 | 指标 | 状态 |
|------|------|------|
| 启动 | < 1s | ✅ |
| 索引 | ~1ms/文档 | ✅ |
| 召回 | < 100ms | ✅ |
| 并发 | 文件锁 | ✅ |

---

## 许可证

MIT

---

*最后更新: 2026-02-08*
