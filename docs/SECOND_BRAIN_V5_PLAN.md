# Second-Brain v5.0 Plan (memU-aligned)

## Current Baseline (v4.4.x)
- Vector recall + lexical fallback + SmartContext injection.
- Structured summary v2.0 -> vector store.
- Brain JSONL store for lightweight facts + scoring.
- PARA memory pathing and periodic flush.

## v5 Target Outcomes
- "越用越聪明": 记忆结构化、生命周期治理、可解释召回、跨会话持续进化。
- memU 风格三层：Resource / Item / Category。
- 双检索与融合：向量 + 词法 + 分类文件 + 图谱。
- 作用域隔离：agent_id / user_id 物理隔离。
- 可回退、不破坏 v4。

## Data Model (v5)
- Resource: 原始对话/外部资料（可追溯）。
- Item: 结构化记忆对象（kind + tags + keywords + entities）。
- Category: 主题聚合文件（可读、可维护、可直接注入）。
- Edge: 图谱关系（item ↔ entity/keyword）。

## Storage Layout
```
memory/95_MemoryV5/
  <agent_id>/<user_id>/
    resources/   # 原始资源 JSON
    items/       # 结构化记忆 JSON
    categories/  # 主题汇总 Markdown
    graphs/      # 图谱输出
    index.sqlite3
```

## Retrieval Pipeline
1. 向量召回 (vector store)
2. 词法召回 (SQLite FTS / fallback match)
3. 分类文件召回 (Category summary)
4. 图谱扩展 (edges -> related items)
5. RRF 融合排序

## Ingest Pipeline
- Summary -> Items
- Items -> Category update
- Items -> Graph edges (entity/keyword)
- Resource -> Traceability

## Lifecycle Governance
- 内置 scope 管理 + 后续支持 TTL/衰减/归档。
- 记忆对象化，便于软删除与审计。

## Acceptance Criteria
- Recall 命中率提升（本地评测集 vs v4 基线）。
- 召回可解释（source + category + origin）。
- 记忆隔离：跨 agent/user 不串。
- 无破坏性升级：v4 pipeline 仍可用。

## Ops Scripts
- Smoke: `python3 scripts/memory_v5_smoke.py`
- Migration: `python3 scripts/memory_v5_migrate.py --path /Users/yizhi/memory`
- Maintenance: `python3 scripts/memory_v5_maintenance.py --agent main --user default`
- Benchmark: `python3 scripts/memory_v5_benchmark.py --cases docs/memory_v5_benchmark_sample.json`

## Rollout Plan
- Phase 1: v5 模块 + config 开关
- Phase 2: ingest 接入 auto_summary / add_document
- Phase 3: recall 融合 + metrics
- Phase 4: 迁移脚本 + 评测脚本

## Verification (2026-03-01)
- 覆盖 agent: `main/coder/writer/researcher/researcher-deep/openclaw-dev/gemini/codex/codex-cli`
- 每个 agent 进行 3 轮写入 -> recall -> 插件融合 recall
- 结果：Memory v5 直接召回与插件融合召回全部命中（3/3）
- 备注：向量后端处于 degraded 模式时依旧可通过 v5/lexical 正常回忆

## Closure Fixes (2026-03-05)
- 修复 scope 路由闭环：`MemoryV5Service` 现在按 `scope` 动态路由独立 `layout/index.sqlite3`，不再固定在初始化 scope。
- 修复跨 scope 运维脚本：`memory_v5_maintenance.py` 读取 items 改为 service 级多 scope 接口。
- 修复中文问句召回：`memory_v5/index.py` 在 lexical 回退中增加中文短片段匹配与打分排序，避免整句匹配过严导致 0 命中。
- 基准脚本增强：`memory_v5_benchmark.py` 新增 `any_scope_hit/any_scope_score/per_scope` 输出，区分全局可回忆能力与单 scope 命中率。

## Notes
- v5 只追加，不替换；可通过 config 关闭。
- 任何失败自动降级到 v4 路径。
- 生产运维建议叠加 execution-governor v1.3 上下文控制面：
  - 参考 `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`
  - 使用 `context_pressure` + `cache_efficiency` + `context_compaction_signal` 做日常巡检与调参闭环。
