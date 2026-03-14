# SOP Document

## Metadata
- SOP ID: SOP-20260217-03
- Name: 工作任务澄清与成功标准
- Tags: work, task, clarification
- Primary triggers: a new task arrives without explicit KPI or acceptance criteria; more than 2 clarification loops occurred for the same task
- Primary outputs: completed task-clarification record; approved success criteria and non-goals
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
- Best Practice compliance: 先定义目标与验收，再进入执行，禁止“边做边猜”；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md。
- Best Method compliance: 双轮澄清（首轮提取目标/约束，二轮复述确认并冻结MVP边界）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md。
- Best Tool compliance: 任务澄清卡 + 必填字段检查 + strict validator；依据：增益[澄清卡模板:返工率下降 >=30%；strict validator:漏项率下降 >=40%；issue 看板:状态可见性提升 >=30%]；回滚[澄清卡模板->增加备注区；strict validator->草稿先宽后严；issue 看板->每日收盘更新]；研究记录：resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Standardize task intake so every work item starts with clear objective, measurable success criteria, and explicit constraints.

## Scope and Boundaries
- In scope: incoming tasks from chat, docs, or tickets and the first scoping pass
- Out of scope: solution implementation details and cross-team scheduling
- Dependencies: task source, owner availability, and agreed deadline

## Trigger Conditions (if/then)
- IF a new task arrives without explicit KPI or acceptance criteria
- THEN run clarification card before any execution work
- IF more than 2 clarification loops occurred for the same task
- THEN trigger escalation and freeze execution scope until decision is made

## Preconditions
- Precondition 1: intake template is available
- Precondition 2: owner can confirm acceptance criteria

## Inputs
- Input 1: raw task request
- Input 2: constraints and deadline context

## Outputs
- Output 1: completed task-clarification record
- Output 2: approved success criteria and non-goals

## Three-Optimal Decision
- Best Practice selected: 先定义目标与验收，再进入执行，禁止“边做边猜”（依据：resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md）
- Best Method selected: 双轮澄清（首轮提取目标/约束，二轮复述确认并冻结MVP边界）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 任务澄清卡 + 必填字段检查 + strict validator（依据：resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-work-task-clarification-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/work-task-clarification-toolchain-research.md`
- 最佳实践: 先定义目标与验收，再进入执行，禁止“边做边猜”
- 最佳方法: 双轮澄清（首轮提取目标/约束，二轮复述确认并冻结MVP边界）（Winner B=4.40, Margin=0.60）
- 最佳工具: 任务澄清卡 + 必填字段检查 + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集任务原文与上下文 | 输入来源可追溯且无关键缺失 | 任务来源链接 |
| 2 | 提取目标、成功指标、截止时间 | 至少1个数值化指标 | 澄清草稿 |
| 3 | 补齐约束与非目标 | 时间/资源/不可协商项完整 | 约束表 |
| 4 | 执行二轮复述确认 | 需求方确认“做什么/不做什么” | 确认记录 |
| 5 | 生成任务澄清卡并冻结MVP边界 | 无歧义项残留 | 澄清卡 |
| 6 | 将任务路由到计划SOP | 下一步SOP已明确 | 路由记录 |
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
- Cycle time target: <= 20 minutes per intake
- First-pass yield target: >= 92 percent tasks pass first-pass clarity gate
- Rework rate ceiling: <= 12 percent tasks need re-clarification
- Adoption target: 100 percent new tasks use this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-work-task-clarification-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-work-task-clarification-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-work-task-clarification-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-work-task-clarification-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-work-task-clarification-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-work-task-clarification-sop.overview.md

