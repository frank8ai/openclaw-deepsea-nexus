# Deep-Sea Nexus v5.1.0 本地部署

## 目标
将当前仓库版本部署到本地 OpenClaw 工作区，并确保门禁与运行态可用。

## 前置条件
- 路径：当前仓库根目录
- workspace 解析优先级：
  - `OPENCLAW_WORKSPACE`
  - 当前仓库位置（若仓库位于 `<workspace>/skills/deepsea-nexus`，deploy/doctor 会自动推断这个 `<workspace>`）
  - 回退 `OPENCLAW_HOME/workspace`
- 当前本机 gemini agent 常用工作区：`~/.openclaw/workspace-gemini`
- Python：`3.8+`
- 可选依赖：`chromadb`、`sentence-transformers`（缺失时自动降级，不阻塞启动）

## 一键部署
在仓库根目录执行：

```bash
bash scripts/deploy_local_v5.sh --full
```

说明：
- `--full`：执行 `run_tests.py` 全量门禁 + 运行态 smoke 检查
- `--quick`：仅执行 `tests/test_memory_v5.py` + 运行态 smoke + v5 benchmark
- `--with-lifecycle-audit`：在 deploy gate 之后追加一次 `memory_v5_maintenance.py --dry-run --write-report`
- `--lifecycle-all-agents`：把上面的 lifecycle audit 扩到所有已发现的 Memory v5 scope
- 脚本会优先使用 `NEXUS_PYTHON_PATH`，失败时自动回退到 `python3`，并自动导出解析后的 `OPENCLAW_WORKSPACE`
- 默认主库目标：
  - `NEXUS_VECTOR_DB=<resolved workspace>/memory/.vector_db_restored`
  - `NEXUS_COLLECTION=deepsea_nexus_restored`
- 当前运行时默认路径优先跟随：
  - `OPENCLAW_WORKSPACE`
  - 其回退 `OPENCLAW_HOME`

如需显式指定：

```bash
OPENCLAW_WORKSPACE=~/.openclaw/workspace-gemini \
NEXUS_PYTHON_PATH=~/miniconda3/envs/openclaw-nexus/bin/python \
NEXUS_VECTOR_DB=~/.openclaw/workspace-gemini/memory/.vector_db_restored \
NEXUS_COLLECTION=deepsea_nexus_restored \
bash scripts/deploy_local_v5.sh --full --with-lifecycle-audit
```

## 一键巡检 + 自动修复（推荐日常）
在仓库根目录执行：

```bash
# 只巡检（只读）
bash scripts/nexus_doctor_local.sh --check

# 巡检并自动修复（默认）
bash scripts/nexus_doctor_local.sh --repair
```

说明：
- 会校验并修复 Gateway 环境变量：
  - `NEXUS_PYTHON_PATH`
  - `NEXUS_VECTOR_DB`
  - `NEXUS_COLLECTION`
- 会校验并拉起关键 Hook：
  - `context-optimizer`
  - `deepsea-rag-recall`
- 会检查主向量库计数与 `nexus_init/nexus_health` 状态
- `--repair` 模式下默认包含一次 `deploy_local_v5.sh --quick` 快速门禁
- 可加 `--skip-deploy` 跳过快速门禁

## 写入护栏（防止写错库）
当前版本默认启用写入护栏，所有主要写入入口都会检查：

- 必须存在：`NEXUS_VECTOR_DB`、`NEXUS_COLLECTION`
- 默认主库目标：
  - `NEXUS_VECTOR_DB=<resolved workspace>/memory/.vector_db_restored`
  - `NEXUS_COLLECTION=deepsea_nexus_restored`

违规会被阻断并记录到：
- `~/.openclaw/workspace/logs/nexus_write_guard_alerts.jsonl`

可选开关：
- `NEXUS_ENFORCE_WRITE_GUARD=0`：关闭护栏（不建议生产）
- `NEXUS_WRITE_GUARD_ALLOW_ANY=1`：允许非主库目标（仅迁移/实验）

## 最近摘要跨库审计与迁移
用于确认“最近摘要是否都在主库”，并可迁移缺失项回主库：

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/audit_recent_summaries.py --days 7 --migrate-missing
```

输出：
- JSON 报告：`docs/reports/summary_audit_<timestamp>.json`
- Markdown 报告：`docs/reports/summary_audit_<timestamp>.md`
- 若发生迁移，会生成回滚脚本：`docs/reports/summary_audit_<timestamp>_rollback.sh`

## Memory v5 生命周期巡检
用于审计当前 scope 的 `TTL / decay / archive` 状态，并显式执行 overdue archive：

```bash
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_maintenance.py --dry-run --write-report
```

说明：
- `--dry-run` 只输出候选，不实际归档
- 去掉 `--dry-run` 才会执行显式 archive move
- `--exclude-ttl-expired` 可把本轮维护限定为纯 age-based archive candidate
- `--apply-archive-backfill` 会显式把 older zero-valued `archive_after_days` rows 回填为当前解析后的 archive defaults
- `--app` / `--run-id` / `--workspace` 可把巡检限定到单个扩展 scope
- backfill 不会在同一次 maintenance 中自动继续 archive 这些 rows；如需归档，需下一次显式 audit/apply

默认输出：
- JSON 报告：`docs/reports/memory_v5_lifecycle_<timestamp>.json`
- Markdown 报告：`docs/reports/memory_v5_lifecycle_<timestamp>.md`

## Memory v5 archive-default backfill（分批执行）
用于仅回填 `archive_after_days=0` 的历史行，不执行 archive move。

```bash
# 先预览首批（不写入）
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_backfill_batches.py --batch-size 100 --max-batches 5 --write-report

# 只看某个扩展 scope（示例）
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_backfill_batches.py --app relay --run-id run-42 --workspace workspace-a --batch-size 100 --max-batches 5 --write-report
```

```bash
# 显式执行分批回填（只回填，不归档）
${NEXUS_PYTHON_PATH:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/.venv-nexus/bin/python3} \
  scripts/memory_v5_backfill_batches.py --apply --batch-size 100 --max-batches 5 --write-report
```

说明：
- 默认是 preview 模式，仅输出当前首批候选
- 只有加 `--apply` 才会写入回填
- 该脚本不会执行 archive move；即使存在 `archive_due` 也不会在这里归档
- `--app` / `--run-id` / `--workspace` 可把回填限定在单个扩展 scope
- `--batch-size` 控制每批最多处理条数
- `--max-batches` 控制单次运行最多处理多少批
- 遇到失败默认停止；如需继续批次可加 `--continue-on-failure`
- 默认报告前缀：`docs/reports/memory_v5_backfill_<timestamp>.{json,md}`

推荐执行顺序：
1. 先跑 lifecycle dry-run，确认 `archive_backfill_candidates` 规模
2. 先跑 backfill preview，核对首批 candidate ids
3. 再跑 `--apply` 分批回填
4. 回填完成后再跑 lifecycle dry-run，确认 `archive_backfill_candidates` 下降或归零

详细步骤见：
- `docs/sop/MemoryV5_Archive_Backfill_Runbook.md`

## 计数口径说明（避免误判）
主库条数不是常量。以下动作会导致 `deepsea_nexus_restored` 的 count 小幅变化：

- smoke/probe 写入验证 marker
- 巡查脚本写入测试样本
- 新会话摘要落库

因此验收优先级应为：
1. 路径正确（`NEXUS_VECTOR_DB`）
2. 集合正确（`NEXUS_COLLECTION`）
3. 可写可读（`write_read_probe: true`）
4. count 为正且持续可查询

不建议把某个固定 count（例如 1234/1236/2800）当成唯一正确性标准。

## 旧链路清理策略（先归档，后删除）
为防误删，旧 hook/旧目录按“3天观察窗口”处理：

- 归档根目录：`~/.openclaw/workspace/.tmp/legacy-hooks-archive`
- 清单文件：`archive_manifest.json`（包含 `delete_after`）
- 自动清理脚本：`~/.openclaw/workspace/scripts/cleanup_legacy_archives.py`
- 定时清理日志：`~/.openclaw/workspace/logs/archive_cleanup.log`

这套策略确保：出现回归时可快速回滚，稳定后再自动清理。

## 推荐运行参数（智能上下文）
当前建议生产参数（已在 `config.json` 默认值中）：

- canonical policy: `docs/sop/Context_Policy_v2_EventDriven.md`
- `smart_context.full_rounds = 8`
- `smart_context.summary_rounds = 20`
- `smart_context.compress_after_rounds = 35`
- `smart_context.trigger_soft_ratio = 0.7`
- `smart_context.trigger_hard_ratio = 0.85`
- 结构化摘要字段：
  - `summary/goal/status/decisions/constraints/blockers/next_actions/questions/evidence/replay`
- 抢救开关：
  - `rescue_enabled/rescue_gold/rescue_decisions/rescue_next_actions`
  - `rescue_goal/rescue_status/rescue_constraints/rescue_blockers/rescue_evidence/rescue_replay`
- 默认调参策略：
  - `smart_context.inject_ratio_auto_tune = false`
  - `context_engine.auto_tune_enabled = false`
  - 若要自动调参，需显式启用；当前默认是 report-first

## 成功判定
- `run_tests.py` 结尾输出 `ALL TESTS PASSED`
- 脚本输出 JSON 状态，至少满足：
  - `available: true`
  - `initialized: true`
  - `plugin_version: "3.0.0"`（插件协议版本）
  - `package_version: "5.1.0"`（当前升级版本）
- v5 benchmark 输出至少满足：
  - `any_scope_hit > 0`
  - `any_scope_score > 0`

## 生效验收（白盒）
部署完成后，建议执行一次白盒确认（不是只看 status）：

```bash
python3 - <<'PY'
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills"))
from deepsea_nexus import nexus_init
from deepsea_nexus.core.plugin_system import get_plugin_registry

assert nexus_init()
sc = get_plugin_registry().get("smart_context")
print("rounds:", sc.config.full_rounds, sc.config.summary_rounds, sc.config.compress_after_rounds)
print("summary_fields:", sc.config.summary_template_fields)
print(
    "rescue:",
    sc.config.rescue_enabled,
    sc.config.rescue_gold,
    sc.config.rescue_decisions,
    sc.config.rescue_next_actions,
    sc.config.rescue_goal,
    sc.config.rescue_status,
    sc.config.rescue_constraints,
    sc.config.rescue_blockers,
    sc.config.rescue_evidence,
    sc.config.rescue_replay,
)
PY
```

期望输出：
- `rounds: 8 20 35`
- `summary_fields:` 包含 `goal/status/constraints/blockers/evidence/replay`
- `rescue:` 输出全部为 `True`

## OpenClaw 侧联动（本机）
如果你希望输入侧先压缩上下文，再由 Deep-Sea 注入记忆，建议启用：

- `hooks.internal.entries.context-optimizer.enabled = true`
- `hooks.internal.entries.deepsea-rag-recall.enabled = true`

并建议在 Gateway 进程环境固定以下变量（防止重启后写错库）：
- `NEXUS_PYTHON_PATH=~/miniconda3/envs/openclaw-nexus/bin/python`
- `OPENCLAW_WORKSPACE=~/.openclaw/workspace-gemini`（若当前 agent workspace 在 gemini）
- `NEXUS_VECTOR_DB=$OPENCLAW_WORKSPACE/memory/.vector_db_restored`
- `NEXUS_COLLECTION=deepsea_nexus_restored`

可选 compaction 建议：
- `agents.defaults.compaction.reserveTokensFloor = 28000`
- `agents.defaults.compaction.memoryFlush.softThresholdTokens = 12000`

### 单一真源防漂移（强烈建议）
为避免 OpenClaw 升级后 `context-optimizer` 默认值回退，使用以下单一真源同步：

```bash
REPO_ROOT="${DEEPSEA_NEXUS_ROOT:-${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/skills/deepsea-nexus}"
cd "$REPO_ROOT"
python3 scripts/sync_openclaw_context_optimizer.py --apply
```

该脚本会：
- 读取 `config.json -> smart_context`（唯一真源）
- 生成 `~/.openclaw/state/context-optimizer-single-source.json`
- 校验并自动恢复 `~/.openclaw/hooks/context-optimizer/handler.js` 到受控模板

建议配合 `~/.openclaw/scripts/config-guardian.sh` 的定时巡检（当前默认每 2 分钟）一起使用，实现升级后自动自愈。

### Execution Governor v1.3 上下文治理联动（推荐）
在保留 Deep-Sea SmartContext 的基础上，建议启用 execution-governor v1.3 的上下文控制面：

```bash
# 应用 v1.3（默认优先）
bash "${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/scripts/apply_execution_governor.sh"

# 验证策略版本与开关
jq -r '.version,.context_management.enabled' "${OPENCLAW_HOME:-$HOME/.openclaw}/state/execution-governor-policy.json"

# 离线烟测（事件 + 命令注册）
node "${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/scripts/execution_governor_context_smoke.js"

# 运行态报表（新增 cache/context/native-capability 维度）
python3 "${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/scripts/execution_governor_report.py" --tail 2000
```

联动价值：
- `SmartContext` 负责“怎么压缩、怎么注入”。
- `execution-governor` 负责“何时压力过高、缓存是否有效、provider 原生能力是否匹配”。
- 两者叠加后，可同时提升质量稳定性与 token 成本可控性。

运行态命令（网关命令）：
- `/execution_context_status`：查看当前会话的压力等级、缓存状态、压缩信号。

更多细节见：
- `docs/sop/Execution_Governor_Context_Management_v1.3_Integration.md`

## 可选：安装 Smart Context 安全 cron
```bash
bash scripts/install_safe_cron.sh --install
```
说明：该 cron 仅生成 digest 报告并执行 summary flush，不做对外动作。

## 可选：安装向量库快照/健康检查 cron
```bash
bash scripts/install_vector_db_maintenance_cron.sh
```
说明：
- 每日生成向量库快照（可恢复）
- 每日健康检查（collection.count）
- 如需自动恢复，运行 `vector_db_healthcheck.py --auto-restore`（默认不启用）

## 常见问题
- `chromadb` 未安装：
  - 现版本会自动进入 degraded mode（lexical fallback），可继续运行。
- `deepsea_nexus` 导入失败：
  - 确认脚本在仓库根目录执行，或显式设置 `PYTHONPATH="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/skills"`。
