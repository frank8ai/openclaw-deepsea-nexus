# SOP Document

## Metadata
- SOP ID: SOP-20260217-22
- Name: 家务与周期维护
- Tags: p1, home, maintenance
- Primary triggers: 存在周期任务且过去30天有遗漏; 同类维护任务连续2次延迟
- Primary outputs: 本周家务维护执行计划; 执行完成和异常记录
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
- Best Practice compliance: 周期化和可视化优先；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md。
- Best Method compliance: 固定窗口执行+完成后记录；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md。
- Best Tool compliance: 周期清单+日历提醒+维护记录；依据：增益[周期清单:漏项率下降 >=30%；固定窗口日历:完成率提升 >=25%；维护记录表:复发问题下降 >=20%]；回滚[周期清单->月度刷新；固定窗口日历->预留备选窗口；维护记录表->最小字段强制]；研究记录：resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
把家务与设备维护任务周期化、可视化，降低遗漏和突发故障。

## Scope and Boundaries
- In scope: 家务例行任务、家庭设备周期维护
- Out of scope: 大型装修和一次性改造
- Dependencies: 周期任务清单、日历窗口、维护记录

## Trigger Conditions (if/then)
- IF 存在周期任务且过去30天有遗漏
- THEN 启用家务维护SOP
- IF 同类维护任务连续2次延迟
- THEN 降低任务粒度并增加提醒

## Preconditions
- Precondition 1: 任务清单已建立
- Precondition 2: 本周可执行窗口存在

## Inputs
- Input 1: 周期任务列表
- Input 2: 本周可用时间

## Outputs
- Output 1: 本周家务维护执行计划
- Output 2: 执行完成和异常记录

## Three-Optimal Decision
- Best Practice selected: 周期化和可视化优先（依据：resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md）
- Best Method selected: 固定窗口执行+完成后记录（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 周期清单+日历提醒+维护记录（依据：resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-home-maintenance-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-home-maintenance-toolchain-research.md`
- 最佳实践: 周期化和可视化优先
- 最佳方法: 固定窗口执行+完成后记录（Winner B=4.40, Margin=0.60）
- 最佳工具: 周期清单+日历提醒+维护记录
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 更新周期任务清单 | 关键任务覆盖完整 | 任务清单 |
| 2 | 安排本周执行窗口 | 每项任务有时间窗口 | 日历安排 |
| 3 | 按窗口执行任务 | 任务状态可更新 | 执行记录 |
| 4 | 记录异常和耗时 | 异常有原因标签 | 异常表 |
| 5 | 处理未完成任务 | 未完成项有重排计划 | 重排清单 |
| 6 | 周末复盘并优化清单 | 清单更新生效 | 复盘记录 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 窗口冲突 | 固定窗口被占用 | 切换到备选窗口 | 升级为次日优先任务 |
| 任务过重 | 单任务耗时超预算 | 拆分为子任务 | 升级到周计划调整 |
| 重复延期 | 同任务延期2次 | 下周优先级提升 | 升级到家庭协同SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键维护任务遗漏率 > 20%
- Stop condition 2: 执行窗口连续2周无效
- Blast radius limit: 家庭维护任务与日历
- Rollback action: 回退到基础周期清单

## SLA and Metrics
- Cycle time target: <= 30 分钟完成周维护计划
- First-pass yield target: >= 90 percent 周期任务按期启动
- Rework rate ceiling: <= 15 percent 任务需二次重排
- Adoption target: 100 percent 周期任务纳入清单
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-home-maintenance-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-home-maintenance-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-home-maintenance-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-home-maintenance-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-home-maintenance-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-home-maintenance-sop.overview.md

