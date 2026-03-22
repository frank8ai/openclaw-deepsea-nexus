"""
Periodic Codex history/session ingestion for zero-intrusion local memory capture.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..memory_v5 import MemoryV5Service
from ..runtime_paths import resolve_codex_home, resolve_workspace_base

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _clean_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _sha1_text(text: str) -> str:
    return hashlib.sha1(str(text or "").encode("utf-8")).hexdigest()


def _read_json_lines(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except Exception:
        return []
    return rows


def resolve_codex_periodic_ingest_workspace_base(config: Optional[Dict[str, Any]] = None) -> str:
    cfg = config if isinstance(config, dict) else {}
    ingest_cfg = cfg.get("codex_periodic_ingest", {}) if isinstance(cfg.get("codex_periodic_ingest", {}), dict) else {}
    override = str(ingest_cfg.get("workspace_base") or "").strip()
    if override:
        return str(Path(override).expanduser())
    configured = resolve_workspace_base(cfg, allow_nexus_base=True, default="")
    configured = str(Path(configured).expanduser()) if configured else ""
    openclaw_home = str(Path(os.path.expanduser("~/.openclaw")))
    if configured and ".openclaw" not in configured.lower():
        return configured
    if os.path.exists(openclaw_home):
        return configured or str(Path(openclaw_home) / "workspace")
    codex_home = str(Path(ingest_cfg.get("codex_home") or resolve_codex_home()).expanduser())
    return str(Path(codex_home) / "deepsea-nexus-workspace")


def _resolve_codex_periodic_ingest_log_path(
    config: Optional[Dict[str, Any]],
    filename: str,
) -> Optional[str]:
    base_path = resolve_codex_periodic_ingest_workspace_base(config)
    if not base_path:
        return None
    try:
        log_dir = Path(base_path).expanduser() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir / filename)
    except Exception:
        return None


def resolve_codex_periodic_ingest_state_path(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    cfg = config if isinstance(config, dict) else {}
    ingest_cfg = cfg.get("codex_periodic_ingest", {}) if isinstance(cfg.get("codex_periodic_ingest", {}), dict) else {}
    override = str(ingest_cfg.get("state_path") or "").strip()
    if override:
        return str(Path(override).expanduser())
    return _resolve_codex_periodic_ingest_log_path(cfg, "codex_periodic_ingest_state.json")


def resolve_codex_periodic_ingest_metrics_path(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    cfg = config if isinstance(config, dict) else {}
    ingest_cfg = cfg.get("codex_periodic_ingest", {}) if isinstance(cfg.get("codex_periodic_ingest", {}), dict) else {}
    override = str(ingest_cfg.get("metrics_path") or "").strip()
    if override:
        return str(Path(override).expanduser())
    return _resolve_codex_periodic_ingest_log_path(cfg, "codex_periodic_ingest_metrics.log")


def read_codex_periodic_ingest_metrics_summary(metrics_path: Optional[str]) -> Dict[str, Any]:
    path = str(metrics_path or "").strip()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in reversed(fh.readlines()[-50:]):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    return payload
    except Exception:
        return {}
    return {}


class CodexPeriodicIngestPlugin(NexusPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = PluginMetadata(
            name="codex_periodic_ingest",
            version="1.0.0",
            description="Zero-intrusion periodic Codex session/history ingest",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self._config: Dict[str, Any] = {}
        self._enabled = True
        self._codex_home = ""
        self._workspace_base = ""
        self._metrics_path: Optional[str] = None
        self._state_path: Optional[str] = None
        self._mem_v5_service: Optional[MemoryV5Service] = None
        self._max_session_messages = 12
        self._max_history_lines = 50
        self._source_sessions = True
        self._source_history = True
        self._state: Dict[str, Any] = {"sessions": {}, "history": {}, "last_scan": {}}
        self._stats: Dict[str, Any] = {
            "runs": 0,
            "stored_documents": 0,
            "session_documents": 0,
            "history_documents": 0,
            "skipped": 0,
            "last_scan": {},
        }

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config if isinstance(config, dict) else {}
        ingest_cfg = self._config.get("codex_periodic_ingest", {}) if isinstance(self._config.get("codex_periodic_ingest", {}), dict) else {}
        self._enabled = bool(ingest_cfg.get("enabled", True))
        self._codex_home = str(
            Path(
                ingest_cfg.get("codex_home") or resolve_codex_home()
            ).expanduser()
        )
        self._workspace_base = resolve_codex_periodic_ingest_workspace_base(self._config)
        self._metrics_path = resolve_codex_periodic_ingest_metrics_path(self._build_runtime_config())
        self._state_path = resolve_codex_periodic_ingest_state_path(self._build_runtime_config())
        self._max_session_messages = max(1, _safe_int(ingest_cfg.get("max_session_messages"), 12))
        self._max_history_lines = max(1, _safe_int(ingest_cfg.get("max_history_lines"), 50))
        sources_cfg = ingest_cfg.get("sources", {}) if isinstance(ingest_cfg.get("sources", {}), dict) else {}
        self._source_sessions = _safe_bool(sources_cfg.get("sessions"), True)
        self._source_history = _safe_bool(sources_cfg.get("history"), True)
        memory_cfg = copy.deepcopy(self._build_runtime_config())
        memory_cfg.setdefault("memory_v5", {})
        memory_cfg["memory_v5"]["async_ingest"] = False
        self._mem_v5_service = MemoryV5Service(memory_cfg)
        self._state = self._load_state()
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True

    def get_health_summary(self) -> Dict[str, Any]:
        return {
            "enabled": self._enabled,
            "codex_home": self._codex_home,
            "workspace_base": self._workspace_base,
            "state_path": self._state_path or "",
            "metrics_path": self._metrics_path or "",
            "runs": int(self._stats.get("runs", 0)),
            "stored_documents": int(self._stats.get("stored_documents", 0)),
            "session_documents": int(self._stats.get("session_documents", 0)),
            "history_documents": int(self._stats.get("history_documents", 0)),
            "skipped": int(self._stats.get("skipped", 0)),
            "last_scan": dict(self._stats.get("last_scan", {}) or {}),
            "last_metrics": read_codex_periodic_ingest_metrics_summary(self._metrics_path),
        }

    def scan_once(self) -> Dict[str, Any]:
        if not self._enabled:
            payload = {
                "enabled": False,
                "session_documents": 0,
                "history_documents": 0,
                "stored_documents": 0,
                "skipped": 0,
                "ts": _now_iso(),
            }
            self._stats["last_scan"] = payload
            return payload

        self._state = self._load_state()
        stored_documents = 0
        skipped = 0
        session_documents = 0
        history_documents = 0

        if self._source_sessions:
            result = self._scan_sessions()
            stored_documents += result["stored_documents"]
            skipped += result["skipped"]
            session_documents += result["session_documents"]

        if self._source_history:
            result = self._scan_history()
            stored_documents += result["stored_documents"]
            skipped += result["skipped"]
            history_documents += result["history_documents"]

        payload = {
            "enabled": True,
            "codex_home": self._codex_home,
            "workspace_base": self._workspace_base,
            "session_documents": session_documents,
            "history_documents": history_documents,
            "stored_documents": stored_documents,
            "skipped": skipped,
            "ts": _now_iso(),
        }
        self._state["last_scan"] = payload
        self._write_state()
        self._record_metric(payload)
        self._stats["runs"] = int(self._stats.get("runs", 0)) + 1
        self._stats["stored_documents"] = int(self._stats.get("stored_documents", 0)) + stored_documents
        self._stats["session_documents"] = int(self._stats.get("session_documents", 0)) + session_documents
        self._stats["history_documents"] = int(self._stats.get("history_documents", 0)) + history_documents
        self._stats["skipped"] = int(self._stats.get("skipped", 0)) + skipped
        self._stats["last_scan"] = payload
        return payload

    def _build_runtime_config(self) -> Dict[str, Any]:
        cfg = copy.deepcopy(self._config)
        cfg.setdefault("paths", {})
        cfg["paths"]["base"] = self._workspace_base
        return cfg

    def _load_state(self) -> Dict[str, Any]:
        path = str(self._state_path or "").strip()
        if not path or not os.path.exists(path):
            return {"sessions": {}, "history": {}, "last_scan": {}}
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return {"sessions": {}, "history": {}, "last_scan": {}}
        if not isinstance(payload, dict):
            return {"sessions": {}, "history": {}, "last_scan": {}}
        payload.setdefault("sessions", {})
        payload.setdefault("history", {})
        payload.setdefault("last_scan", {})
        return payload

    def _write_state(self) -> None:
        if not self._state_path:
            return
        path = Path(self._state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _record_metric(self, payload: Dict[str, Any]) -> None:
        if not self._metrics_path:
            return
        path = Path(self._metrics_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = dict(payload)
        record.setdefault("component", "codex_periodic_ingest")
        record.setdefault("schema_version", "5.5.0")
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _scan_sessions(self) -> Dict[str, int]:
        sessions_root = Path(self._codex_home) / "sessions"
        if not sessions_root.exists():
            return {"stored_documents": 0, "session_documents": 0, "skipped": 0}

        stored = 0
        skipped = 0
        documents = 0
        session_state = self._state.setdefault("sessions", {})
        for path in sorted(sessions_root.rglob("rollout-*.jsonl")):
            fingerprint = self._fingerprint(path)
            path_key = str(path)
            previous = session_state.get(path_key, {}) if isinstance(session_state.get(path_key), dict) else {}
            if previous.get("fingerprint") == fingerprint:
                skipped += 1
                continue
            document = self._build_session_document(path)
            if not document:
                session_state[path_key] = {"fingerprint": fingerprint, "source_id": ""}
                skipped += 1
                continue
            result = self._ingest_document(document)
            if result.get("stored"):
                stored += 1
                documents += 1
            else:
                skipped += 1
            session_state[path_key] = {
                "fingerprint": fingerprint,
                "source_id": document["source_id"],
            }
        return {"stored_documents": stored, "session_documents": documents, "skipped": skipped}

    def _scan_history(self) -> Dict[str, int]:
        history_path = Path(self._codex_home) / "history.jsonl"
        if not history_path.exists():
            return {"stored_documents": 0, "history_documents": 0, "skipped": 0}
        rows = _read_json_lines(history_path)
        history_state = self._state.setdefault("history", {})
        consumed_lines = _safe_int(history_state.get("consumed_lines"), 0)
        if len(rows) < consumed_lines:
            consumed_lines = 0
        new_rows = rows[consumed_lines:]
        history_state["consumed_lines"] = len(rows)
        history_state["fingerprint"] = self._fingerprint(history_path)
        if not new_rows:
            return {"stored_documents": 0, "history_documents": 0, "skipped": 1}

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in new_rows:
            session_id = str(row.get("session_id") or "unknown").strip() or "unknown"
            grouped.setdefault(session_id, []).append(row)

        stored = 0
        skipped = 0
        documents = 0
        for session_id, items in grouped.items():
            document = self._build_history_document(session_id, items)
            if not document:
                skipped += 1
                continue
            result = self._ingest_document(document)
            if result.get("stored"):
                stored += 1
                documents += 1
            else:
                skipped += 1
        return {"stored_documents": stored, "history_documents": documents, "skipped": skipped}

    def _fingerprint(self, path: Path) -> str:
        try:
            stat = path.stat()
        except Exception:
            return ""
        return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"

    def _build_session_document(self, path: Path) -> Optional[Dict[str, Any]]:
        rows = _read_json_lines(path)
        if not rows:
            return None
        meta: Dict[str, Any] = {}
        messages: List[Dict[str, str]] = []
        for row in rows:
            row_type = str(row.get("type") or "").strip()
            payload = row.get("payload", {}) if isinstance(row.get("payload", {}), dict) else {}
            timestamp = str(row.get("timestamp") or payload.get("timestamp") or "").strip()
            if row_type == "session_meta":
                meta = payload
                continue
            if row_type == "response_item" and payload.get("type") == "message":
                role = str(payload.get("role") or "").strip().lower()
                if role not in {"user", "assistant"}:
                    continue
                text = self._extract_message_text(payload.get("content"))
                if text:
                    messages.append({"role": role, "text": text, "timestamp": timestamp})
                continue
            if row_type == "event_msg":
                event_type = str(payload.get("type") or "").strip().lower()
                if event_type in {"user_message", "agent_message"}:
                    role = "user" if event_type == "user_message" else "assistant"
                    text = _clean_text(payload.get("message"))
                    if text:
                        messages.append({"role": role, "text": text, "timestamp": timestamp})

        if not meta and not messages:
            return None

        session_id = str(meta.get("id") or path.stem).strip() or path.stem
        recent_messages = messages[-self._max_session_messages :]
        digest_seed = json.dumps(
            {
                "session_id": session_id,
                "message_count": len(recent_messages),
                "messages": recent_messages,
                "meta": {
                    "cwd": meta.get("cwd", ""),
                    "originator": meta.get("originator", ""),
                    "source": meta.get("source", ""),
                    "model_provider": meta.get("model_provider", ""),
                },
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        digest = _sha1_text(digest_seed)[:12]
        title = f"Codex Session {session_id}"
        lines = [
            f"session_id: {session_id}",
            f"cwd: {meta.get('cwd', '')}",
            f"originator: {meta.get('originator', '')}",
            f"source: {meta.get('source', '')}",
            f"model_provider: {meta.get('model_provider', '')}",
            "",
        ]
        for item in recent_messages:
            stamp = f"[{item['timestamp']}] " if item.get("timestamp") else ""
            lines.append(f"{stamp}{item['role']}: {item['text']}")
        content = "\n".join([line for line in lines if line is not None]).strip()
        metadata = {
            "kind": "codex_session",
            "source_path": str(path),
            "session_id": session_id,
            "cwd": str(meta.get("cwd") or ""),
            "originator": str(meta.get("originator") or ""),
            "source": str(meta.get("source") or ""),
            "model_provider": str(meta.get("model_provider") or ""),
            "message_count": len(recent_messages),
            "source_runtime": "codex",
            "captured_at": _now_iso(),
        }
        return {
            "title": title,
            "content": content,
            "tags": ["codex", "codex_session"],
            "kind": "codex_session",
            "metadata": metadata,
            "source_id": f"codex_session:{session_id}:{digest}",
        }

    def _build_history_document(self, session_id: str, rows: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not rows:
            return None
        recent_rows = list(rows)[-self._max_history_lines :]
        texts = []
        for row in recent_rows:
            text = _clean_text(row.get("text"))
            if not text:
                continue
            ts = str(row.get("ts") or "").strip()
            prefix = f"[{ts}] " if ts else ""
            texts.append(prefix + text)
        if not texts:
            return None
        digest = _sha1_text(json.dumps(recent_rows, ensure_ascii=False, sort_keys=True))[:12]
        metadata = {
            "kind": "codex_history",
            "session_id": session_id,
            "line_count": len(texts),
            "source_path": str(Path(self._codex_home) / "history.jsonl"),
            "source_runtime": "codex",
            "captured_at": _now_iso(),
        }
        return {
            "title": f"Codex History {session_id}",
            "content": "\n".join(texts),
            "tags": ["codex", "codex_history"],
            "kind": "codex_history",
            "metadata": metadata,
            "source_id": f"codex_history:{session_id}:{digest}",
        }

    def _extract_message_text(self, payload: Any) -> str:
        if not isinstance(payload, list):
            return ""
        parts: List[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            content_type = str(item.get("type") or "").strip().lower()
            if content_type not in {"input_text", "output_text", "text"}:
                continue
            text = _clean_text(item.get("text"))
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    def _ingest_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        if self._mem_v5_service is None:
            return {"stored": False}
        try:
            return self._mem_v5_service.ingest_document(
                title=document["title"],
                content=document["content"],
                tags=list(document.get("tags", []) or []),
                source_id=str(document.get("source_id") or ""),
                metadata=dict(document.get("metadata", {}) or {}),
                kind=str(document.get("kind") or "document"),
            )
        except Exception as exc:
            logger.warning("codex_periodic_ingest degraded: %s", exc)
            return {"stored": False, "error": str(exc)}
