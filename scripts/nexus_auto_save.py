#!/usr/bin/env python3
"""
Nexus Auto-Save Script
自动从对话日志中提取摘要并保存到向量库
"""

import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
NEXUS_ROOT = Path(
    os.environ.get("DEEPSEA_NEXUS_ROOT", SCRIPT_DIR.parent)
).expanduser().resolve()
OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser()
WORKSPACE_ROOT = Path(
    os.environ.get("OPENCLAW_WORKSPACE", OPENCLAW_HOME / "workspace")
).expanduser()
NEXUS_PATH = str(NEXUS_ROOT)
VECTOR_DB_PATH = os.path.expanduser(
    os.environ.get("NEXUS_VECTOR_DB", str(WORKSPACE_ROOT / "memory" / ".vector_db_restored"))
)
LOG_DIR = str(OPENCLAW_HOME / "logs")


def extract_summaries_from_logs(hours: int = 1) -> list:
    """
    从日志中提取摘要
    
    Args:
        hours: 检查过去几小时的日志
        
    Returns:
        提取的摘要列表 [(content, timestamp), ...]
    """
    summaries = []
    cutoff = datetime.now() - timedelta(hours=hours)
    
    # 检查 OpenClaw 日志
    log_patterns = [
        Path(LOG_DIR) / "ai-interactions.log",
        Path("/tmp/openclaw/openclaw.log"),
    ]
    
    for log_path in log_patterns:
        if not log_path.exists():
            continue
            
        try:
            content = log_path.read_text()
            
            # 匹配摘要格式
            # 格式: ## 📋 总结 \n - 要点1 \n - 要点2
            pattern = r'## 📋 总结\s*\n([\s\S]*?)(?=\n\n|$)'
            matches = re.findall(pattern, content, re.MULTILINE)
            
            for match in matches:
                # 清理摘要内容
                clean_content = match.strip()
                if clean_content and len(clean_content) > 10:
                    summaries.append((clean_content, datetime.now()))
                    
        except Exception as e:
            print(f"读取日志错误: {e}")
    
    return summaries


def save_to_nexus(content: str, tags: str = "auto-summary") -> Optional[str]:
    """
    保存摘要到向量库
    """
    try:
        sys.path.insert(0, NEXUS_PATH)
        from deepsea_nexus import nexus_init, nexus_write
        from deepsea_nexus.write_guard import validate_write_target, emit_write_guard_alert

        ok, detail = validate_write_target(context="scripts.nexus_auto_save")
        if not ok:
            emit_write_guard_alert(
                {
                    "event": "write_guard_blocked",
                    "context": "scripts.nexus_auto_save",
                    "reason": detail.get("reason", "unknown"),
                    "vector_db": detail.get("vector_db", ""),
                    "collection": detail.get("collection", ""),
                }
            )
            print(f"[AutoSave] 写入阻断: {detail.get('reason', 'unknown')}")
            return None
        
        nexus_init(blocking=False)
        
        result = nexus_write(
            content,
            f"自动摘要 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            priority="P1",
            kind="summary",
            source="nexus_auto_save",
            tags=f"type:summary,{tags}",
        )
        
        return result
        
    except Exception as e:
        print(f"保存错误: {e}")
        return None


def main():
    """主函数"""
    print(f"⏰ [{datetime.now().isoformat()}] Nexus Auto-Save 开始...")
    
    # 提取摘要
    summaries = extract_summaries_from_logs(hours=1)
    
    if not summaries:
        print("未找到新的摘要")
        return
    
    print(f"找到 {len(summaries)} 条摘要")
    
    # 保存到向量库
    saved = 0
    for content, timestamp in summaries:
        result = save_to_nexus(content)
        if result:
            saved += 1
            print(f"✅ 保存成功: {result}")
    
    print(f"💾 完成: 保存 {saved}/{len(summaries)} 条摘要")


if __name__ == "__main__":
    main()
