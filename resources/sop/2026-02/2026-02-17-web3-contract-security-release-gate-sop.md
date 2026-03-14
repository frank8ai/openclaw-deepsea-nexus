# SOP Document

## Metadata
- SOP ID: SOP-20260217-40
- Name: 合约安全上线门禁
- Tags: web3, contract, security, release-gate
- Primary triggers: 智能合约进入主网发布前; 权限模型或升级策略发生变更
- Primary outputs: 安全门禁通过记录（审计/测试/权限）; 上线决策与回滚预案
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
- Best Practice compliance: 合约上线必须满足审计、权限、暂停与升级四重门禁。；依据：OpenZeppelin Contracts:https://docs.openzeppelin.com/contracts/5.x/；Solidity Security Considerations:https://docs.soliditylang.org/en/latest/security-considerations.html；OWASP Smart Contract Security Testing Guide:https://scs.owasp.org/SCSTG/；研究记录：resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md。
- Best Method compliance: 预发布清单 -> 安全测试 -> 权限演练 -> 上线审批。；依据：Winner A=4.55，Runner-up=3.70，Margin=0.85，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md。
- Best Tool compliance: Slither/Echidna + OpenZeppelin库 + 多签审批面板。；依据：高危漏洞上线率下降 >=50%；权限配置错误下降 >=40%；回滚：触发pause并切回上一稳定合约版本；研究记录：resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat.
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review dates.
- Compliance reviewer: yizhi

## Objective
在主网发布前用硬门禁拦截高风险合约缺陷和权限漏洞。

## Scope and Boundaries
- In scope: 审计要求、静态分析、权限检查、pause和升级策略
- Out of scope: 代币市场活动执行
- Dependencies: 审计报告、测试流水线、多签审批

## Trigger Conditions (if/then)
- IF 智能合约进入主网发布前
- THEN run this SOP in the same execution window.
- IF 权限模型或升级策略发生变更
- THEN escalate to hard-gate review and block risky actions until decision.

## Preconditions
- Precondition 1: owner, approver, and execution roles are confirmed.
- Precondition 2: success metrics and stop conditions are numeric and auditable.

## Inputs
- Input 1: 合约版本与审计结果
- Input 2: 权限配置与升级计划

## Outputs
- Output 1: 安全门禁通过记录（审计/测试/权限）
- Output 2: 上线决策与回滚预案

## Three-Optimal Decision
- Best Practice selected: 合约上线必须满足审计、权限、暂停与升级四重门禁。（依据：resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md）
- Best Method selected: 预发布清单 -> 安全测试 -> 权限演练 -> 上线审批。（依据：Winner A=4.55，Margin=0.85）
- Best Tool selected: Slither/Echidna + OpenZeppelin库 + 多签审批面板。（依据：resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-internet-web3-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/web3-contract-security-release-gate-toolchain-research.md`
- 最佳实践: 合约上线必须满足审计、权限、暂停与升级四重门禁。
- 最佳方法: 预发布清单 -> 安全测试 -> 权限演练 -> 上线审批。（Winner A=4.55, Margin=0.85）
- 最佳工具: Slither/Echidna + OpenZeppelin库 + 多签审批面板。
- 本轮优化:
  - 将三优研究结论写入合规声明与执行流程。
  - 用非可协商约束 + 风险证据矩阵做发布门禁。
  - 固化双轨指标与自动降级门禁，避免“过程忙碌替代结果价值”。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 定义目标、主结果指标与不可协商约束 | 指标可量化且约束完整 | 目标卡 |
| 2 | 收集输入并确认角色、审批与时间窗口 | 角色和审批链完整 | 输入清单 |
| 3 | 执行 合约安全上线门禁 核心流程 | 关键门禁全部通过 | 执行记录 |
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
- Log location: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-iteration-log.md
- Required record fields: source, trigger, gate results, primary metric, process metric, decision, owner, timestamp.

## Change Control
- Rule updates this cycle (1-3 only):
1. IF objective or non-negotiables are missing, THEN block execution until fields are complete.
2. IF any hard gate fails, THEN run one focused correction loop and re-validate before release.
3. IF primary result metric degrades in trend review, THEN trigger downgrade assessment and rollback to stable baseline.

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-sop.md --strict`
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-closed-loop-pilot.md
- L0 abstract: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-web3-contract-security-release-gate-sop.overview.md
