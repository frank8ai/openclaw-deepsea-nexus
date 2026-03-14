# SOP Document

## Metadata
- SOP ID: SOP-20260217-23
- Name: 数字安全与备份权限管理
- Tags: p1, digital, security
- Primary triggers: 存在关键数据或多账号系统; 检测到异常登录或权限漂移
- Primary outputs: 安全检查报告; 整改任务与完成记录
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
- Best Practice compliance: 最小权限和可恢复性优先；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md。
- Best Method compliance: 固定周期检查+异常即时处理；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md。
- Best Tool compliance: 备份计划+权限审计清单+密码管理器；依据：增益[备份任务计划:数据丢失风险下降 >=30%；权限审计清单:过权风险下降 >=25%；密码管理器:弱口令风险下降 >=30%]；回滚[备份任务计划->月度恢复演练；权限审计清单->双人复核；密码管理器->应急恢复方案]；研究记录：resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立数字安全例行流程，保障备份可恢复、权限最小化、凭证可管理。

## Scope and Boundaries
- In scope: 账户密码、数据备份、权限审计
- Out of scope: 企业级SOC或渗透测试
- Dependencies: 备份方案、权限清单、密码管理工具

## Trigger Conditions (if/then)
- IF 存在关键数据或多账号系统
- THEN 执行数字安全SOP
- IF 检测到异常登录或权限漂移
- THEN 立即进入安全应急分支

## Preconditions
- Precondition 1: 关键资产清单已建立
- Precondition 2: 备份目标和恢复路径可访问

## Inputs
- Input 1: 资产与账号清单
- Input 2: 当前备份和权限状态

## Outputs
- Output 1: 安全检查报告
- Output 2: 整改任务与完成记录

## Three-Optimal Decision
- Best Practice selected: 最小权限和可恢复性优先（依据：resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md）
- Best Method selected: 固定周期检查+异常即时处理（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 备份计划+权限审计清单+密码管理器（依据：resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-digital-security-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-digital-security-toolchain-research.md`
- 最佳实践: 最小权限和可恢复性优先
- 最佳方法: 固定周期检查+异常即时处理（Winner B=4.40, Margin=0.60）
- 最佳工具: 备份计划+权限审计清单+密码管理器
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 盘点关键数据和账户 | 资产清单完整 | 资产清单 |
| 2 | 执行备份并验证完整性 | 备份可恢复 | 备份验证 |
| 3 | 审计权限与共享设置 | 高风险权限为0 | 权限报告 |
| 4 | 检查密码强度与复用 | 弱口令清零 | 密码报告 |
| 5 | 处理异常项并复核 | 整改项全部关闭 | 整改清单 |
| 6 | 输出本周期安全状态和下周期计划 | 计划可执行 | 安全周报 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 备份失败 | 备份任务报错或校验失败 | 立即重跑并切换备份路径 | 升级到应急恢复流程 |
| 权限异常 | 发现不应有的高权限 | 立即回收并记录 | 升级到owner审计 |
| 异常登录 | 新设备或异地登录警报 | 强制改密和会话失效 | 升级到安全事件响应 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 关键资产未备份
- Stop condition 2: 高风险权限未在24小时内回收
- Blast radius limit: 账户权限和备份任务
- Rollback action: 回退到上一个已验证安全配置

## SLA and Metrics
- Cycle time target: <= 45 分钟完成周期安全检查
- First-pass yield target: >= 90 percent 安全检查首轮通过
- Rework rate ceiling: <= 15 percent 整改需二次处理
- Adoption target: 100 percent 关键资产纳入安全流程
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-digital-security-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-digital-security-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-digital-security-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-digital-security-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-digital-security-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-digital-security-sop.overview.md

