# SOP Document

## Metadata
- SOP ID: SOP-20260217-13
- Name: 生活财务运行
- Tags: life, financial, operations
- Primary triggers: weekly finance review window starts; forecasted cash buffer falls below threshold
- Primary outputs: updated weekly budget status; exception list and next-week actions
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
- Best Practice compliance: 现金流与账单优先，先稳健再优化收益；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md。
- Best Method compliance: 周度资金检查（收入/支出/账单/缓冲）+ 异常阈值触发；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md。
- Best Tool compliance: 预算表 + 账单日历 + 异常清单；依据：增益[预算表:超支率下降 >=20%；账单日历:逾期率下降 >=30%；异常清单:响应速度提升 >=25%]；回滚[预算表->固定分类字典；账单日历->周固定更新；异常清单->限制Top3异常]；研究记录：resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Standardize weekly budget, bill, and cash-flow checks to reduce surprises and keep spending aligned with plan.

## Scope and Boundaries
- In scope: weekly money review, bill tracking, and monthly rollover prep
- Out of scope: investment strategy design and tax filing preparation
- Dependencies: budget sheet, bill calendar, and account balances

## Trigger Conditions (if/then)
- IF weekly finance review window starts
- THEN run finance ops checklist and update cash-flow status
- IF forecasted cash buffer falls below threshold
- THEN trigger spending freeze and bill-priority protocol

## Preconditions
- Precondition 1: latest transactions are imported
- Precondition 2: bill due dates are visible

## Inputs
- Input 1: income and expense records
- Input 2: upcoming bill list

## Outputs
- Output 1: updated weekly budget status
- Output 2: exception list and next-week actions

## Three-Optimal Decision
- Best Practice selected: 现金流与账单优先，先稳健再优化收益（依据：resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md）
- Best Method selected: 周度资金检查（收入/支出/账单/缓冲）+ 异常阈值触发（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 预算表 + 账单日历 + 异常清单（依据：resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-life-financial-operations-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/life-financial-operations-toolchain-research.md`
- 最佳实践: 现金流与账单优先，先稳健再优化收益
- 最佳方法: 周度资金检查（收入/支出/账单/缓冲）+ 异常阈值触发（Winner B=4.40, Margin=0.60）
- 最佳工具: 预算表 + 账单日历 + 异常清单
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 汇总本周资金流水 | 记录覆盖率 >=95% | 流水汇总 |
| 2 | 核对账单与到期日 | 未来14天账单清晰 | 账单表 |
| 3 | 对比预算与实际支出 | 偏差项有标签 | 预算偏差表 |
| 4 | 检查现金缓冲阈值 | 缓冲低于阈值即预警 | 现金流检查 |
| 5 | 执行纠偏动作（削减/延后/重排） | 纠偏动作可落地 | 行动清单 |
| 6 | 输出下周财务计划 | 关键风险已显式 | 下周计划 |
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
- Cycle time target: <= 30 minutes per weekly finance run
- First-pass yield target: >= 95 percent bills tracked before due date
- Rework rate ceiling: <= 10 percent spending categories exceed plan
- Adoption target: 100 percent weeks include finance log
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-life-financial-operations-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-life-financial-operations-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-life-financial-operations-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-life-financial-operations-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-life-financial-operations-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-life-financial-operations-sop.overview.md

