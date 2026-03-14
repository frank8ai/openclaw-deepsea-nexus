# SOP Document

## Metadata
- SOP ID: SOP-20260217-25
- Name: 复杂决策与多模型评估
- Tags: p2, decision, multi, model
- Primary triggers: 决策影响级别为medium或high; 关键信息缺口 >= 3项
- Primary outputs: 多模型对比结论; 执行建议和停止条件
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
- Best Practice compliance: 高影响决策必须多模型交叉；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md。
- Best Method compliance: 三模型对比+风险矩阵+止损线；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md。
- Best Tool compliance: 决策卡+对比表+风险矩阵；依据：增益[决策卡模板:漏项率下降 >=30%；多模型对比表:风险识别率提升 >=25%；风险矩阵:止损速度提升 >=20%]；回滚[决策卡模板->精简字段；多模型对比表->双人复核；风险矩阵->周期校准]；研究记录：resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
在高影响决策中强制执行多模型对比，提升决策质量与可追溯性。

## Scope and Boundaries
- In scope: 中高影响决策、不可逆变更决策
- Out of scope: 低影响即时事务
- Dependencies: Decision Card模板、多模型库、风险矩阵

## Trigger Conditions (if/then)
- IF 决策影响级别为medium或high
- THEN 执行多模型决策SOP
- IF 关键信息缺口 >= 3项
- THEN 强制纳入概率模型并延期执行

## Preconditions
- Precondition 1: 问题定义和目标已明确
- Precondition 2: 至少3个候选模型可用

## Inputs
- Input 1: 决策问题与约束
- Input 2: 候选方案与风险信息

## Outputs
- Output 1: 多模型对比结论
- Output 2: 执行建议和停止条件

## Three-Optimal Decision
- Best Practice selected: 高影响决策必须多模型交叉（依据：resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md）
- Best Method selected: 三模型对比+风险矩阵+止损线（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 决策卡+对比表+风险矩阵（依据：resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-decision-multi-model-toolchain-research.md`
- 最佳实践: 高影响决策必须多模型交叉
- 最佳方法: 三模型对比+风险矩阵+止损线（Winner B=4.40, Margin=0.60）
- 最佳工具: 决策卡+对比表+风险矩阵
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 定义决策目标、约束、成功阈值 | 目标和阈值可量化 | 决策卡 |
| 2 | 选择至少3个模型 | 模型适用性说明完整 | 模型选择记录 |
| 3 | 产出多模型对比表 | 每个模型含行动和禁行项 | 对比表 |
| 4 | 构建风险矩阵和停止条件 | 高风险项有止损动作 | 风险矩阵 |
| 5 | 做方案选择并记录理由 | 选择理由可追溯 | 选择记录 |
| 6 | 执行后复盘并回写规则 | 1-3条规则更新完成 | 复盘记录 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 模型冲突 | 模型建议相反 | 按约束优先级裁剪 | 升级到决策owner裁决 |
| 证据不足 | 关键指标缺失 | 补证据前不执行 | 升级到研究SOP |
| 执行后偏差过大 | 结果偏离预测 > 30% | 触发止损并重评 | 升级高压事件SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 成功指标无法量化
- Stop condition 2: 关键风险无止损动作
- Blast radius limit: 决策文档和执行路径
- Rollback action: 回退到前一稳定方案

## SLA and Metrics
- Cycle time target: <= 90 分钟完成单次决策评估
- First-pass yield target: >= 90 percent 决策评估首轮完成
- Rework rate ceiling: <= 15 percent 决策需二次评估
- Adoption target: 100 percent medium/high决策使用本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-decision-multi-model-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-decision-multi-model-sop.overview.md

