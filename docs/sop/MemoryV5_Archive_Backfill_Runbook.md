# Memory V5 Archive-Default Backfill Runbook

## 目标
在不触发 archive move 的前提下，分批回填历史 `archive_after_days=0` 行。

## 适用场景
- lifecycle 报告显示 `archive_backfill_candidates > 0`
- 需要先治理历史生命周期字段，再决定后续 archive 策略

## 前置约束
- 使用当前仓库的 `scripts/memory_v5_backfill_batches.py`
- 使用当前运行 workspace 对应的 `OPENCLAW_WORKSPACE` 和 `NEXUS_VECTOR_DB`
- 先确认 `run_tests.py` 和 deploy smoke 通过

## 执行步骤
1. 先做 lifecycle 基线审计

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_maintenance.py --dry-run --write-report
```

2. 预览首批 backfill 候选（不写入）

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_backfill_batches.py --batch-size 100 --max-batches 5 --write-report
```

3. 显式分批 apply（仅回填，不归档）

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_backfill_batches.py --apply --batch-size 100 --max-batches 5 --write-report
```

4. 回填后复审 lifecycle

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_maintenance.py --dry-run --write-report
```

## 验收标准
- `memory_v5_backfill_*` 报告里：
  - `totals.updated > 0`
  - `totals.failed == 0`
- 二次 lifecycle 报告里：
  - `archive_backfill_candidates` 明显下降或归零
- 回填过程中不出现 archive move（该脚本本身不会执行 archive）

## 失败处理
- 若 `failed > 0`：
  - 默认策略是停止后复查 `failed_ids`
  - 定位 scope / item 是否存在并发写入、DB 锁或路径错误
- 若需要继续未完成批次：
  - 修复问题后重复执行同一 `--apply` 命令
  - 已成功回填项不会重复成为候选

## 备注
- 回填是生命周期字段治理动作，不等同于归档执行。
- 归档执行应使用 `memory_v5_maintenance.py` 的 explicit archive 路径，单独评审后进行。
