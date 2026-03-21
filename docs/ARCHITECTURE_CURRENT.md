# Deep-Sea Nexus Current Architecture

Last updated: 2026-03-18

This document describes the current runtime architecture for the
`v5.3.0` release pack.

For a shorter technical entrypoint, read `TECHNICAL_OVERVIEW_CURRENT.md`
first.

## Scope

This document is the current implementation source of truth for:

- package structure
- runtime layers
- data and control flow
- current vs compatibility boundaries

It does not replace:

- product docs in `product/`
- public API contract in `API_CURRENT.md`
- policy rules in `sop/Context_Policy_v2_EventDriven.md`

## Version Model

- Package release: `5.3.0`
- Async plugin runtime protocol: `3.0.0`
- Current context-governance baseline: `8 / 20 / 35`

The release number tracks the current product/runtime bundle. The plugin
protocol tracks the long-lived async runtime contract.

## Runtime Layers

### 1. Package-root public surface

Primary user-facing imports are re-exported from the package root:

- `__init__.py`
- `compat.py`

Current supported surface includes:

- sync compatibility API
- async app API
- Memory v5 scoped API
- CLI

New code should prefer package-root imports over deep internal imports.

### 2. Async application container

The async runtime container lives in:

- `app.py`
- `core/plugin_system.py`
- `core/config_manager.py`
- `core/event_bus.py`

`create_app()` builds the application, loads plugins, and exposes them through
`app.plugins`.

Important runtime property:

- sync compatibility calls and async app instances share one in-process plugin
  registry
- repeated initialization in one process reuses plugin objects instead of
  creating fully isolated runtimes

### 3. Memory core

The current semantic memory implementation is centered on:

- `plugins/nexus_core_plugin.py`

It owns:

- durable write behavior
- hybrid retrieval
- degraded lexical fallback
- write guard behavior
- Memory v5 fusion on the active runtime path

This is the current memory core. Historical `nexus_core.py` variants should be
treated as compatibility or archaeology, not primary runtime design.

### 4. Context governance and context assembly

The current context layer is composed of:

- `plugins/smart_context.py`
- `plugins/context_engine.py`
- `plugins/context_engine_runtime.py`
- `plugins/smart_context_runtime.py`
- `plugins/smart_context_*`

Together these modules own:

- per-round state evaluation
- summary vs compressed behavior
- rescue-before-compress behavior
- injection gating and budget trimming
- summary / evidence / replay aware assembly
- evidence-gated durable decision writes
- budgeted compatibility-context assembly for older helper entrypoints

The current policy contract is externalized in:

- `sop/Context_Policy_v2_EventDriven.md`

The runtime implementation must conform to that policy instead of inventing a
separate hidden rule set.

### 5. Runtime middleware

Current tool-output middleware lives in:

- `plugins/runtime_middleware_plugin.py`

Its role is to provide:

- tool-event normalization
- RTK-style output compression
- token-before / token-after accounting
- token-aware capture gating
- evidence snapshot persistence for tool output
- OpenClaw-first tool-call adaptation

Current boundary:

- internal plugin, not public API
- capture-side only in `v5.3.0`
- does not replace current recall ranking or inject policy

### 6. Execution guard

Current tool-risk guard lives in:

- `plugins/execution_guard_plugin.py`

Its role is to provide:

- report-first risk classification for tool events
- secrets / credential / boundary / second-brain asset checks
- `allow / ask / block / context` decisions
- execution-governor guardrails export
- structured guard metadata attached to tool events

Current boundary:

- internal plugin, not public API
- report-only by default in `v5.3.0`
- does not hard-stop host execution unless a future enforcement mode is enabled

### 7. Memory v5 scoped store

Current durable scoped memory lives under:

- `memory_v5/`

Its role is to provide:

- `agent_id / user_id` isolation
- resource / item / category organization
- scoped retrieval and maintenance
- shared lifecycle classification for TTL / decay / archive state
- explicit archive maintenance without silent background mutation

Main concepts:

- `MemoryScope`
- `MemoryV5Service`
- optional `item_kind_defaults`
  - lets specific memory kinds override global TTL / decay / archive defaults
    without changing the overall runtime baseline
  - resolved lifecycle defaults are persisted per item on new writes, so
    later config changes do not silently rewrite prior archive boundaries
  - zero-valued archive rows remain explicit operator backfill candidates instead
    of being silently reinterpreted at runtime

### 8. Operational layer

Operational entrypoints include:

- `run_tests.py`
- `scripts/deploy_local_v5.sh`
- `scripts/nexus_doctor_local.sh`
- `scripts/memory_v5_smoke.py`
- `scripts/memory_v5_benchmark.py`
- `scripts/memory_v5_maintenance.py`
  - operator-facing lifecycle audit / explicit archive entrypoint
  - can emit JSON / Markdown artifacts for bounded operator review
  - default report drop location is repo-local `docs/reports/` when `--write-report` is used
  - can also explicitly backfill zero-valued archive defaults without auto-archiving in the same pass
- maintenance and compatibility scripts under `scripts/`
- `scripts/context_recall_scorecard.py`
  - evaluates repo-local recall/inject golden cases and prompt budget ratios
  - current baseline covers 22 repo-local cases across
    decision/evidence/constraint/replay, continuation/blocker/reversal,
    stale-summary/stale-evidence, contradictory blocker/constraint,
    cross-session drift, evidence-vs-replay conflict, no-scope recovery
    fallback, and topic-switch slices

This layer is part of the current release because the product promise includes
local verification and operability, not just library APIs.

## Main Data Model

### Working context

Ephemeral typed state used to keep long tasks continuous:

- goal
- status
- constraints
- blockers
- next actions
- open questions
- evidence pointers
- replay command

This state is especially important before compression.

### Durable decision layer

Stable decisions that remain meaningful after the immediate task window.

A durable decision should include:

- decision
- why
- relevant constraint
- evidence pointer
- reversal condition

### Evidence layer

Raw operational material stays outside summaries:

- files
- logs
- commands
- artifacts
- reports
- session traces

The runtime should preserve pointers, not embed large raw evidence payloads in
summary state.

### Scoped memory layout

Current scoped filesystem layout is rooted at:

- `memory/95_MemoryV5/<agent_id>/<user_id>/`

Scope hardening notes:

- path segments are normalized/sanitized before creating directories
- `app_id / run_id / workspace` stay in SQLite scope columns and are used in
  scope-key category IDs to prevent cross-scope category overwrite

Key subtrees include:

- `resources/`
- `items/`
- `items_archive/`
- `categories/`
- `graphs/`
- `index.sqlite3`

## Main Runtime Flows

### Capture / write flow

1. A caller enters through sync API, async plugin, or Memory v5 service.
2. Runtime normalizes the write into the current memory path.
3. SmartContext may emit summaries or decision blocks.
   - decision blocks only persist as durable decision material when evidence or
     replay support exists
4. Memory core persists searchable artifacts.
5. Memory v5 stores scoped durable items when enabled.

### Recall / inject flow

1. Query enters sync API, async runtime, or context assembly path.
2. Memory core resolves hybrid recall candidates.
3. SmartContext / ContextEngine decide whether to inject.
   - recalled and graph-injected items should carry stable
     `why / source / evidence` traces
   - current reranking uses typed-query intent plus evidence/scope hints before
     final budget trimming
   - repo-local scorecard coverage now includes research continuation,
     constraint/replay resumption, blocker recovery, multi-reversal,
     stale-summary/evidence conflict, contradictory blocker/constraint,
     cross-session continuity drift, evidence-vs-replay conflict,
     no-scope recovery fallback, and branch/topic switch slices
   - context-starved continuation queries can award an extra scope-matched
     summary bonus before looser lexical fallback
     - `context_starved_scope`
   - freshness hints and resume-without-replay fallback now influence rerank when
     the query explicitly asks for current state or a resume path
     - traces can surface `fresh=current|stale` and `fallback=summary`
4. Budgeting and trimming happen before final prompt assembly.
   - compatibility helpers must reuse this path instead of formatting their own
     unmanaged recall block
5. Memory v5 recall applies the same lifecycle classification before final hits
   are returned.
   - TTL-expired items are filtered
   - older items can decay instead of being hard-dropped

### Compression / rescue flow

1. Runtime evaluates rounds and context pressure.
2. Current baseline applies:
   - `0-8`: full
   - `9-20`: summary
   - `21-35`: compressed summary + rescued state
   - `>35`: compressed mode with stronger archive posture
3. Before compression, typed state is rescued.
4. Output keeps evidence pointers and replay hints, not raw logs.
5. Lifecycle maintenance stays explicit.
   - `audit_lifecycle()` reports TTL / decay / archive posture
   - `archive_due_items()` only archives when explicitly invoked

## OpenClaw Integration Boundary

Deep-Sea Nexus integrates with OpenClaw, but the boundary is explicit.

### Deep-Sea Nexus owns

- local memory model
- public package surface
- local context-governance logic
- current policy implementation
- local verification toolchain

### OpenClaw / surrounding runtime owns

- hook registration and message routing
- outer event timing
- broader execution-governor policy
- top-level agent orchestration outside the package

### Shared contract

- Deep-Sea Nexus provides the local memory + context-governance implementation
- OpenClaw provides the surrounding event and prompt lifecycle

## Current vs Compatibility

### Treat as current

- package-root imports
- `plugins/nexus_core_plugin.py`
- current `smart_context` / `context_engine` modules
- `memory_v5/`
- current docs in this release pack

### Treat as compatibility or archaeology

- historical `nexus_core.py` variants
- old architecture/PRD/usage docs
- older version-labelled SmartContext design notes
- old tests and scripts whose main purpose is migration support

Compatibility paths still matter because gradual migration is part of the
product, but they should not drive new architecture decisions.

## Refactor Guardrails

- Do not build new code against historical internals when a package-root or
  current plugin path exists.
- Do not treat archive docs as runtime truth.
- Keep sync API behavior stable unless an explicit breaking migration is
  planned.
- Keep context-governance behavior aligned with the canonical policy doc.
- Keep runtime tuning defaults report-first unless an explicit operator opt-in
  enables auto-tune writes.

## Read Next

- release-level technical map:
  - `TECHNICAL_OVERVIEW_CURRENT.md`
- public API:
  - `API_CURRENT.md`
- context policy:
  - `sop/Context_Policy_v2_EventDriven.md`
- local deploy and validation:
  - `LOCAL_DEPLOY.md`
