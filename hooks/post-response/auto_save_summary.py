#!/usr/bin/env python3
"""
智能摘要自动保存 Hook
每次AI回复后自动解析并保存摘要到向量库
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

# 添加Deep-Sea Nexus路径
def _resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def _resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", _resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


NEXUS_PATH = str(
    Path(
        os.environ.get(
            "NEXUS_SKILL_PATH",
            _resolve_workspace_root() / "skills" / "deepsea-nexus",
        )
    ).expanduser().resolve()
)
sys.path.insert(0, NEXUS_PATH)

def _write_summary_json(summary: dict, response: str, conversation_id: str, user_query: str) -> str:
    """Write summary artifact JSON and return path."""
    fallback_dir = (_resolve_openclaw_home() / "logs" / "summaries" / "structured").resolve()
    os.makedirs(fallback_dir, exist_ok=True)
    log_file = os.path.join(fallback_dir, f"{conversation_id}.json")
    data = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "user_query": user_query,
        "full_response": response,
        "core_output": summary.get("本次核心产出", "") or summary.get("core_output", ""),
        "tech_points": summary.get("技术要点", []) or summary.get("tech_points", []),
        "code_pattern": summary.get("代码模式", "") or summary.get("code_pattern", ""),
        "decision_context": summary.get("决策上下文", "") or summary.get("decision_context", ""),
        "pitfall_record": summary.get("避坑记录", "") or summary.get("pitfall_record", ""),
        "applicable_scene": summary.get("适用场景", "") or summary.get("applicable_scene", ""),
        "search_keywords": summary.get("搜索关键词", []) or summary.get("search_keywords", []),
        "project关联": summary.get("项目关联", "") or summary.get("project关联", "") or summary.get("project", ""),
        "confidence": summary.get("置信度", "medium") or summary.get("confidence", "medium"),
    }
    with open(log_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return log_file


def _maybe_write_warm(summary_path: str, project_name: str) -> None:
    warm_enabled = str(os.environ.get("NEXUS_AUTO_SAVE_WARM_WRITE", "0")).strip().lower()
    if warm_enabled not in {"1", "true", "yes", "on"}:
        return
    if not project_name:
        return
    warm_writer = os.path.join(NEXUS_PATH, "scripts", "warm_writer.py")
    if not os.path.exists(warm_writer):
        return
    subprocess.run([sys.executable, warm_writer, "--from", summary_path], check=False)


def _extract_tag_list(text: str, max_items: int = 6):
    raw = re.split(r"[,\s|;]+", text or "")
    out = []
    for item in raw:
        clean = item.strip().strip("[]()")
        if not clean:
            continue
        if clean not in out:
            out.append(clean)
        if len(out) >= max_items:
            break
    return out


def _first_non_empty(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_summary_dict(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}

    def pick(*keys, default=""):
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, list) and value:
                return value
        return default

    tech_points = pick("tech_points", "技术要点", default=[])
    if not isinstance(tech_points, list):
        tech_points = []
    search_keywords = pick("search_keywords", "搜索关键词", default=[])
    if not isinstance(search_keywords, list):
        search_keywords = []
    entities = pick("entities", "实体", default=[])
    if not isinstance(entities, list):
        entities = []

    return {
        "core_output": pick("core_output", "本次核心产出"),
        "tech_points": [str(x).strip() for x in tech_points if str(x).strip()],
        "code_pattern": pick("code_pattern", "代码模式"),
        "decision_context": pick("decision_context", "决策上下文"),
        "pitfall_record": pick("pitfall_record", "避坑记录"),
        "applicable_scene": pick("applicable_scene", "适用场景"),
        "search_keywords": [str(x).strip() for x in search_keywords if str(x).strip()],
        "project关联": pick("project关联", "项目关联", "project"),
        "next_actions": pick("next_actions", "下一步"),
        "questions": pick("questions", "问题"),
        "entities": [str(x).strip() for x in entities if str(x).strip()],
        "confidence": pick("confidence", "置信度", default="medium"),
    }


def _summary_has_signal(summary_dict: dict) -> bool:
    if not isinstance(summary_dict, dict):
        return False
    fields = [
        summary_dict.get("core_output", ""),
        summary_dict.get("code_pattern", ""),
        summary_dict.get("decision_context", ""),
        summary_dict.get("pitfall_record", ""),
        summary_dict.get("applicable_scene", ""),
    ]
    if any(isinstance(v, str) and v.strip() for v in fields):
        return True
    for key in ("tech_points", "search_keywords", "entities"):
        values = summary_dict.get(key, [])
        if isinstance(values, list) and any(str(x).strip() for x in values):
            return True
    return False


def _summary_to_searchable_text(summary_dict: dict) -> str:
    parts = [
        summary_dict.get("core_output", ""),
        " ".join(summary_dict.get("tech_points", [])),
        summary_dict.get("code_pattern", ""),
        summary_dict.get("decision_context", ""),
        summary_dict.get("pitfall_record", ""),
        summary_dict.get("applicable_scene", ""),
        " ".join(summary_dict.get("search_keywords", [])),
        summary_dict.get("project关联", ""),
        summary_dict.get("next_actions", ""),
        summary_dict.get("questions", ""),
        " ".join(summary_dict.get("entities", [])),
    ]
    return " ".join([str(x).strip() for x in parts if str(x).strip()])


def _extract_summary_dict_from_response(response: str) -> dict:
    match = re.search(r"```json\s*\n([\s\S]*?)\n```", response or "", re.DOTALL)
    if not match:
        return {}
    try:
        payload = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return {}
    return _normalize_summary_dict(payload)


def _build_summary_from_policy_hint(summary_hint: str, user_query: str):
    if not summary_hint:
        return None

    lines = [x.strip() for x in str(summary_hint).splitlines() if x.strip()]

    def pick(prefix):
        prefix_l = prefix.lower()
        for line in lines:
            if line.lower().startswith(prefix_l):
                return line.split(":", 1)[1].strip() if ":" in line else ""
        return ""

    state = pick("State")
    decisions = pick("Decisions")
    blocker = pick("Blocker")
    replay = pick("Replay")
    next_action = pick("Next")
    evidence = pick("Evidence")

    if not any([state, decisions, blocker, replay, next_action, evidence]):
        return None

    from auto_summary import StructuredSummary

    keywords = _extract_tag_list(decisions.replace("|", " ").replace(")", " "))
    keywords.extend([x for x in ["context-policy-v2", "openclaw", "event-driven"] if x not in keywords])

    tech_points = []
    if decisions:
        tech_points.extend([x.strip() for x in decisions.split("|") if x.strip()])
    if replay:
        tech_points.append(f"replay={replay}")

    summary = StructuredSummary(
        core_output=_first_non_empty(state, user_query, "Context policy summary captured"),
        tech_points=tech_points[:8],
        code_pattern=replay,
        decision_context=decisions,
        pitfall_record=blocker,
        applicable_scene="OpenClaw Context Policy v2 auto-save",
        search_keywords=keywords[:10],
        project关联="openclaw/deepsea-nexus",
        next_actions=next_action,
        questions="",
        entities=[],
        confidence="medium",
    )
    return summary


def _ensure_response_has_summary_block(response: str, summary_hint: str, user_query: str) -> str:
    from auto_summary import SummaryParser

    base = str(response or "").strip()
    if not base and summary_hint:
        base = summary_hint.strip()
    if not base:
        return ""

    parser = SummaryParser()
    _reply, parsed = parser.parse(base)
    if parsed is not None:
        return base

    structured = _build_summary_from_policy_hint(summary_hint, user_query)
    if structured is None:
        return base

    json_block = json.dumps(structured.to_dict(), ensure_ascii=False, indent=2)
    return f"{base}\n\n```json\n{json_block}\n```"


def _load_context() -> dict:
    raw = os.environ.get("NEXUS_HOOK_CONTEXT", "{}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid NEXUS_HOOK_CONTEXT json: {error}") from error
    if not isinstance(parsed, dict):
        raise RuntimeError("NEXUS_HOOK_CONTEXT must be a json object")
    return parsed


def _store_to_nexus(
    *,
    conversation_id: str,
    source: str,
    user_query: str,
    response: str,
    summary_hint: str,
) -> dict:
    from auto_summary import SummaryParser
    from nexus_core import nexus_init, nexus_stats, nexus_write
    from write_guard import emit_write_guard_alert, validate_write_target

    ok, detail = validate_write_target(context="hooks.post_response.auto_save_summary")
    if not ok:
        emit_write_guard_alert(
            {
                "event": "write_guard_blocked",
                "context": "hooks.post_response.auto_save_summary",
                "reason": detail.get("reason", "unknown"),
                "vector_db": detail.get("vector_db", ""),
                "collection": detail.get("collection", ""),
            }
        )
        raise RuntimeError(f"write guard blocked: {detail.get('reason', 'unknown')}")

    nexus_init(blocking=False)
    before_docs = int(nexus_stats().get("total_documents", 0))

    reply, summary = SummaryParser.parse(response)
    summary_dict = _normalize_summary_dict(summary.to_dict()) if summary is not None else {}
    if not _summary_has_signal(summary_dict):
        summary_dict = _extract_summary_dict_from_response(response)
    if not _summary_has_signal(summary_dict):
        hint_summary = _build_summary_from_policy_hint(summary_hint, user_query)
        if hint_summary is not None:
            summary_dict = _normalize_summary_dict(hint_summary.to_dict())

    stored_count = 0
    doc_ids = []

    raw_content = str(reply or response).strip()
    if raw_content:
        raw_doc_id = nexus_write(
            raw_content,
            f"对话 {conversation_id} - 原文",
            priority="P2",
            kind="summary",
            source=source,
            tags="type:content,origin:auto_save_hook",
        )
        if raw_doc_id:
            stored_count += 1
            doc_ids.append(str(raw_doc_id))

    has_summary = _summary_has_signal(summary_dict)
    if has_summary:
        core_output = _first_non_empty(
            summary_dict.get("core_output", ""),
            summary_dict.get("本次核心产出", ""),
            user_query,
            "Auto-saved summary",
        )
        summary_keywords = summary_dict.get("search_keywords", [])
        if isinstance(summary_keywords, list):
            summary_keywords = [str(x).strip() for x in summary_keywords if str(x).strip()]
        else:
            summary_keywords = []
        keyword_tags = ",".join(summary_keywords[:8])
        summary_text = _first_non_empty(
            _summary_to_searchable_text(summary_dict),
            core_output,
            json.dumps(summary_dict, ensure_ascii=False),
        )
        summary_doc_id = nexus_write(
            summary_text,
            f"对话 {conversation_id} - 摘要",
            priority="P1",
            kind="summary",
            source=source,
            tags=f"type:structured_summary,origin:auto_save_hook,{keyword_tags}".strip(","),
        )
        if summary_doc_id:
            stored_count += 1
            doc_ids.append(str(summary_doc_id))

        metadata_doc_id = nexus_write(
            json.dumps(summary_dict, ensure_ascii=False),
            f"对话 {conversation_id} - 摘要元数据",
            priority="P2",
            kind="fact",
            source=source,
            tags=f"type:summary_metadata,origin:auto_save_hook,{keyword_tags}".strip(","),
        )
        if metadata_doc_id:
            stored_count += 1
            doc_ids.append(str(metadata_doc_id))

        summary_path = _write_summary_json(summary_dict, response, conversation_id, user_query)
        project_name = summary_dict.get("project关联", "") or summary_dict.get("project", "")
        _maybe_write_warm(summary_path, project_name)
    elif summary_hint:
        hint_doc_id = nexus_write(
            summary_hint,
            f"对话 {conversation_id} - Handoff Hint",
            priority="P1",
            kind="summary",
            source=source,
            tags="type:summary_hint,origin:auto_save_hook",
        )
        if hint_doc_id:
            stored_count += 1
            doc_ids.append(str(hint_doc_id))

    after_docs = int(nexus_stats().get("total_documents", before_docs))
    return {
        "stored_count": stored_count,
        "doc_ids": doc_ids,
        "has_summary": has_summary,
        "before_docs": before_docs,
        "after_docs": after_docs,
    }


def main() -> int:
    context = _load_context()

    response = context.get("response", "")
    summary_hint = context.get("summary_hint", "")
    user_query = context.get("user_query", "")
    conversation_id = context.get("conversation_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    source = context.get("source", "nexus-auto-save/message:sent")

    if not response and not summary_hint:
        print("⚠️ 未检测到回复或摘要提示，跳过保存")
        return 0

    effective_response = _ensure_response_has_summary_block(response, summary_hint, user_query)
    if not effective_response:
        print("⚠️ 有效回复为空，跳过保存")
        return 0

    try:
        result = _store_to_nexus(
            conversation_id=conversation_id,
            source=source,
            user_query=user_query,
            response=effective_response,
            summary_hint=summary_hint,
        )
        if result["has_summary"]:
            print(
                f"✅ 摘要已保存 | 对话: {conversation_id} | 写入: {result['stored_count']} | "
                f"docs: {result['before_docs']}->{result['after_docs']}"
            )
        else:
            print(
                f"ℹ️ 已保存原文/提示 | 对话: {conversation_id} | 写入: {result['stored_count']} | "
                f"docs: {result['before_docs']}->{result['after_docs']}"
            )
        return 0
    except Exception as error:
        save_to_fallback(
            response=response,
            summary_hint=summary_hint,
            conversation_id=conversation_id,
            user_query=user_query,
        )
        print(f"❌ 保存失败: {error}")
        return 1


def save_to_fallback(response: str, summary_hint: str, conversation_id: str, user_query: str):
    """降级保存到文件"""
    fallback_dir = os.path.expanduser("~/.openclaw/logs/summaries")
    os.makedirs(fallback_dir, exist_ok=True)

    summary = ""
    summary_match = re.search(r'## 📋 总结\s*\n\s*([\s\S]*?)(?=\n\n|$)', response or "")
    if summary_match:
        summary = summary_match.group(1).strip()
    if not summary:
        summary = summary_hint or ""

    log_file = os.path.join(fallback_dir, f"{conversation_id}.json")
    data = {
        "timestamp": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "user_query": user_query,
        "summary": summary,
        "summary_hint": summary_hint,
        "full_response": response,
        "fallback": True,
    }

    with open(log_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
