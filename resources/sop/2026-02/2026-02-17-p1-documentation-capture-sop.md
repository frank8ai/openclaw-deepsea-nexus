# SOP Document

## Metadata
- SOP ID: SOP-20260217-17
- Name: 文档沉淀与知识归档
- Tags: p1, documentation, capture
- Primary triggers: 出现可复用结论或关键决策; 同类问题重复出现 >= 2 次
- Primary outputs: 结构化知识条目; 可检索标签和引用链接
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
- Best Practice compliance: 决策后快速沉淀并链接原始证据；依据：PRISMA 2020:https://www.bmj.com/content/372/bmj.n71；PRISMA-S:https://systematicreviewsjournal.biomedcentral.com/articles/10.1186/s13643-020-01542-z；NIST Information Quality:https://www.nist.gov/director/nist-information-quality-standards；研究记录：resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md。
- Best Method compliance: 模板化记录+标签索引+定期清理；依据：Winner B=4.40，Runner-up=3.80，Margin=0.60，硬约束=passed；研究记录：resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md。
- Best Tool compliance: 沉淀模板+标签规范+路径校验；依据：增益[沉淀模板:复用率提升 >=30%；标签规范:检索命中率提升 >=25%；路径校验脚本:失链率下降 >=30%]；回滚[沉淀模板->增加自由备注区；标签规范->标签白名单；路径校验脚本->发布前强制校验]；研究记录：resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md。
- Simplicity and maintainability check: workflow keeps minimum necessary steps and avoids tool/process bloat
- Closed-loop writeback check: each cycle writes back 1-3 rules with source links and review date
- Compliance reviewer: yizhi

## Objective
建立决策与知识沉淀流程，保证关键信息可追溯、可检索、可复用。

## Scope and Boundaries
- In scope: 决策记录、复盘结论、可复用工作流
- Out of scope: 临时草稿和一次性闲聊记录
- Dependencies: 文档模板、统一命名规则、标签规范

## Trigger Conditions (if/then)
- IF 出现可复用结论或关键决策
- THEN 在24小时内完成文档沉淀
- IF 同类问题重复出现 >= 2 次
- THEN 补充常见问题和标准做法条目

## Preconditions
- Precondition 1: 目标文档路径已确定
- Precondition 2: 相关证据或来源可访问

## Inputs
- Input 1: 决策结论与背景
- Input 2: 证据链接和执行结果

## Outputs
- Output 1: 结构化知识条目
- Output 2: 可检索标签和引用链接

## Three-Optimal Decision
- Best Practice selected: 决策后快速沉淀并链接原始证据（依据：resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md）
- Best Method selected: 模板化记录+标签索引+定期清理（依据：Winner B=4.40，Margin=0.60）
- Best Tool selected: 沉淀模板+标签规范+路径校验（依据：resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md）
- Scorecard reference: resources/sop/2026-02/2026-02-17-p1-documentation-capture-scorecard.md

## 三优原则研究与升级（Toolchain）
- 研究日期: 2026-02-17
- Search SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Web_Research.md`
- Research SOP工具: `${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}/SOP/SOP_HQ_Deep_Research.md`
- 外部证据包: `resources/sop/2026-02/2026-02-17-sop-toolchain-research-pack.md`
- 本SOP研究记录: `resources/sop/2026-02/research-toolchain/p1-documentation-capture-toolchain-research.md`
- 最佳实践: 决策后快速沉淀并链接原始证据
- 最佳方法: 模板化记录+标签索引+定期清理（Winner B=4.40, Margin=0.60）
- 最佳工具: 沉淀模板+标签规范+路径校验
- 本轮优化:
  - 依据外部权威来源 + 内部scorecard双证据确定三优结论。
  - 将三优结论回写到合规声明与执行段，避免只停留在描述层。
  - 保留工具回滚路径，确保工具服务于方法与结果。

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | 收集决策与证据来源 | 来源可追溯 | 来源清单 |
| 2 | 按模板填写问题、结论、证据、行动 | 模板关键字段完整 | 沉淀草稿 |
| 3 | 添加标签与关联链接 | 至少2个有效标签 | 标签记录 |
| 4 | 发布到统一目录 | 路径和命名符合规范 | 发布路径 |
| 5 | 加入检索索引 | 可通过关键词召回 | 检索结果 |
| 6 | 在周复盘中检查复用情况 | 复用次数可统计 | 复用统计 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 来源缺失 | 关键结论无证据链接 | 标记待补并暂不发布 | 升级至文档owner |
| 标签冲突 | 同一文档标签语义冲突 | 按标签白名单重标 | 升级到规范维护者 |
| 路径错误 | 链接404或引用失效 | 修复路径并重跑检查 | 升级到仓库维护 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| Non-negotiable breach (legal/safety/security/data integrity) | Stop execution immediately and block release | Revert to last approved SOP version and open incident record |
| Primary result metric degrades for 2 consecutive monthly cycles | Downgrade SOP status to `draft` and stop rollout | Restore previous stable SOP and rerun pilot >= 5 with strict validation |

## Rollback and Stop Conditions
- Stop condition 1: 核心条目证据缺失率 > 20%
- Stop condition 2: 检索命中率连续两周 < 70%
- Blast radius limit: 知识库条目和索引
- Rollback action: 回退到上一版本条目并重新标注

## SLA and Metrics
- Cycle time target: <= 30 分钟完成单条沉淀
- First-pass yield target: >= 90 percent 条目一次发布通过
- Rework rate ceiling: <= 15 percent 条目需要二次补写
- Adoption target: 100 percent 关键决策有沉淀记录
- Result metric (primary): first-pass yield target and adoption target are primary release and downgrade metrics.
- Process metric (secondary): cycle time target and rework rate ceiling are secondary diagnostic metrics.
- Replacement rule: process metrics cannot replace result metrics for release decisions.

## Logging and Evidence
- Log location: resources/sop/2026-02/2026-02-17-p1-documentation-capture-iteration-log.md
- Required record fields: run date, owner, trigger, gate result, cycle time, pass or fail, rework reason

## Change Control
- Rule updates this cycle (1-3 only):
1. IF 关键字段缺失或阈值未定义 -> 阻断执行并补齐字段
2. IF 任一硬门禁失败 -> 执行一次聚焦修正后再校验
3. IF rework连续2次超阈值 -> 收紧触发条件并简化步骤

## Release Readiness
- Validation command:
  - python3 scripts/validate_sop_factory.py --sop resources/sop/2026-02/2026-02-17-p1-documentation-capture-sop.md --strict
- Auto-downgrade gate: if monthly KPI trend shows primary result metric degradation for 2 consecutive cycles, set `Status: draft` and rerun pilot + strict validation.
- Release decision: approve
- Approver: yizhi
- Approval date: 2026-02-17

## Links
- Scorecard: resources/sop/2026-02/2026-02-17-p1-documentation-capture-scorecard.md
- Iteration log: resources/sop/2026-02/2026-02-17-p1-documentation-capture-iteration-log.md
- Related decision cards: resources/decisions/2026-02/2026-02-17-programming-learning-platform-task-clarification.md
- L0 abstract: resources/sop/2026-02/2026-02-17-p1-documentation-capture-sop.abstract.md
- L1 overview: resources/sop/2026-02/2026-02-17-p1-documentation-capture-sop.overview.md

