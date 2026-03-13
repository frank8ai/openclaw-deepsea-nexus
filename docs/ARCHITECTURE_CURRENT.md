# Deep-Sea Nexus Current Architecture

Last updated: 2026-03-12

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
- `plugins/context_engine.py`
- `auto_summary.py`

These modules still contain significant historical logic and are valid refactor
targets, but they are part of the current runtime.

Current cleanup status:

- `plugins/context_engine.py` fallback now uses the current sync compatibility
  API as an adapter instead of constructing legacy `NexusCore()` directly
- `plugins/smart_context.py` relies on the loaded runtime plugin and no longer
  imports the legacy core module directly

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
- `scripts/deploy_local_v5.sh`
- `scripts/memory_v5_smoke.py`
- `scripts/memory_v5_maintenance.py`
- `scripts/memory_v5_benchmark.py`

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
- `plugins/nexus_core.py`: compatibility alias to `plugins/nexus_core_plugin.py`
- `nexus_core.py`: compatibility-heavy legacy shell still referenced by some
  scripts and tests
- `src/nexus_core.py`: historical implementation snapshot

## Refactor Guardrails

- Do not remove `nexus_core.py` until `plugins/context_engine.py` and legacy
  scripts stop instantiating `NexusCore()` directly.
- Prefer package-root imports over deep module imports in new code.
- Keep sync API behavior stable unless a specific breaking migration is planned.
- Treat `README.md`, `README_EN.md`, this document, and `docs/API_CURRENT.md`
  as the current documentation set.

## Validation Baseline

- `python3 -m unittest tests.test_memory_v5 -v`
- `python3 run_tests.py`
