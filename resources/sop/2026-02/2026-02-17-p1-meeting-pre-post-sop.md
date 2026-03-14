# SOP Document

## Metadata
- SOP ID: SOP-20260217-16
- Name: 会议准备与行动闭环
- Tags: p1, meeting, pre, post
- Primary triggers: 会议时长 >= 20 分钟或参会人 >= 3; 连续2次会议行动项完成率 < 80%
- Primary outputs: 会议纪要与决策结论; 行动项清单（责任人、截止时间）
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
- Best Practice compliance: 会前目标清晰、会中聚焦议程、会后行动闭环；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md。
- Best Method compliance: 三段式流程（会前准备、会中推进、会后追踪）；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md。
- Best Tool compliance: 议程模板+计时器+行动项看板；依据：增益[会议议程模板:议程偏移下降 >=30%；计时器:超时率下降 >=25%；行动项看板:完成率提升 >=30%]；回滚[会议议程模板->固定最小模板；计时器->关键议题延时机制；行动项看板->每日收盘更新]；研究记录：resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立可执行会议流程，确保每次会议都产生可追踪行动项和明确责任。

## Scope and Boundaries
- In scope: 周例会、项目会、跨职能协调会
- Out of scope: 纯信息广播型通知
- Dependencies: 参会人清单、议程模板、行动项看板

## Trigger Conditions (if/then)
- IF 会议时长 >= 20 分钟或参会人 >= 3
- THEN 启用会议SOP并提前产出会前目标与议程
- IF 连续2次会议行动项完成率 < 80%
- THEN 立即升级为强制会后行动项审查模式

## Preconditions
- Precondition 1: 会议目标和主持人已确定
- Precondition 2: 会后责任人可在24小时内确认行动项

## Inputs
- Input 1: 会议主题与背景
- Input 2: 参会人列表与时间窗口

## Outputs
- Output 1: 会议纪要与决策结论
- Output 2: 行动项清单（责任人、截止时间）

## Three-Optimal Decision
- Best Practice selected: 会前目标清晰、会中聚焦议程、会后行动闭环（依据：resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md）
- Best Method selected: 三段式流程（会前准备、会中推进、会后追踪）（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 议程模板+计时器+行动项看板（依据：resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-meeting-pre-post-toolchain-research.md`
- 最佳实践: 会前目标清晰、会中聚焦议程、会后行动闭环
- 最佳方法: 三段式流程（会前准备、会中推进、会后追踪）（Winner B=4.40, Margin=0.60）
- 最佳工具: 议程模板+计时器+行动项看板
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 会前24小时明确会议目标与期望输出 | 目标和输出为可验证条目 | 会前议程 |
| 2 | 会前分发议程并收集补充议题 | 关键议题在会前已确认 | 议题列表 |
| 3 | 会中按议程推进并控制时间 | 每个议题有结论或待办 | 会议记录 |
| 4 | 会中实时标记行动项责任人与截止时间 | 行动项字段完整 | 行动项表 |
| 5 | 会后24小时发布纪要和行动项 | 纪要已发送且可访问 | 纪要链接 |
| 6 | 跟踪行动项并在下次会议复核 | 行动项完成率达到阈值 | 完成率报表 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 议程冲突 | 会中临时新增高优先事项 | 压缩低优先议题并记录延期 | 升级到主持人决策 |
| 行动项无人认领 | 会后2小时仍无责任人 | 主持人指定并确认 | 升级到项目owner |
| 会议超时 | 超时>20% | 拆分后续专题会 | 升级到周计划SOP |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 连续2次会议无可执行行动项
- Stop condition 2: 行动项完成率连续2周 < 60%
- Blast radius limit: 会议文档、任务状态
- Rollback action: 退回最小议程模式并重训主持流程

## SLA and Metrics
- Cycle time target: <= 20 分钟会前准备
- First-pass yield target: >= 90 percent 会议首轮达成明确结论
- Rework rate ceiling: <= 15 percent 行动项需二次澄清
- Adoption target: 100 percent 关键会议使用本SOP
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-meeting-pre-post-sop.overview.md

