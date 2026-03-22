# Deepsea-Nexus Capability Autotune Lab Design

**Date:** 2026-03-22
**Scope:** `C:/Users/frank/.codex/skills/skills/deepsea-nexus`
**Status:** approved for implementation

## Goal

Add an internal, report-first autotune lab that improves Deepsea-Nexus memory and context-management quality offline, with the first optimization focus on compression rules for tool-output capture.

## Problem

Deepsea-Nexus already has:

- evidence-gated durable memory
- SmartContext / ContextEngine governance
- RTK-style `runtime_middleware`
- report-first operator tooling

What it does not have is a repeatable offline loop that can:

- score current compression behavior against golden cases
- compare candidate rule sets without mutating production state
- recommend better compression/context settings with evidence

This gap matters most in high-noise tool output. Poor compression loses blockers, failures, and diffs; overly conservative compression wastes prompt budget and weakens long-session continuity.

## Design Principles

- report-first only; no silent runtime drift
- production memory/runtime remain the system of record
- autotune outputs recommendations, not enforced changes
- prioritize compression-rule quality first, then context-management signals
- reuse existing Deepsea scorecard patterns instead of inventing a separate evaluation style

## Architecture

Add a new internal subsystem: `capability_autotune_lab`.

It has four parts:

1. `CapabilityAutotuneLabPlugin`
   - internal plugin
   - owns health summary and latest report pointers
   - exposes report-first lab status to CLI/runtime observability

2. Configurable compression profiles in `runtime_middleware`
   - make RTK-style compression rules tunable by config
   - expose parameters like preview sizes, failure caps, dedupe caps, and truncation behavior

3. Offline experiment runner script
   - runs baseline plus candidate profile mutations
   - scores compression behavior against golden cases
   - optionally includes existing context recall scorecard in the overall report

4. Golden eval packs
   - repo-local JSON cases for tool-output compression
   - binary checks only: preserve failures, preserve changed files, keep key evidence, reduce token cost

## Data Flow

1. Runner loads current config and golden eval pack.
2. Runner constructs experiments:
   - baseline
   - bounded candidate mutations
3. Each experiment runs:
   - compression-rule eval
   - optional context recall scorecard snapshot
4. Scores are aggregated into:
   - per-experiment pass rate
   - compression token savings
   - failed eval categories
5. Best candidate becomes `promote_recommended`; all others are `discard` or `keep_for_lab`.
6. Report artifacts are written locally; plugin/CLI surface the latest summary.

## Initial Optimization Surface

### Compression rules

- `git_diff` preview capacity
- `grep` unique match cap
- `test/lint` failure-line cap
- `build/container/network` preview cap
- repeated-line dedupe policy
- summary truncation behavior

### Context-management signals

Initial v1 only observes these, it does not auto-tune them:

- prompt budget ratio from `context_recall_scorecard`
- line-budget ratio from `context_recall_scorecard`
- whether compression candidates would conflict with recall budget goals

## Non-Goals

- no self-modifying production config
- no auto-writing durable memory from lab output
- no live mutation of `MemoryV5Service`
- no runtime prompt self-editing loop
- no host-enforced optimizer behavior

## Files

### New

- `plugins/capability_autotune_lab_plugin.py`
- `scripts/capability_autotune_lab.py`
- `scripts/capability_autotune_report.py`
- `docs/evals/runtime_middleware_compression_golden_cases.json`
- `docs/releases/V5_4_0_RELEASE_2026-03-22.md`
- `docs/releases/V5_4_0_RELEASE_2026-03-22_ZH.md`

### Modified

- `plugins/runtime_middleware_plugin.py`
- `app.py`
- `__main__.py`
- `core/config_manager.py`
- `config.json`
- `_version.py`
- `README.md`
- `docs/TECHNICAL_OVERVIEW_CURRENT.md`
- `docs/ARCHITECTURE_CURRENT.md`
- `docs/LOCAL_DEPLOY.md`
- `tests/test_memory_v5.py`

## Validation

- unit tests for config-driven compression behavior
- unit tests for compression golden-case scoring
- unit tests for CLI path/health exposure
- focused script test for report generation
- full `tests.test_memory_v5` run before completion

## Acceptance Criteria

- Deepsea can evaluate multiple compression candidates offline from repo-local fixtures
- runtime middleware compression behavior is tunable by config, not hardcoded only
- lab outputs a machine-readable recommendation and human-readable report
- CLI exposes latest autotune report path and summary
- production runtime remains report-first and unchanged unless a human applies the recommendation
