# SOP Document

## Metadata
- SOP ID: SOP-20260217-26
- Name: 个人系统季度迭代
- Tags: p2, quarterly, system, refactor
- Primary triggers: 进入季度重构窗口; 关键健康指标连续2周恶化
- Primary outputs: 季度重构计划; 分批实施记录和验证结果
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
- Best Practice compliance: 先体检后改造，先可逆后不可逆；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md。
- Best Method compliance: 季度审计+分批重构+每批验证；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md。
- Best Tool compliance: 审计清单+分批计划+回归检查表；依据：增益[系统审计清单:问题发现率提升 >=30%；分批发布计划:回归事故下降 >=25%；回归检查表:漏测下降 >=20%]；回滚[系统审计清单->指标分层；分批发布计划->每批限范围；回归检查表->核心项优先]；研究记录：resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
按季度执行系统体检和重构，降低技术债并保持生产稳定。

## Scope and Boundaries
- In scope: 架构审计、模块重构、性能与可维护性优化
- Out of scope: 全量重写和不可逆迁移
- Dependencies: 监控指标、回归测试、发布窗口

## Trigger Conditions (if/then)
- IF 进入季度重构窗口
- THEN 执行季度系统迭代SOP
- IF 关键健康指标连续2周恶化
- THEN 提前触发专项重构评估

## Preconditions
- Precondition 1: 当前系统指标可获取
- Precondition 2: 有可用的回归验证路径

## Inputs
- Input 1: 系统健康指标与技术债列表
- Input 2: 资源预算和发布窗口

## Outputs
- Output 1: 季度重构计划
- Output 2: 分批实施记录和验证结果

## Three-Optimal Decision
- Best Practice selected: 先体检后改造，先可逆后不可逆（依据：resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md）
- Best Method selected: 季度审计+分批重构+每批验证（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 审计清单+分批计划+回归检查表（依据：resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p2-quarterly-system-refactor-toolchain-research.md`
- 最佳实践: 先体检后改造，先可逆后不可逆
- 最佳方法: 季度审计+分批重构+每批验证（Winner B=4.40, Margin=0.60）
- 最佳工具: 审计清单+分批计划+回归检查表
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集系统健康与债务指标 | 指标覆盖核心模块 | 健康报表 |
| 2 | 确定Top重构目标 | 目标与指标绑定 | 目标列表 |
| 3 | 拆分分批重构计划 | 每批可独立回滚 | 分批计划 |
| 4 | 执行一批并回归验证 | 回归通过 | 验证报告 |
| 5 | 灰度发布并观测 | 关键指标无异常 | 观测数据 |
| 6 | 季度复盘与下季输入 | 形成1-3条改进规则 | 季度复盘 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 回归失败 | 核心测试失败 | 停止发布并回滚 | 升级到质量门禁SOP |
| 指标恶化 | 性能下降超阈值 | 暂停后续批次并排查 | 升级到异常响应SOP |
| 范围失控 | 重构范围超出计划 | 冻结新增需求 | 升级到项目owner |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键批次不可回滚
- Stop condition 2: 灰度阶段异常率 > 10%
- Blast radius limit: 系统模块和发布节奏
- Rollback action: 回退到上个稳定版本

## SLA and Metrics
- Cycle time target: <= 5 个工作日完成单批重构
- First-pass yield target: >= 90 percent 批次首轮回归通过
- Rework rate ceiling: <= 15 percent 批次需二次修复
- Adoption target: 100 percent 季度窗口执行本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-weekly-daily-plan.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p2-quarterly-system-refactor-sop.overview.md

