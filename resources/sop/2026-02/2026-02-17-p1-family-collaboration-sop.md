# SOP Document

## Metadata
- SOP ID: SOP-20260217-21
- Name: 家庭协同与分工沟通
- Tags: p1, family, collaboration
- Primary triggers: 家庭固定任务超过5项或跨成员依赖明显; 任务漏办连续2周 >= 2项
- Primary outputs: 周分工与时间安排; 沟通纪要与待办
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
- Best Practice compliance: 固定分工+可见化时间协同；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md。
- Best Method compliance: 周计划+日历同步+周沟通；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md。
- Best Tool compliance: 分工表+共享日历+沟通清单；依据：增益[家庭分工表:漏办率下降 >=30%；共享日历:冲突减少 >=25%；周沟通清单:执行一致性提升 >=20%]；回滚[家庭分工表->周更新一次；共享日历->固定同步时点；周沟通清单->限制议题数]；研究记录：resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立家庭任务协同机制，实现责任清晰、时间协同和沟通闭环。

## Scope and Boundaries
- In scope: 家庭分工、日历协调、周沟通
- Out of scope: 家庭长期价值观讨论
- Dependencies: 共享日历、分工表、沟通清单

## Trigger Conditions (if/then)
- IF 家庭固定任务超过5项或跨成员依赖明显
- THEN 启用家庭协同SOP
- IF 任务漏办连续2周 >= 2项
- THEN 执行分工重排与优先级重设

## Preconditions
- Precondition 1: 家庭成员可访问共享日历
- Precondition 2: 每周至少一次沟通窗口可用

## Inputs
- Input 1: 家庭任务清单
- Input 2: 成员时间安排

## Outputs
- Output 1: 周分工与时间安排
- Output 2: 沟通纪要与待办

## Three-Optimal Decision
- Best Practice selected: 固定分工+可见化时间协同（依据：resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md）
- Best Method selected: 周计划+日历同步+周沟通（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 分工表+共享日历+沟通清单（依据：resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-family-collaboration-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-family-collaboration-toolchain-research.md`
- 最佳实践: 固定分工+可见化时间协同
- 最佳方法: 周计划+日历同步+周沟通（Winner B=4.40, Margin=0.60）
- 最佳工具: 分工表+共享日历+沟通清单
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 汇总本周家庭关键任务 | 任务优先级明确 | 任务清单 |
| 2 | 分配责任人和完成时间 | 每项任务有owner | 分工表 |
| 3 | 同步到共享日历 | 冲突时段已解决 | 日历截图 |
| 4 | 执行中更新状态 | 状态每2天更新 | 状态记录 |
| 5 | 周沟通复核执行情况 | 漏办项有原因 | 沟通纪要 |
| 6 | 调整下周分工规则 | 更新规则1-3条 | 规则更新 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 分工冲突 | 同一任务多人认领或无人认领 | 即时重分配并确认 | 升级到本周沟通会议 |
| 时间冲突 | 日历冲突未解决 | 优先保留关键任务窗口 | 升级到周计划重排 |
| 沟通中断 | 两周未完成沟通 | 恢复最小沟通流程 | 升级到应急分工模式 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键任务漏办率 > 30%
- Stop condition 2: 共享日历不可用超过3天
- Blast radius limit: 家庭任务记录和时间安排
- Rollback action: 回退到上周稳定分工版本

## SLA and Metrics
- Cycle time target: <= 30 分钟完成周协同计划
- First-pass yield target: >= 90 percent 家庭关键任务按期启动
- Rework rate ceiling: <= 15 percent 任务需二次分配
- Adoption target: 100 percent 家庭关键任务使用协同流程
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-family-collaboration-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-family-collaboration-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-family-collaboration-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-family-collaboration-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-family-collaboration-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-family-collaboration-sop.overview.md

