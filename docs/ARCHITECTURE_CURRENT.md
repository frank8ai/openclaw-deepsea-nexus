# Deep-Sea Nexus Current Architecture

Last updated: 2026-03-13

This document is the source of truth for the current Deep-Sea Nexus runtime in
package release `5.0.0`.

## Version Model

- Package release: `5.0.0`
- Async plugin runtime protocol: `3.0.0`
- Compatibility promise: keep the legacy sync API stable while newer features
  land in the package and Memory v5 layers

The mixed version numbers are intentional. Package release tracks product
changes; plugin protocol tracks the long-lived hot-pluggable runtime contract.

## Runtime Layers

### 1. Root package API

Primary user-facing imports are re-exported from the package root:

- `__init__.py`
- `compat.py`

Supported entrypoints:

- Sync compatibility API: `nexus_init`, `nexus_recall`, `nexus_add`,
  `nexus_health`, `manual_flush`
- Async app API: `create_app`
- Memory v5 API: `MemoryV5Service`, `MemoryScope`
- Shared runtime path helpers: `runtime_paths.py`

### 2. Async application container

The async lifecycle lives here:

- `app.py`
- `core/plugin_system.py`
- `core/config_manager.py`
- `core/event_bus.py`

`create_app()` builds the application, loads plugins, and exposes them through
`app.plugins`.

Important runtime constraint:

- the sync compatibility API and async app instances share the same in-process
  plugin registry
- repeated `create_app()` calls in one process therefore reuse registered
  plugin objects instead of treating each app as a fully isolated container

### 3. Current memory plugin path

The current semantic memory implementation is:

- `plugins/nexus_core_plugin.py`

It is the active plugin used by `app.py` and the sync compatibility layer.
Hybrid retrieval, degraded lexical fallback, write guards, and Memory v5 fusion
all live here.

### 4. Context assembly and injection

Current context-related runtime modules:

- `plugins/smart_context.py`
- `plugins/smart_context_storage.py`
- `plugins/smart_context_graph_inject.py`
- `plugins/smart_context_recall.py`
- `plugins/smart_context_rescue.py`
- `plugins/smart_context_graph.py`
- `plugins/smart_context_decision.py`
- `plugins/smart_context_inject.py`
- `plugins/smart_context_text.py`
- `plugins/smart_context_runtime.py`
- `plugins/context_engine.py`
- `plugins/context_engine_runtime.py`
- `auto_summary.py`
- `runtime_paths.py`

These modules still contain significant historical logic and are valid refactor
targets, but they are part of the current runtime.

Current cleanup status:

- `plugins/context_engine.py` fallback now uses the current sync compatibility
  API as an adapter instead of constructing legacy `NexusCore()` directly
- `plugins/smart_context.py` relies on the loaded runtime plugin and no longer
  imports the legacy core module directly
- `plugins/context_engine_runtime.py` now owns ContextEngine budget, trim,
  metrics, and auto-tune state so `plugins/context_engine.py` can focus on
  retrieval and context assembly
- `plugins/smart_context_runtime.py` now owns SmartContext inject metrics,
  alert streak, auto-tune, and config persistence state so
  `plugins/smart_context.py` can focus on retrieval, summaries, and inject
  decisions
- `plugins/smart_context_text.py` now owns shared summary, keyword, decision,
  and topic extraction helpers reused by both `SmartContextPlugin` and the
  legacy `store_conversation(...)` convenience path
- `plugins/smart_context_inject.py` now owns shared inject-item trimming,
  signal scoring, and dynamic threshold/max-items rules reused by
  `SmartContextPlugin`
- `plugins/smart_context_decision.py` now owns shared context-starved,
  inject-trigger, and topic-switch rules reused by `SmartContextPlugin`
- `plugins/smart_context_graph.py` now owns decision/topic block document
  payloads plus graph-edge extraction/assembly reused by `SmartContextPlugin`
- `plugins/smart_context_rescue.py` now owns rescue-text extraction and
  NOW-state merge helpers reused by `SmartContextPlugin`
- `plugins/smart_context_recall.py` now owns recall-result normalization,
  de-duplication, and threshold/fallback selection reused by
  `SmartContextPlugin`
- `plugins/smart_context_graph_inject.py` now owns graph-inject gating and
  formatted graph-evidence item assembly reused by `SmartContextPlugin`
- `plugins/smart_context_storage.py` now owns shared SmartContext document
  payload assembly for round-context writes and conversation-summary writes
- legacy `store_conversation(...)` now joins user and assistant text with real
  newlines before decision/topic extraction so its compatibility path matches
  the current plugin behavior
- runtime path resolution for metrics and Memory v5 roots is now centralized in
  `runtime_paths.py` instead of being reimplemented in multiple active modules

### 5. Memory v5 scoped store

Current durable scoped memory lives under:

- `memory_v5/`

Main concepts:

- `MemoryScope`: explicit `agent_id` + `user_id` isolation
- filesystem-backed item/resource/category layout
- SQLite-backed retrieval and maintenance services

### 6. Operational entrypoints

Current operational entrypoints:

- `run_tests.py`
- `scripts/_legacy_layout.py`
- `scripts/archive_repo_runtime_data.py`
- `scripts/deploy_local_v5.sh`
- `scripts/memory_v5_smoke.py`
- `scripts/memory_v5_maintenance.py`
- `scripts/memory_v5_benchmark.py`

Legacy maintenance scripts now use `scripts/_legacy_layout.py` to resolve the
historical `memory/90_Memory` filesystem layout without importing
`src/nexus_core.py` directly.

Repo-local runtime artifacts such as `logs/`, non-venv `__pycache__/`, and an
optional stale `.venv/` are now archived out of the working tree via
`scripts/archive_repo_runtime_data.py`.

## Canonical Usage Paths

### Sync compatibility path

Use this when existing automation expects the historical sync API:

```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

nexus_init()
hits = nexus_recall("what did we decide?", n=5)
nexus_add("We kept FastAPI.", "Decision", "architecture")
```

### Async application path

Use this when managing the runtime explicitly:

```python
from deepsea_nexus import create_app

app = create_app()
await app.initialize()
await app.start()
hits = await app.plugins["nexus_core"].search_recall("decision", n=5)
await app.stop()
```

### Memory v5 path

Use this when scoped filesystem memory is the primary integration:

```python
from deepsea_nexus import MemoryScope, MemoryV5Service

service = MemoryV5Service({"memory_v5": {"enabled": True, "async_ingest": False}})
scope = MemoryScope(agent_id="main", user_id="default")
service.ingest_document(title="Decision", content="We kept FastAPI.", scope=scope)
```

## Deprecated But Still Present

These files exist for compatibility or history and should not be treated as the
current implementation:

- `DOCUMENTATION.md`: archived v2.3 technical doc
- `docs/architecture_v3.md`: archived v4.1-on-v3 architecture doc
- `docs/USAGE_GUIDE.md`: historical compatibility guide, not the v5 source of truth
- `plugins/nexus_core.py`: compatibility alias to `plugins/nexus_core_plugin.py`
- `nexus_core.py`: compatibility-heavy legacy shell still referenced by some
  historical docs and tests
- `src/nexus_core.py`: historical implementation snapshot
- `tests/test_core.py`, `tests/test_complete.py`: archived v2-era tests, not part
  of the v5 release gate

## Refactor Guardrails

- Do not remove `nexus_core.py` until historical docs/tests are either migrated
  or explicitly archived.
- Prefer package-root imports over deep module imports in new code.
- Keep sync API behavior stable unless a specific breaking migration is planned.
- Treat `README.md`, `README_EN.md`, this document, and `docs/API_CURRENT.md`
  as the current documentation set.

## Validation Baseline

- `python3 -m unittest tests.test_memory_v5 -v`
- `python3 run_tests.py`
