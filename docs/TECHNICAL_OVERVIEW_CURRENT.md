# Deep-Sea Nexus Technical Overview

Last updated: 2026-03-14

This document is the technical entrypoint for the current `v5.0.0` release
pack.

## Release Context

- Package release: `5.0.0`
- Async plugin runtime protocol: `3.0.0`
- Current context-governance baseline: `8 / 20 / 35`
- Primary rule source:
  - `sop/Context_Policy_v2_EventDriven.md`

The mixed version numbers are intentional:

- package release tracks the current product/runtime bundle
- plugin protocol tracks the long-lived async runtime contract

## System Model

Deep-Sea Nexus is organized around three ideas:

### 1. Public access surfaces

- Sync compatibility API
  - existing automation can keep using `nexus_init / nexus_recall / nexus_add`
- Async application runtime
  - `create_app()` and plugin lifecycle
- Memory v5 scoped API
  - `MemoryScope / MemoryV5Service`

### 2. Three-layer memory model

- `Working Context`
  - current goal, status, constraints, blockers, next, questions
- `Durable Decision`
  - stable decisions that carry evidence pointers
- `Evidence Store`
  - raw files, logs, commands, reports, artifacts

### 3. Context governance loop

- capture
- recall
- inject
- compress
- rescue
- replay

All durable memory should flow through that loop, not around it.

## Current Runtime Subsystems

### Memory core

Main responsibility:

- durable recall and write behavior
- degraded fallback behavior
- hybrid retrieval
- Memory v5 fusion

Current implementation center:

- `plugins/nexus_core_plugin.py`

### Context governance

Main responsibility:

- decide what stays full, summary, or compressed
- preserve typed state before compression
- assemble injected context within budget
- surface replay/evidence-aware summaries

Current implementation centers:

- `plugins/smart_context.py`
- `plugins/context_engine.py`
- `plugins/smart_context_*`
- `plugins/context_engine_runtime.py`
- `plugins/smart_context_runtime.py`

### Memory v5 scoped store

Main responsibility:

- `agent_id / user_id` isolation
- resource / item / category organization
- SQLite-backed scoped retrieval

Current implementation center:

- `memory_v5/`

### Operations and verification

Main responsibility:

- local deploy
- doctor / health
- smoke / benchmark
- maintenance scripts

Current entrypoints:

- `scripts/deploy_local_v5.sh`
- `scripts/nexus_doctor_local.sh`
- `scripts/memory_v5_smoke.py`
- `scripts/memory_v5_benchmark.py`

## Main Data / Control Flows

### Write / capture flow

1. User or automation calls sync API, async plugin, or Memory v5 service.
2. Runtime normalizes the input into current write path(s).
3. SmartContext may emit summaries or decision blocks.
   - durable decision blocks are evidence-gated
4. Memory core persists searchable artifacts.
5. Memory v5 stores scoped durable items when enabled.

### Recall / inject flow

1. Query enters sync API, async runtime, or context assembly path.
2. Memory core returns hybrid recall candidates.
3. SmartContext / ContextEngine decide whether and how much to inject.
4. Final prompt receives only budgeted, trimmed, current-context-safe material.
   - compatibility helpers should still end up on this budgeted path

### Compression / rescue flow

1. Runtime evaluates rounds and pressure.
2. `8 / 20 / 35` determines full, summary, and compressed phases.
3. Before compression, typed state is rescued:
   - `goal/status/constraints/blockers/decisions/next/questions/evidence/replay`
4. Summary output keeps pointers, not raw evidence payloads.

## Current Governance Notes

- durable decision storage is evidence-gated
  - no evidence pointer or replay hint -> do not write the decision as L2 durable memory
- runtime tuning is report-first by default
  - current default config does not silently auto-tune SmartContext or ContextEngine
  - tuning must be explicitly enabled

## Integration Boundaries

### What Deep-Sea Nexus owns

- local memory and recall behavior
- public package entrypoints
- context-governance logic
- scoped memory model
- local verification toolchain

### What OpenClaw or surrounding runtime owns

- message routing into hooks
- hook lifecycle and event timing
- broader execution-governor policy
- top-level agent orchestration outside the package

### Contract between them

- Deep-Sea Nexus provides the policy and local runtime implementation
- OpenClaw hook/runtime provides the outer event and prompt assembly environment

## Compatibility Boundaries

Current release still keeps compatibility paths alive, but they are not the
center of the current design.

Treat these as compatibility or migration surfaces, not new implementation
targets:

- historical sync-oriented wrappers
- legacy docs under older version names
- old architecture and PRD documents

Prefer for new work:

- package-root imports
- `plugins/nexus_core_plugin.py`
- current SmartContext / ContextEngine modules
- current docs in this release pack

## Read Next

- system structure details:
  - `ARCHITECTURE_CURRENT.md`
- supported public interfaces:
  - `API_CURRENT.md`
- context governance rules:
  - `sop/Context_Policy_v2_EventDriven.md`
- local deploy and verification:
  - `LOCAL_DEPLOY.md`
