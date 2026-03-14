# OpenClaw Deep-Sea Nexus Technical Overview

Last updated: 2026-03-14

This document is the technical entrypoint for the current `v5.0.1` release
pack.

## Release Context

- Package release: `5.0.1`
- Async plugin runtime protocol: `3.0.0`
- Current context-governance baseline: `8 / 20 / 35`
- Primary rule source:
  - `sop/Context_Policy_v2_EventDriven.md`

The mixed version numbers are intentional:

- package release tracks the current product/runtime bundle
- plugin protocol tracks the long-lived async runtime contract

## System Model

OpenClaw Deep-Sea Nexus is organized around three ideas:

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
- report-first lifecycle audit for TTL / decay / archive state
- explicit archive maintenance for overdue items

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
- `scripts/memory_v5_maintenance.py`
  - current operator entrypoint for lifecycle audit and explicit archive maintenance
  - can also write JSON / Markdown reports for handoff and audit trails
  - report output now also includes thresholded `status / alerts / hot_scopes / recommendations`
  - `--write-report` defaults those artifacts into `docs/reports/`
- `scripts/context_recall_scorecard.py`
  - current default pack covers 22 repo-local recall/inject golden cases
  - scorecard also reports prompt token/line budget utilization

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
   - recalled items should carry stable `why / source / evidence` traces before
     prompt assembly
   - current inject-side reranking is typed-query, evidence-aware, and
     scope-aware
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
- Memory v5 lifecycle governance is explicit, not silent background mutation
  - recall applies TTL expiry and decay weighting through the same lifecycle rules
  - lifecycle audit is report-first
  - archive moves require an explicit maintenance call
  - item kinds can optionally override global TTL / decay / archive defaults
    without changing the baseline config for all memory
  - resolved lifecycle defaults are persisted on new writes, so later config
    changes do not silently reclassify existing items
  - zero-valued archive-default rows can be audited as backfill candidates and
    only change through an explicit operator backfill step
- runtime tuning is report-first by default
  - current default config does not silently auto-tune SmartContext or ContextEngine
  - tuning must be explicitly enabled
- current recall evaluation is repo-local and repeatable
  - default golden pack covers decision, evidence, constraint, replay,
    continuation, blocker, reversal, stale-summary conflict, stale-evidence conflict,
    contradictory blockers/constraints, evidence-vs-replay conflict,
    cross-session continuity drift, no-scope recovery fallback, and
    branch/topic-switch cases
  - context-starved continuation queries can bias toward scope-matched summaries
    before looser semantic candidates
    - `context_starved_scope`
  - rerank traces can now surface freshness and fallback hints
    - `fresh=current`
    - `fresh=stale`
    - `fallback=summary`
  - scorecard tracks both ranking quality and prompt budget consumption

## Integration Boundaries

### What OpenClaw Deep-Sea Nexus owns

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

- OpenClaw Deep-Sea Nexus provides the policy and local runtime implementation
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
