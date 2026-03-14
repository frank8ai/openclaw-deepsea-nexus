# SOP Document

## Metadata
- SOP ID: SOP-20260217-24
- Name: 自动化编排与集成
- Tags: p2, automation, orchestration
- Primary triggers: 同类任务重复 >= 3次/周; 自动化异常率 > 10%
- Primary outputs: 自动化脚本和执行计划; 监控告警与回滚说明
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
- [x] Trigger conditions are testable (if/then with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: 不允许以速度换取安全、合规和数据完整性。
- Outcome metric and baseline: 使用近6次样本做基线并定义目标增量。
- Reversibility and blast radius: 仅影响流程和任务配置，可单周期回滚。
- Evidence tier justification: R2场景下6次试运行满足E3要求。
- Best Practice compliance: 自动化必须可观测且可回滚；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md。
- Best Method compliance: 脚本化+告警+演练回滚；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md。
- Best Tool compliance: 脚本仓库+告警系统+回滚手册；依据：增益[自动化脚本:人工工时下降 >=30%；告警规则:异常发现提前 >=25%；回滚手册:恢复时间下降 >=20%]；回滚[自动化脚本->快速回滚脚本；告警规则->阈值调优；回滚手册->周度演练]；研究记录：resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立可控自动化编排流程，减少重复劳动并确保故障可快速回滚。

## Scope and Boundaries
- In scope: 脚本化任务、提醒触发、系统集成流程
- Out of scope: 高风险不可逆基础设施变更
- Dependencies: 脚本仓库、告警通道、回滚手册

## Trigger Conditions (if/then)
- IF 同类任务重复 >= 3次/周
- THEN 启动自动化SOP并脚本化
- IF 自动化异常率 > 10%
- THEN 切回半自动并修复后重放

## Preconditions
- Precondition 1: 任务输入输出边界清晰
- Precondition 2: 存在可验证回滚路径

## Inputs
- Input 1: 任务流程定义
- Input 2: 运行约束和异常阈值

## Outputs
- Output 1: 自动化脚本和执行计划
- Output 2: 监控告警与回滚说明

## Three-Optimal Decision
- Best Practice selected: 自动化必须可观测且可回滚（依据：resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md）
- Best Method selected: 脚本化+告警+演练回滚（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 脚本仓库+告警系统+回滚手册（依据：resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-automation-orchestration-toolchain-research.md`
- 最佳实践: 自动化必须可观测且可回滚
- 最佳方法: 脚本化+告警+演练回滚（Winner B=4.40, Margin=0.60）
- 最佳工具: 脚本仓库+告警系统+回滚手册
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 识别可自动化重复任务 | 频次和收益可量化 | 任务基线 |
| 2 | 设计脚本输入输出和失败分支 | 失败分支完整 | 流程图 |
| 3 | 实现最小可运行脚本 | 核心路径可运行 | 脚本运行记录 |
| 4 | 接入告警与日志 | 异常可被探测 | 告警截图 |
| 5 | 执行回滚演练 | 回滚在目标时间内成功 | 演练报告 |
| 6 | 灰度启用并追踪指标 | 异常率在阈值内 | 运行报表 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 脚本失败 | 关键步骤退出码非0 | 立即切回手工流程 | 升级到自动化owner |
| 告警失真 | 误报率连续两天 > 20% | 调阈值并分级告警 | 升级到监控维护者 |
| 回滚失败 | 回滚步骤未完成 | 执行应急手册人工恢复 | 升级高压事件SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 回滚演练失败
- Stop condition 2: 自动化异常率连续2周 > 10%
- Blast radius limit: 自动化任务和相关状态
- Rollback action: 回退到半自动/手工流程

## SLA and Metrics
- Cycle time target: <= 2 天完成单流程自动化上线
- First-pass yield target: >= 90 percent 自动化首轮通过
- Rework rate ceiling: <= 15 percent 自动化需二次修复
- Adoption target: 100 percent 符合条件任务纳入自动化评估
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-automation-orchestration-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-automation-orchestration-sop.overview.md

