# SOP Document

## Metadata
- SOP ID: SOP-20260217-27
- Name: 旅行出差准备与执行
- Tags: p2, travel, readiness
- Primary triggers: 确认出行计划; 关键资料缺失或行程变更
- Primary outputs: 行前准备清单完成状态; 行中变更和应急记录
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
- Best Practice compliance: 关键资料和应急预案先于舒适性安排；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md。
- Best Method compliance: 分阶段清单准备+行中检查点；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md。
- Best Tool compliance: 行前清单+行程板+应急卡片；依据：增益[行前清单:漏项下降 >=30%；行程板:延误应对速度提升 >=25%；应急卡片:应急响应提升 >=20%]；回滚[行前清单->出行后复盘更新；行程板->单一来源维护；应急卡片->出发前复核]；研究记录：resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立旅行/出差准备与执行流程，减少临场风险并提升应急恢复能力。

## Scope and Boundaries
- In scope: 证件、行程、预算、应急准备与执行跟踪
- Out of scope: 长期签证策略与跨国税务规划
- Dependencies: 出行清单、行程信息、应急联系人

## Trigger Conditions (if/then)
- IF 确认出行计划
- THEN 执行旅行准备SOP
- IF 关键资料缺失或行程变更
- THEN 进入应急分支并重排

## Preconditions
- Precondition 1: 出行日期和目的地已确认
- Precondition 2: 至少有1个应急联系人

## Inputs
- Input 1: 行程与预算信息
- Input 2: 证件和预订状态

## Outputs
- Output 1: 行前准备清单完成状态
- Output 2: 行中变更和应急记录

## Three-Optimal Decision
- Best Practice selected: 关键资料和应急预案先于舒适性安排（依据：resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md）
- Best Method selected: 分阶段清单准备+行中检查点（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 行前清单+行程板+应急卡片（依据：resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-travel-readiness-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-travel-readiness-toolchain-research.md`
- 最佳实践: 关键资料和应急预案先于舒适性安排
- 最佳方法: 分阶段清单准备+行中检查点（Winner B=4.40, Margin=0.60）
- 最佳工具: 行前清单+行程板+应急卡片
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 确认证件和关键预订 | 证件和核心预订齐全 | 证件清单 |
| 2 | 完成行前清单打勾 | 关键项完成率100% | 清单记录 |
| 3 | 设置行程检查点和提醒 | 检查点可执行 | 提醒截图 |
| 4 | 准备应急联系人和替代路线 | 应急信息可访问 | 应急卡 |
| 5 | 行中记录变更并快速重排 | 变更有处置记录 | 变更日志 |
| 6 | 返程后复盘并更新清单 | 至少1条规则更新 | 复盘条目 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 证件问题 | 证件缺失或过期 | 立即切换到替代方案 | 升级到出行暂停决策 |
| 行程延误 | 关键节点延误 > 2小时 | 启动备选路线 | 升级到应急联系人联动 |
| 预算超支 | 实时支出超预算阈值 | 压缩非关键支出 | 升级到财务运行SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键证件不可用
- Stop condition 2: 应急联络链不可达
- Blast radius limit: 个人出行计划和预算
- Rollback action: 回退到保守行程方案

## SLA and Metrics
- Cycle time target: <= 60 分钟完成行前总检查
- First-pass yield target: >= 90 percent 出行关键清单首轮完成
- Rework rate ceiling: <= 15 percent 行程需二次重排
- Adoption target: 100 percent 出行计划使用本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-travel-readiness-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-travel-readiness-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-travel-readiness-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-travel-readiness-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-travel-readiness-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-travel-readiness-sop.overview.md

