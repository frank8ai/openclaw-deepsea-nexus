# Handoff - Builder A Scope Parity Ops Docs

- Date: 2026-03-15
- Status: `closed`

## 1. Current Goal

- What this task is trying to achieve:
  - 同步运维文档到最新 scope 选择器能力。
- What this round was supposed to finish:
  - `LOCAL_DEPLOY` 与 runbook 参数说明一致。

## 2. Source Of Truth

- `docs/exec-plans/2026-03-15-v5-1-scope-precision-parity.md`

## 3. What Was Completed

- Implemented:
  - 运维文档补齐了 scope 精度参数入口，支持对 backfill/maintenance 按 `app/run/workspace` 定位执行。
- Updated docs:
  - `docs/LOCAL_DEPLOY.md`
  - `docs/sop/MemoryV5_Archive_Backfill_Runbook.md`
- Tests / checks run:
  - `bash -n scripts/deploy_local_v5.sh`
  - `rg -n "run-id|workspace|--app|memory_v5_backfill_batches" docs/LOCAL_DEPLOY.md docs/sop/MemoryV5_Archive_Backfill_Runbook.md`

## 4. What Was Not Done

- Intentionally left out:
  - 未改动 runtime 代码。
- Still blocked:
  - 无。
- Not yet validated:
  - 无（文档校验已执行）。

## 5. Recommended Next Step

- Highest-value next action:
  - 跟随 lead 做全量 gate，确认文档变更无回归影响。
- Suggested validation:
  - `bash -n scripts/deploy_local_v5.sh`
  - `rg -n "run-id|workspace|--app|memory_v5_backfill_batches" docs/LOCAL_DEPLOY.md docs/sop/MemoryV5_Archive_Backfill_Runbook.md`
