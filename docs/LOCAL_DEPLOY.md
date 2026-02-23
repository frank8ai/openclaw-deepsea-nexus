# Deep-Sea Nexus v4.4.0 本地部署

## 目标
将当前仓库版本部署到本地 OpenClaw 工作区，并确保门禁与运行态可用。

## 前置条件
- 路径：`~/.openclaw/workspace/skills/deepsea-nexus`
- Python：`3.8+`
- 可选依赖：`chromadb`、`sentence-transformers`（缺失时自动降级，不阻塞启动）

## 一键部署
在仓库根目录执行：

```bash
bash scripts/deploy_local_v4.sh --full
```

说明：
- `--full`：执行 `run_tests.py` 全量门禁 + 运行态 smoke 检查
- `--quick`：仅执行 `tests/test_units.py` + 运行态 smoke 检查
- 脚本默认优先使用 `~/miniconda3/envs/openclaw-nexus/bin/python`，并默认主库：
  - `NEXUS_VECTOR_DB=~/.openclaw/workspace/memory/.vector_db_restored`
  - `NEXUS_COLLECTION=deepsea_nexus_restored`

如需显式指定：

```bash
NEXUS_PYTHON_PATH=~/miniconda3/envs/openclaw-nexus/bin/python \
NEXUS_VECTOR_DB=~/.openclaw/workspace/memory/.vector_db_restored \
NEXUS_COLLECTION=deepsea_nexus_restored \
bash scripts/deploy_local_v4.sh --full
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
  - `nexus-auto-recall`
  - `nexus-auto-save`
- 会检查主向量库计数与 `nexus_init/nexus_health` 状态
- `--repair` 模式下默认包含一次 `deploy_local_v4.sh --quick` 快速门禁
- 可加 `--skip-deploy` 跳过快速门禁

## 写入护栏（防止写错库）
当前版本默认启用写入护栏，所有主要写入入口都会检查：

- 必须存在：`NEXUS_VECTOR_DB`、`NEXUS_COLLECTION`
- 默认主库目标：
  - `NEXUS_VECTOR_DB=~/.openclaw/workspace/memory/.vector_db_restored`
  - `NEXUS_COLLECTION=deepsea_nexus_restored`

违规会被阻断并记录到：
- `~/.openclaw/workspace/logs/nexus_write_guard_alerts.jsonl`

可选开关：
- `NEXUS_ENFORCE_WRITE_GUARD=0`：关闭护栏（不建议生产）
- `NEXUS_WRITE_GUARD_ALLOW_ANY=1`：允许非主库目标（仅迁移/实验）

## 最近摘要跨库审计与迁移
用于确认“最近摘要是否都在主库”，并可迁移缺失项回主库：

```bash
/Users/yizhi/.openclaw/workspace/.venv-nexus/bin/python \
  scripts/audit_recent_summaries.py --days 7 --migrate-missing
```

输出：
- JSON 报告：`docs/reports/summary_audit_<timestamp>.json`
- Markdown 报告：`docs/reports/summary_audit_<timestamp>.md`
- 若发生迁移，会生成回滚脚本：`docs/reports/summary_audit_<timestamp>_rollback.sh`

## 推荐运行参数（智能上下文）
当前建议生产参数（已在 `config.json` 默认值中）：

- `smart_context.full_rounds = 8`
- `smart_context.summary_rounds = 20`
- `smart_context.compress_after_rounds = 35`
- `smart_context.trigger_soft_ratio = 0.7`
- `smart_context.trigger_hard_ratio = 0.85`
- 抢救开关：`rescue_enabled/rescue_gold/rescue_decisions/rescue_next_actions = true`

## 成功判定
- `run_tests.py` 结尾输出 `ALL TESTS PASSED`
- 脚本输出 JSON 状态，至少满足：
  - `available: true`
  - `initialized: true`
  - `plugin_version: "3.0.0"`（插件协议版本）
  - `package_version: "4.4.0"`（发布版本）

## 生效验收（白盒）
部署完成后，建议执行一次白盒确认（不是只看 status）：

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "/Users/yizhi/.openclaw/workspace/skills")
from deepsea_nexus import nexus_init
from deepsea_nexus.core.plugin_system import get_plugin_registry

assert nexus_init()
sc = get_plugin_registry().get("smart_context")
print("rounds:", sc.config.full_rounds, sc.config.summary_rounds, sc.config.compress_after_rounds)
print("rescue:", sc.config.rescue_enabled, sc.config.rescue_gold, sc.config.rescue_decisions, sc.config.rescue_next_actions)
PY
```

期望输出：
- `rounds: 8 20 35`
- `rescue: True True True True`

## OpenClaw 侧联动（本机）
如果你希望输入侧先压缩上下文，再由 Deep-Sea 注入记忆，建议启用：

- `hooks.internal.entries.context-optimizer.enabled = true`
- `nexus-auto-recall`（workspace hook）保持启用
- `deepsea-rag-recall`（managed hook）建议保持关闭，避免重复注入

并建议在 Gateway 进程环境固定以下变量（防止重启后写错库）：
- `NEXUS_PYTHON_PATH=~/miniconda3/envs/openclaw-nexus/bin/python`
- `NEXUS_VECTOR_DB=~/.openclaw/workspace/memory/.vector_db_restored`
- `NEXUS_COLLECTION=deepsea_nexus_restored`

可选 compaction 建议：
- `agents.defaults.compaction.reserveTokensFloor = 28000`
- `agents.defaults.compaction.memoryFlush.softThresholdTokens = 12000`

## 可选：安装 Smart Context 安全 cron
```bash
bash scripts/install_safe_cron.sh --install
```
说明：该 cron 仅生成 digest 报告并执行 summary flush，不做对外动作。

## 常见问题
- `chromadb` 未安装：
  - 现版本会自动进入 degraded mode（lexical fallback），可继续运行。
- `deepsea_nexus` 导入失败：
  - 确认脚本在仓库根目录执行，或显式设置 `PYTHONPATH=~/.openclaw/workspace/skills`。
