# SOP Document

## Metadata
- SOP ID: SOP-20260217-08
- Name: 学习目标拆解
- Tags: study, goal, decomposition
- Primary triggers: a new learning objective is added; weekly completion is below 75 percent
- Primary outputs: skill decomposition table; milestone schedule with checkpoints
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
- Best Practice compliance: 把学习目标拆成技能树、里程碑、可测检查点；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md。
- Best Method compliance: 自顶向下分解 + 每周里程碑回看；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md。
- Best Tool compliance: 学习目标卡 + 进度表 + strict validator；依据：增益[学习目标卡:清晰度提升 >=30%；进度表:偏差发现提前 >=25%；strict validator:漏项减少 >=35%]；回滚[学习目标卡->模板简化；进度表->周复盘强制更新；strict validator->草稿迭代后发布]；研究记录：resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Decompose learning goals into skill units, milestones, and review checkpoints that can be executed weekly.

## Scope and Boundaries
- In scope: new learning topic setup and weekly learning plan alignment
- Out of scope: final exam execution details and tool-specific drills
- Dependencies: target topic map, timeframe, and current proficiency estimate

## Trigger Conditions (if/then)
- IF a new learning objective is added
- THEN run decomposition to produce skill tree and milestones
- IF weekly completion is below 75 percent
- THEN rescope milestone difficulty and sequence

## Preconditions
- Precondition 1: target topic and deadline are defined
- Precondition 2: current level estimate exists

## Inputs
- Input 1: learning objective statement
- Input 2: available study hours

## Outputs
- Output 1: skill decomposition table
- Output 2: milestone schedule with checkpoints

## Three-Optimal Decision
- Best Practice selected: 把学习目标拆成技能树、里程碑、可测检查点（依据：resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md）
- Best Method selected: 自顶向下分解 + 每周里程碑回看（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 学习目标卡 + 进度表 + strict validator（依据：resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-study-goal-decomposition-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/study-goal-decomposition-toolchain-research.md`
- 最佳实践: 把学习目标拆成技能树、里程碑、可测检查点
- 最佳方法: 自顶向下分解 + 每周里程碑回看（Winner B=4.40, Margin=0.60）
- 最佳工具: 学习目标卡 + 进度表 + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 定义学习终点能力 | 终点能力可评估 | 目标定义 |
| 2 | 拆分为技能树与子主题 | 层级不超过3层且无重叠 | 技能树图 |
| 3 | 为每周设置里程碑 | 每周有可交付产出 | 里程碑表 |
| 4 | 定义检查点与达标阈值 | 检查点可量化 | 检查清单 |
| 5 | 绑定学习资源与练习路径 | 资源-目标映射完整 | 资源映射 |
| 6 | 复核并冻结本阶段计划 | 范围清晰无冲突 | 冻结记录 |
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
- Cycle time target: <= 30 minutes per goal decomposition
- First-pass yield target: >= 90 percent goals have measurable milestones
- Rework rate ceiling: <= 12 percent milestones need major re-scope
- Adoption target: 100 percent new goals use this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-study-goal-decomposition-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-study-goal-decomposition-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-study-goal-decomposition-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-study-goal-decomposition-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-study-goal-decomposition-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-study-goal-decomposition-sop.overview.md

