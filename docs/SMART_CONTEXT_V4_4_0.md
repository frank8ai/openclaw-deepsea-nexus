# Smart Context / vNext Brain 升级方案（v4.4.0）

> Archived reference: this is a v4.4.0 upgrade plan, not the current runtime source of truth.
> Current docs:
> - `sop/Context_Policy_v2_EventDriven.md`
> - `LOCAL_DEPLOY.md`
> - `ARCHITECTURE_CURRENT.md`
> - `API_CURRENT.md`

## 目标
- 始终带着正确背景工作：目标/偏好/项目/安全边界不丢。
- 长任务沉淀为可复用资产：Pack/Card/SOP/Prompt。
- 控制 token：默认只加载当日索引 + 当前 session slice。
- 工程可运营：可观测、可评测、可灰度、可回滚。

## 固定目录
- Root index: `MEMORY.md`（导航，<500 tokens）
- Daily shard: `90_Memory/YYYY-MM-DD/_DAILY_INDEX.md`
- Session slice: `90_Memory/YYYY-MM-DD/session_HHMM_<Topic>.md`
- Long-term: `Obsidian/10_Projects/`, `Obsidian/20_Knowledge/`
- Code snippets: `Obsidian/00_Inbox/Code_Snippet.md`
- Deep research artifacts:
  - Pack: `SOP/research/YYYY-MM-DD/<topic>-deep-research-pack.md`
  - Card: `90_Memory/YYYY-MM-DD/<topic>-deep-research-card.md`

## 每次对话工作流
1. 开始：仅加载 `_DAILY_INDEX.md` + 当前 session slice。
2. 过程中：关键决策/事实立即写 `#GOLD`。
3. 结束：必须输出两段式
   - `## 📋 总结`（3-5 条）
   - 结构化 JSON v3.1（固定字段）
4. 话题切换或接近满载：执行 `SAVE_AND_FLUSH`
   - 写暂停点
   - `_DAILY_INDEX.md` 标记 `#PAUSED`
   - 下轮按需恢复

## 结构化摘要 v3.1 字段
- 本次核心产出
- 技术要点（3-5）
- 代码模式
- 决策上下文
- 避坑记录
- 适用场景
- 搜索关键词
- 项目关联（可选）
- 置信度

模板：`resources/sop/TEMPLATE.structured-summary-v3.1.json`

## 自动触发
- 话题切换
- 每 50 条消息
- 上下文 > 4000 tokens 前
- 出现 `#GOLD`
- 用户说“记住/保存这个”

## 记忆优先级
- `#GOLD`: 永久
- `#P0`: 身份/安全/偏好
- `#P1`: 项目决策
- `#P2`: 临时调试

## 4.4.0 实装能力
- Pack/Card 模板：
  - `resources/sop/TEMPLATE.deep-research-pack.md`
  - `resources/sop/TEMPLATE.deep-research-card.md`
- 字段检查脚本：
  - `scripts/validate_research_artifacts.py`
- Digest 报告脚本（仅报告，不危险动作）：
  - `scripts/smart_context_digest.py`
- 安全 cron 安装脚本：
  - `scripts/install_safe_cron.sh`
- 指标统一 schema（`schema_version=4.4.0`）：
  - `smart_context` / `context_engine` / `nexus_core`

## 直接执行命令
### 1) 复制模板并开始研究
```bash
cp resources/sop/TEMPLATE.deep-research-pack.md SOP/research/$(date +%F)/<topic>-deep-research-pack.md
cp resources/sop/TEMPLATE.deep-research-card.md 90_Memory/$(date +%F)/<topic>-deep-research-card.md
```

### 2) 检查 Pack/Card 是否完整
```bash
python3 scripts/validate_research_artifacts.py \
  --pack SOP/research/$(date +%F)/<topic>-deep-research-pack.md \
  --card 90_Memory/$(date +%F)/<topic>-deep-research-card.md \
  --strict
```

### 3) 生成 digest 报告
```bash
python3 scripts/smart_context_digest.py --mode morning
python3 scripts/smart_context_digest.py --mode progress
python3 scripts/smart_context_digest.py --mode nightly
```

### 4) 安装/移除安全 cron
```bash
bash scripts/install_safe_cron.sh --install
bash scripts/install_safe_cron.sh --remove
```

## KPI 与停止条件
- hit@5 >= 0.82
- 空检索率 <= 3%
- 注入噪声 <= 20%
- 超预算率 <= 2%
- p95 时延 <= 基线 +20%
- 触发停止：任一核心 KPI 连续 2 窗下降 >5%，或空检索率 24h >5%
