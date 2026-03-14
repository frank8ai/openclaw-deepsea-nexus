# SOP Document

## Metadata
- SOP ID: SOP-20260217-20
- Name: 学习迁移与应用实践
- Tags: p1, learning, transfer
- Primary triggers: 完成一次学习会话或模块; 连续2次学习后无迁移产出
- Primary outputs: 实践产出（题解或功能实现）; 迁移复盘记录
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
- Non-negotiables check: 执行中不允许绕过安全、合规、数据完整性约束。
- Outcome metric and baseline: 使用近6次历史样本作为基线，并定义目标增量。
- Reversibility and blast radius: 该流程仅变更流程文档和任务状态，可单周期回滚。
- Evidence tier justification: R2流程以6次试运行记录满足E3要求。
- Best Practice compliance: 学习后尽快应用，防止知识停留在理解层；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md。
- Best Method compliance: 72小时迁移窗口+小任务验证；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md。
- Best Tool compliance: 迁移任务清单+练习仓库+迁移日志；依据：增益[迁移任务清单:迁移率提升 >=30%；实战练习仓库:复盘质量提升 >=25%；迁移日志:闭环速度提升 >=20%]；回滚[迁移任务清单->拆小任务；实战练习仓库->周归档；迁移日志->最小字段强制]；研究记录：resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
把学习内容转化为可交付应用结果，提升知识迁移与长期掌握。

## Scope and Boundaries
- In scope: 课程学习后的题目实践、项目微任务实践
- Out of scope: 纯理论阅读记录
- Dependencies: 学习内容、实践题库、项目任务池

## Trigger Conditions (if/then)
- IF 完成一次学习会话或模块
- THEN 在72小时内创建并执行迁移任务
- IF 连续2次学习后无迁移产出
- THEN 强制安排迁移专场并削减新学习输入

## Preconditions
- Precondition 1: 学习目标与内容已记录
- Precondition 2: 存在可执行实践任务

## Inputs
- Input 1: 学习笔记和重点概念
- Input 2: 对应实践任务

## Outputs
- Output 1: 实践产出（题解或功能实现）
- Output 2: 迁移复盘记录

## Three-Optimal Decision
- Best Practice selected: 学习后尽快应用，防止知识停留在理解层（依据：resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md）
- Best Method selected: 72小时迁移窗口+小任务验证（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 迁移任务清单+练习仓库+迁移日志（依据：resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-learning-transfer-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-learning-transfer-toolchain-research.md`
- 最佳实践: 学习后尽快应用，防止知识停留在理解层
- 最佳方法: 72小时迁移窗口+小任务验证（Winner B=4.40, Margin=0.60）
- 最佳工具: 迁移任务清单+练习仓库+迁移日志
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 提取本次学习的3个关键概念 | 概念可映射到任务 | 概念清单 |
| 2 | 为每个概念匹配一个实践任务 | 任务可在当天启动 | 任务映射表 |
| 3 | 执行最小实践并提交结果 | 有可运行或可验证结果 | 实践产物 |
| 4 | 记录问题与卡点 | 卡点有分类 | 问题记录 |
| 5 | 针对卡点进行定向补学 | 补学与卡点一一对应 | 补学记录 |
| 6 | 完成迁移复盘并更新下次学习重点 | 下次重点明确 | 迁移复盘 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 任务过大 | 预计时长超2小时 | 拆分为最小可交付子任务 | 升级到学习计划调整 |
| 无可用实践题 | 任务池为空 | 从当前项目提取微任务 | 升级到内容owner |
| 迁移失败率高 | 连续2次未产出有效结果 | 降级难度并增加示例 | 升级到专项辅导 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 连续两周迁移完成率 < 60%
- Stop condition 2: 迁移任务无验证结果
- Blast radius limit: 学习任务和实践仓库
- Rollback action: 回退到基础迁移任务集

## SLA and Metrics
- Cycle time target: <= 45 分钟完成一次迁移任务规划
- First-pass yield target: >= 85 percent 迁移任务首轮有产出
- Rework rate ceiling: <= 15 percent 迁移任务需重做
- Adoption target: 100 percent 学习模块后执行迁移
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-learning-transfer-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-learning-transfer-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-learning-transfer-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-learning-transfer-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-learning-transfer-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-learning-transfer-sop.overview.md

