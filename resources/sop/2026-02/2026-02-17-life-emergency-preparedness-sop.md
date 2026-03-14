# SOP Document

## Metadata
- SOP ID: SOP-20260217-14
- Name: 生活应急准备
- Tags: life, emergency, preparedness
- Primary triggers: monthly preparedness check date arrives; critical item missing or expired
- Primary outputs: updated readiness status; issue list with owner and due date
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
- Best Practice compliance: 联系人、路线、物资、演练四件套持续有效；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md。
- Best Method compliance: 月度检查 + 缺项即修复 + 季度演练；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md。
- Best Tool compliance: 应急清单 + 联系树 + 演练记录；依据：增益[应急清单:缺项发现率提升 >=30%；联系树:响应效率提升 >=25%；演练记录:可用性提升 >=20%]；回滚[应急清单->季度更新；联系树->双渠道备份；演练记录->固定演练日]；研究记录：resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Maintain a practical emergency readiness routine for contacts, routes, supplies, and drills with periodic verification.

## Scope and Boundaries
- In scope: household emergency planning and monthly readiness drills
- Out of scope: real-time emergency command operations
- Dependencies: emergency contact list, route map, and supply checklist

## Trigger Conditions (if/then)
- IF monthly preparedness check date arrives
- THEN run preparedness checklist and verify contact-route-supply status
- IF critical item missing or expired
- THEN trigger immediate replenish and schedule mini-drill

## Preconditions
- Precondition 1: contact list has at least two alternates
- Precondition 2: supply inventory file exists

## Inputs
- Input 1: contacts, route, and supply inventory
- Input 2: drill schedule

## Outputs
- Output 1: updated readiness status
- Output 2: issue list with owner and due date

## Three-Optimal Decision
- Best Practice selected: 联系人、路线、物资、演练四件套持续有效（依据：resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md）
- Best Method selected: 月度检查 + 缺项即修复 + 季度演练（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 应急清单 + 联系树 + 演练记录（依据：resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/life-emergency-preparedness-toolchain-research.md`
- 最佳实践: 联系人、路线、物资、演练四件套持续有效
- 最佳方法: 月度检查 + 缺项即修复 + 季度演练（Winner B=4.40, Margin=0.60）
- 最佳工具: 应急清单 + 联系树 + 演练记录
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 核对应急联系人树 | 至少双备份联系人有效 | 联系树 |
| 2 | 核对避险路线与集合点 | 路线可执行且可到达 | 路线图 |
| 3 | 盘点应急物资有效期 | 关键物资完整率 >=90% | 物资清单 |
| 4 | 发现缺项立即补齐 | 缺项24小时内闭环 | 补齐记录 |
| 5 | 执行小规模演练 | 演练时长与问题记录完整 | 演练记录 |
| 6 | 写入复盘与下月计划 | 风险项有负责人 | 下月计划 |
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
- Cycle time target: <= 35 minutes per monthly run
- First-pass yield target: >= 90 percent critical items in ready state
- Rework rate ceiling: <= 10 percent unresolved critical gaps
- Adoption target: 100 percent months complete one drill
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-life-emergency-preparedness-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-life-emergency-preparedness-sop.overview.md

