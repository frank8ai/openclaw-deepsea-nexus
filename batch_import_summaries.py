#!/usr/bin/env python3
"""
批量导入摘要 JSON 文件到向量库（已弃用）

⚠️ Deprecated: 请使用 `skills/deepsea-nexus/scripts/flush_summaries.py`。
这个脚本保留仅为兼容旧 cron 配置，内部已转发到新脚本。

步骤：
1. 检查 `NEXUS_SUMMARY_LOG_DIR` 或 `OPENCLAW_HOME/logs/summaries` 目录
2. 将所有待处理的摘要导入向量库
3. 清理已导入的文件

支持的 JSON 格式：
{
  "core_output": "string",
  "tech_points": ["string", ...],
  "code_pattern": "string",
  "decision_context": "string",
  "pitfall_record": "string",
  "applicable_scene": "string",
  "search_keywords": ["string", ...],
  "project关联": "string",
  "confidence": "high/medium/low",
  "source": "string (可选)"
}
"""

import os
import sys
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from runtime_paths import resolve_openclaw_home


def resolve_nexus_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return SCRIPT_DIR


def configure_import_paths(nexus_root: Path) -> None:
    candidate = str(nexus_root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def resolve_summary_log_dir() -> Path:
    override = os.environ.get("NEXUS_SUMMARY_LOG_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(resolve_openclaw_home()) / "logs" / "summaries").resolve()


def resolve_import_log_path() -> Path:
    return (Path(resolve_openclaw_home()) / "logs" / "nexus-import.log").resolve()


NEXUS_ROOT = resolve_nexus_root()
configure_import_paths(NEXUS_ROOT)

# 摘要文件目录
SUMMARIES_DIR = str(resolve_summary_log_dir())
# 批量导入日志
IMPORT_LOG = str(resolve_import_log_path())


def log(message: str, level: str = "INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    Path(IMPORT_LOG).parent.mkdir(parents=True, exist_ok=True)
    with open(IMPORT_LOG, 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")


def import_summary_file(filepath: str) -> bool:
    """导入单个摘要文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 兼容：当前 deepsea_nexus 对外稳定 API 为 nexus_add(content,title,tags)
        # 将结构化摘要拼成可检索的纯文本，并把关键词/置信度等写入 tags。
        from deepsea_nexus import nexus_add

        core_output = data.get("core_output", "")
        tech_points = data.get("tech_points", []) or []
        code_pattern = data.get("code_pattern", "")
        decision_context = data.get("decision_context", "")
        pitfall_record = data.get("pitfall_record", "")
        applicable_scene = data.get("applicable_scene", "")
        search_keywords = data.get("search_keywords", []) or []
        project_assoc = data.get("project关联", "")
        confidence = data.get("confidence", "medium")
        source = data.get("source", os.path.basename(filepath))

        title = (project_assoc or source or os.path.basename(filepath)).strip() or "summary"

        parts = []
        if core_output:
            parts.append(f"CORE_OUTPUT:\n{core_output}")
        if tech_points:
            parts.append("TECH_POINTS:\n" + "\n".join(f"- {p}" for p in tech_points if p))
        if code_pattern:
            parts.append(f"CODE_PATTERN:\n{code_pattern}")
        if decision_context:
            parts.append(f"DECISION_CONTEXT:\n{decision_context}")
        if pitfall_record:
            parts.append(f"PITFALL_RECORD:\n{pitfall_record}")
        if applicable_scene:
            parts.append(f"APPLICABLE_SCENE:\n{applicable_scene}")
        if search_keywords:
            parts.append("SEARCH_KEYWORDS:\n" + ", ".join(str(k) for k in search_keywords if k))
        if project_assoc:
            parts.append(f"PROJECT:\n{project_assoc}")
        if source:
            parts.append(f"SOURCE:\n{source}")
        if confidence:
            parts.append(f"CONFIDENCE:\n{confidence}")

        content = "\n\n".join(parts).strip()
        if not content:
            log(f"❌ 导入失败: {filepath} - 空内容", "ERROR")
            return False

        tags_items = []
        if isinstance(search_keywords, list):
            tags_items.extend([str(k).strip() for k in search_keywords if str(k).strip()])
        if project_assoc:
            tags_items.append(f"project:{project_assoc}")
        if confidence:
            tags_items.append(f"confidence:{confidence}")
        if source:
            tags_items.append(f"source:{source}")
        tags = ",".join(tags_items)

        doc_id = nexus_add(content=content, title=title, tags=tags)

        if doc_id:
            log(f"✅ 导入成功: {filepath} (doc_id={doc_id})", "INFO")
            return True
        else:
            log(f"❌ 导入失败: {filepath} - 未返回 doc_id", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ 导入失败: {filepath} - {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "DEBUG")
        return False


def batch_import():
    """批量导入所有摘要文件"""
    log("=" * 50, "INFO")
    log("开始批量导入摘要", "INFO")
    
    # 检查目录是否存在
    if not os.path.exists(SUMMARIES_DIR):
        log(f"⚠️ 目录不存在: {SUMMARIES_DIR}", "WARNING")
        return {"total": 0, "imported": 0, "failed": 0}
    
    # 查找所有 JSON 文件
    pattern = os.path.join(SUMMARIES_DIR, "*.json")
    files = glob.glob(pattern)
    
    if not files:
        log("📭 没有找到待处理的摘要文件", "INFO")
        return {"total": 0, "imported": 0, "failed": 0}
    
    log(f"📦 待处理文件数: {len(files)}", "INFO")
    
    stats = {"total": len(files), "imported": 0, "failed": 0}
    
    for filepath in files:
        log(f"处理: {os.path.basename(filepath)}", "DEBUG")
        if import_summary_file(filepath):
            stats["imported"] += 1
            # 导入成功后删除文件
            try:
                os.remove(filepath)
                log(f"🗑️  已删除: {filepath}", "DEBUG")
            except Exception as e:
                log(f"⚠️  删除失败: {filepath} - {str(e)}", "WARNING")
        else:
            stats["failed"] += 1
    
    log(f"📊 导入完成: 总计 {stats['total']}, 成功 {stats['imported']}, 失败 {stats['failed']}", "INFO")
    log("=" * 50, "INFO")
    
    return stats


if __name__ == "__main__":
    try:
        stats = batch_import()
        # 输出简洁状态
        print(json.dumps(stats, ensure_ascii=False))
    except Exception as e:
        log(f"💥 批量导入异常: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "DEBUG")
        print(json.dumps({"total": 0, "imported": 0, "failed": 0, "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
