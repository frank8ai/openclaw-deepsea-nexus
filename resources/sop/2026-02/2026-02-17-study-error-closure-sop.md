# SOP Document

## Metadata
- SOP ID: SOP-20260217-11
- Name: 学习错题与薄弱点闭环
- Tags: study, error, closure
- Primary triggers: practice session finishes with mistakes logged; same error type appears in 3 or more attempts
- Primary outputs: corrective action plan per error category; updated mastery score and closed/open status
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
- Best Practice compliance: 错误按根因分类，优先处理高频高影响错误；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md。
- Best Method compliance: 错因分桶 -> 定向修复 -> 再测闭环；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md。
- Best Tool compliance: 错题本 + 根因标签 + 复测清单；依据：增益[错题本模板:漏记率下降 >=30%；根因标签:复发率下降 >=20%；复测清单:修复率提升 >=25%]；回滚[错题本模板->最小字段；根因标签->每周校准；复测清单->固定窗口]；研究记录：resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Capture errors by root cause and run targeted correction loops until weak points cross minimum mastery thresholds.

## Scope and Boundaries
- In scope: mistake review after practice tests or retrieval sessions
- Out of scope: new-topic planning and unrelated project execution
- Dependencies: error log, root-cause tags, and remediation task bank

## Trigger Conditions (if/then)
- IF practice session finishes with mistakes logged
- THEN run error-closure loop for top weak points
- IF same error type appears in 3 or more attempts
- THEN escalate to deep remediation block

## Preconditions
- Precondition 1: error logs include question and cause
- Precondition 2: remediation tasks are available

## Inputs
- Input 1: error entries
- Input 2: mastery threshold

## Outputs
- Output 1: corrective action plan per error category
- Output 2: updated mastery score and closed/open status

## Three-Optimal Decision
- Best Practice selected: 错误按根因分类，优先处理高频高影响错误（依据：resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md）
- Best Method selected: 错因分桶 -> 定向修复 -> 再测闭环（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 错题本 + 根因标签 + 复测清单（依据：resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-study-error-closure-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/study-error-closure-toolchain-research.md`
- 最佳实践: 错误按根因分类，优先处理高频高影响错误
- 最佳方法: 错因分桶 -> 定向修复 -> 再测闭环（Winner B=4.40, Margin=0.60）
- 最佳工具: 错题本 + 根因标签 + 复测清单
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集本轮错误样本 | 样本完整且可追溯 | 错误清单 |
| 2 | 按根因分类（概念/步骤/粗心） | 每条仅1主因 | 根因标签 |
| 3 | 识别高频错误优先队列 | 高频项优先级明确 | 优先队列 |
| 4 | 执行定向修复训练 | 修复动作与根因匹配 | 修复记录 |
| 5 | 进行复测验证 | 高频错误复发率下降 | 复测结果 |
| 6 | 更新规则并沉淀模板 | 规则1-3条可复用 | 规则更新 |
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
- Cycle time target: <= 40 minutes per error-closure batch
- First-pass yield target: >= 87 percent high-frequency errors show mastery lift
- Rework rate ceiling: <= 15 percent errors reopen after closure
- Adoption target: 100 percent sessions with errors trigger this SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-study-error-closure-iteration-log.md
- Required record fields: run date, owner, trigger, gate results, cycle time, pass/fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or success metric is missing at intake, THEN block execution until both are present.
2. IF a hard gate fails, THEN perform one focused correction loop and rerun validation.
3. IF rework exceeds threshold in 2 consecutive runs, THEN adjust trigger threshold and retrain checklist usage.

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-study-error-closure-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-study-error-closure-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-study-error-closure-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-study-error-closure-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-study-error-closure-sop.overview.md

