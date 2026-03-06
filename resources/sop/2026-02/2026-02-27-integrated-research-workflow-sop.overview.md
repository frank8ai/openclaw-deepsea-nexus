# L1 Overview: Integrated Research Workflow v2.0

## Default
- Default mode: **Fast Mode**
- Upgrade triggers: 出现“决策/对外/钱/安全”任一关键词，或你主观判断风险升高 -> 强制切 **Deep Mode**

## Purpose
将研究工具栈与治理门禁整合为统一流程，保证“快”与“稳”并存。

## Modes
- **Fast Mode**: 快速概览，主用 `web_search` + `browser` 抽样核验。
- **Deep Mode**: 系统研究，主用 `codex-deep-search` + `browser` + 本地核验。
- **X-Signals Mode**: 最新动态信号，主用 `x-tweet-fetcher`，强制二跳核验。

## Routing Rules
- IF 需要时效/破圈线索 -> X-Signals Mode
- IF 需要快速概览 -> Fast Mode
- IF 需要决策级证据 -> Deep Mode

## Evidence Rules
- X 信号仅作线索，必须二跳核验才可进入 Key Claims。
- 关键结论必须有可点击证据链接。
- 输出必须包含反例/争议点。

## Output Skeleton
1) TL;DR
2) Key Claims (with evidence)
3) Counterpoints / Unknowns
4) Repro Steps (queries, filters)
5) Next Actions

## SLA
- Fast <= 10min
- Deep <= 60min
