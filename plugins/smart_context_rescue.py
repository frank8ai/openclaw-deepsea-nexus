"""
Shared rescue helpers for SmartContext compression fallback.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from . import smart_context_text


DEFAULT_DECISION_KEYWORDS = list(smart_context_text.DECISION_KEYWORDS)
GOAL_PREFIXES = ("goal", "objective", "目标", "当前目标", "目的")
STATUS_PREFIXES = ("status", "state", "phase", "状态", "阶段")
NEXT_PREFIXES = ("next", "todo", "next step", "next action", "下一步", "待办", "后续")
CONSTRAINT_PREFIXES = ("constraint", "constraints", "约束", "限制")
BLOCKER_PREFIXES = ("blocker", "blockers", "blocked", "risk", "risks", "阻塞", "卡点", "风险")
EVIDENCE_PREFIXES = (
    "evidence",
    "evidence pointer",
    "log",
    "logs",
    "path",
    "paths",
    "file",
    "files",
    "artifact",
    "artifacts",
    "证据",
    "日志",
    "路径",
    "文件",
    "报告",
)
REPLAY_PREFIXES = ("replay", "repro", "repro_entry", "command", "cmd", "复现", "重放", "命令")
COMMAND_PREFIXES = (
    "python",
    "python3",
    "pytest",
    "bash",
    "sh",
    "node",
    "npm",
    "pnpm",
    "yarn",
    "uv",
    "openclaw",
    "git",
    "make",
)
FILE_EXTENSIONS = (".py", ".md", ".json", ".yaml", ".yml", ".txt", ".log", ".sh", ".js", ".ts", ".tsx", ".sql")
MAX_ITEM_LENGTH = 220


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for item in items:
        cleaned = (item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def _normalized_lines(conversation: str) -> List[str]:
    lines: List[str] = []
    for raw in (conversation or "").splitlines():
        line = raw.strip().strip("`").strip()
        line = line.lstrip("-*• ").strip()
        if not line or line == "```":
            continue
        lines.append(line[:MAX_ITEM_LENGTH])
    return lines


def _extract_prefixed_items(lines: List[str], prefixes: tuple[str, ...], *, max_items: int = 4) -> List[str]:
    matches: List[str] = []
    for line in lines:
        lowered = line.lower()
        for prefix in prefixes:
            prefix_lower = prefix.lower()
            for separator in (":", "："):
                token = f"{prefix_lower}{separator}"
                if not lowered.startswith(token):
                    continue
                value = line[len(prefix) + 1 :].strip()
                if value:
                    matches.append(value[:MAX_ITEM_LENGTH])
                break
        if len(_dedupe(matches)) >= max(1, int(max_items)):
            break
    return _dedupe(matches)[: max(1, int(max_items))]


def _extract_prefixed_first(lines: List[str], prefixes: tuple[str, ...]) -> str:
    matches = _extract_prefixed_items(lines, prefixes, max_items=1)
    return matches[0] if matches else ""


def _extract_keyword_lines(lines: List[str], keywords: tuple[str, ...], *, max_items: int = 4) -> List[str]:
    matches: List[str] = []
    for line in lines:
        lowered = line.lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            matches.append(line[:MAX_ITEM_LENGTH])
        if len(_dedupe(matches)) >= max(1, int(max_items)):
            break
    return _dedupe(matches)[: max(1, int(max_items))]


def _looks_like_command(line: str) -> bool:
    parts = line.split()
    return bool(parts) and parts[0].lower() in COMMAND_PREFIXES and len(parts) >= 2


def _extract_shell_commands(lines: List[str], *, max_items: int = 2) -> List[str]:
    commands = [line[:MAX_ITEM_LENGTH] for line in lines if _looks_like_command(line)]
    return _dedupe(commands)[: max(1, int(max_items))]


def _extract_file_lines(lines: List[str], *, max_items: int = 4) -> List[str]:
    matches: List[str] = []
    for line in lines:
        if _looks_like_command(line):
            continue
        if _canonical_item(line, REPLAY_PREFIXES) != line.strip():
            continue
        if "/" in line or any(ext in line for ext in FILE_EXTENSIONS):
            matches.append(line[:MAX_ITEM_LENGTH])
        if len(_dedupe(matches)) >= max(1, int(max_items)):
            break
    return _dedupe(matches)[: max(1, int(max_items))]


def _canonical_item(item: str, prefixes: tuple[str, ...] = ()) -> str:
    cleaned = (item or "").strip()
    lowered = cleaned.lower()
    for prefix in prefixes:
        prefix_lower = prefix.lower()
        for separator in (":", "："):
            token = f"{prefix_lower}{separator}"
            if lowered.startswith(token):
                return cleaned[len(prefix) + 1 :].strip()
    return cleaned


def _merge_items(primary: List[str], secondary: List[str], *, max_items: int, prefixes: tuple[str, ...] = ()) -> List[str]:
    merged: List[str] = []
    seen = set()
    for item in (primary or []) + (secondary or []):
        canonical = _canonical_item(item, prefixes)
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        merged.append(canonical)
        if len(merged) >= max(1, int(max_items)):
            break
    return merged


def collect_rescue_updates(
    conversation: str,
    *,
    rescue_gold: bool,
    rescue_decisions: bool,
    rescue_next_actions: bool,
    rescue_goal: bool = True,
    rescue_status: bool = True,
    rescue_constraints: bool = True,
    rescue_blockers: bool = True,
    rescue_evidence: bool = True,
    rescue_replay: bool = True,
    decision_keywords: Optional[List[str]] = None,
    context_before: int = 30,
    context_after: int = 70,
    question_min_length: int = 6,
) -> Dict[str, Any]:
    conversation = conversation or ""
    lines = _normalized_lines(conversation)
    updates: Dict[str, Any] = {
        "current_goal": "",
        "current_status": "",
        "decisions": [],
        "constraints": [],
        "blockers": [],
        "next_actions": [],
        "open_questions": [],
        "evidence_pointers": [],
        "replay_commands": [],
    }

    if rescue_goal:
        updates["current_goal"] = _extract_prefixed_first(lines, GOAL_PREFIXES)

    if rescue_status:
        updates["current_status"] = _extract_prefixed_first(lines, STATUS_PREFIXES)

    if rescue_gold:
        gold_matches = re.findall(r"#GOLD[:\s]*(.+?)(?:\n|$)", conversation)
        updates["decisions"] = _dedupe(gold_matches)

    if rescue_decisions:
        decision_blocks = smart_context_text.extract_decision_blocks(conversation, max_items=4)
        decision_contexts: List[str] = []
        for keyword in decision_keywords or DEFAULT_DECISION_KEYWORDS:
            if keyword not in conversation:
                continue
            idx = conversation.find(keyword)
            if idx == -1:
                continue
            context = conversation[max(0, idx - int(context_before)) : idx + int(context_after)].strip()
            if context:
                decision_contexts.append(context[:MAX_ITEM_LENGTH])
        updates["decisions"] = _merge_items(
            updates["decisions"],
            decision_blocks + decision_contexts,
            max_items=4,
        )

    if rescue_next_actions:
        next_actions = _extract_prefixed_items(lines, NEXT_PREFIXES, max_items=4)
        next_actions = _merge_items(
            next_actions,
            smart_context_text.extract_actions(conversation, max_items=4),
            max_items=4,
            prefixes=NEXT_PREFIXES,
        )
        updates["next_actions"] = next_actions
        question_matches = re.findall(r"[?？](.+?)(?:\n|$)", conversation)
        updates["open_questions"] = _dedupe(
            [match.strip() for match in question_matches if len(match.strip()) >= int(question_min_length)]
        )

    if rescue_constraints:
        updates["constraints"] = _merge_items(
            _extract_prefixed_items(lines, CONSTRAINT_PREFIXES, max_items=4),
            _extract_keyword_lines(lines, ("必须", "不能", "不要", "兼容", "只读", "不该破坏"), max_items=4),
            max_items=4,
            prefixes=CONSTRAINT_PREFIXES,
        )

    if rescue_blockers:
        updates["blockers"] = _merge_items(
            _extract_prefixed_items(lines, BLOCKER_PREFIXES, max_items=4),
            _extract_keyword_lines(lines, ("卡住", "阻塞", "失败", "风险", "缺少", "报错", "未通过"), max_items=4),
            max_items=4,
            prefixes=BLOCKER_PREFIXES,
        )

    if rescue_evidence:
        evidence_lines = _merge_items(
            _extract_prefixed_items(lines, EVIDENCE_PREFIXES, max_items=4),
            _extract_file_lines(lines, max_items=4),
            max_items=4,
            prefixes=EVIDENCE_PREFIXES,
        )
        entity_refs = [
            item
            for item in smart_context_text.extract_key_entities(conversation, limit=4)
            if "/" in item or any(ext in item for ext in FILE_EXTENSIONS)
        ]
        updates["evidence_pointers"] = _merge_items(evidence_lines, entity_refs, max_items=4)

    if rescue_replay:
        updates["replay_commands"] = _merge_items(
            _extract_prefixed_items(lines, REPLAY_PREFIXES, max_items=2),
            _extract_shell_commands(lines, max_items=2),
            max_items=2,
            prefixes=REPLAY_PREFIXES,
        )

    return updates


def apply_rescue_updates(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, int]:
    state = state if isinstance(state, dict) else {}
    result = {
        "decisions_rescued": 0,
        "goal_rescued": 0,
        "status_rescued": 0,
        "constraints_rescued": 0,
        "blockers_rescued": 0,
        "next_actions_rescued": 0,
        "goals_rescued": 0,
        "open_questions_rescued": 0,
        "questions_rescued": 0,
        "evidence_rescued": 0,
        "replay_rescued": 0,
    }

    scalar_mapping = {
        "current_goal": "goal_rescued",
        "current_status": "status_rescued",
    }
    for key, count_key in scalar_mapping.items():
        value = str(updates.get(key, "") or "").strip()
        if not value or state.get(key) == value:
            continue
        state[key] = value
        result[count_key] += 1

    list_mapping = {
        "decisions": "decisions_rescued",
        "constraints": "constraints_rescued",
        "blockers": "blockers_rescued",
        "next_actions": "next_actions_rescued",
        "open_questions": "open_questions_rescued",
        "evidence_pointers": "evidence_rescued",
        "replay_commands": "replay_rescued",
    }
    for key, count_key in list_mapping.items():
        bucket = state.setdefault(key, [])
        if not isinstance(bucket, list):
            bucket = [str(bucket)] if bucket else []
            state[key] = bucket
        for item in updates.get(key, []):
            if item in bucket:
                continue
            bucket.append(item)
            result[count_key] += 1

    result["goals_rescued"] = result["next_actions_rescued"]
    result["questions_rescued"] = result["open_questions_rescued"]
    return result
