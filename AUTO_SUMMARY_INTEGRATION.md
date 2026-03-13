# 自动摘要集成方案

> Archived reference: this note describes an older integration gap and is not
> the current source of truth for the v5 runtime.
> Current docs:
> - `docs/README.md`
> - `docs/ARCHITECTURE_CURRENT.md`
> - `docs/API_CURRENT.md`
> - `docs/LOCAL_DEPLOY.md`

## 问题
OpenClaw 没有自动调用 skill hooks 来保存对话摘要。

## 解决方案

### 方案1: Cron Job 定时保存（推荐）

配置 cron job 定期保存摘要：

```bash
# 每小时保存一次摘要摘要
0 * * * * cd ~/workspace/skills/deepsea-nexus && ./save_summary.sh "cron自动保存"
```

可选：同时写入 PARA Warm（有项目关联时）
```bash
0 * * * * cd ~/workspace/skills/deepsea-nexus && python scripts/flush_summaries.py
```

### 方案2: 手动命令

每次对话后手动保存：
```bash
cd ~/workspace/skills/deepsea-nexus
./save_summary.sh "对话摘要内容"
```

### 方案3: OpenClaw Hook 集成（需修改 OpenClaw）

在 OpenClaw 源码中添加：
```python
from deepsea_nexus import DeepSeaNexus

# 回复后调用
nexus = DeepSeaNexus()
nexus.auto_summary(response)
```

## 当前状态
- ✅ 恢复向量库: 2213 条
- ✅ 保存命令: save_summary.sh
- ❌ 自动集成: 未配置
- ⚠️ 需要: OpenClaw 钩子调用
