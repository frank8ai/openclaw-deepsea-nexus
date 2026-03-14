# SOP Document

## Metadata
- SOP ID: SOP-20260217-09
- Name: 学习主动检索会话
- Tags: study, active, retrieval, session
- Primary triggers: study session starts; retrieval accuracy below threshold for two sessions
- Primary outputs: retrieval score log; session summary and next focus list
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
- Best Practice compliance: 主动检索优先于被动重读，先测后学；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md。
- Best Method compliance: 检索-纠错-重测三段会话；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md。
- Best Tool compliance: 题集/闪卡 + 计时器 + 会话日志；依据：增益[题库/闪卡:回忆率提升 >=25%；计时器:单次效率提升 >=20%；会话日志:错因闭环率提升 >=30%]；回滚[题库/闪卡->每周校准题库；计时器->放宽窗口；会话日志->最小字段记录]；研究记录：resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Run learning sessions using active retrieval first, then targeted review, to improve long-term retention.

## Scope and Boundaries
- In scope: daily or scheduled study sessions for conceptual or procedural material
- Out of scope: course enrollment and external tutoring logistics
- Dependencies: question bank, notes, and session timer

## Trigger Conditions (if/then)
- IF study session starts
- THEN perform retrieval-first session before passive reread
- IF retrieval accuracy below threshold for two sessions
- THEN trigger concept-focused remediation block

## Preconditions
- Precondition 1: study target is selected
- Precondition 2: question prompts are prepared

## Inputs
- Input 1: topic prompts and questions
- Input 2: session duration and rules

## Outputs
- Output 1: retrieval score log
- Output 2: session summary and next focus list

## Three-Optimal Decision
- Best Practice selected: 主动检索优先于被动重读，先测后学（依据：resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md）
- Best Method selected: 检索-纠错-重测三段会话（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 题集/闪卡 + 计时器 + 会话日志（依据：resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/study-active-retrieval-session-toolchain-research.md`
- 最佳实践: 主动检索优先于被动重读，先测后学
- 最佳方法: 检索-纠错-重测三段会话（Winner B=4.40, Margin=0.60）
- 最佳工具: 题集/闪卡 + 计时器 + 会话日志
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 选择本次主题和题目集 | 范围单一可完成 | 会话计划 |
| 2 | 先做闭卷检索测试 | 禁止先翻资料 | 检索成绩 |
| 3 | 标注错误并定位原因 | 错因有分类 | 错因表 |
| 4 | 进行定向复习 | 只补弱点不全量重读 | 复习记录 |
| 5 | 进行二次检索测试 | 分数较首轮提升 | 复测成绩 |
| 6 | 写会话总结与下次计划 | 下次主题与目标明确 | 会话日志 |
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
- Cycle time target: <= 45 minutes per session
- First-pass yield target: >= 85 percent sessions meet retrieval target
- Rework rate ceiling: <= 15 percent sessions require full redo
- Adoption target: 100 percent planned sessions follow this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-study-active-retrieval-session-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-study-active-retrieval-session-sop.overview.md

