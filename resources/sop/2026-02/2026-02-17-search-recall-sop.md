# SOP Document

## Metadata
- SOP ID: SOP-20260217-02
- Name: Search Recall Execution
- Tags: search, recall
- Primary triggers: user query contains memory triggers (`还记得`, `上次`, `之前提到`) OR query intent is historical lookup; first-pass top1 relevance is below `0.35` OR top3 median relevance is below `0.25`
- Primary outputs: top-k recall results with relevance, source, and snippet; search quality record (latency, relevance, pass/fail gate decision)
- Owner: yizhi
- Team: deepsea-nexus
- Version: v1.2
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
- Non-negotiables check: only approved local memory stores are queried, and source paths are preserved for traceability.
- Outcome metric and baseline: top1 relevance baseline 0.29 to target >= 0.35, first-pass success baseline 70% to target >= 85%.
- Reversibility and blast radius: retrieval workflow only; rollback is immediate by reverting to single-pass recall path.
- Evidence tier justification: 8 pilot runs with measurable relevance and latency outcomes meet E3 requirement.
- Best Practice compliance: evidence-linked semantic recall with threshold gates and fallback.；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md。
- Best Method compliance: two-pass recall (original query, then expansion if gate fails).；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md。
- Best Tool compliance: `nexus_recall` for primary recall, `smart_search` for trigger-aware expansion, `rg` for source validation.；依据：增益[`nexus_recall`:consistent baseline retrieval；`smart_search`:improved first relevant hit rate；`rg`:fast local evidence validation]；回滚[`nexus_recall`->fallback to single-pass only；`smart_search`->disable expansion path；`rg`->manual source check]；研究记录：resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
Return high-confidence recall results for user queries with explicit source evidence and predictable quality.

## Scope and Boundaries
- In scope: `nexus_recall`, `search_recall`, `smart_search`, and result formatting for user-facing recall output.
- Out of scope: document ingestion policy, embedding model retraining, and archive compaction.
- Dependencies: `nexus_core` service initialized and vector store accessible.

## Trigger Conditions (if/then)
- IF user query contains memory triggers (`还记得`, `上次`, `之前提到`) OR query intent is historical lookup,
- THEN run this SOP with top-k recall.
- IF first-pass top1 relevance is below `0.35` OR top3 median relevance is below `0.25`,
- THEN trigger second-pass query expansion.

## Preconditions
- Precondition 1: `python3 nexus_core.py health` returns initialized and available.
- Precondition 2: recall stats show documents count greater than 0.

## Inputs
- Input 1: raw user query.
- Input 2: target `n` (default 5, expanded pass uses 8).

## Outputs
- Output 1: top-k recall results with relevance, source, and snippet.
- Output 2: search quality record (latency, relevance, pass/fail gate decision).

## Three-Optimal Decision
- Best Practice selected: evidence-linked semantic recall with threshold gates and fallback.（依据：resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md）
- Best Method selected: two-pass recall (original query, then expansion if gate fails).（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: `nexus_recall` for primary recall, `smart_search` for trigger-aware expansion, `rg` for source validation.（依据：resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md）
- Scorecard reference: `resources/sop/2026-02/2026-02-17-search-recall-scorecard.md`

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/search-recall-toolchain-research.md`
- 最佳实践: evidence-linked semantic recall with threshold gates and fallback.
- 最佳方法: two-pass recall (original query, then expansion if gate fails).（Winner B=4.40, Margin=0.60）
- 最佳工具: `nexus_recall` for primary recall, `smart_search` for trigger-aware expansion, `rg` for source validation.
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | Run readiness checks (`health`, `stats`) | service available and docs > 0 | command outputs |
| 2 | Normalize and classify query intent | query intent tagged (`recall` or `semantic`) | classification note |
| 3 | Execute first-pass recall with original query | top1 >= 0.35 and top3 median >= 0.25 OR mark gate fail | result list with scores |
| 4 | If gate fails, run second-pass with up to 2 rewritten queries and n=8 | at least one pass reaches gate OR escalate | second-pass logs |
| 5 | Merge, dedupe, and rank final results | final output has source and relevance for each item | final response block |
| 6 | Record metrics and update iteration log | latency and pass rate recorded | weekly log entry |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| Service unavailable | health check unavailable or initialized false | stop and return system-not-ready response | escalate to maintainer immediately |
| Low relevance after second pass | top1 < 0.35 and top3 median < 0.25 | request clarifying query and keep top evidence only | escalate as retrieval-quality incident |
| Empty result set | result count is 0 after second pass | fallback to keyword-focused query and narrowed scope | escalate if repeated 3 times in one cycle |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: health check fails or document count is 0.
- Stop condition 2: p95 end-to-end latency exceeds 90 seconds for 3 consecutive runs.
- Blast radius limit: retrieval output and SOP artifacts only (`resources/sop` and query-response formatting).
- Rollback action: disable second-pass expansion and revert to stable single-pass recall workflow.

## SLA and Metrics
- Cycle time target: <= 90 seconds end-to-end per recall request.
- First-pass yield target: >= 85 percent requests pass first-pass relevance gate.
- Rework rate ceiling: <= 15 percent requests require second-pass expansion.
- Adoption target: 100 percent memory-intent queries follow this SOP.
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: `resources/sop/2026-02/2026-02-17-search-recall-iteration-log.md`.
- Required record fields: query class, top1 relevance, top3 median relevance, total latency, pass stage.

## Change Control
- Rule updates this cycle (1-3 only):
1. IF first-pass relevance gate fails, THEN execute two-pass expansion before final response.
2. IF health check fails, THEN block retrieval and return explicit system readiness message.
3. IF low relevance repeats 3 times in a cycle, THEN require query intent clarification prompt.

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-search-recall-sop.md --strict`
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: `resources/sop/2026-02/2026-02-17-search-recall-scorecard.md`
- Iteration log: `resources/sop/2026-02/2026-02-17-search-recall-iteration-log.md`
- Related decision cards: `resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md`
- L0 abstract: resources/sop/2026-02/2026-02-17-search-recall-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-search-recall-sop.overview.md

