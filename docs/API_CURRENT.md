# Deep-Sea Nexus Current API

Last updated: 2026-03-12

This document describes the supported public API surface for the current
Deep-Sea Nexus package release.

## Recommended Imports

Prefer imports from the package root:

```python
from deepsea_nexus import (
    __version__,
    create_app,
    get_version,
    nexus_add,
    nexus_health,
    nexus_init,
    nexus_recall,
    MemoryScope,
    MemoryV5Service,
)
```

Avoid new code that imports from historical internals such as `nexus_core.py`,
`src/nexus_core.py`, or `plugins/nexus_core.py`.

## Sync Compatibility API

These functions remain the safest entrypoint for existing automation:

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

## Async Application API

Use the async application path when you need direct lifecycle control:

```python
from deepsea_nexus import create_app

app = create_app()
await app.initialize()
await app.start()

nexus = app.plugins["nexus_core"]
hits = await nexus.search_recall("architecture decision", n=5)

await app.stop()
```

Current application and plugin plumbing:

- `app.py`
- `core/plugin_system.py`
- `plugins/nexus_core_plugin.py`

## Memory v5 API

Memory v5 is the current scoped memory layer:

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
```

## CLI Entry Point

The package CLI now exposes the current package surface:

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

## Version Contract

- `__version__`: current package release version (`5.0.0`)
- `get_version()`: same package release version
- `nexus_health()["version"]`: current plugin runtime protocol version

That distinction is deliberate and explains why package release and runtime
plugin protocol may show different numbers.

## Historical Docs

These files are still useful for migration archaeology, but they are not the
current API source of truth:

- `DOCUMENTATION.md`
- `docs/architecture_v3.md`
