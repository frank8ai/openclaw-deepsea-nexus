# Changelog - Deep-Sea Nexus v5.x

> Historical changelog: this file records older release notes and is not the
> current source of truth for the v5 runtime.
> Current docs:
> - `README.md`
> - `README_EN.md`
> - `docs/README.md`
> - `docs/ARCHITECTURE_CURRENT.md`
> - `docs/API_CURRENT.md`

## Version 5.5.0 (2026-03-22)
### 🔄 Zero-Intrusion Codex Memory Ingest
- ✅ package version advanced to `5.5.0`
- ✅ added internal `codex_periodic_ingest` plugin
  - scans local `~/.codex/sessions/**/*.jsonl`
  - scans appended `~/.codex/history.jsonl`
  - persists incremental state and metrics
  - writes Codex digests into Memory v5 without OpenClaw hooks
- ✅ added operator entrypoints:
  - `scripts/codex_periodic_ingest.py`
  - `scripts/install_codex_periodic_ingest_task.py`
- ✅ extended CLI observability:
  - `health --json` now exposes `plugins.codex_periodic_ingest.summary`
  - `paths --json` now exposes Codex ingest paths and helper scripts
- ✅ release docs aligned:
  - `docs/releases/V5_5_0_RELEASE_2026-03-22.md`
  - `docs/releases/V5_5_0_RELEASE_2026-03-22_ZH.md`

## Version 5.1.0 (2026-03-14, in progress)
### 🚧 Governance Optimization Kickoff
- ✅ package version advanced to `5.1.0` (upgrade lane)
- ✅ event bus wildcard subscriptions are now operational:
  - `core/event_bus.py` supports glob-style subscriber patterns
    (e.g. `session.*`, `nexus.*`)
  - exact + wildcard handlers are deduplicated per callback per emit cycle
- ✅ unit coverage added for wildcard event subscription behavior:
  - `tests/test_units.py::TestEventBus::test_wildcard_subscriber_receives_matching_events`
- ✅ release/upgrade docs aligned with `v5.1.0` lane:
  - `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
  - package/docs/README version anchors updated to 5.1 context
- ✅ GitHub introduction/docs surface now exposes product core features explicitly:
  - `README.md` and `README_EN.md` include a "core features at a glance" section
  - `docs/README.md` includes feature-entry alignment rules
  - `docs/product/capabilities.md` adds the v5.1 intro-facing feature map
- ✅ normalized host-specific absolute paths in exec-plan docs to portable forms
  (`<repo-root>` + `$HOME`) to satisfy repository cleanup gates
- ✅ memory_v5 governance tooling now supports explicit extended scope targeting:
  - `scripts/memory_v5_maintenance.py` accepts `--app`, `--run-id`, `--workspace`
  - lifecycle maintenance can be scoped to contextual sub-scope without `--all-agents`
- ✅ scope-precision parity now covers maintenance/backfill/benchmark tools:
  - `scripts/memory_v5_backfill_batches.py` accepts `--app`, `--run-id`, `--workspace`
  - `scripts/memory_v5_benchmark.py` accepts `--app`, `--run-id`, `--workspace`
  - tests include explicit-scope paths for backfill and benchmark scripts
- ✅ validation refresh on current branch:
  - `python3 -m pytest -q` => `251 passed, 4 skipped, 1 warning`
  - `git diff --check` clean

## Version 5.0.0 Hotfix 1 (2026-03-14)
### 🛡️ Runtime Hardening + Security/Isolation Fixes on top of v5.0.0
- ✅ `scripts/import_sessions.py` removed unsafe `eval(...)` frontmatter path
  - now uses `yaml.safe_load(...)` for structured list/dict parsing only
- ✅ Memory v5 scope path hardening:
  - `memory_v5/layout.py` now sanitizes path-like scope segments to block
    traversal/escape writes
- ✅ Memory v5 category scope isolation hardening:
  - `memory_v5/service.py` category IDs now include scope-key digest
  - category artifacts no longer collide across same `agent/user` with different
    `app/run/workspace`
- ✅ Event/runtime stability hardening:
  - `core/event_bus.py` no longer depends on pre-existing default event loop at
    construction
  - `plugins/session_manager.py` sync API paths now run async persistence/event
    emission via safe sync/async bridge
- ✅ Ops consistency:
  - restored wrapper hook entrypoints:
    - `hooks/agent_end/run_save.sh`
    - `hooks/before_agent_start/run_recall.sh`
  - `.gitignore` updated so runtime wrapper scripts remain versioned
- ✅ Validation: `python3 -m pytest -q` => `247 passed, 4 skipped`
- Release note:
  - `docs/releases/V5_0_0_HOTFIX_1_2026-03-14.md`

## Version 4.4.2 (2026-02-23)
### 🛡️ v4.4.2 - Write Guard Hardening + Recent Summary Audit
- ✅ 新增统一写入护栏模块：`write_guard.py`
  - 强制检查 `NEXUS_VECTOR_DB` / `NEXUS_COLLECTION`
  - 默认目标锁定主库：
    - `~/.openclaw/workspace/memory/.vector_db_restored`
    - `deepsea_nexus_restored`
  - 违规写入会落审计日志：`~/.openclaw/workspace/logs/nexus_write_guard_alerts.jsonl`
- ✅ 写入入口 hard-guard + 写后校验：
  - `compat.nexus_add` / `compat.nexus_write`
  - `plugins.nexus_core_plugin.add_document`（防止绕过 compat）
  - `hooks/agent_end/save_context.py`
  - `scripts/nexus_auto_save.py`
- ✅ 新增跨库摘要审计与迁移脚本：`scripts/audit_recent_summaries.py`
  - 可扫描所有向量库最近摘要分布
  - 可将“主库缺失摘要”迁移回主库
  - 自动生成 JSON/Markdown 报告与可回滚脚本
- ✅ 本轮验收结果（7天窗口）：
  - `recent_non_main_missing_candidates = 0`
  - `migrated = 0`
  - `main_count_after = 2822`
  - 报告：`docs/reports/summary_audit_20260223T083842Z.{json,md}`

## Version 4.4.1 (2026-02-23)
### 🧪 v4.4.1 - Memory Contract Ops + PARA Scoring Iteration
- ✅ `nexus_audit_contract.py` 增强为可运营审计：
  - 兼容 `tags` 的 `list/str/tag` 解析
  - metadata fallback (`priority/kind/source/source_file`)
  - 新增 `group_coverage`（`new_contract` / `legacy_source_file` / `legacy_unknown`）
  - 新增 `--show-missing` 缺失样本输出
- ✅ `para_recall.py` 升级为三维评分：
  - `relevance + importance + recency` 可调权重
  - 读取 `.memory_signal.json`（importance/half-life）
  - 输出 `score_breakdown` 便于解释排序
- ✅ `warm_writer.py` 增强：
  - 自动写入 `.memory_signal.json`
  - 自动晋升到 `20_Knowledge/Areas/<Project>.md`（`entry_id` 去重）
- ✅ 文档补全：
  - `docs/SOP_MEMORY_GAP_ITERATION_2026-02-23.md`
  - `docs/reports/2026-02-23-contract-audit.md`

#### 实测（sample=200）
- 审计命令：
  - `NEXUS_VECTOR_DB=${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/memory/.vector_db_restored`
  - `NEXUS_COLLECTION=deepsea_nexus_restored`
  - `python scripts/nexus_audit_contract.py --limit 200 --show-missing 12`
- 覆盖率：
  - `priority`: `0.0`
  - `kind`: `0.0`
  - `source`: `0.965`
- 分组：
  - `legacy_source_file`: 191
  - `legacy_unknown`: 9
- 结论：历史库仍以 legacy 样本为主，新契约写入链路已具备可验证审计能力。

## Version 4.4.0 (2026-02-18)
### 🧠 v4.4.0 - Smart Context Completion Release
- ✅ 将 Smart Context 全链路从 4.3.1 正式提升到 4.4.0（代码/配置/文档/脚本统一）
- ✅ `schema_version` 统一为 `4.4.0`（`smart_context` / `context_engine` / `nexus_core`）
- ✅ 安全 cron 标识升级为 `deepsea-nexus-v4.4.0`
- ✅ 发布文档入口统一到 `docs/SMART_CONTEXT_V4_4_0.md`
- ✅ second-brain HQ Pack/Card 严格校验通过（`validate_research_artifacts.py --strict`）
- ✅ 回归测试通过（`run_tests.py`）

## Version 4.3.1 (2026-02-18)
### 🧠 v4.3.1 - Smart Context Upgrade (Option B+)
- ✅ Deep Research artifact templates:
  - `resources/sop/TEMPLATE.deep-research-pack.md`
  - `resources/sop/TEMPLATE.deep-research-card.md`
  - `resources/sop/TEMPLATE.structured-summary-v3.1.json`
- ✅ Strict artifact validator: `scripts/validate_research_artifacts.py`
- ✅ Safe digest generator (report-only): `scripts/smart_context_digest.py`
- ✅ Safe cron installer/remover: `scripts/install_safe_cron.sh`
- ✅ Metrics schema alignment (`schema_version=4.3.1`) across:
  - `smart_context`
  - `context_engine`
  - `nexus_core`
- ✅ Context engine metrics path fallback aligned with workspace/base_path resolution

## Version 4.3.0 (2026-02-18)
### 🛡️ v4.3 - Degraded Stability + Hybrid Recall
- ✅ Degraded vector mode when `chromadb` is unavailable (service stays usable)
- ✅ Hybrid retrieval path (vector + lexical fallback + optional brain merge)
- ✅ Python 3.8-safe plugin lock initialization in `PluginRegistry`
- ✅ Plugin lifecycle state sync (`registry` 与 `plugin.state` 一致)
- ✅ Extended observability: recall/path metrics + context trim/search fallback metrics
- ✅ Test gate stabilization (`run_tests.py` runtime capability probe + robust import path)
- ✅ Local deploy script and runbook (`scripts/deploy_local_v4.sh`, `docs/LOCAL_DEPLOY.md`)

## Version 4.2.0 (2026-02-17)
### 🧭 v4.2 - PARA Second Brain
- ✅ Obsidian PARA init + templates
- ✅ Warm writer (from structured summaries)
- ✅ L0/L1/L2 layer files (.abstract/.overview/Warm)
- ✅ Directory-recursive PARA recall (project-first)
- ✅ Optional warm update hook via summary flush

## Version 4.1.1 (2026-02-16)
### 🧠 v4.1.1 - Observability + Resilience
- ✅ SmartContext metrics log (summary/inject/graph/rescue/context status)
- ✅ Inject hit-rate alerts + auto-tune with persisted config
- ✅ Summary quality guard (entity retention)
- ✅ NOW.md rescue trimming (top-priority retention)

## Version 4.1.2 (2026-02-16)
### 🧠 v4.1.2 - Hard Rules for Summary + Top-K Inject
- ✅ Per-turn summary cards with fixed template fields
- ✅ Topic switch boundary summaries (anti-context-bleed)
- ✅ Strict Top-K recall + per-item/total line budget trimming

## Version 4.1.3 (2026-02-16)
### 🧠 v4.1.3 - Context Engine Budgeting
- ✅ ContextEngine budgeted context block (NOW + recent summary + Top-K recall)
- ✅ Hook integrates ContextEngine for pre-run injection
- ✅ Configurable budgets via context_engine section

## Version 4.1.4 (2026-02-16)
### 🧠 v4.1.4 - Context Metrics + Auto-Tune
- ✅ ContextEngine metrics log (tokens/items/lines)
- ✅ Budget auto-tune based on rolling token usage
- ✅ Config-persisted tuning with safe interval

## Version 4.1.5 (2026-02-16)
### 🧠 v4.1.5 - Signal-Aware Inject
- ✅ 主题块写入与图谱关联（topic_block）
- ✅ 注入信号优先级（决策/主题/摘要加权）
- ✅ 动态 Top-K 门控（低信号降注入，高信号提升）
- ✅ 指标看板脚本（context_metrics_dashboard.py）
- ✅ 低成本模型路由脚本（model_router.py）
- ✅ Control UI Canvas 图表（context_metrics_export.py）

## Version 4.1.0 (2026-02-16)
### 🧠 v4.1 - Associative Memory
- ✅ Light knowledge graph for decision blocks (SQLite)
- ✅ Graph + vector hybrid recall injection
- ✅ Adaptive inject tuning (self-correcting threshold)

## Version 4.0.0 (2026-02-16)
### 🧠 v4.0 - Smarter Memory Loop
- ✅ Optional real embeddings with safe fallback
- ✅ Usage-aware recall ranking + dedupe
- ✅ Tiered recall + novelty gate
- ✅ Async-core compat sync bridge

## Version 3.1.0 (2026-02-13)

### 🎯 v3.1 - Smart Context Summary System

#### New Features
- ✅ **Structured Summary v2.0** - 9-field knowledge accumulation
  - Core output (本次核心产出)
  - Technical points (技术要点)
  - Code patterns (代码模式)
  - Decision context (决策上下文)
  - Pitfall records (避坑记录)
  - Applicable scenes (适用场景)
  - Search keywords (搜索关键词)
  - Project association (项目关联)
  - Confidence self-assessment (置信度)

- ✅ **Context-aware AI Reasoning** - 让第二大脑越来越聪明
  - LLM auto-generates structured summaries via system prompt
  - JSON format for machine-readable summaries
  - Hybrid storage (original + summary + metadata + keywords)
  - Keyword indexing for precise retrieval

- ✅ **Enhanced Storage Strategy**
  - 4 documents per conversation summary:
    1. Original content
    2. Structured summary (searchable text)
    3. Metadata (JSON format)
    4. Keywords index

#### Core Components
- `auto_summary.py` - Enhanced with StructuredSummary class
- `nexus_core.py` - Added `nexus_add_structured_summary()`
- `docs/SYSTEM_PROMPT_TEMPLATE.md` - New LLM prompt template
- `tests/test_summary.py` - Comprehensive test suite (5/5 passing)

#### Backward Compatibility
- ✅ Legacy summary format still supported
- ✅ Old API (nexus_add, nexus_recall) unchanged
- ✅ Automatic format detection and conversion

#### Performance
- No additional latency for summary generation
- Better retrieval precision with keyword indexing
- Lower storage overhead with structured approach

---

## Version 3.0.0 (2026-02-13)

### 🚀 v3.0 - Hot-Pluggable Architecture

#### New Architecture
- ✅ **Hot-Pluggable Plugin System** - Dynamic load/unload
- ✅ **Event-Driven Communication** - Decoupled modules
- ✅ **Unified Compression** - Eliminates code duplication
- ✅ **100% Backward Compatible** - Zero breaking changes
- ✅ **Async First** - Non-blocking operations
- ✅ **Hot Reload Config** - Update without restart

#### Core Components
- `core/plugin_system.py` - Lifecycle management
- `core/event_bus.py` - Pub/Sub system
- `core/config_manager.py` - Config with hot-reload
- `storage/compression.py` - Unified compression (gzip/zstd/lz4)
- `plugins/session_manager.py` - Session lifecycle
- `plugins/flush_manager.py` - Archival automation
- `app.py` - Main application container
- `compat.py` - Backward compatibility layer

#### Performance Improvements
- 2x compression speed
- 3x event processing
- 40% memory reduction
- Better concurrency support

---

## Version 2.0.0 (2026-02-08)

### Added
- Complete core engine implementation (nexus_core.py)
- Session management (CRUD operations)
- Index maintenance and parsing (parse_index)
- Memory recall system with relevance scoring
- Daily flush and archiving system
- Cross-date archive search (recall_archives)
- Session splitting tool (session_split.py)
- Index rebuild tool (index_rebuild.py)
- Migration tool for v1.0 -> v2.0 (migrate.py)
- Complete CLI interface
- Unit tests with 80%+ coverage
- Configuration via config.yaml
- Logging system (src/logger.py)
- Custom exceptions (src/exceptions.py)
- File locking for concurrency (src/lock.py)
- AGENTS.md protocol integration

### Changed
- Refactored data structures for better type safety
- Improved token economy (< 300 tokens for index)
- Optimized recall algorithm with GOLD priority

### Fixed
- Fixed active session path issues
- Fixed recall result type consistency
- Fixed index parsing edge cases

### Performance
- Startup time: < 1 second ✅
- Index size: < 300 tokens ✅
- Recall latency: < 100ms ✅

---

## Version 1.0.0 (2026-02-07)

- Initial prototype
- Basic session management
- Simple index system
