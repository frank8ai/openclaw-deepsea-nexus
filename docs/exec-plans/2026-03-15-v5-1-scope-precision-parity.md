# Execution Plan - v5.1 Scope Precision Parity

- Date: 2026-03-15
- Slug: `v5-1-scope-precision-parity`
- Status: `closed`
- Plan Type: `parallel delivery`

## 1. Objective

- Primary goal:
  - 把 `memory_v5` 运维脚本的 scope 精度能力对齐到同一标准。
- This round deliverable:
  - `maintenance / backfill_batches / benchmark` 三个入口都支持显式 `app/run/workspace` 选择器。

## 2. Source Of Truth

- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `scripts/memory_v5_maintenance.py`
- `scripts/memory_v5_backfill_batches.py`
- `scripts/memory_v5_benchmark.py`
- `tests/test_memory_v5.py`

## 3. Team Topology

- `Lead` (bridge-main, this session):
  - 负责核心代码实现、测试补齐、最终集成和门禁。
- `Builder-A` (ops docs):
  - 负责运维入口文档（参数/命令样例）同步。
- `Builder-B` (regression review):
  - 负责 regression command matrix 与回归结果回填。

Recommended concurrent size: `3 Codex sessions total` (1 lead + 2 builders).

## 4. File Ownership Contract

`Lead` owned files:

- `scripts/memory_v5_backfill_batches.py`
- `scripts/memory_v5_benchmark.py`
- `tests/test_memory_v5.py`
- `CHANGELOG.md`
- `docs/exec-plans/2026-03-15-v5-1-scope-precision-parity.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-lead-scope-parity.md`

`Builder-A` owned files:

- `docs/LOCAL_DEPLOY.md`
- `docs/sop/MemoryV5_Archive_Backfill_Runbook.md`
- `docs/exec-plans/2026-03-15-v5-1-brief-builder-a-scope-parity.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-scope-parity.md`

`Builder-B` owned files:

- `docs/product/capabilities.md`
- `docs/exec-plans/2026-03-15-v5-1-brief-builder-b-scope-parity.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-scope-parity.md`

Forbidden for all builders:

- touching lead-owned code files
- touching another builder's owned files
- direct merge/conflict-resolution on `main`

## 5. Validation Gate

Builder-A minimum:

- `bash -n scripts/deploy_local_v5.sh`
- `rg -n "run-id|workspace|--app|memory_v5_backfill_batches" docs/LOCAL_DEPLOY.md docs/sop/MemoryV5_Archive_Backfill_Runbook.md`

Builder-B minimum:

- `rg -n "scope|app/run/workspace|lifecycle" docs/product/capabilities.md`

Lead final gate:

- `python3 -m pytest -q tests/test_memory_v5.py -k "BackfillBatchesScript or BenchmarkScript"`
- `python3 -m pytest -q`
- `git diff --check`

## 6. Merge Rule

- Only Lead integrates and publishes final status.
- If any helper needs ownership change, update `ACTIVE-WORKSTREAMS.md` first.

## 7. Closeout Snapshot

- Builder-A handoff: `closed`
- Builder-B handoff: `closed`
- Lead handoff: `closed`
- Final gate:
  - `python3 -m pytest -q tests/test_memory_v5.py -k "BackfillBatchesScript or BenchmarkScript"` => `6 passed`
  - `python3 -m pytest -q` => `256 passed, 4 skipped, 1 warning`
  - `git diff --check`
