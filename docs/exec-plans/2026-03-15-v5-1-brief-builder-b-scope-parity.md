# Codex Agent Brief - Builder B (Scope Parity Review)

- Date: 2026-03-15
- Task: `v5-1-scope-precision-parity`
- Role: `builder`
- Status: `active`

## 1. Objective

- What this agent owns:
  - 产品能力文档中的 scope 精度描述回填。
- What this round should finish:
  - capabilities 文档与 runtime 行为一致。

## 2. Source Of Truth

- `docs/exec-plans/2026-03-15-v5-1-scope-precision-parity.md`
- `scripts/memory_v5_backfill_batches.py`
- `scripts/memory_v5_benchmark.py`

## 3. File Ownership

- Owned files:
  - `docs/product/capabilities.md`
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-scope-parity.md`
- Allowed-to-read files:
  - full repository
- Forbidden-to-edit files:
  - `scripts/memory_v5_backfill_batches.py`
  - `scripts/memory_v5_benchmark.py`
  - `tests/test_memory_v5.py`
  - `CHANGELOG.md`

## 4. Validation

- `rg -n "scope|app/run/workspace|lifecycle" docs/product/capabilities.md`

## 5. Handoff

- Handoff path:
  - `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-scope-parity.md`
- Must report:
  - files touched
  - commands run
  - blockers
