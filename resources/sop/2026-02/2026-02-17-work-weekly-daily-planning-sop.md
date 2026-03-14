# SOP Document

## Metadata
- SOP ID: SOP-20260217-04
- Name: 工作周计划与日计划
- Tags: work, weekly, daily, planning
- Primary triggers: it is Monday planning window or daily kickoff time; daily completion trend falls below 80 percent for 2 days
- Primary outputs: weekly top outcomes list; daily time-blocked task plan
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
- Best Practice compliance: 周目标驱动日计划，限制并行任务数（WIP）防止切换损耗；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md。
- Best Method compliance: 周-日双层规划（周定义结果，日定义时间块与优先级）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md。
- Best Tool compliance: 周计划板 + 日历 time-block + strict validator；依据：增益[周计划看板:完成率提升 >=20%；日历时间块:延误率下降 >=25%；strict validator:漏项率下降 >=30%]；回滚[周计划看板->缩减字段；日历时间块->预留20%缓冲；strict validator->草稿迭代后激活]；研究记录：resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Build a repeatable planning cadence that aligns weekly outcomes with daily execution blocks and measurable completion.

## Scope and Boundaries
- In scope: weekly planning and daily plan refresh for active work commitments
- Out of scope: long-term annual goal redesign
- Dependencies: calendar blocks, backlog list, and owner priorities

## Trigger Conditions (if/then)
- IF it is Monday planning window or daily kickoff time
- THEN run planning SOP to produce weekly and daily execution map
- IF daily completion trend falls below 80 percent for 2 days
- THEN trigger scope rebalance and remove low-value items

## Preconditions
- Precondition 1: priority list is up to date
- Precondition 2: calendar has available focus blocks

## Inputs
- Input 1: weekly backlog and constraints
- Input 2: today available hours

## Outputs
- Output 1: weekly top outcomes list
- Output 2: daily time-blocked task plan

## Three-Optimal Decision
- Best Practice selected: 周目标驱动日计划，限制并行任务数（WIP）防止切换损耗（依据：resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md）
- Best Method selected: 周-日双层规划（周定义结果，日定义时间块与优先级）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 周计划板 + 日历 time-block + strict validator（依据：resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/work-weekly-daily-planning-toolchain-research.md`
- 最佳实践: 周目标驱动日计划，限制并行任务数（WIP）防止切换损耗
- 最佳方法: 周-日双层规划（周定义结果，日定义时间块与优先级）（Winner B=4.40, Margin=0.60）
- 最佳工具: 周计划板 + 日历 time-block + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 汇总本周待办与可用工时 | 工时与任务量可匹配 | 待办清单 |
| 2 | 确定周三大结果（Top 3） | 每项有结果定义与截止 | 周目标卡 |
| 3 | 拆到每日时间块 | 每日关键任务 <=3 | 日历块 |
| 4 | 设置WIP限制与中断策略 | 并行任务不超阈值 | WIP记录 |
| 5 | 每日收盘更新完成率与偏差 | 偏差有原因标签 | 日报记录 |
| 6 | 周末复盘并调下周计划 | 形成下周修正规则1-3条 | 周复盘 |
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
- Cycle time target: <= 25 minutes per daily planning run
- First-pass yield target: >= 90 percent planned critical tasks started on time
- Rework rate ceiling: <= 15 percent tasks rescheduled without rationale
- Adoption target: 100 percent workdays start with plan record
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-work-weekly-daily-planning-sop.overview.md

