# Deep-Sea Nexus v2.0 完整开发任务清单 (v1.1)

> 说明：这是 v2.0 阶段的历史任务清单。
> 当前产品与实现真源请看：`product/README.md`、`ARCHITECTURE_CURRENT.md`、`API_CURRENT.md`。

```
================================================================================
                    Deep-Sea Nexus v2.0 完整开发任务清单 (v1.1)
================================================================================

版本: 1.1
更新: 2026-02-07
状态: 待开发

================================================================================
Day 1: 基础设施
================================================================================

[ ] M1.1 创建项目结构
    [ ] P0 创建根目录 ~/.openclaw/workspace/DEEP_SEA_NEXUS_V2（legacy，v3 使用 ~/.openclaw/workspace/skills/deepsea-nexus）
    [ ] P0 创建子目录 (7 个)
    [ ] P0 创建 .gitignore
    [ ] P0 初始化 Git 仓库
    [ ] P0 创建 .editorconfig
    [ ] P0 创建 requirements.txt (空文件，纯 Python) ← 新增
    [ ] P0 创建 README.md (基础模板) ← 新增

[ ] M1.2 配置文件
    [ ] P0 编写 config.yaml (全部配置项)
    [ ] P0 编写 src/config.py (NexusConfig 类)
    [ ] P1 环境变量覆盖功能
    [ ] P0 单元测试: Config 类 (5 个测试)

[ ] M1.3 数据结构
    [ ] P0 编写 src/data_structures.py
        [ ] SessionStatus 枚举
        [ ] SessionMetadata 数据类
        [ ] DailyIndex 数据类
        [ ] RecallResult 数据类
        [ ] IndexEntry 数据类
        [ ] NexusConfig 数据类
    [ ] P0 单元测试: 数据结构 (5 个测试)

[ ] M1.4 测试框架
    [ ] P0 创建 tests/conftest.py
    [ ] P0 创建 tests/__init__.py
    [ ] P0 创建 tests/test_phase1.py
    [ ] P1 配置 pytest 覆盖率报告

[ ] M1.5 日志系统 ← 新增
    [ ] P0 创建 src/logger.py
    [ ] P0 日志级别配置
    [ ] P0 日志格式定义
    [ ] P0 控制台输出
    [ ] P1 文件输出

[ ] M1.6 错误处理基础 ← 新增
    [ ] P0 创建 src/exceptions.py
    [ ] P0 SessionNotFoundError
    [ ] P0 IndexFileError
    [ ] P0 StorageFullError
    [ ] P0 TimeoutError
    [ ] P0 单元测试: 异常 (3 个测试)

验收标准 Day 1:
  ✓ 所有目录创建完成
  ✓ config.yaml 语法正确
  ✓ README.md 基础模板
  ✓ NexusConfig 类可读取 10 个配置项
  ✓ 所有单元测试通过
  ✓ 索引 < 300 tokens
  ✓ 异常类定义完成

================================================================================
Day 2: Nexus Core - 基础功能
================================================================================

[ ] M2.1 目录管理模块
    [ ] P0 _ensure_directories() - 创建所有目录
    [ ] P0 _ensure_today_index() - 确保今日索引存在
    [ ] P0 _create_index_file() - 创建索引文件模板
    [ ] P0 单元测试: 目录管理 (3 个测试) ← 更新

[ ] M2.2 Session 管理 - 创建
    [ ] P0 start_session(topic, auto_create=True) -> str
    [ ] P0 生成唯一 session_id (HHMM_Topic)
    [ ] P0 创建 Session 文件模板
    [ ] P0 添加到索引
    [ ] P0 单元测试: 创建 Session (5 个测试)

[ ] M2.3 Session 管理 - 写入
    [ ] P0 write_session(session_id, content, is_gold, append) -> bool
    [ ] P0 追加/覆盖内容
    [ ] P0 #GOLD 标记处理
    [ ] P0 同步更新索引
    [ ] P0 单元测试: 写入 Session (5 个测试)

[ ] M2.4 Session 管理 - 读取
    [ ] P0 read_session(session_id, max_tokens) -> Optional[str]
    [ ] P0 按 max_tokens 截断
    [ ] P0 单元测试: 读取 Session (3 个测试)

[ ] M2.5 活跃 Session
    [ ] P0 get_active_session() -> Optional[str]
    [ ] P0 获取最新 Session
    [ ] P0 单元测试: 活跃 Session (2 个测试)

[ ] M2.6 并发安全 ← 新增 (高优先级)
    [ ] P0 创建 src/lock.py
    [ ] P0 FileLock 类 (基于 flock)
    [ ] P0 写入时加锁
    [ ] P0 超时检测 (30 秒)
    [ ] P0 单元测试: 文件锁 (3 个测试)

验收标准 Day 2:
  ✓ Session CRUD 完整
  ✓ GOLD 标记工作
  ✓ 文件正确创建
  ✓ 索引正确更新
  ✓ 并发安全 (文件锁)

================================================================================
Day 3: Nexus Core - 索引与召回
================================================================================

[ ] M3.1 索引管理 - 读取
    [ ] P0 read_today_index() -> str
    [ ] P0 返回 < 300 tokens
    [ ] P0 单元测试: 读取索引 (3 个测试)

[ ] M3.2 索引管理 - 解析
    [ ] P0 parse_index(index_content) -> DailyIndex
    [ ] P0 解析 Sessions 列表
    [ ] P0 解析 GOLD Keys
    [ ] P0 解析 Topics
    [ ] P0 单元测试: 解析索引 (5 个测试)

[ ] M3.3 索引管理 - 更新
    [ ] P0 _add_session_to_index(session_id, topic)
    [ ] P0 _touch_session(session_id)
    [ ] P0 _add_gold_key(session_id, content)
    [ ] P0 单元测试: 更新索引 (3 个测试)

[ ] M3.4 召回引擎 - 搜索索引
    [ ] P0 _search_index(index, query) -> List[Dict]
    [ ] P0 匹配 Session 名称
    [ ] P0 匹配 GOLD Keys
    [ ] P0 相关度评分 (GOLD 权重 1.5x)
    [ ] P0 单元测试: 搜索索引 (5 个测试)

[ ] M3.5 召回引擎 - 提取内容
    [ ] P0 _extract_relevant_parts(content, query) -> str
    [ ] P0 提取包含关键词的行
    [ ] P0 限制返回数量 (最多 5 条)
    [ ] P0 单元测试: 提取内容 (3 个测试)

[ ] M3.6 召回主流程
    [ ] P0 recall(query, max_results, max_tokens) -> List[RecallResult]
    [ ] P0 完整召回流程
    [ ] P0 相关度排序
    [ ] P0 单元测试: 召回 (5 个测试)

[ ] M3.7 跨日期搜索 ← 新增
    [ ] P1 recall_archives(query, days=7) -> List[RecallResult]
    [ ] P1 搜索最近 N 天索引
    [ ] P1 搜索月度归档
    [ ] P1 合并结果
    [ ] P1 单元测试: 跨日期 (3 个测试)

验收标准 Day 3:
  ✓ 索引解析正确
  ✓ 搜索评分正确
  ✓ GOLD 优先
  ✓ 召回准确率 > 80%
  ✓ 跨日期搜索可选

================================================================================
Day 4: Flush 系统与工具
================================================================================

[ ] M4.1 Flush - 单个 Session
    [ ] P0 flush_session(session_id) -> bool
    [ ] P0 从索引移除
    [ ] P0 移动到归档
    [ ] P0 单元测试: Flush Session (3 个测试)

[ ] M4.2 Flush - 每日 Flush
    [ ] P0 daily_flush() -> Dict
    [ ] P0 收集活跃 Session
    [ ] P0 移动到月度归档
    [ ] P0 创建新索引
    [ ] P0 返回统计
    [ ] P0 单元测试: 每日 Flush (3 个测试)

[ ] M4.3 统计功能
    [ ] P0 get_stats() -> Dict
    [ ] P0 今日 Session 数
    [ ] P0 索引大小
    [ ] P0 单元测试: 统计 (2 个测试)

[ ] M4.4 工具脚本 - daily_flush.py
    [ ] P0 定时执行入口
    [ ] P0 命令行参数
    [ ] P0 输出统计
    [ ] P1 守护进程模式

[ ] M4.5 工具脚本 - session_split.py
    [ ] P0 自动检测大文件 (>50KB)
    [ ] P0 按大小分割
    [ ] P0 更新索引
    [ ] P1 分割策略优化

[ ] M4.6 工具脚本 - index_rebuild.py
    [ ] P0 重建索引
    [ ] P0 扫描所有 Session
    [ ] P0 重新生成索引
    [ ] P1 增量重建

[ ] M4.7 工具脚本 - migrate.py ← 新增
    [ ] P1 从 v1.0 迁移
    [ ] P1 检测旧文件
    [ ] P1 导入并保持 UUID
    [ ] P1 验证迁移结果

验收标准 Day 4:
  ✓ Flush 正确工作
  ✓ 归档正确
  ✓ 工具脚本可用
  ✓ 迁移工具可选

================================================================================
Day 5: 测试与验证
================================================================================

[ ] M5.1 单元测试完整覆盖
    [ ] P0 补充遗漏测试
    [ ] P0 达到 80% 覆盖率
    [ ] P0 修复失败测试

[ ] M5.2 集成测试
    [ ] P0 test_complete_flow: 创建→写入→召回
    [ ] P0 test_multi_session: 多 Session
    [ ] P0 test_gold_sync: GOLD 同步
    [ ] P0 test_flush_flow: Flush 流程
    [ ] P0 test_index_size: 索引大小验证
    [ ] P0 test_concurrency: 并发安全验证 ← 新增

[ ] M5.3 性能测试
    [ ] P0 PT01: 启动时间 < 1s
    [ ] P0 PT02: 召回延迟 < 100ms
    [ ] P0 PT03: 索引 < 300 tokens
    [ ] P0 PT04: 每轮 < 1000 tokens
    [ ] P1 性能基准记录 (benchmark.txt) ← 新增

[ ] M5.4 人工验收
    [ ] P0 验证启动消耗
    [ ] P0 验证召回准确率
    [ ] P0 验证 GOLD 标记
    [ ] P0 验证 Flush 流程
    [ ] P1 用户体验测试

[ ] M5.5 Bug 修复
    [ ] P0 修复所有阻塞 Bug
    [ ] P1 修复非阻塞 Bug

验收标准 Day 5:
  ✓ 80%+ 测试覆盖
  ✓ 所有性能指标达标
  ✓ 无阻塞 Bug
  ✓ 性能基准记录

================================================================================
Day 6: 集成与部署
================================================================================

[ ] M6.1 AGENTS.md 集成
    [ ] P0 添加 v2.0 协议
    [ ] P0 启动规则 (< 500 tokens)
    [ ] P0 对话规则 (recall)
    [ ] P0 写入规则 (#GOLD)
    [ ] P0 Session 规则
    [ ] P1 OpenClaw 配置示例

[ ] M6.2 CLI 完善
    [ ] P0 --init 初始化
    [ ] P0 --stats 统计
    [ ] P0 --session TOPIC 创建
    [ ] P0 --write CONTENT 写入
    [ ] P0 --recall QUERY 召回
    [ ] P0 --index 显示索引
    [ ] P0 --flush 执行 Flush
    [ ] P0 --migrate 迁移工具 ← 新增
    [ ] P1 --help 自动帮助信息 ← 新增

[ ] M6.3 README.md 完善
    [ ] P0 产品介绍
    [ ] P0 安装步骤
    [ ] P0 使用示例
    [ ] P0 API 文档
    [ ] P0 故障排除

[ ] M6.4 部署脚本
    [ ] P0 deploy.sh 部署脚本
    [ ] P0 权限设置
    [ ] P0 环境检查
    [ ] P1 回滚脚本 (rollback.sh) ← 新增

验收标准 Day 6:
  ✓ AGENTS.md 集成完成
  ✓ CLI 完整可用 (含帮助)
  ✓ 文档完整
  ✓ 部署脚本可用

================================================================================
Day 7: 完善与发布
================================================================================

[ ] M7.1 代码审查
    [ ] P0 代码风格检查 (Black)
    [ ] P0 类型注解检查 (Mypy)
    [ ] P0 安全审查
    [ ] P1 性能审查

[ ] M7.2 错误处理完善
    [ ] P0 文件不存在异常
    [ ] P0 磁盘满异常
    [ ] P0 超时异常
    [ ] P0 日志记录
    [ ] P1 全局异常处理器

[ ] M7.3 日志系统完善
    [ ] P0 日志轮转 (logging.handlers)
    [ ] P0 日志级别配置
    [ ] P0 日志格式
    [ ] P1 日志分析工具

[ ] M7.4 最终测试
    [ ] P0 完整流程测试
    [ ] P0 边界条件测试
    [ ] P0 压力测试 (10 并发)
    [ ] P0 回归测试
    [ ] P1 混沌测试 (模拟故障)

[ ] M7.5 发布准备
    [ ] P0 CHANGELOG.md 更新
    [ ] P0 版本号更新 (2.0.0)
    [ ] P0 标签创建 (git tag v2.0.0)
    [ ] P1 Release 说明

验收标准 Day 7:
  ✓ 代码质量达标
  ✓ 错误处理完整
  ✓ 日志系统完善
  ✓ 测试 100% 通过
  ✓ 可发布版本

================================================================================
最终验收清单
================================================================================

功能验收:
  [ ] Session 创建/写入/读取/关闭
  [ ] 索引创建/更新/搜索/解析
  [ ] 召回引擎 (含跨日期可选)
  [ ] GOLD 标记与同步
  [ ] Flush 归档 (手动/定时)
  [ ] 并发安全 (文件锁)
  [ ] CLI 工具 (7 个命令)
  [ ] 迁移工具 (v1.0 -> v2.0)

性能验收:
  [ ] 启动 < 1 秒
  [ ] 索引 < 300 tokens
  [ ] 召回 < 100ms
  [ ] 每轮 < 1000 tokens
  [ ] 并发安全 (文件锁)

集成验收:
  [ ] AGENTS.md 集成完成
  [ ] OpenClaw 对接测试
  [ ] CLI 帮助信息完整

文档验收:
  [ ] README.md 完整 (产品/安装/使用/API/故障)
  [ ] CHANGELOG.md 更新
  [ ] 代码注释完整

安全验收:
  [ ] 文件锁并发安全
  [ ] 异常处理完整
  [ ] 日志记录完整
  [ ] 无敏感信息泄露

================================================================================
任务统计 (v1.1)
================================================================================

按优先级:
  P0 必须完成: 48 个 (+6)
  P1 应该完成: 22 个 (+5)
  P2 可选: 8 个

总计: 58 个任务 (+11)

按类型:
  代码开发: 32 个 (+4)
  单元测试: 20 个 (+4)
  集成测试: 6 个 (+1)
  文档编写: 6 个
  脚本开发: 4 个

新增项:
  ✓ README.md 基础模板
  ✓ requirements.txt
  ✓ 日志系统 (src/logger.py)
  ✓ 错误处理 (src/exceptions.py)
  ✓ 并发安全 (src/lock.py)
  ✓ 跨日期搜索 (可选)
  ✓ 迁移工具 (migrate.py)
  └── 回滚脚本 (rollback.sh)

================================================================================
```
