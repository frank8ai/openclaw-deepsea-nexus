# Codex Agent Brief - Builder A (Scope Parity Ops Docs)

- Date: 2026-03-15
- Task: `v5-1-scope-precision-parity`
- Role: `builder`
- Status: `active`

## 1. Objective

- What this agent owns:
  - `memory_v5` 运维文档参数口径同步。
- What this round should finish:
  - 文档中 backfill/maintenance 参数与脚本实现一致。

## 2. Source Of Truth

- `docs/exec-plans/2026-03-15-v5-1-scope-precision-parity.md`
- `scripts/memory_v5_backfill_batches.py`
- `scripts/memory_v5_maintenance.py`

## 3. File Ownership

- Owned files:
  - `docs/LOCAL_DEPLOY.md`
  - `docs/sop/MemoryV5_Archive_Backfill_Runbook.md`
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-scope-parity.md`
- Allowed-to-read files:
  - full repository
- Forbidden-to-edit files:
  - `scripts/memory_v5_backfill_batches.py`
  - `scripts/memory_v5_benchmark.py`
  - `tests/test_memory_v5.py`
  - `CHANGELOG.md`

## 4. Validation

- `bash -n scripts/deploy_local_v5.sh`
- `rg -n "run-id|workspace|--app|memory_v5_backfill_batches" docs/LOCAL_DEPLOY.md docs/sop/MemoryV5_Archive_Backfill_Runbook.md`

## 5. Handoff

- Handoff path:
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-scope-parity.md`
- Must report:
  - files touched
  - commands run
  - blockers
