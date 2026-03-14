# SOP Document

## Metadata
- SOP ID: SOP-20260217-07
- Name: 工作异常响应与恢复
- Tags: work, incident, response
- Primary triggers: an incident signal is detected and severity is unknown; severity is medium or high and impact expands
- Primary outputs: severity classification and containment action; recovery summary and post-incident action list
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
- Best Practice compliance: 先分级再处置，优先控制爆炸半径；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md。
- Best Method compliance: 事件流程五段（检测 -> 分级 -> 遏制 -> 恢复 -> 复盘）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md。
- Best Tool compliance: 事件模板 + 严重度矩阵 + strict validator；依据：增益[事件模板:响应一致性提升 >=30%；严重度矩阵:分级正确率提升 >=25%；strict validator:漏项下降 >=35%]；回滚[事件模板->最小字段先行；严重度矩阵->手工override并复盘；strict validator->合并评审时运行]；研究记录：resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Create a repeatable incident workflow for fast detection, severity classification, containment, recovery, and post-incident review.

## Scope and Boundaries
- In scope: task/system incidents affecting delivery, quality, or availability
- Out of scope: major architecture redesign or unrelated business planning
- Dependencies: incident channel, owner on-call path, and recovery checklist

## Trigger Conditions (if/then)
- IF an incident signal is detected and severity is unknown
- THEN run incident SOP and classify severity within 10 minutes
- IF severity is medium or high and impact expands
- THEN trigger containment protocol and management escalation

## Preconditions
- Precondition 1: incident channel is available
- Precondition 2: owner and backup owner are known

## Inputs
- Input 1: incident signal and logs
- Input 2: affected scope and users

## Outputs
- Output 1: severity classification and containment action
- Output 2: recovery summary and post-incident action list

## Three-Optimal Decision
- Best Practice selected: 先分级再处置，优先控制爆炸半径（依据：resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md）
- Best Method selected: 事件流程五段（检测 -> 分级 -> 遏制 -> 恢复 -> 复盘）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 事件模板 + 严重度矩阵 + strict validator（依据：resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-work-incident-response-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/work-incident-response-toolchain-research.md`
- 最佳实践: 先分级再处置，优先控制爆炸半径
- 最佳方法: 事件流程五段（检测 -> 分级 -> 遏制 -> 恢复 -> 复盘）（Winner B=4.40, Margin=0.60）
- 最佳工具: 事件模板 + 严重度矩阵 + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 接收事件信号并建单 | 事件时间与来源完整 | 事件单 |
| 2 | 10分钟内完成严重度分级 | 分级规则可解释 | 分级记录 |
| 3 | 启动遏制动作 | 扩散趋势停止 | 遏制日志 |
| 4 | 执行恢复并验证核心链路 | 核心服务恢复可用 | 恢复记录 |
| 5 | 对外/对内同步状态 | 同步节奏符合SLA | 通知记录 |
| 6 | 24小时内完成复盘与规则回写 | 1-3条规则落地 | 复盘报告 |
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
- Cycle time target: <= 60 minutes to stable containment
- First-pass yield target: >= 90 percent incidents classified correctly on first pass
- Rework rate ceiling: <= 15 percent incidents require reopen
- Adoption target: 100 percent incidents logged with this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-work-incident-response-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-work-incident-response-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-work-incident-response-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-work-incident-response-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-work-incident-response-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-work-incident-response-sop.overview.md

