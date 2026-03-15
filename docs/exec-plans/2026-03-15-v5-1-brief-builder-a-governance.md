# Codex Agent Brief - Builder A (Governance Runtime)

- Date: 2026-03-15
- Task: `v5-1-governance`
- Role: `builder`
- Status: `active`

## 1. Objective

- What this agent owns:
  - event/scope/lifecycle governance runtime and tests
- What this round should finish:
  - 至少一个可验证 slice，保持 `v5.1.0` 兼容升级路径

## 2. Source Of Truth

- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `docs/exec-plans/2026-03-15-v5-1-multi-agent-execution-split.md`
- `tests/test_memory_v5.py`

## 3. File Ownership

- Owned files:
  - `core/event_bus.py`
  - `memory_v5/service.py`
  - `scripts/memory_v5_maintenance.py`
  - `scripts/memory_v5_backfill_batches.py`
  - `scripts/memory_v5_benchmark.py`
  - `tests/test_memory_v5.py`
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-governance.md`
- Allowed-to-read files:
  - full repository
- Forbidden-to-edit files:
  - `docs/README.md`
  - `docs/LOCAL_DEPLOY.md`
  - `docs/product/roadmap.md`
  - `README.md`
  - `README_EN.md`
  - `CHANGELOG.md`
  - `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`

## 4. Interface Contract

- Inputs expected from other agents:
  - Lead 提供的所有权快照与优先级
- Outputs this agent must produce:
  - runtime/test 变更 + 可重放命令 + 结果
- Shared contracts that must not change silently:
  - Memory v5 lifecycle operator semantics (`audit/archive/backfill`)
  - EventBus wildcard compatibility semantics (sync + async)

## 5. Constraints

- Product / architecture constraints:
  - 不扩展到新产品面，不做大规模重构
- Naming / style constraints:
  - 遵守当前 runtime 命名，不引入无文档新术语
- Validation constraints:
  - 新行为必须在 `tests/test_memory_v5.py` 对应落用例

## 6. Validation

- Narrow checks:
  - `python3 -m pytest -q tests/test_memory_v5.py -k "EventBus or MaintenanceScript or BackfillBatchesScript or BenchmarkScript"`
- Broader checks if needed:
  - `python3 -m pytest -q tests/test_memory_v5.py`
- What may remain unverified:
  - full-suite cross-module regressions由 Lead 最终兜底

## 7. Handoff Expectations

- Handoff file path:
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-governance.md`
- Must report:
  - files touched
  - commands run
  - tests run
  - skipped checks
  - blockers

