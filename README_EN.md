# Deep-Sea Nexus v5.0.0

Long-term memory and context-governance tooling for Codex and OpenClaw agent workflows.

[简体中文](README.md)

## Overview

Deep-Sea Nexus provides a practical memory layer for agent systems:

- Semantic recall with vector, lexical, and scoped Memory v5 retrieval
- Backward-compatible Python API for existing automation
- Session lifecycle management and summary ingestion
- SmartContext injection with context-budget controls
- Operational scripts for smoke tests, migration, maintenance, and deploy checks

## Key Runtime Paths

- Main skill root: `skills/deepsea-nexus/`
- Current architecture: `docs/ARCHITECTURE_CURRENT.md`
- Current API surface: `docs/API_CURRENT.md`
- Memory v5 plan: `docs/SECOND_BRAIN_V5_PLAN.md`
- Local deployment guide: `docs/LOCAL_DEPLOY.md`
- Context-governance SOP: `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`
- Historical docs kept for reference only:
  - `DOCUMENTATION.md`
  - `docs/architecture_v3.md`

## Python API

### Backward-Compatible API

```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

nexus_init()
hits = nexus_recall("what did we decide last time?", n=5)
doc_id = nexus_add(
    "We chose FastAPI for the control plane.",
    "Architecture Decision",
    "fastapi,architecture",
)
```

### Summary and Context Helpers

```python
from deepsea_nexus import StructuredSummary, create_summary_prompt, parse_summary

prompt = create_summary_prompt()
reply, summary = parse_summary("assistant response here")
assert summary is None or isinstance(summary, StructuredSummary)
```

### Memory v5

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

## Memory v5 Layout

`memory_v5` stores durable memory under a scoped filesystem layout:

```text
memory/95_MemoryV5/
  <agent_id>/<user_id>/
    resources/
    items/
    items_archive/
    categories/
    graphs/
    index.sqlite3
```

## Useful Commands

- Smoke: `python3 scripts/memory_v5_smoke.py`
- Benchmark: `python3 scripts/memory_v5_benchmark.py --cases docs/memory_v5_benchmark_sample.json`
- Maintenance: `python3 scripts/memory_v5_maintenance.py --all-agents`
- Local doctor: `bash scripts/nexus_doctor_local.sh --check --skip-deploy`

## Verification

Recommended local checks:

```bash
python3 -m unittest tests.test_memory_v5 -v
python3 scripts/memory_v5_smoke.py
```

For broader runtime verification, use:

- `python3 run_tests.py`
- `docs/LOCAL_DEPLOY.md`
- `scripts/deploy_local_v5.sh`
