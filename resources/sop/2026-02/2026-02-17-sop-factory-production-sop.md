# SOP Document

## Metadata
- SOP ID: SOP-20260217-15
- Name: SOP Factory Production
- Tags: sop, factory, production
- Primary triggers: task frequency is >= 3 per month AND outcome variance coefficient is <= 0.20; an active SOP has first-pass yield < 85% or rework rate > 20% in one review window
- Primary outputs: SOP artifact triplet (`sop.md`, `scorecard.md`, `iteration-log.md`) with release decision; strict validation evidence and 1-3 rule updates for next cycle
- Owner: yizhi
- Team: deepsea-nexus
- Version: v1.3
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
- [x] Trigger conditions are testable (`if/then` with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: all SOP releases must pass legal/safety/security/data-integrity checks before any speed or cost optimization.
- Outcome metric and baseline: baseline from at least 3 historical samples and pilot results from at least 5 runs are mandatory.
- Reversibility and blast radius: this SOP changes process artifacts only; rollback is immediate by reverting markdown artifacts and status.
- Evidence tier justification: R2 process release with 6-run pilot and strict validator evidence satisfies E3.
- Best Practice compliance: non-compensatory standard stack with explicit hard-gate release policy.；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md。
- Best Method compliance: six-step factory pipeline (classify -> baseline -> scorecard -> author -> pilot -> iterate).；依据：Winner B=4.55，Runner-up=3.80，Margin=0.75，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md。
- Best Tool compliance: markdown templates, strict validator, and `rg` checks for completeness and references.；依据：增益[Markdown templates:>=30% drafting consistency gain；`validate_sop_factory.py --strict`:>=40% reduction in gate-miss defects；`rg`:>=30% reduction in manual review time]；回滚[Markdown templates->keep custom notes in appendix；`validate_sop_factory.py --strict`->keep draft mode until pilot is complete；`rg`->manual section-by-section review]；研究记录：resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Produce or upgrade repeatable SOPs into active status in one controlled cycle with strict, machine-verifiable release quality, and mandatory direct injection of the supreme standard stack plus four hard mechanisms.

## Scope and Boundaries
- In scope: SOP candidate classification, baseline capture, scorecard selection, SOP authoring, pilot review, and strict release validation.
- Out of scope: exploratory one-off tasks with unstable steps, and production system changes outside SOP artifacts.
- Dependencies: `agent/patterns/sop-factory.md`, `resources/sop/TEMPLATE*.md`, `scripts/validate_sop_factory.py`.

## Trigger Conditions (if/then)
- IF task frequency is >= 3 per month AND outcome variance coefficient is <= 0.20,
- THEN route to this SOP for standardization and release.
- IF an active SOP has first-pass yield < 85% or rework rate > 20% in one review window,
- THEN route to this SOP for mandatory iteration and re-release.

## Preconditions
- Precondition 1: owner is assigned and at least 3 baseline samples are available.
- Precondition 2: candidate task has explicit objective, measurable outputs, and known constraints.

## Inputs
- Input 1: candidate task description with frequency and variance data.
- Input 2: baseline metrics, constraints, and current tool/method options.

## Outputs
- Output 1: SOP artifact triplet (`sop.md`, `scorecard.md`, `iteration-log.md`) with release decision.
- Output 2: strict validation evidence and 1-3 rule updates for next cycle.

## Three-Optimal Decision
- Best Practice selected: non-compensatory standard stack with explicit hard-gate release policy.（依据：resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md）
- Best Method selected: six-step factory pipeline (classify -> baseline -> scorecard -> author -> pilot -> iterate).（依据：Winner B=4.55，Margin=0.75）
- Best Tool selected: markdown templates, strict validator, and `rg` checks for completeness and references.（依据：resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md）
- Scorecard reference: `resources/sop/2026-02/2026-02-17-sop-factory-production-scorecard.md`

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/sop-factory-production-toolchain-research.md`
- 最佳实践: non-compensatory standard stack with explicit hard-gate release policy.
- 最佳方法: six-step factory pipeline (classify -> baseline -> scorecard -> author -> pilot -> iterate).（Winner B=4.55, Margin=0.75）
- 最佳工具: markdown templates, strict validator, and `rg` checks for completeness and references.
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | Classify candidate and confirm SOP routing | Frequency >= 3/month and CV <= 0.20 are recorded | routing note |
| 2 | Capture baseline from recent runs | at least 3 baseline samples exist for cycle time, FPY, rework | baseline table |
| 3 | Build three-optimal scorecard and select method | winner score >= 3.50 and margin >= 0.20 or documented override | scorecard |
| 4 | Inject supreme standard stack and four hard mechanisms into the candidate SOP before drafting details | all seven principle declarations and all four mechanisms are explicitly present and testable | governance injection checklist |
| 5 | Author SOP v1 from template with all hard fields | trigger, inputs/outputs, exceptions, rollback, SLA all filled | SOP draft |
| 6 | Run pilot and produce iteration log | at least 5 pilot runs logged and 1-3 rules updated | iteration log |
| 7 | Run strict validator and resolve failures | `validate_sop_factory.py --strict` exit code is 0 | validation output |
| 8 | Release decision and indexing | release decision is approve and links are valid | release section |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| Unstable task routed too early | frequency < 3/month or CV > 0.20 | return candidate to decision-card track | escalate to owner for revisit date |
| Evidence tier mismatch | R/E mapping fails (`R1->E2`, `R2->E3`, `R3->E4`) | block activation and upgrade evidence tier | escalate as release hold |
| Strict validation failure | validator reports missing sections or unchecked gates | run one focused correction loop and re-validate | escalate if second pass still fails |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: baseline sample count is below 3.
- Stop condition 2: strict validation fails after two correction loops.
- Blast radius limit: `resources/sop/*`, `agent/patterns/decision-rules.md`, and related SOP index references only.
- Rollback action: revert candidate SOP to draft status and restore last active SOP version.

## SLA and Metrics
- Cycle time target: <= 90 minutes per SOP production cycle.
- First-pass yield target: >= 90 percent SOP candidates pass strict validation on first attempt.
- Rework rate ceiling: <= 15 percent SOP candidates require second correction loop.
- Adoption target: 100 percent qualified repeatable tasks follow SOP factory routing.
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: `resources/sop/2026-02/2026-02-17-sop-factory-production-iteration-log.md`
- Required record fields: candidate ID, routing metrics, baseline values, winner option, validation result, release decision, rule updates.

## Change Control
- Rule updates this cycle (1-3 only):
1. IF task frequency < 3/month OR CV > 0.20, THEN route to Decision Card instead of SOP Factory.
2. IF reversibility class and evidence tier fail mapping, THEN block activation until evidence is upgraded.
3. IF strict validator fails, THEN correction loop is mandatory before release decision can be approve.

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-sop-factory-production-sop.md --strict`
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: `resources/sop/2026-02/2026-02-17-sop-factory-production-scorecard.md`
- Iteration log: `resources/sop/2026-02/2026-02-17-sop-factory-production-iteration-log.md`
- Related decision cards: `resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md`
- L0 abstract: resources/sop/2026-02/2026-02-17-sop-factory-production-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-sop-factory-production-sop.overview.md
