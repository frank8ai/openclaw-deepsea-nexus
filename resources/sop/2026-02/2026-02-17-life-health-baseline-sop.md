# SOP Document

## Metadata
- SOP ID: SOP-20260217-12
- Name: 生活健康基线
- Tags: life, health, baseline
- Primary triggers: week starts or health baseline review day arrives; two or more baseline metrics miss target for 3 days
- Primary outputs: health baseline plan with targets; daily adherence record
- Owner: yizhi
- Team: deepsea-nexus
- Version: v1.4
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
- Non-negotiables check: no destructive action and no external side effects are allowed without explicit confirmation.
- Outcome metric and baseline: baseline from 6 shadow runs in current window and target deltas defined in SLA section.
- Reversibility and blast radius: confined to SOP artifacts and task-level operations; rollback can be executed within one cycle.
- Evidence tier justification: 6 pilot runs with recorded baseline/current metrics and rule updates satisfy E3.
- Best Practice compliance: 睡眠、运动、饮食三基线优先，先稳定再优化；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md。
- Best Method compliance: 周计划 + 日追踪 + 连续偏离触发纠偏；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md。
- Best Tool compliance: 健康基线表 + 日追踪打卡 + 周复盘；依据：增益[基线目标表:清晰度提升 >=30%；日追踪打卡:连续执行率提升 >=25%；周复盘模板:恢复速度提升 >=20%]；回滚[基线目标表->每周校准；日追踪打卡->仅跟踪关键项；周复盘模板->强制1-3规则]；研究记录：resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Run a weekly health baseline routine covering sleep, activity, and meal planning with measurable adherence.

## Scope and Boundaries
- In scope: weekly health check-in and daily baseline adherence tracking
- Out of scope: medical diagnosis and emergency clinical response
- Dependencies: sleep log, activity log, and meal plan checklist

## Trigger Conditions (if/then)
- IF week starts or health baseline review day arrives
- THEN run baseline check and set weekly minimum targets
- IF two or more baseline metrics miss target for 3 days
- THEN trigger recovery week plan and reduce overload

## Preconditions
- Precondition 1: sleep and activity logs are available
- Precondition 2: current constraints are known

## Inputs
- Input 1: sleep, activity, and meal data
- Input 2: weekly schedule

## Outputs
- Output 1: health baseline plan with targets
- Output 2: daily adherence record

## Three-Optimal Decision
- Best Practice selected: 睡眠、运动、饮食三基线优先，先稳定再优化（依据：resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md）
- Best Method selected: 周计划 + 日追踪 + 连续偏离触发纠偏（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 健康基线表 + 日追踪打卡 + 周复盘（依据：resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-life-health-baseline-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/life-health-baseline-toolchain-research.md`
- 最佳实践: 睡眠、运动、饮食三基线优先，先稳定再优化
- 最佳方法: 周计划 + 日追踪 + 连续偏离触发纠偏（Winner B=4.40, Margin=0.60）
- 最佳工具: 健康基线表 + 日追踪打卡 + 周复盘
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 设定本周三项基线目标 | 目标可量化 | 周目标 |
| 2 | 拆分到每日最小动作 | 每日动作可执行 | 每日计划 |
| 3 | 执行并记录打卡 | 日记录完整率 >=90% | 打卡日志 |
| 4 | 识别连续偏离信号 | 连续偏离天数可见 | 偏离统计 |
| 5 | 启动纠偏周策略 | 调整后48小时见效 | 纠偏计划 |
| 6 | 周末复盘并更新阈值 | 规则1-3条更新 | 周复盘 |
## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| Ambiguous input | required field missing or conflicting | request missing field and hold workflow | escalate to owner same day |
| SLA breach risk | elapsed time exceeds 80% of target with incomplete output | switch to minimum viable output and close critical items first | escalate with carry-over list |
| Quality gate failure | one or more hard gates unchecked | stop release and revise draft | escalate as hold decision |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: non-negotiable constraint violation is detected
- Stop condition 2: same gate fails twice in one run window
- Blast radius limit: workflow artifacts and linked task records only
- Rollback action: revert to previous active SOP version and mark current attempt as hold

## SLA and Metrics
- Cycle time target: <= 20 minutes per weekly baseline run
- First-pass yield target: >= 85 percent days meet baseline targets
- Rework rate ceiling: <= 15 percent days require reset
- Adoption target: 100 percent weeks include baseline record
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-life-health-baseline-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-life-health-baseline-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-life-health-baseline-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-life-health-baseline-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-life-health-baseline-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-life-health-baseline-sop.overview.md

