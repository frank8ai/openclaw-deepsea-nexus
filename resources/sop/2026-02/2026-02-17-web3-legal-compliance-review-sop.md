# SOP Document

## Metadata
- SOP ID: SOP-20260217-48
- Name: 法务合规审查（Web3）
- Tags: web3, legal, compliance, kyc-aml
- Primary triggers: 新产品或活动涉及跨地区用户; 监管政策变更或合规风险预警
- Primary outputs: 合规审查结论与限制清单; KYC/AML触发规则与执行记录
- Owner: yizhi
- Team: deepsea-nexus
- Version: v1.0
- Status: active
- Risk tier: high
- Reversibility class: R3
- Evidence tier at release: E4
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
- Non-negotiables check: non-negotiable constraints (legal/safety/security/data integrity) are checked before execution and are non-compensatory.
- Outcome metric and baseline: baseline derived from 6 pilot runs with target deltas defined in SLA and Metrics.
- Reversibility and blast radius: R3 with explicit blast-radius limit and rollback actions.
- Evidence tier justification: E4 chosen based on risk tier `high` and reversibility `R3`.
- Best Practice compliance: 跨地区Web3业务必须先完成合规门禁再上线。；依据：FATF Virtual Assets Guidance:https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Guidance-rba-virtual-assets-2021.html；OFAC Virtual Currency Sanctions Action:https://ofac.treasury.gov/recent-actions/20221011；NIST SCRM:https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final；研究记录：resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md。
- Best Method compliance: 地区映射 -> 规则判定 -> 合规审批 -> 发布复核。；依据：Winner A=4.55，Runner-up=3.70，Margin=0.85，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md。
- Best Tool compliance: 合规清单 + 规则引擎 + 审查台账。；依据：违规发布概率下降 >=40%；审查效率提升 >=25%；回滚：立即下线违规入口并恢复合规默认配置；研究记录：resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat.
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review dates.
- Compliance reviewer: yizhi

## Objective
把法务合规要求前置到业务设计与发布流程，降低监管与执法风险。

## Scope and Boundaries
- In scope: 地区限制、KYC/AML触发、宣传口径合规审查
- Out of scope: 税务申报执行
- Dependencies: 法务顾问、合规规则库、地区策略配置

## Trigger Conditions (if/then)
- IF 新产品或活动涉及跨地区用户
- THEN run this SOP in the same execution window.
- IF 监管政策变更或合规风险预警
- THEN escalate to hard-gate review and block risky actions until decision.

## Preconditions
- Precondition 1: owner, approver, and execution roles are confirmed.
- Precondition 2: success metrics and stop conditions are numeric and auditable.

## Inputs
- Input 1: 业务方案与目标地区
- Input 2: 当前监管要求与内部政策

## Outputs
- Output 1: 合规审查结论与限制清单
- Output 2: KYC/AML触发规则与执行记录

## Three-Optimal Decision
- Best Practice selected: 跨地区Web3业务必须先完成合规门禁再上线。（依据：resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md）
- Best Method selected: 地区映射 -> 规则判定 -> 合规审批 -> 发布复核。（依据：Winner A=4.55，Margin=0.85）
- Best Tool selected: 合规清单 + 规则引擎 + 审查台账。（依据：resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/web3-legal-compliance-review-toolchain-research.md`
- 最佳实践: 跨地区Web3业务必须先完成合规门禁再上线。
- 最佳方法: 地区映射 -> 规则判定 -> 合规审批 -> 发布复核。（Winner A=4.55, Margin=0.85）
- 最佳工具: 合规清单 + 规则引擎 + 审查台账。
- 本轮优化:
  - 将三优研究结论写入合规声明与执行流程。
  - 用非可协商约束 + 风险证据矩阵做发布门禁。
  - 固化双轨指标与自动降级门禁，避免“过程忙碌替代结果价值”。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 定义目标、主结果指标与不可协商约束 | 指标可量化且约束完整 | 目标卡 |
| 2 | 收集输入并确认角色、审批与时间窗口 | 角色和审批链完整 | 输入清单 |
| 3 | 执行 法务合规审查（Web3） 核心流程 | 关键门禁全部通过 | 执行记录 |
| 4 | 记录主结果指标与过程指标 | 双轨指标均有数值 | 指标快照 |
| 5 | 异常时触发 Kill Switch 并执行回滚 | 停机、沟通、回滚动作可追溯 | 异常处置记录 |
| 6 | 复盘并写回 1-3 条规则 | 规则具备条件/动作/检查/避免四元组 | 规则更新记录 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 输入或约束不完整 | 关键字段缺失或冲突 | 补齐信息并阻断高风险执行 | escalate to owner |
| 主结果指标异常退化 | 主结果指标低于阈值 | 触发Kill Switch并进入应急回滚 | escalate to incident owner |
| 合规或安全风险触发 | 出现违规或高危告警 | 立即停止并走合规审批 | escalate to compliance/security owner |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: primary result metric cannot be measured or verified.
- Stop condition 2: non-negotiable constraints are violated or unresolved.
- Blast radius limit: SOP artifacts, execution plan, and directly related systems only.
- Rollback action: rollback to last stable strategy and freeze further risky changes until review.

## SLA and Metrics
- Cycle time target: <= 90 分钟完成单次闭环执行
- First-pass yield target: >= 88 percent 场景首轮通过
- Rework rate ceiling: <= 18 percent 需要二次修正
- Adoption target: 100 percent 适用场景执行本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-iteration-log.md
- Required record fields: source, trigger, gate results, primary metric, process metric, decision, owner, timestamp.

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or non-negotiables are missing, THEN block execution until fields are complete.
2. IF any hard gate fails, THEN run one focused correction loop and re-validate before release.
3. IF primary result metric degrades in trend review, THEN trigger downgrade assessment and rollback to stable baseline.

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-sop.md --strict`
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-web3-legal-compliance-review-sop.overview.md
