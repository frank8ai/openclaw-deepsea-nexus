# Deep-Sea Nexus Current API

Last updated: 2026-03-18

This document describes the supported public API surface for the current
`v5.3.0` release pack.

## Import Rules

Prefer imports from the package root:

```python
from deepsea_nexus import (
    __version__,
    create_app,
    get_version,
    nexus_add,
    nexus_add_document,
    nexus_add_documents,
    nexus_health,
    nexus_init,
    nexus_recall,
    nexus_search,
    MemoryScope,
    MemoryV5Service,
)
```

Avoid new code that imports from historical internals such as:

- `nexus_core.py`
- `src/nexus_core.py`
- `plugins/nexus_core.py`

## Public API Groups

### 1. Sync compatibility API

Safest entrypoint for existing automation:

- `nexus_init()`
- `nexus_recall(query, n=5)`
- `nexus_search(query, n=5)`
- `nexus_add(content, title, tags)`
- `nexus_add_document(...)`
- `nexus_add_documents(...)`
- `nexus_stats()`
- `nexus_health()`
- `start_session(topic)`
- `get_session(session_id)`
- `close_session(session_id)`
- `manual_flush()`

Example:

```python
from deepsea_nexus import nexus_init, nexus_recall

nexus_init()
hits = nexus_recall("previous architecture decision", n=5)
```

### 2. Async application API

Use this when you need direct lifecycle control:

```python
from deepsea_nexus import create_app

app = create_app()
await app.initialize()
await app.start()

nexus = app.plugins["nexus_core"]
hits = await nexus.search_recall("architecture decision", n=5)

await app.stop()
```

Current contract:

- `create_app()` returns the async application container
- `app.plugins["nexus_core"]` is the current memory plugin
- the plugin registry is shared with sync compatibility paths in-process
- current internal plugin set also includes `runtime_middleware`
- current internal plugin set also includes `execution_guard`
- they are intentionally internal in `v5.3.0`
  - do not build new integrations directly against it as if it were public API

### 3. Memory v5 scoped API

Use this when scoped durable memory is the primary integration surface:

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
hits = service.recall("control plane", scope=scope)
report = service.audit_lifecycle(scope=scope)
archive_plan = service.archive_due_items(scope=scope, dry_run=True)
```

Current contract:

- `MemoryScope` is the current isolation unit
- `agent_id / user_id` define filesystem-level partition under Memory v5 root
- `app_id / run_id / workspace` participate in record-level scope filtering
  (SQLite scope columns and scope-key category IDs)
- Memory v5 is part of the current release, not an experimental side path
- scope segments are sanitized before file-path materialization to prevent
  path-traversal style escapes from configured memory roots
- lifecycle governance is report-first
  - `audit_lifecycle()` reports TTL / decay / archive state
  - `audit_lifecycle()` also surfaces zero-valued archive-default backfill candidates for older rows
  - `archive_due_items(dry_run=True)` previews explicit archive work
  - `archive_due_items(dry_run=False)` applies the archive move only when explicitly requested
- lifecycle defaults can be narrowed per item kind when needed
  - optional config:
    - `memory_v5.item_kind_defaults.<kind>.ttl_days`
    - `memory_v5.item_kind_defaults.<kind>.decay_half_life_days`
    - `memory_v5.item_kind_defaults.<kind>.archive_after_days`
  - resolved lifecycle defaults are persisted on write for new items
  - later config changes do not silently reclassify already-written items
  - default config remains unchanged unless these overrides are set
- current operator entrypoint:
  - `python3 scripts/memory_v5_maintenance.py --dry-run`
  - add `--exclude-ttl-expired` if the maintenance pass should only consider age-based archive candidates
  - add `--apply-archive-backfill` to explicitly write resolved archive defaults into zero-valued rows
  - backfill does not silently archive those rows in the same pass; rerun audit/archive if needed
  - optional report outputs:
    - `--json-out <path>`
    - `--md-out <path>`
    - or `--write-report` to emit both into the default repo report directory

### 4. CLI

Current package CLI commands:

```bash
python -m deepsea_nexus version
python -m deepsea_nexus health --json
python -m deepsea_nexus paths --json
python -m deepsea_nexus recall "control plane" -n 3
```

Supported commands:

- `version`
- `health`
- `paths`
- `recall`

Current CLI status payloads now also surface:

- `health`
  - `plugins.runtime_middleware.summary`
  - `plugins.execution_guard.summary`
- `paths`
  - `runtime_middleware_metrics_path`
  - `runtime_middleware_last_metrics`
  - `execution_guard_metrics_path`
  - `execution_governor_guardrails_path`
  - `execution_guard_last_metrics`

### 5. Compatibility context helpers

These helpers still exist for older integrations:

- `ContextEngine`
- `get_engine()`
- `smart_retrieve(query, n=5)`
- `inject_context(query, n=5)`
- `detect_trigger(text)`
- `store_summary(conversation_id, response)`

Current boundary:

- keep them for compatibility
- do not treat them as the preferred surface for new integrations
- current `inject_context()` should still flow through the same budgeted
  context-assembly rules as the main runtime path

### 6. Internal runtime middleware

Current release includes an internal `runtime_middleware` plugin with:

- tool-event normalization
- RTK-style compression
- token-aware capture gating
- `tool_event` writes into Memory v5
- OpenClaw `tool-call` adapter entrypoint

Current boundary:

- keep it internal in `v5.2.0`
- configure and observe it through runtime config / CLI status
- do not treat it as stable public Python API yet

### 7. Internal execution guard

Current release includes an internal `execution_guard` plugin with:

- tool-risk taxonomy classification
- secrets / credentials / boundary checks
- report-first `allow / ask / block / context` decisions
- execution-governor guardrails export
- `tool_event.metadata.guard` attachment

Current boundary:

- keep it internal in `v5.3.0`
- expose health and path information through CLI / reports only
- do not treat it as stable public Python API yet

## Version Contract

- `__version__`
  - current package release version
- `get_version()`
  - same package release version
- `nexus_health()["version"]`
  - current plugin runtime protocol version

That distinction is intentional. Package release and runtime protocol are
related but not identical.

## Compatibility Contract

The current release intentionally preserves compatibility behavior for older
automation, but the compatibility surface has boundaries:

- existing sync automation should keep working through package-root functions
- new code should not be built directly on historical internal modules
- compatibility context helpers should be treated as bridge surfaces, not the
  primary integration target
- current architecture decisions should follow:
  - `TECHNICAL_OVERVIEW_CURRENT.md`
  - `ARCHITECTURE_CURRENT.md`
  - `sop/Context_Policy_v2_EventDriven.md`

## Not Public / Not Recommended

These paths may still exist in the repo, but they are not current public API:

- historical `nexus_core.py` implementations
- deep internal helper modules under `plugins/smart_context_*`
- older architecture and PRD documents
- archive-only scripts and migration artifacts

## Read Next

- technical map:
  - `TECHNICAL_OVERVIEW_CURRENT.md`
- implementation structure:
  - `ARCHITECTURE_CURRENT.md`
- context-governance rules:
  - `sop/Context_Policy_v2_EventDriven.md`
