# SOP Document

## Metadata
- SOP ID: SOP-20260217-05
- Name: 工作执行闭环与状态更新
- Tags: work, execution, loop
- Primary triggers: a task is in progress and next action is not logged; blocker remains unresolved for more than 4 hours
- Primary outputs: updated task status with evidence; blocker log and next action
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
- Best Practice compliance: 每个执行回路必须有“下一步动作 + 当前状态 + 阻塞信号”；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md。
- Best Method compliance: 30分钟执行回路（执行 -> 更新 -> 判定阻塞 -> 路由）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md。
- Best Tool compliance: 状态看板 + 阻塞升级清单 + strict validator；依据：增益[状态看板:阻塞可见性提升 >=30%；阻塞升级清单:阻塞时长下降 >=25%；strict validator:变更质量稳定]；回滚[状态看板->每日两次刷新；阻塞升级清单->设升级阈值；strict validator->批量校验]；研究记录：resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Standardize execution into short closed loops with explicit status updates and blocker handling.

## Scope and Boundaries
- In scope: active task execution from start to completion updates
- Out of scope: task intake and final quarterly reporting
- Dependencies: prioritized task list, owner, and current status board

## Trigger Conditions (if/then)
- IF a task is in progress and next action is not logged
- THEN run execution loop to define next action and update status
- IF blocker remains unresolved for more than 4 hours
- THEN escalate blocker and switch to fallback task

## Preconditions
- Precondition 1: task has defined owner and due date
- Precondition 2: status board is reachable

## Inputs
- Input 1: current task record
- Input 2: available work window

## Outputs
- Output 1: updated task status with evidence
- Output 2: blocker log and next action

## Three-Optimal Decision
- Best Practice selected: 每个执行回路必须有“下一步动作 + 当前状态 + 阻塞信号”（依据：resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md）
- Best Method selected: 30分钟执行回路（执行 -> 更新 -> 判定阻塞 -> 路由）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 状态看板 + 阻塞升级清单 + strict validator（依据：resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-work-execution-loop-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/work-execution-loop-toolchain-research.md`
- 最佳实践: 每个执行回路必须有“下一步动作 + 当前状态 + 阻塞信号”
- 最佳方法: 30分钟执行回路（执行 -> 更新 -> 判定阻塞 -> 路由）（Winner B=4.40, Margin=0.60）
- 最佳工具: 状态看板 + 阻塞升级清单 + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 选择当前最高优先任务 | 优先级依据明确 | 任务快照 |
| 2 | 定义30分钟下一步动作 | 动作可在单回路完成 | Next Action |
| 3 | 执行并记录中间结果 | 结果可验证 | 执行记录 |
| 4 | 更新状态（done/in-progress/blocked） | 无“未知状态” | 看板状态 |
| 5 | 若阻塞则触发升级或切换备用任务 | 阻塞处理时限明确 | 阻塞单 |
| 6 | 收盘写回指标 | cycle/fpy/rework 已更新 | 日指标 |
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
- Cycle time target: <= 30 minutes per execution loop
- First-pass yield target: >= 88 percent loops end with clear next state
- Rework rate ceiling: <= 14 percent loops require redo due to unclear status
- Adoption target: 100 percent in-progress tasks use loop status updates
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-work-execution-loop-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-work-execution-loop-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-work-execution-loop-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-work-execution-loop-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-work-execution-loop-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-work-execution-loop-sop.overview.md

