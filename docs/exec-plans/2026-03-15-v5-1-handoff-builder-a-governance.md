# Handoff - Builder A Governance Runtime

- Date: 2026-03-15
- Status: `closed`

## 1. Current Goal

- What this task is trying to achieve:
  - 完成 `v5.1.0` 的 event/scope/lifecycle runtime 增量优化。
- What this round was supposed to finish:
  - 一组可验证、可集成的 runtime + test 变更。

## 2. Source Of Truth

- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `docs/exec-plans/2026-03-15-v5-1-multi-agent-execution-split.md`
- `tests/test_memory_v5.py`

## 3. What Was Completed

- Implemented:
  - `core/event_bus.py` wildcard subscriptions are operational for governance listeners (`session.*`, `nexus.*`) with sync/async compatibility preserved.
  - `scripts/memory_v5_maintenance.py` now accepts explicit extended scope selectors (`app/run_id/workspace`) for targeted lifecycle audit/archive runs.
  - `scripts/memory_v5_maintenance.py` / `scripts/memory_v5_backfill_batches.py` / `scripts/memory_v5_benchmark.py` now support full-scope discovery for `--all-agents` by reading distinct scope columns from each scope index.
  - `tests/test_memory_v5.py` includes coverage for all-agents extended scope discovery and explicit-scope maintenance execution.
- Updated docs:
  - `CHANGELOG.md` updated with v5.1 governance/runtime closeout notes.
  - this handoff moved from `in-progress` to `closed`.
- Tests / checks run:
  - `python3 -m pytest -q tests/test_memory_v5.py -k "EventBus or MaintenanceScript or BackfillBatchesScript or BenchmarkScript"` => `15 passed`
  - `python3 -m pytest -q` => `251 passed, 4 skipped, 1 warning`
  - `git diff --check`

## 4. What Was Not Done

- Intentionally left out:
  - no broad runtime redesign outside `v5.1.0` governance hardening scope.
- Still blocked:
  - none.
- Not yet validated:
  - none (builder-scope gate + full gate were both executed).

## 5. Key Decisions

- Decision:
  - keep lifecycle maintenance defaults stable (`agent/user`) while adding optional explicit selectors for `app/run/workspace`.
- Reason:
  - preserve existing operator workflows while enabling full-scope precision when needed.
- Future implication:
  - maintenance/backfill/benchmark tooling can audit both base scopes and contextual sub-scopes without introducing separate scripts.

## 6. Risks / Watchouts

- Technical risk:
  - all-agents scope discovery depends on lifecycle tables existing in the scope index; empty/malformed indexes fall back to base scope.
- Operational risk:
  - operators should use explicit `app/run/workspace` filters for targeted interventions to avoid broad-scope dry-runs.
- Context / dependency risk:
  - none open for this slice.

## 7. Recommended Next Step

- Highest-value next action:
  - continue next governance optimization slice from `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`.
- Suggested validation:
  - `python3 -m pytest -q tests/test_memory_v5.py -k "EventBus or MaintenanceScript or BackfillBatchesScript or BenchmarkScript"`
- Suggested owner / context to load first:
  - next Lead + `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
