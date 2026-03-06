# SOP Document

## Metadata
- SOP ID: SOP-20260227-01
- Name: Integrated Research Workflow v2.0
- Tags: research, web-search, deep-search, x-signals, governance
- Primary triggers: 用户提出研究需求、需要外部证据、需要核验断言、需要跟踪最新动态、或高频研究任务需要标准化
- Primary outputs: 结构化研究报告（TL;DR + 证据项 + 反例 + 路径）、证据包、或新的专用 SOP 路由
- Owner: yizhi
- Team: deepsea-nexus
- Version: v2.0
- Status: draft (pending 5 pilot runs)
- Risk tier: medium
- Reversibility class: R1 (Information only)
- Evidence tier at release: E2 (Target E3 after pilot)
- Effective condition: Workspace has research skill stack and deepsea-nexus governance tools.
- Review cycle: Monthly
- Retirement condition: 核心工具（如深搜/X工具）失效，或研究成功率连续两月低于 80%
- Created on: 2026-02-27
- Last reviewed on: 2026-02-27

## Hard Gates (must pass before activation)
- [x] Non-negotiables (legal/safety/security/data integrity) are explicitly checked.
- [x] Objective is explicit and measurable.
- [x] Outcome metric includes baseline and target delta.
- [x] Trigger conditions are testable (`if/then` with threshold or signal).
- [x] Inputs and outputs are defined.
- [x] Reversibility class and blast radius are declared.
- [x] Quality gates exist for critical steps.
- [x] Exception and rollback paths are defined.
- [x] SLA and metrics are numeric.

## Principle Compliance Declaration
- Non-negotiables check: 禁止采集私有敏感数据，所有 X 信号必须经过二跳核验。
- Outcome metric and baseline: 目标是将研究“结论-证据”匹配率从 70% 提升至 >= 90%。
- Reversibility and blast radius: R1 (仅信息输出)，影响范围限于研究报告。
- Evidence tier justification: 基于 skill stack 的工具集成，初始设定为 E2。
- Best Practice compliance: 路由式研究 + 证据强度分级。
- Best Method compliance: 三段闭环（Fast/Deep/Writeback）。
- Best Tool compliance: 集成 web_search, deep_search, browser, x-tweet-fetcher。
- Simplicity and maintainability check: 统一路由表，避免工具堆砌。
- Closed-loop writeback check: 每次任务强制记录迭代日志。
- Compliance reviewer: yizhi

## Objective
集成高效工具链（Skill Stack）与严谨治理（SOP Factory），建立一套“快慢结合、证据可靠、可持续复利”的研究生产线。

## Scope and Boundaries
- In scope: 资讯采集、深度调研、X/Twitter 信号发现、多源交叉验证、研究报告生成。
- Out of scope: 商业机密情报窃取、大规模爬虫、非公开数据库爆破。
- Dependencies: `web_search`, `codex-deep-search`, `browser`, `x-tweet-fetcher`.

## Trigger Conditions (if/then)
- IF 需要快速概览/时效信息 -> THEN 路由至 **Fast Mode** (`web_search`).
- IF 需要深度、系统性、高可信度报告 -> THEN 路由至 **Deep Mode** (`codex-deep-search`).
- IF 需要跟踪突发、项目动态、社区风向 -> THEN 路由至 **X-Signals Mode** (`x-tweet-fetcher`).
- IF 涉及投资/安全/公开发布等高风险决策 -> THEN 强制升级至 **Deep Mode** 并补齐二跳核验。

## Preconditions
- Precondition 1: `codex-deep-search` 环境可用。
- Precondition 2: `x-tweet-fetcher` 无需 Key 即可正常拉取。

## Inputs
- Input 1: 研究目标/Query。
- Input 2: 期望证据层级 (E1-E3)。

## Outputs
- Output 1: 2.0 版结构化报告（TL;DR + 证据 + 反例 + Repro）。
- Output 2: 迭代日志条目（用于 SOP Factory）。

## Three-Optimal Decision
- Best Practice selected: 路由式研究路由 + 二跳核验门禁。
- Best Method selected: 混合深度搜索 + X实时信号 + 自动化浏览器核验。
- Best Tool selected: `codex-deep-search` (核心), `x-tweet-fetcher` (信号), `browser` (核验)。
- Scorecard reference: `2026-02-27-integrated-research-workflow-scorecard.md`

## Procedure
| Step | Action | Quality Gate | Evidence |
|---|---|---|---|
| 1 | **需求分类与路由** | 明确 Fast/Deep/X 模式 | 路由标注 |
| 2 | **执行检索/采集** | 信号/数据覆盖目标 Query | 原始日志/推文列表 |
| 3 | **二跳核验 (X/Fast)** | 所有关键断言带官方/多源链接 | 链接列表 |
| 4 | **交叉验证 (Deep)** | 至少 3 个独立来源或 1 个权威来源 | 交叉引用标记 |
| 5 | **综合输出** | 包含 TL;DR 和反例(Counterpoints) | 最终报告 |
| 6 | **闭环记录** | 填写 iteration-log 并更新规则 (1-3条) | 迭代日志 |

## Exceptions
| Scenario | Detection Signal | Response | Escalation |
|---|---|---|---|
| 工具失效 | 命令返回错误或 0 结果 | 降级路由（如 Deep -> Web + Browser） | 记录工具故障日志 |
| X 信号断言无法核验 | 找不到二跳证据 | 标注为“传言/未经证实”或剔除 | 标注高不确定性 |

## Kill Switch
| Trigger threshold | Immediate stop | Rollback action |
|---|---|---|
| 发现采集到敏感/隐私数据 | 立即停止并删除本地副本 | 清理缓存，撤回未发送的报告 |
| 核心工具连续 3 次无响应 | 停止当前任务，切换回手动模式 | 开启系统健康自检 |

## Rollback and Stop Conditions
- Stop condition 1: 达到证据层级目标（如 E3）。
- Stop condition 2: 搜索深度达到 5 层且无新线索。
- Blast radius limit: 仅限研究产出物，不修改生产系统。
- Rollback action: 撤回错误结论，更新 SOP 迭代日志。

## SLA and Metrics
- Cycle time target: Fast <= 10min; Deep <= 60min.
- First-pass yield target: >= 85% (初次产出即满足决策需求)。
- Rework rate ceiling: <= 15%.
- Adoption target: 100% 研究任务进入本 SOP。
- Result metric (primary): 证据项的可点击率和准确率。

## Logging and Evidence
- Log location: `2026-02-27-integrated-research-workflow-iteration-log.md`
- Required record fields: Query, Mode, ToolChain, EvidenceCount, VerificationStatus.

## Change Control
- Rule updates this cycle (1-3 only):
1. 所有 X 推文作为信号，必须强制经过 browser/web_search 二跳核验才能入选 Key Claims。
2. 决策类研究必须包含“反例/争议点”段落。
3. 如果 `codex-deep-search` 耗时超过 45min，强制在 30min 时产出 interim 报告。

## Release Readiness
- Validation command:
  - `python3 scripts/validate_sop_factory.py --sop skills/deepsea-nexus/resources/sop/2026-02/2026-02-27-integrated-research-workflow-sop.md --strict`
- Auto-downgrade gate: 如果月度准确率 < 80%，状态降为 draft。
- Release decision: draft
- Approver: yizhi
- Approval date: 2026-02-27

## Links
- Scorecard: `2026-02-27-integrated-research-workflow-scorecard.md`
- Iteration log: `2026-02-27-integrated-research-workflow-iteration-log.md`
- L0 abstract: `2026-02-27-integrated-research-workflow-sop.abstract.md`
- L1 overview: `2026-02-27-integrated-research-workflow-sop.overview.md`
