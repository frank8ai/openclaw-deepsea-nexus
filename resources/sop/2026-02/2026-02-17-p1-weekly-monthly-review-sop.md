# SOP Document

## Metadata
- SOP ID: SOP-20260217-19
- Name: 周月复盘与规则更新
- Tags: p1, weekly, monthly, review
- Primary triggers: 到达周末或月末复盘窗口; 关键指标连续2周期反向变化
- Primary outputs: 复盘结论和偏差原因; 1-3条规则更新
- Owner: yizhi
- Team: deepsea-nexus
- Version: v1.3
- Status: active
- Risk tier: medium
- Reversibility class: R2
- Evidence tier at release: E3
- Effective condition: all hard gates checked; strict validation passes; release approved
- Review cycle: monthly
- Retirement condition: primary result metric degrades for 2 consecutive monthly cycles, workflow obsolete, or compliance change
- Created on: 2026-02-17
- Last reviewed on: 2026-02-17

## Hard Gates (must pass before activation)
- [x] Non-negotiables (legal/safety/security/data integrity) are explicitly checked.
- [x] Objective is explicit and measurable.
- [x] Outcome metric includes baseline and target delta.
- [x] Trigger conditions are testable (if/then with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: 执行中不允许绕过安全、合规、数据完整性约束。
- Outcome metric and baseline: 使用近6次历史样本作为基线，并定义目标增量。
- Reversibility and blast radius: 该流程仅变更流程文档和任务状态，可单周期回滚。
- Evidence tier justification: R2流程以6次试运行记录满足E3要求。
- Best Practice compliance: 复盘必须产出可执行规则；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md。
- Best Method compliance: 指标对比+偏差归因+小步规则更新；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md。
- Best Tool compliance: 复盘模板+指标看板+规则库；依据：增益[复盘模板:复盘质量提升 >=30%；指标看板:偏差定位速度提升 >=25%；规则库:复用率提升 >=20%]；回滚[复盘模板->强制偏差分析；指标看板->指标分层；规则库->定期清理]；研究记录：resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立周/月复盘机制，把指标偏差转化为可执行规则更新。

## Scope and Boundaries
- In scope: 周复盘、月复盘、关键里程碑复盘
- Out of scope: 纯状态汇报会议
- Dependencies: 指标面板、规则库、复盘模板

## Trigger Conditions (if/then)
- IF 到达周末或月末复盘窗口
- THEN 执行复盘SOP并输出规则更新
- IF 关键指标连续2周期反向变化
- THEN 强制开启专项复盘

## Preconditions
- Precondition 1: 本周期指标数据可用
- Precondition 2: 上周期规则更新可追踪

## Inputs
- Input 1: 周期指标数据
- Input 2: 执行日志和异常记录

## Outputs
- Output 1: 复盘结论和偏差原因
- Output 2: 1-3条规则更新

## Three-Optimal Decision
- Best Practice selected: 复盘必须产出可执行规则（依据：resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md）
- Best Method selected: 指标对比+偏差归因+小步规则更新（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 复盘模板+指标看板+规则库（依据：resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-weekly-monthly-review-toolchain-research.md`
- 最佳实践: 复盘必须产出可执行规则
- 最佳方法: 指标对比+偏差归因+小步规则更新（Winner B=4.40, Margin=0.60）
- 最佳工具: 复盘模板+指标看板+规则库
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集周期指标与目标值 | 关键指标齐全 | 指标快照 |
| 2 | 对比基线和当前值 | 偏差量化 | 差异表 |
| 3 | 分析偏差根因 | 至少1个可验证根因 | 根因分析 |
| 4 | 制定1-3条规则更新 | 规则可测试 | 规则草案 |
| 5 | 发布规则并标注生效时间 | 规则状态可追踪 | 规则记录 |
| 6 | 定义下周期验证计划 | 验证指标明确 | 下周期计划 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 数据缺失 | 关键指标未采集 | 先补采集后再发布结论 | 升级到数据owner |
| 规则冲突 | 新旧规则语义冲突 | 保留旧规则并标记新规则draft | 升级评审人裁决 |
| 规则过多 | 单周期更新>3条 | 按影响度只保留Top3 | 升级到下周期处理 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键指标缺失无法归因
- Stop condition 2: 规则冲突未解决
- Blast radius limit: 复盘文档和规则库
- Rollback action: 回退本周期规则到draft

## SLA and Metrics
- Cycle time target: <= 60 分钟完成周复盘
- First-pass yield target: >= 90 percent 复盘首轮完成规则更新
- Rework rate ceiling: <= 15 percent 规则需二次修订
- Adoption target: 100 percent 周月复盘使用本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-weekly-monthly-review-sop.overview.md

