# SOP: X 文章对照与第二大脑迭代（2026-02-23）

## 1. 研究输入
- 来源：`https://x.com/lijiuer92/status/2025678747509391664`（OpenClaw Memory终极指南）
- 结论主张（抽取）：  
  - 记忆系统要补齐：重要性、时序衰减、自动晋升、可运营审计。  
  - 风险要可观测：静默失败、契约漂移、检索排序失真。

## 2. 当前系统基线（核对后）
- 已有：L0/L1/L2、项目优先召回、Warm 自动写入、结构化摘要。
- 已有（你最新落地）：`nexus_write` 分层契约（P0/P1/P2/kind/source）接管主要写入入口。
- 缺口（本轮前）：  
  1) 审计脚本对 tags 解析不够稳（历史 list/str/metadata 混合）。  
  2) 缺少 old/new 分组覆盖率，运营上无法快速判断“新契约”渗透率。  
  3) PARA 召回缺少显式 importance 信号和更清晰的 recency+importance 评分解释。  

## 3. 本轮迭代（只补缺口，不重复已实现）

### 3.1 契约审计增强（可运营）
- 文件：`scripts/nexus_audit_contract.py`
- 变更：
  - 统一解析 tags（兼容 `list` / `str` / `tag` 字段）。
  - 支持 metadata 回退解析：`priority` / `kind` / `source` / `source_file`。
  - 新增分组覆盖率：`new_contract` / `legacy_source_file` / `legacy_unknown`。
  - 新增 `--show-missing` 输出缺失样本，方便快速回填策略。
  - 输出改为标准 JSON，便于后续自动采集。

### 3.2 PARA 召回打分增强（会越来越聪明）
- 文件：`scripts/para_recall.py`
- 变更：
  - 三维评分：`relevance + importance + recency`（权重可调）。
  - 读取项目信号文件 `.memory_signal.json`，使用 `importance_score` 与 `decay_half_life_days`。
  - trace 记录中新增 `score_breakdown`，便于线上排查“为什么这个项目排前”。

### 3.3 Warm 写入增强（自动晋升）
- 文件：`scripts/warm_writer.py`
- 变更：
  - 新增项目信号文件：`10_Projects/<Project>/.memory_signal.json`
    - 字段：`importance_score` / `priority` / `confidence` / `decay_half_life_days` / `entry_id`
  - 增加自动晋升写入：`20_Knowledge/Areas/<Project>.md`
    - 去重依据：`entry_id`
    - 晋升内容：Objective、Decisions、Next、Pitfalls、Keywords、来源链接
  - L1 Overview 增加 importance 与半衰期说明，提升人工审阅效率。

## 4. 验收命令

```bash
# 1) Warm 写入（验证 signal + promotion）
python3 scripts/warm_writer.py --from /path/to/summary.json

# 2) PARA 召回（验证三维评分输出）
python3 scripts/para_recall.py --query "你的查询" --top-projects 3 --json

# 3) 契约审计（验证分组覆盖与缺失样本）
NEXUS_VECTOR_DB=... NEXUS_COLLECTION=... \
python3 scripts/nexus_audit_contract.py --limit 200 --show-missing 10
```

## 4.1 本轮实测快照（2026-02-23）
- `sample=200`
- `priority` 覆盖率：`0.0`
- `kind` 覆盖率：`0.0`
- `source` 覆盖率：`0.965`
- `group_coverage`：`legacy_source_file=191`，`legacy_unknown=9`

报告文件：`docs/reports/2026-02-23-contract-audit.md`

## 5. 下一步建议（按优先级）
1. 对 `legacy_*` 样本做轻量回填策略（先补 `priority/kind`，再补 `source`）。
2. 在 CI/cron 中固定跑 `nexus_audit_contract.py`，将 `group_coverage` 写入日报。
3. 用真实线上 query 集验证 `para_recall` 的权重（默认 0.6/0.25/0.15）并做 A/B。
