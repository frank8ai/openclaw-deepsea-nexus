# SOP Document

## Metadata
- SOP ID: SOP-20260217-10
- Name: 学习间隔复习
- Tags: study, spaced, review
- Primary triggers: review day arrives for queued items; recall rate drops below threshold in two consecutive intervals
- Primary outputs: updated recall scores per interval; next-interval schedule
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
- Best Practice compliance: 间隔复习优先，按遗忘曲线安排回看节奏；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md。
- Best Method compliance: 固定间隔+阈值自适应（低分缩短间隔）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md。
- Best Tool compliance: 复习队列 + 间隔规则表 + 结果日志；依据：增益[复习队列:漏复习率下降 >=30%；间隔规则表:保持率提升 >=20%；结果日志:调参速度提升 >=25%]；回滚[复习队列->每周清理；间隔规则表->退回基础间隔；结果日志->最小字段强制]；研究记录：resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Standardize spaced repetition scheduling so learned items are reviewed at optimal intervals with measurable recall quality.

## Scope and Boundaries
- In scope: ongoing review queue for previously studied items
- Out of scope: new topic decomposition and exam-day logistics
- Dependencies: review queue, interval schedule, and recall score records

## Trigger Conditions (if/then)
- IF review day arrives for queued items
- THEN execute interval-based review session
- IF recall rate drops below threshold in two consecutive intervals
- THEN shorten interval and add focused remediation

## Preconditions
- Precondition 1: review queue is current
- Precondition 2: previous recall score exists

## Inputs
- Input 1: queued review items
- Input 2: interval rule set

## Outputs
- Output 1: updated recall scores per interval
- Output 2: next-interval schedule

## Three-Optimal Decision
- Best Practice selected: 间隔复习优先，按遗忘曲线安排回看节奏（依据：resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md）
- Best Method selected: 固定间隔+阈值自适应（低分缩短间隔）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 复习队列 + 间隔规则表 + 结果日志（依据：resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-study-spaced-review-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/study-spaced-review-toolchain-research.md`
- 最佳实践: 间隔复习优先，按遗忘曲线安排回看节奏
- 最佳方法: 固定间隔+阈值自适应（低分缩短间隔）（Winner B=4.40, Margin=0.60）
- 最佳工具: 复习队列 + 间隔规则表 + 结果日志
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 刷新待复习队列 | 队列无过期堆积 | 队列快照 |
| 2 | 按间隔规则安排当日批次 | 每批数量在可执行范围 | 批次计划 |
| 3 | 执行检索复习并评分 | 每题有评分 | 复习结果 |
| 4 | 低于阈值项缩短间隔 | 调整规则明确 | 调整记录 |
| 5 | 高分项延长间隔 | 规则一致 | 更新队列 |
| 6 | 输出下一轮计划 | 下次窗口已排定 | 下轮计划 |
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
- Cycle time target: <= 35 minutes per review batch
- First-pass yield target: >= 88 percent items meet recall threshold
- Rework rate ceiling: <= 14 percent items require interval rollback
- Adoption target: 100 percent queued reviews follow schedule
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-study-spaced-review-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-study-spaced-review-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-study-spaced-review-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-study-spaced-review-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-study-spaced-review-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-study-spaced-review-sop.overview.md

