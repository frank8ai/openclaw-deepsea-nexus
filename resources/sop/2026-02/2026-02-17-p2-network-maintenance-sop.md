# SOP Document

## Metadata
- SOP ID: SOP-20260217-28
- Name: 人脉维护与周期触达
- Tags: p2, network, maintenance
- Primary triggers: 关键联系人数量 >= 10; 关键联系人连续30天未触达
- Primary outputs: 本周期触达计划; 触达记录和下一步行动
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
- Best Practice compliance: 先关键后泛化，触达后必须记录；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md。
- Best Method compliance: 分层名单+周期触达+复盘；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md。
- Best Tool compliance: 分层清单+节奏表+触达记录卡；依据：增益[关系分层清单:触达命中率提升 >=30%；触达节奏表:漏触达率下降 >=25%；触达记录卡:跟进质量提升 >=20%]；回滚[关系分层清单->季度复核分层；触达节奏表->允许弹性窗口；触达记录卡->最小字段记录]；研究记录：resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立人脉维护的周期触达机制，提升关键关系的稳定性和跟进质量。

## Scope and Boundaries
- In scope: 关键联系人分层、触达计划、触达后记录
- Out of scope: 泛社交扩列活动
- Dependencies: 联系人清单、触达渠道、记录模板

## Trigger Conditions (if/then)
- IF 关键联系人数量 >= 10
- THEN 执行人脉维护SOP
- IF 关键联系人连续30天未触达
- THEN 触发补触达计划

## Preconditions
- Precondition 1: 联系人分层已定义
- Precondition 2: 触达渠道可用

## Inputs
- Input 1: 联系人名单和分层
- Input 2: 可用触达时间窗口

## Outputs
- Output 1: 本周期触达计划
- Output 2: 触达记录和下一步行动

## Three-Optimal Decision
- Best Practice selected: 先关键后泛化，触达后必须记录（依据：resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md）
- Best Method selected: 分层名单+周期触达+复盘（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 分层清单+节奏表+触达记录卡（依据：resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-network-maintenance-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-network-maintenance-toolchain-research.md`
- 最佳实践: 先关键后泛化，触达后必须记录
- 最佳方法: 分层名单+周期触达+复盘（Winner B=4.40, Margin=0.60）
- 最佳工具: 分层清单+节奏表+触达记录卡
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 更新联系人分层 | 关键层名单准确 | 分层清单 |
| 2 | 生成本周触达计划 | 每位关键联系人有时间点 | 触达计划 |
| 3 | 执行触达并记录反馈 | 反馈有要点 | 触达记录 |
| 4 | 识别需跟进事项 | 跟进项有截止时间 | 跟进列表 |
| 5 | 执行跟进并更新状态 | 跟进完成可验证 | 完成记录 |
| 6 | 周期复盘调整分层与频率 | 形成1-3条规则更新 | 复盘记录 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 触达无回应 | 两次触达无反馈 | 切换渠道并降低频率 | 升级为低优先层 |
| 跟进堆积 | 未完成跟进 > 5项 | 清理低价值项 | 升级周计划重排 |
| 记录缺失 | 触达后无记录 | 24小时内补录 | 升级到流程重训 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键层触达完成率 < 70%
- Stop condition 2: 触达记录完整率 < 80%
- Blast radius limit: 联系人记录和触达计划
- Rollback action: 回退到最小关键层触达计划

## SLA and Metrics
- Cycle time target: <= 40 分钟完成周期触达计划
- First-pass yield target: >= 90 percent 关键触达按计划完成
- Rework rate ceiling: <= 15 percent 触达需二次跟进改写
- Adoption target: 100 percent 关键联系人纳入周期管理
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-network-maintenance-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-network-maintenance-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-network-maintenance-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-network-maintenance-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-network-maintenance-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-network-maintenance-sop.overview.md

