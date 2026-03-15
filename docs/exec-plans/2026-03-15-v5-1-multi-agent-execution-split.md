# Execution Plan - v5.1 Multi-Agent Execution Split

- Date: 2026-03-15
- Slug: `v5-1-multi-agent-execution-split`
- Status: `ready`
- Plan Type: `parallel delivery`

## 1. Objective

- Primary goal:
  - 在不打断当前主计划推进的前提下，将 `v5.1.0` 升级 lane 拆成可并行的、低冲突的执行单元。
- This round deliverable:
  - 固化 `Lead + Builder-A + Builder-B` 的文件所有权、验收门槛、交接节奏和集成顺序。

## 2. Source Of Truth

- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `docs/exec-plans/2026-03-14-core-context-governance-polish.md`
- `docs/README.md`
- `docs/LOCAL_DEPLOY.md`
- `tests/test_memory_v5.py`

## 3. Team Topology

- `Lead` (existing codex already driving the plan):
  - 维护主计划、分配边界、做最终集成和最终验证。
- `Builder-A` (governance runtime):
  - 负责 event/scope/lifecycle 代码与测试。
- `Builder-B` (ops/docs surface):
  - 负责运维入口与文档一致性收口。

Recommended concurrent size: `3 Codex sessions total` (1 lead + 2 builders).

## 4. File Ownership Contract

`Lead` owned files:

- `docs/exec-plans/2026-03-15-v5-1-multi-agent-execution-split.md`
- `docs/exec-plans/2026-03-15-v5-1-brief-lead.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-lead.md`
- `docs/releases/V5_1_0_UPGRADE_PLAN_2026-03-14.md`
- `CHANGELOG.md`

`Builder-A` owned files:

- `core/event_bus.py`
- `memory_v5/service.py`
- `scripts/memory_v5_maintenance.py`
- `scripts/memory_v5_backfill_batches.py`
- `scripts/memory_v5_benchmark.py`
- `tests/test_memory_v5.py`
- `docs/exec-plans/2026-03-15-v5-1-brief-builder-a-governance.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-builder-a-governance.md`

`Builder-B` owned files:

- `docs/README.md`
- `docs/LOCAL_DEPLOY.md`
- `docs/product/roadmap.md`
- `README.md`
- `README_EN.md`
- `docs/exec-plans/2026-03-15-v5-1-brief-builder-b-ops.md`
- `docs/exec-plans/2026-03-15-v5-1-handoff-builder-b-ops.md`

Forbidden for all builders:

- touching another builder's owned files in the same round
- direct force-push or conflict-resolution on shared integration branch

## 5. Worktree Layout

- repo path:
  - `/Users/yizhi/bridge-codex-entity/deepsea-nexus`
- bootstrap command:
  - `/Users/yizhi/scripts/codex-multi-agent-bootstrap.sh /Users/yizhi/bridge-codex-entity/deepsea-nexus v5-1-governance lead builder-a builder-b`
- expected branch names:
  - `codex/v5-1-governance/lead`
  - `codex/v5-1-governance/builder-a`
  - `codex/v5-1-governance/builder-b`
- shared registry:
  - `/Users/yizhi/worktrees/deepsea-nexus/ACTIVE-WORKSTREAMS.md`

## 6. Execution Loop

1. Lead posts the latest ownership snapshot in `ACTIVE-WORKSTREAMS.md`.
2. Builder-A and Builder-B work in parallel and only edit owned files.
3. Each builder updates its handoff file before pause or completion.
4. Lead integrates Builder-A first (contracts/runtime/tests), then Builder-B (docs/ops wording).
5. Lead runs final validation gate and publishes closeout handoff.

## 7. Validation Gate

Builder-A minimum:

- `python3 -m pytest -q tests/test_memory_v5.py -k "EventBus or MaintenanceScript or BackfillBatchesScript or BenchmarkScript"`

Builder-B minimum:

- `bash -n scripts/deploy_local_v5.sh`
- docs consistency check:
  - `rg -n "v5\\.1\\.0|v5\\.0\\.0|upgrade lane|stable baseline" docs README.md README_EN.md`

Lead final gate:

- `python3 -m pytest -q`
- `git diff --check`

## 8. Merge Rule

- Only Lead can merge branches and resolve conflicts.
- If a builder needs a file outside owned scope, it must request reassignment in `ACTIVE-WORKSTREAMS.md` first.
- Any ownership conflict means pause parallel work and re-split before continuing.
