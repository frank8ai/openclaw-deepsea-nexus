---
name: deepsea-nexus
description: >
  Long-term memory skill with semantic recall, scoped Memory v5 storage,
  session lifecycle support, and context-governance integrations.
---
# Deep-Sea Nexus Skill

Current package release: `5.0.0`
Current plugin runtime protocol: `3.0.0`

## What This Skill Provides

- semantic recall with vector, lexical, and hybrid retrieval
- backward-compatible sync API for existing automation
- async application runtime with hot-pluggable plugins
- scoped Memory v5 storage for agent/user isolation
- SmartContext and summary ingestion helpers

## Recommended Entry Points

### Sync compatibility API

```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

nexus_init()
hits = nexus_recall("what did we decide?", n=5)
doc_id = nexus_add("We kept FastAPI.", "Decision", "architecture")
```

### Async application API

```python
from deepsea_nexus import create_app
import asyncio

async def main():
    app = create_app()
    await app.initialize()
    await app.start()
    hits = await app.plugins["nexus_core"].search_recall("decision", n=5)
    await app.stop()

asyncio.run(main())
```

### Memory v5 API

```python
from deepsea_nexus import MemoryScope, MemoryV5Service

service = MemoryV5Service({"memory_v5": {"enabled": True, "async_ingest": False}})
scope = MemoryScope(agent_id="main", user_id="default")
service.ingest_document(title="Decision", content="We kept FastAPI.", scope=scope)
```

## Useful Commands

```bash
python3 scripts/memory_v5_smoke.py
python3 scripts/memory_v5_maintenance.py --all-agents
python3 scripts/memory_v5_benchmark.py --cases docs/memory_v5_benchmark_sample.json --all-agents
bash scripts/deploy_local_v5.sh --quick
python -m deepsea_nexus health --json
```

## Source Of Truth

- `README.md`
- `README_EN.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/API_CURRENT.md`
- `docs/LOCAL_DEPLOY.md`

## Historical Docs

These remain in the repo for migration history only:

- `DOCUMENTATION.md`
- `docs/architecture_v3.md`

## Compatibility Notes

- Keep the sync API stable for existing callers.
- Prefer package-root imports in new code.
- `plugins/nexus_core.py` is now a compatibility alias; use
  `plugins/nexus_core_plugin.py` for current plugin work.
