# SOP Document

## Metadata
- SOP ID: SOP-20260217-18
- Name: 项目启动与范围风险对齐
- Tags: p1, project, kickoff
- Primary triggers: 新项目立项或重大版本开工; 范围变更请求 >= 2 次
- Primary outputs: 项目启动包（范围、风险、依赖）; 启动评审结论与行动清单
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
- Best Practice compliance: 启动前先对齐范围风险依赖；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md。
- Best Method compliance: 启动会+清单化评审+门禁通过；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md。
- Best Tool compliance: 启动模板+风险矩阵+依赖图；依据：增益[启动清单模板:漏项率下降 >=30%；风险矩阵:重大风险提前发现 >=25%；依赖图:延误预警提前 >=20%]；回滚[启动清单模板->核心字段优先；风险矩阵->双人复核；依赖图->周更新一次]；研究记录：resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
在项目启动阶段完成范围、风险、依赖和里程碑对齐，建立可执行启动基线。

## Scope and Boundaries
- In scope: 新项目启动、重大版本启动
- Out of scope: 已进入稳定迭代阶段的日常任务
- Dependencies: 启动模板、风险矩阵、依赖清单

## Trigger Conditions (if/then)
- IF 新项目立项或重大版本开工
- THEN 执行项目启动SOP并产出启动包
- IF 范围变更请求 >= 2 次
- THEN 触发范围重评与风险重估

## Preconditions
- Precondition 1: 项目owner已确定
- Precondition 2: 核心干系人可参加启动评审

## Inputs
- Input 1: 项目目标与边界
- Input 2: 资源约束与里程碑

## Outputs
- Output 1: 项目启动包（范围、风险、依赖）
- Output 2: 启动评审结论与行动清单

## Three-Optimal Decision
- Best Practice selected: 启动前先对齐范围风险依赖（依据：resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md）
- Best Method selected: 启动会+清单化评审+门禁通过（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 启动模板+风险矩阵+依赖图（依据：resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-project-kickoff-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-project-kickoff-toolchain-research.md`
- 最佳实践: 启动前先对齐范围风险依赖
- 最佳方法: 启动会+清单化评审+门禁通过（Winner B=4.40, Margin=0.60）
- 最佳工具: 启动模板+风险矩阵+依赖图
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集项目目标、约束、干系人 | 目标和约束可量化 | 项目概览 |
| 2 | 明确范围和非目标 | 范围边界无歧义 | 范围清单 |
| 3 | 识别Top风险和缓解动作 | 高风险均有应对 | 风险矩阵 |
| 4 | 列出关键依赖与负责人 | 关键依赖均有owner | 依赖图 |
| 5 | 召开启动评审并确认里程碑 | 干系人确认通过 | 评审纪要 |
| 6 | 发布启动包并进入执行 | 启动包可检索可追踪 | 启动包链接 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 范围争议 | 同一需求有多版本解释 | 冻结当前版本并升级裁决 | 升级到项目owner |
| 风险无负责人 | 高风险条目无owner | 会中指定负责人 | 升级到管理层 |
| 依赖不可达 | 外部依赖交付日期不确定 | 建立替代路径 | 升级到里程碑重排 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 启动包关键字段缺失
- Stop condition 2: 高风险无缓解方案
- Blast radius limit: 启动文档和项目计划
- Rollback action: 回退到上一版启动包并重审

## SLA and Metrics
- Cycle time target: <= 2 个工作日完成启动包
- First-pass yield target: >= 90 percent 启动评审一次通过
- Rework rate ceiling: <= 15 percent 启动包二次返工
- Adoption target: 100 percent 新项目使用本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-project-kickoff-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-project-kickoff-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-project-kickoff-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-project-kickoff-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-project-kickoff-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-project-kickoff-sop.overview.md

