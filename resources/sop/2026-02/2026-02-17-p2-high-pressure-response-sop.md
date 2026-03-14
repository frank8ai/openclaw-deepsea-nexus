# SOP Document

## Metadata
- SOP ID: SOP-20260217-29
- Name: 高压事件处置与恢复
- Tags: p2, high, pressure, response
- Primary triggers: 出现高压事件信号或重大异常; 事件影响扩散到多个关键链路
- Primary outputs: 处置结论和沟通记录; 恢复验证报告和复盘规则
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
- Best Practice compliance: 先止损再沟通再恢复；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md。
- Best Method compliance: 分级处置+模板沟通+检查清单恢复；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md。
- Best Tool compliance: 分级表+沟通模板+恢复清单；依据：增益[事件分级表:分级正确率提升 >=25%；危机沟通模板:信息偏差下降 >=30%；恢复检查清单:恢复时间下降 >=20%]；回滚[事件分级表->允许人工override；危机沟通模板->现场补充说明；恢复检查清单->关键项优先]；研究记录：resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立高压事件的标准处置流程，确保快速止损、清晰沟通和可验证恢复。

## Scope and Boundaries
- In scope: 突发高压事件、危机沟通、恢复与复盘
- Out of scope: 长期战略重构讨论
- Dependencies: 事件分级规则、沟通模板、恢复清单

## Trigger Conditions (if/then)
- IF 出现高压事件信号或重大异常
- THEN 立即启动高压事件SOP
- IF 事件影响扩散到多个关键链路
- THEN 升级分级并进入应急沟通模式

## Preconditions
- Precondition 1: 应急联系人链可达
- Precondition 2: 恢复验证路径已定义

## Inputs
- Input 1: 事件信号和影响范围
- Input 2: 当前系统状态和沟通对象

## Outputs
- Output 1: 处置结论和沟通记录
- Output 2: 恢复验证报告和复盘规则

## Three-Optimal Decision
- Best Practice selected: 先止损再沟通再恢复（依据：resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md）
- Best Method selected: 分级处置+模板沟通+检查清单恢复（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 分级表+沟通模板+恢复清单（依据：resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-high-pressure-response-toolchain-research.md`
- 最佳实践: 先止损再沟通再恢复
- 最佳方法: 分级处置+模板沟通+检查清单恢复（Winner B=4.40, Margin=0.60）
- 最佳工具: 分级表+沟通模板+恢复清单
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 接收事件并快速分级 | 10分钟内完成分级 | 分级记录 |
| 2 | 执行止损动作 | 扩散趋势被抑制 | 止损日志 |
| 3 | 对内外发布同步信息 | 关键信息一致 | 沟通记录 |
| 4 | 执行恢复动作并验证 | 核心链路恢复 | 恢复报告 |
| 5 | 持续监控直到稳定 | 关键指标回到阈值 | 监控曲线 |
| 6 | 24小时内复盘并回写规则 | 1-3条规则更新 | 复盘结论 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 分级不清 | 分级争议超过1轮 | 按最高风险临时分级 | 升级到事件owner裁决 |
| 沟通失真 | 外部信息与内部不一致 | 统一口径并重新同步 | 升级沟通负责人 |
| 恢复不稳定 | 恢复后30分钟再次告警 | 回滚到稳定版本 | 升级异常响应SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键链路未恢复
- Stop condition 2: 沟通口径持续冲突
- Blast radius limit: 事件处置、沟通和恢复流程
- Rollback action: 回退到上个稳定状态并重启分级

## SLA and Metrics
- Cycle time target: <= 30 分钟完成首轮止损和同步
- First-pass yield target: >= 90 percent 高压事件首轮分级正确
- Rework rate ceiling: <= 15 percent 处置需二次分级
- Adoption target: 100 percent 高压事件执行本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-high-pressure-response-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-high-pressure-response-sop.overview.md

