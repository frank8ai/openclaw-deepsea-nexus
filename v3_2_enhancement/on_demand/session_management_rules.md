# Session Management Rules - 会话管理详细规则 (F1)
# 按需层 - 管理 Session 生命周期时加载

## 概述

Session 管理是 Deep-Sea Nexus 的核心功能之一，负责：
- 创建和追踪会话
- 管理会话状态流转
- 控制并发数量
- 自动归档不活跃会话

## Session 生命周期

```
Start Session → Active → Close → Archive → Cleanup
     ↓              ↓        ↓         ↓        ↓
   创建文件      更新活跃   标记关闭   移动归档   清理旧档
```

## API 使用

### SessionManager

```python
from session_manager import SessionManager

manager = SessionManager()

# 创建会话
session_id = manager.start_session("Python 学习")

# 获取会话信息
info = manager.get_session(session_id)
print(f"主题: {info.topic}")
print(f"创建时间: {info.created_at}")

# 更新活跃状态
manager.update_activity(session_id)

# 列出活跃会话
for s in manager.list_active_sessions():
    print(f"- {s.session_id}: {s.topic}")

# 关闭会话
manager.close_session(session_id)

# 统计
print(manager.get_stats())
```

## 配置参数

```yaml
F1_Session:
  auto_archive_days: 30    # 30天不活跃自动归档
  max_concurrent: 10       # 最大并发会话数
  retention_days: 90      # 归档保留90天
  
  naming_convention:
    format: "session_{HHMM}_{Topic}.md"
    example: "session_0900_Python.md"
```

## 文件命名规范

| 时间 | 主题 | 示例 |
|------|------|------|
| 09:00 | Python | `session_0900_Python.md` |
| 14:30 | Meme Audit | `session_1430_MemeAudit.md` |
| 20:00 | System | `session_2000_System.md` |

## Session 状态

| 状态 | 说明 | 操作 |
|------|------|------|
| active | 活跃中 | 正常操作 |
| paused | 暂停 | 用户切换话题 |
| closed | 已关闭 | 等待归档 |
| archived | 已归档 | 只读 |

## 工作流程

### Phase A: Boot (Start of Turn)
1. 读取 `_DAILY_INDEX.md`
2. 分析用户意图：恢复/新建/切换
3. 加载对应 Session 文件

### Phase B: Execution
- 执行当前任务
- 遇到 #GOLD 立即更新 Index
- 大段代码外部化存储

### Phase C: Context Flush
- 总结当前状态
- 更新 Index
- 清理上下文

## CLI 命令

```bash
# 创建新会话
REPO_ROOT="${DEEPSEA_NEXUS_ROOT:-${OPENCLAW_HOME:-$HOME/.openclaw}/skills/deepsea-nexus}"
cd "$REPO_ROOT"
python3 -c "
from session_manager import SessionManager
manager = SessionManager()
session_id = manager.start_session('New Topic')
print(f'Session: {session_id}')
"

# 查看统计
python3 -c "
from session_manager import SessionManager
manager = SessionManager()
print(manager.get_stats())
"
```

## 最佳实践

1. **一个话题一个文件**: 不要混用
2. **及时更新 Index**: 状态变更立即记录
3. **定期清理**: 利用自动 Flush
4. **命名规范**: 便于检索
