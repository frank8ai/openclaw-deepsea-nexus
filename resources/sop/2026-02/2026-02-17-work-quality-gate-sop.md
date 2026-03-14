# SOP Document

## Metadata
- SOP ID: SOP-20260217-06
- Name: 工作质量门禁与评审
- Tags: work, quality, gate
- Primary triggers: deliverable is marked ready for release; critical checklist item fails
- Primary outputs: quality-gate verdict; release decision with evidence
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
- Best Practice compliance: 先质量门禁后发布，关键项失败即阻断；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md。
- Best Method compliance: 双阶段评审（自检 -> 同行评审）+ 缺陷闭环；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md。
- Best Tool compliance: 质量清单 + 测试记录 + strict validator；依据：增益[质量清单:漏检下降 >=30%；回归记录:回归失败率下降 >=20%；strict validator:激活错误下降 >=40%]；回滚[质量清单->按风险分层；回归记录->最小字段强制；strict validator->合并批次校验]；研究记录：resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Ensure every deliverable passes a minimum quality gate before release, with traceable evidence and rollback path.

## Scope and Boundaries
- In scope: pre-release review, checklist validation, and acceptance sign-off
- Out of scope: feature ideation and long-term roadmap changes
- Dependencies: deliverable draft, acceptance checklist, and reviewer availability

## Trigger Conditions (if/then)
- IF deliverable is marked ready for release
- THEN run quality-gate review before any release action
- IF critical checklist item fails
- THEN block release and open corrective loop

## Preconditions
- Precondition 1: acceptance criteria are documented
- Precondition 2: reviewer and owner are available

## Inputs
- Input 1: deliverable artifact
- Input 2: quality checklist

## Outputs
- Output 1: quality-gate verdict
- Output 2: release decision with evidence

## Three-Optimal Decision
- Best Practice selected: 先质量门禁后发布，关键项失败即阻断（依据：resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md）
- Best Method selected: 双阶段评审（自检 -> 同行评审）+ 缺陷闭环（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 质量清单 + 测试记录 + strict validator（依据：resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-work-quality-gate-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/work-quality-gate-toolchain-research.md`
- 最佳实践: 先质量门禁后发布，关键项失败即阻断
- 最佳方法: 双阶段评审（自检 -> 同行评审）+ 缺陷闭环（Winner B=4.40, Margin=0.60）
- 最佳工具: 质量清单 + 测试记录 + strict validator
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 载入验收标准与风险清单 | 标准版本唯一且有效 | 标准清单 |
| 2 | 执行自检（功能/稳定/边界） | 关键项通过率100% | 自检记录 |
| 3 | 执行同行评审 | 至少1名评审确认 | 评审意见 |
| 4 | 处理缺陷并回归验证 | blocker缺陷为0 | 缺陷单 |
| 5 | 输出发布决策 | 决策理由可追溯 | 发布结论 |
| 6 | 写入质量指标与复盘项 | 指标完整且可比较 | 质量周报 |
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
- Cycle time target: <= 35 minutes per release review
- First-pass yield target: >= 93 percent items pass gate on first review
- Rework rate ceiling: <= 10 percent items need second corrective pass
- Adoption target: 100 percent releases pass this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-work-quality-gate-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-work-quality-gate-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-work-quality-gate-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-work-quality-gate-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-work-quality-gate-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-work-quality-gate-sop.overview.md

