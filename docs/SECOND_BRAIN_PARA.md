# Second Brain PARA (vNext)

目标：把 Deep-Sea Nexus 的结构化摘要、向量检索与 Obsidian PARA 体系结合，形成“可执行第二大脑”。

## 完成状态（基于历史提交与实测）
当前状态：`已完成开发并可用`（v4.4.0）。

关键提交：
- `4fa3290`：新增 PARA 二脑主流程（初始化、检索、Warm 写入、文档）
- `d3d095b`：新增 `para_validate.py` 与自动 Warm 写入钩子
- `0fc9417`：补充系统审计脚本与日志增强

验收结论：
- `run_tests.py` 可通过（含 brain unit/integration）。
- `para_init -> warm_writer -> para_validate -> para_recall` 链路可执行。

## OpenViking 风格对齐点
- 低常驻上下文：L0/L1/L2 分层，默认只用最短摘要参与上下文。
- 项目优先召回：目录递归检索按 Project 优先，减少跨项目噪声。
- 会话产出即资产：结构化摘要自动写 Warm/Overview，形成可执行状态卡。
- 可验证可回归：`para_validate.py` 提供 Warm/Blueprint 新鲜度检查。

## 目录结构（默认）
- `Obsidian/10_Projects/`
- `Obsidian/20_Knowledge/Areas/`
- `Obsidian/20_Knowledge/Resources/`
- `Obsidian/20_Knowledge/Archive/`
- `Obsidian/90_Memory/`

## L0/L1/L2 层级
- L0: `.abstract.md`（超短摘要）
- L1: `.overview.md`（项目概览）
- L2: `Warm.md` + `Blueprint.md`（完整可执行信息）

## 快速使用
### 1) 初始化 PARA
```bash
python scripts/para_init.py --obsidian ~/Obsidian
```

### 2) 自动写 Warm（从结构化摘要）
```bash
python scripts/warm_writer.py --from ~/.openclaw/logs/summaries/xxxx.json
```

### 3) 目录递归检索（项目优先）
```bash
python scripts/para_recall.py --query "故障转移系统" --top-projects 3
```

### 4) Warm 就绪验收（<=2 分钟重启）
```bash
python scripts/para_validate.py --project "YourProject" --max-age-minutes 120
```

## 自动接入（建议）
- `scripts/smart_context_digest.py`：生成 morning/progress/nightly 报告（只写报告，不危险动作）
- `scripts/flush_summaries.py`：自动存入向量库并按 project 更新 Warm 卡片
- `scripts/install_safe_cron.sh`：一键安装/移除推荐 cron

详见：`docs/SMART_CONTEXT_V4_4_0.md`

## 常见坑
- `warm_writer.py` 识别项目名优先使用 `project`/`project_name` 等字段；仅写 `project_association` 可能被归到 `Untitled`。
- `para_validate.py` 只检查目标项目目录（`10_Projects/<ProjectName>`），项目名需与 Warm 目标一致。

## 2026-02-23 增强（可运营 + 可演进）
- `warm_writer.py` 新增 `.memory_signal.json`（importance/priority/half-life），并自动晋升到 `20_Knowledge/Areas/<Project>.md`。
- `para_recall.py` 改为三维排序：`relevance + importance + recency`，支持可调权重与 score breakdown trace。
- `nexus_audit_contract.py` 增强：兼容 list/str/metadata 解析，输出 `new_contract vs legacy` 分组覆盖率。

详见 SOP：`docs/SOP_MEMORY_GAP_ITERATION_2026-02-23.md`
