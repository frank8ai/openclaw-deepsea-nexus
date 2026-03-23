"""
Canonical typed-context contract helpers.

This module keeps the current context-governance payload stable across:
- SmartContext summary emit
- ContextEngine structured-summary compatibility
- Memory v5 ingest
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _pick_value(data: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data.get(key) is not None:
            return data.get(key)
    return None


def _pick_text(data: Mapping[str, Any], *keys: str) -> str:
    value = _pick_value(data, *keys)
    if isinstance(value, list):
        return "; ".join(_normalize_list(value))
    return _safe_str(value)


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        items: List[str] = []
        for item in value:
            items.extend(_normalize_list(item))
        return _dedupe(items)
    if isinstance(value, dict):
        return _normalize_list(list(value.values()))

    text = _safe_str(value)
    if not text:
        return []

    separators = ("\n", ";", "|")
    chunks = [text]
    for separator in separators:
        next_chunks: List[str] = []
        for chunk in chunks:
            if separator not in chunk:
                next_chunks.append(chunk)
                continue
            next_chunks.extend(part.strip() for part in chunk.split(separator))
        chunks = next_chunks
    return _dedupe(chunks)


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        cleaned = _safe_str(item)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
    return out


def normalize_typed_context(payload: Any) -> Dict[str, Any]:
    data = payload if isinstance(payload, Mapping) else {}

    summary = _pick_text(data, "summary", "本次核心产出", "核心产出", "core_output")
    goal = _pick_text(data, "goal", "objective", "目标", "当前目标")
    status = _pick_text(data, "status", "state", "phase", "状态", "阶段")

    decisions = _normalize_list(
        _pick_value(data, "decisions", "decision", "决策", "decision_context", "决策上下文")
    )
    constraints = _normalize_list(
        _pick_value(data, "constraints", "constraint", "约束", "限制")
    )
    blockers = _normalize_list(
        _pick_value(data, "blockers", "blocker", "risks", "risk", "阻塞", "卡点", "风险")
    )
    next_actions = _normalize_list(
        _pick_value(data, "next_actions", "next", "下一步", "todo", "待办")
    )
    questions = _normalize_list(
        _pick_value(data, "questions", "question", "问题", "open_questions", "待澄清问题")
    )
    evidence = _normalize_list(
        _pick_value(data, "evidence", "evidence_pointers", "证据", "evidence_pointer")
    )
    replay = _normalize_list(
        _pick_value(data, "replay", "replay_commands", "replay_command", "复现", "重放", "命令")
    )
    decision_reversal_conditions = _normalize_list(
        _pick_value(
            data,
            "decision_reversal_conditions",
            "decision_reversal_condition",
            "reversal_conditions",
            "reversal_condition",
            "决策反转条件",
            "推翻条件",
            "撤销条件",
        )
    )
    waiting_on = _normalize_list(
        _pick_value(data, "waiting_on", "waiting", "blocked_on", "等待项", "等待对象", "待确认")
    )
    assumptions = _normalize_list(
        _pick_value(data, "assumptions", "assumption", "关键假设", "假设")
    )
    modified_files = _normalize_list(
        _pick_value(data, "modified_files", "modified_file", "changed_files", "files_changed", "已修改文件", "修改文件")
    )
    change_scope = _normalize_list(
        _pick_value(data, "change_scope", "change_scopes", "branch_scope", "变更范围", "分支范围")
    )
    key_changes = _normalize_list(
        _pick_value(data, "key_changes", "key_change", "changes", "change_log", "关键变更", "关键修改")
    )
    verification_subject = _pick_text(
        data,
        "verification_subject",
        "verify_subject",
        "验证对象",
        "验证主题",
    )
    verification_command = _pick_text(
        data,
        "verification_command",
        "verify_command",
        "验证命令",
        "verify_cmd",
    )
    verification_result = _pick_text(
        data,
        "verification_result",
        "verify_result",
        "验证结果",
    )
    verification_status = _pick_text(
        data,
        "verification_status",
        "verification",
        "verification_result",
        "test_status",
        "验证状态",
        "验证结果",
    )
    failure_fingerprint = _pick_text(
        data,
        "failure_fingerprint",
        "error_fingerprint",
        "失败指纹",
        "错误指纹",
    )
    rollback_notes = _normalize_list(
        _pick_value(data, "rollback_notes", "rollback_note", "rollback", "回滚笔记", "回滚说明", "回退说明")
    )
    rollback_trigger = _pick_text(
        data,
        "rollback_trigger",
        "回滚触发",
        "回退触发",
    )
    rollback_target = _pick_text(
        data,
        "rollback_target",
        "回滚目标",
        "恢复目标",
    )
    topics = _normalize_list(_pick_value(data, "topics", "topic", "主题"))
    keywords = _normalize_list(_pick_value(data, "keywords", "search_keywords", "搜索关键词"))
    entities = _normalize_list(_pick_value(data, "entities", "entity", "实体"))

    tech_points = _normalize_list(_pick_value(data, "tech_points", "技术要点", "key_points"))
    code_pattern = _pick_text(data, "code_pattern", "代码模式")
    pitfall_record = _pick_text(data, "pitfall_record", "避坑记录", "pitfalls")
    applicable_scene = _pick_text(data, "applicable_scene", "适用场景", "scene")
    project = _pick_text(data, "project", "project_name", "项目关联", "project关联")
    confidence = _pick_text(data, "confidence", "置信度") or "medium"

    return {
        "summary": summary,
        "goal": goal,
        "status": status,
        "decisions": decisions,
        "constraints": constraints,
        "blockers": blockers,
        "next_actions": next_actions,
        "questions": questions,
        "evidence": evidence,
        "replay": replay,
        "decision_reversal_conditions": decision_reversal_conditions,
        "waiting_on": waiting_on,
        "assumptions": assumptions,
        "modified_files": modified_files,
        "change_scope": change_scope,
        "key_changes": key_changes,
        "verification_subject": verification_subject,
        "verification_command": verification_command,
        "verification_result": verification_result,
        "verification_status": verification_status,
        "failure_fingerprint": failure_fingerprint,
        "rollback_notes": rollback_notes,
        "rollback_trigger": rollback_trigger,
        "rollback_target": rollback_target,
        "topics": topics,
        "keywords": keywords,
        "entities": entities,
        "project": project,
        "confidence": confidence,
        "tech_points": tech_points,
        "code_pattern": code_pattern,
        "pitfall_record": pitfall_record,
        "applicable_scene": applicable_scene,
    }


def export_typed_context(payload: Any) -> Dict[str, Any]:
    data = normalize_typed_context(payload)
    decision_text = "; ".join(data["decisions"])
    next_text = "; ".join(data["next_actions"])
    question_text = "; ".join(data["questions"])
    evidence_text = "; ".join(data["evidence"])
    replay_text = "; ".join(data["replay"])
    decision_reversal_text = "; ".join(data["decision_reversal_conditions"])
    waiting_on_text = "; ".join(data["waiting_on"])
    assumptions_text = "; ".join(data["assumptions"])
    modified_files_text = "; ".join(data["modified_files"])
    change_scope_text = "; ".join(data["change_scope"])
    key_changes_text = "; ".join(data["key_changes"])
    rollback_text = "; ".join(data["rollback_notes"])
    topic_text = "; ".join(data["topics"])

    exported = dict(data)
    exported.update(
        {
            "本次核心产出": data["summary"],
            "核心产出": data["summary"],
            "core_output": data["summary"],
            "决策上下文": decision_text,
            "decision_context": decision_text,
            "下一步": next_text,
            "问题": question_text,
            "决策反转条件": decision_reversal_text,
            "等待项": waiting_on_text,
            "关键假设": assumptions_text,
            "已修改文件": modified_files_text,
            "修改文件": modified_files_text,
            "变更范围": change_scope_text,
            "关键变更": key_changes_text,
            "关键修改": key_changes_text,
            "验证对象": data["verification_subject"],
            "验证命令": data["verification_command"],
            "verification_subject": data["verification_subject"],
            "verification_command": data["verification_command"],
            "verification_result": data["verification_result"],
            "验证结果": data["verification_result"],
            "验证状态": data["verification_status"],
            "verification_status": data["verification_status"],
            "失败指纹": data["failure_fingerprint"],
            "failure_fingerprint": data["failure_fingerprint"],
            "回滚笔记": rollback_text,
            "回滚说明": rollback_text,
            "回滚触发": data["rollback_trigger"],
            "回滚目标": data["rollback_target"],
            "rollback_trigger": data["rollback_trigger"],
            "rollback_target": data["rollback_target"],
            "搜索关键词": list(data["keywords"]),
            "search_keywords": list(data["keywords"]),
            "实体": list(data["entities"]),
            "topic": data["topics"][0] if data["topics"] else "",
            "主题": topic_text,
            "项目关联": data["project"],
            "project关联": data["project"],
            "置信度": data["confidence"],
            "技术要点": list(data["tech_points"]),
            "代码模式": data["code_pattern"],
            "避坑记录": data["pitfall_record"],
            "适用场景": data["applicable_scene"],
            "evidence_pointers": list(data["evidence"]),
            "replay_commands": list(data["replay"]),
            "replay_command": data["replay"][0] if data["replay"] else "",
        }
    )
    return exported


def durable_decision_evidence(payload: Any) -> Dict[str, Any]:
    data = normalize_typed_context(payload)
    evidence = list(data.get("evidence", []) or [])
    replay = list(data.get("replay", []) or [])
    supported = bool(evidence or replay)
    return {
        "supported": supported,
        "reason": "ok" if supported else "missing_evidence",
        "evidence": evidence,
        "replay": replay,
        "decision_count": len(list(data.get("decisions", []) or [])),
    }


def sanitize_typed_context_for_durable_write(payload: Any) -> Dict[str, Any]:
    data = normalize_typed_context(payload)
    gate = durable_decision_evidence(data)
    if gate["supported"]:
        return data
    sanitized = dict(data)
    sanitized["decisions"] = []
    return sanitized


def typed_context_to_searchable_text(payload: Any) -> str:
    data = normalize_typed_context(payload)
    parts: List[str] = [
        data["summary"],
        data["goal"],
        data["status"],
        " ".join(data["decisions"]),
        " ".join(data["constraints"]),
        " ".join(data["blockers"]),
        " ".join(data["next_actions"]),
        " ".join(data["questions"]),
        " ".join(data["evidence"]),
        " ".join(data["replay"]),
        " ".join(data["decision_reversal_conditions"]),
        " ".join(data["waiting_on"]),
        " ".join(data["assumptions"]),
        " ".join(data["modified_files"]),
        " ".join(data["change_scope"]),
        " ".join(data["key_changes"]),
        data["verification_subject"],
        data["verification_command"],
        data["verification_result"],
        data["verification_status"],
        data["failure_fingerprint"],
        " ".join(data["rollback_notes"]),
        data["rollback_trigger"],
        data["rollback_target"],
        " ".join(data["topics"]),
        " ".join(data["keywords"]),
        " ".join(data["entities"]),
        " ".join(data["tech_points"]),
        data["code_pattern"],
        data["pitfall_record"],
        data["applicable_scene"],
        data["project"],
    ]
    return " ".join(part for part in parts if _safe_str(part))
