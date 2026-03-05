#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def make_trace_id(prefix: str = "tr") -> str:
    ts = int(now_utc().timestamp() * 1000)
    salt = hashlib.sha1(f"{ts}:{os.getpid()}".encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{ts}_{salt}"


def stable_hash(value: str, length: int = 12) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:length]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n")
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def confidence_to_score(value: Any) -> float:
    if isinstance(value, (int, float)):
        score = float(value)
        if score > 1.0:
            score = score / 100.0
        return max(0.0, min(1.0, score))

    text = str(value or "").strip().lower()
    mapping = {
        "high": 0.9,
        "h": 0.9,
        "高": 0.9,
        "medium": 0.65,
        "med": 0.65,
        "m": 0.65,
        "中": 0.65,
        "low": 0.35,
        "l": 0.35,
        "低": 0.35,
    }
    return mapping.get(text, 0.5)


def score_to_confidence_label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def sanitize_slug(value: str, fallback: str = "unknown") -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\-_]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or fallback


def safe_title(value: str, fallback: str = "Untitled", max_len: int = 80) -> str:
    text = (value or "").strip().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    if not text:
        return fallback
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def load_policy(policy_path: str | None = None) -> dict[str, Any]:
    root = workspace_root()
    target = Path(policy_path) if policy_path else (root / "config" / "knowledge-pipeline" / "policy.v1.json")
    if not target.is_absolute():
        target = (root / target).resolve()
    data = load_json(target, {})
    if not isinstance(data, dict):
        raise ValueError(f"invalid policy json: {target}")
    data.setdefault("paths", {})
    data.setdefault("classification", {})
    data.setdefault("limits", {})
    return data


def resolve_path(path_value: str) -> Path:
    p = Path(os.path.expanduser(path_value))
    if p.is_absolute():
        return p
    return (workspace_root() / p).resolve()


def ensure_pipeline_dirs(policy: dict[str, Any]) -> dict[str, Path]:
    paths = policy.get("paths", {})
    resolved = {
        "inbox_raw": resolve_path(paths.get("inbox_raw", "Obsidian/00_Inbox/raw")),
        "inbox_normalized": resolve_path(paths.get("inbox_normalized", "Obsidian/00_Inbox/normalized")),
        "cards_root": resolve_path(paths.get("cards_root", "Obsidian/10_Cards")),
        "moc_root": resolve_path(paths.get("moc_root", "Obsidian/20_MOC")),
        "projects_reports": resolve_path(paths.get("projects_reports", "Obsidian/30_Projects/_reports")),
        "playbooks_root": resolve_path(paths.get("playbooks_root", "Obsidian/40_Playbooks")),
        "archive_root": resolve_path(paths.get("archive_root", "Obsidian/90_Archive")),
        "metrics_root": resolve_path(paths.get("metrics_root", "logs/knowledge-pipeline")),
    }
    for v in resolved.values():
        v.mkdir(parents=True, exist_ok=True)
    return resolved


def classify_text(text: str, policy: dict[str, Any]) -> tuple[str, str, int]:
    t = normalize_text(text)
    cls = policy.get("classification", {})
    domain_keywords = cls.get("domain_keywords", {})
    action_keywords = cls.get("action_keywords", {})

    def score_map(keyword_map: dict[str, Iterable[str]], default_key: str) -> tuple[str, int]:
        best_key = default_key
        best_score = -1
        for key, kws in keyword_map.items():
            score = 0
            for kw in kws:
                kw_norm = normalize_text(str(kw))
                if kw_norm and kw_norm in t:
                    score += 1
            if score > best_score:
                best_key = key
                best_score = score
        return best_key, max(best_score, 0)

    domain, domain_score = score_map(domain_keywords, cls.get("default_domain", "ops"))
    action, action_score = score_map(action_keywords, cls.get("default_action", "summarize"))
    return domain, action, domain_score + action_score


def render_tags(tags: list[str]) -> str:
    quoted = [f"'{t}'" for t in tags]
    return "[" + ", ".join(quoted) + "]"


def emit_metric(
    metrics_root: Path,
    stage: str,
    trace_id: str,
    duration_ms: int,
    success: bool,
    tokens: int = 0,
    error_class: str = "",
    extras: dict[str, Any] | None = None,
) -> Path:
    payload = {
        "date": date.today().isoformat(),
        "trace_id": trace_id,
        "stage": stage,
        "duration_ms": int(max(0, duration_ms)),
        "tokens": int(max(0, tokens)),
        "success": bool(success),
        "error_class": error_class,
        "ts": now_iso(),
    }
    if extras:
        payload.update(extras)
    metric_path = metrics_root / f"metrics-{date.today().isoformat()}.jsonl"
    append_jsonl(metric_path, payload)
    return metric_path


def read_markdown_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    front = content[4:end]
    body = content[end + 5 :]
    meta: dict[str, Any] = {}
    for raw in front.splitlines():
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            items = [i.strip().strip("\"'") for i in v[1:-1].split(",") if i.strip()]
            meta[k] = items
        else:
            meta[k] = v.strip("\"'")
    return meta, body.lstrip("\n")


def dump_frontmatter(meta: dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            values = ", ".join([f"'{x}'" for x in v])
            lines.append(f"{k}: [{values}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def parse_iso_week(dt: datetime | None = None) -> tuple[int, int]:
    now = dt or now_utc()
    year, week, _ = now.isocalendar()
    return year, week
