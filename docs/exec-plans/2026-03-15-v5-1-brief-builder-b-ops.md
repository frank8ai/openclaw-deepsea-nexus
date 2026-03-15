# Codex Agent Brief - Builder B (Ops and Docs Surface)

- Date: 2026-03-15
- Task: `v5-1-governance`
- Role: `builder`
- Status: `active`

## 1. Objective

- What this agent owns:
  - ops/docs surface consistency for the `v5.1.0` lane
- What this round should finish:
  - 完成运维入口与文档口径收口，不改运行时核心逻辑

## 2. Source Of Truth

- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `docs/README.md`
- `docs/LOCAL_DEPLOY.md`
- `docs/product/roadmap.md`
- `README.md`
- `README_EN.md`

## 3. File Ownership

- Owned files:
  - `docs/README.md`
  - `docs/LOCAL_DEPLOY.md`
  - `docs/product/roadmap.md`
  - `README.md`
  - `README_EN.md`
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-ops.md`
- Allowed-to-read files:
  - full repository
- Forbidden-to-edit files:
  - `core/event_bus.py`
  - `memory_v5/service.py`
  - `scripts/memory_v5_maintenance.py`
  - `scripts/memory_v5_backfill_batches.py`
  - `scripts/memory_v5_benchmark.py`
  - `tests/test_memory_v5.py`
  - `CHANGELOG.md`
  - `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`

## 4. Interface Contract

- Inputs expected from other agents:
  - Builder-A 对 runtime 能力的最终状态说明
- Outputs this agent must produce:
  - docs/ops 文本更新 + 一致性扫描结果
- Shared contracts that must not change silently:
  - `v5.0.0` 是 stable baseline
  - `v5.1.0` 是 upgrade lane
  - local deploy / doctor / maintenance operator path

## 5. Constraints

- Product / architecture constraints:
  - 不引入新产品承诺，不虚构未落地能力
- Naming / style constraints:
  - 中文与英文文档版本号和状态叙述保持一致
- Validation constraints:
  - 完成版本口径和入口命令一致性检查

## 6. Validation

- Narrow checks:
  - `bash -n scripts/deploy_local_v5.sh`
  - `rg -n "v5\\.1\\.0|v5\\.0\\.0|upgrade lane|stable baseline" docs README.md README_EN.md`
- Broader checks if needed:
  - `python3 -m pytest -q tests/test_memory_v5.py -k "OperationalEntrypathCleanup"`
- What may remain unverified:
  - runtime path真实执行由 Lead 在最终集成时统一兜底

## 7. Handoff Expectations

- Handoff file path:
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-ops.md`
- Must report:
  - files touched
  - commands run
  - tests run
  - skipped checks
  - blockers

