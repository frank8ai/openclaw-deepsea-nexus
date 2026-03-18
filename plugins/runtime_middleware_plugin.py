"""
Runtime middleware plugin for tool-output normalization and RTK-style compression.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..memory_v5 import MemoryScope, MemoryV5Service
from ..plugins.context_engine_runtime import ContextEngineRuntimeState
from ..runtime_paths import resolve_log_path

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r\n", "\n").replace("\r", "\n")


def _normalize_args(args: Any) -> List[str]:
    if isinstance(args, (list, tuple)):
        return [str(item).strip() for item in args if str(item).strip()]
    if args is None:
        return []
    raw = str(args).strip()
    if not raw:
        return []
    return [part for part in re.split(r"\s+", raw) if part]


@dataclass
class ToolEvent:
    tool_name: str
    args: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    cwd: str = ""
    timestamp: str = field(default_factory=_now_iso)
    source_runtime: str = "openclaw"
    scope: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = ""

    def normalized(self) -> "ToolEvent":
        tool_name = str(self.tool_name or "").strip() or "shell"
        event_id = str(self.event_id or "").strip()
        if not event_id:
            seed = "|".join([tool_name, " ".join(self.args), self.cwd, self.timestamp, str(self.exit_code)])
            event_id = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
        return ToolEvent(
            tool_name=tool_name,
            args=_normalize_args(self.args),
            stdout=_clean_text(self.stdout),
            stderr=_clean_text(self.stderr),
            exit_code=_safe_int(self.exit_code),
            duration_ms=max(0, _safe_int(self.duration_ms)),
            cwd=str(self.cwd or "").strip(),
            timestamp=str(self.timestamp or "").strip() or _now_iso(),
            source_runtime=str(self.source_runtime or "").strip() or "openclaw",
            scope={str(key): str(value) for key, value in (self.scope or {}).items() if str(key).strip()},
            metadata=dict(self.metadata or {}),
            event_id=event_id,
        )

    def combined_output(self) -> str:
        parts = [part for part in [self.stdout, self.stderr] if part.strip()]
        return "\n".join(parts).strip()


@dataclass
class CompressedToolEvent:
    event_id: str
    tool_name: str
    event_kind: str
    summary: str
    structured: Dict[str, Any]
    token_before: int
    token_after: int
    reduction_ratio: float
    salience_score: float
    compression_mode: str
    warnings: List[str] = field(default_factory=list)
    evidence_ref: str = ""
    source_runtime: str = "openclaw"


class ToolOutputTransformer:
    def transform(self, event: ToolEvent) -> CompressedToolEvent:
        raise NotImplementedError


class RtkTransformer(ToolOutputTransformer):
    ERROR_PATTERNS = (
        "error",
        "exception",
        "failed",
        "failure",
        "traceback",
        "panic:",
        "fatal",
        "undefined",
        "assertionerror",
    )

    def __init__(self) -> None:
        self._token_runtime = ContextEngineRuntimeState()

    def estimate_tokens(self, text: str) -> int:
        return self._token_runtime.estimate_tokens(text)

    def transform(self, event: ToolEvent) -> CompressedToolEvent:
        event = event.normalized()
        combined = event.combined_output()
        event_kind = self._classify_event_kind(event)
        structured, summary, warnings, mode = self._compress(event, event_kind)
        token_before = self.estimate_tokens(combined)
        token_after = self.estimate_tokens(summary + "\n" + json.dumps(structured, ensure_ascii=False))
        reduction_ratio = 0.0
        if token_before > 0:
            reduction_ratio = max(0.0, min(1.0, (token_before - token_after) / float(token_before)))
        salience = self._score_salience(event, event_kind, combined, structured)
        return CompressedToolEvent(
            event_id=event.event_id,
            tool_name=event.tool_name,
            event_kind=event_kind,
            summary=summary,
            structured=structured,
            token_before=token_before,
            token_after=token_after,
            reduction_ratio=round(reduction_ratio, 3),
            salience_score=round(salience, 3),
            compression_mode=mode,
            warnings=warnings,
            source_runtime=event.source_runtime,
        )

    def _classify_event_kind(self, event: ToolEvent) -> str:
        tool = event.tool_name.lower()
        args = " ".join(event.args).lower()
        command = f"{tool} {args}".strip()
        if tool == "git" and "diff" in args:
            return "git_diff"
        if tool == "git":
            return "git"
        if tool in {"rg", "grep", "findstr"} or " rg " in f" {command} " or " grep " in f" {command} ":
            return "grep"
        if any(token in command for token in ("pytest", "unittest", "go test", "cargo test", "npm test", "pnpm test", "yarn test")):
            return "test"
        if any(token in command for token in ("eslint", "ruff", "flake8", "mypy", "pylint", "tsc", "golangci-lint")):
            return "lint"
        if any(token in command for token in ("go build", "cargo build", "npm run build", "pnpm build", "yarn build", "make", "cmake")):
            return "build"
        if tool in {"docker", "podman", "kubectl"}:
            return "container"
        if tool in {"curl", "wget", "http", "ping"}:
            return "network"
        return "shell"

    def _compress(self, event: ToolEvent, event_kind: str) -> tuple[Dict[str, Any], str, List[str], str]:
        lines = [line.strip() for line in event.combined_output().split("\n") if line.strip()]
        if not lines:
            summary = f"{event.tool_name} exited with code {event.exit_code} and produced no output."
            return {"lines": [], "exit_code": event.exit_code}, summary, [], "empty"
        if event_kind == "git_diff":
            return self._compress_git_diff(event, lines)
        if event_kind == "grep":
            return self._compress_grep(event, lines)
        if event_kind in {"test", "lint"}:
            return self._compress_failures(event, lines, event_kind)
        if event_kind in {"build", "container", "network"}:
            return self._compress_operational(event, lines, event_kind)
        return self._compress_generic(event, lines)

    def _compress_git_diff(self, event: ToolEvent, lines: List[str]) -> tuple[Dict[str, Any], str, List[str], str]:
        files: List[str] = []
        additions = 0
        deletions = 0
        hunks = 0
        preview: List[str] = []
        for line in lines:
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    files.append(parts[2].replace("a/", ""))
            elif line.startswith("@@"):
                hunks += 1
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
                if len(preview) < 6:
                    preview.append(line[:180])
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
                if len(preview) < 6:
                    preview.append(line[:180])
        file_preview = ", ".join(files[:4]) if files else "unknown files"
        summary = f"git diff touched {len(files)} file(s) ({file_preview}); +{additions}/-{deletions} line changes across {hunks} hunks."
        structured = {
            "files": files[:20],
            "file_count": len(files),
            "additions": additions,
            "deletions": deletions,
            "hunks": hunks,
            "preview": preview,
            "exit_code": event.exit_code,
        }
        warnings = ["git diff file list truncated"] if len(files) > 20 else []
        return structured, summary, warnings, "git_diff"

    def _compress_grep(self, event: ToolEvent, lines: List[str]) -> tuple[Dict[str, Any], str, List[str], str]:
        unique: List[str] = []
        seen = set()
        for line in lines:
            trimmed = line[:220]
            if trimmed in seen:
                continue
            seen.add(trimmed)
            unique.append(trimmed)
        summary = f"{event.tool_name} returned {len(lines)} matching line(s); {len(unique[:10])} unique preview line(s) kept."
        structured = {"matches": unique[:10], "match_count": len(lines), "unique_count": len(unique), "exit_code": event.exit_code}
        warnings = ["grep matches truncated"] if len(unique) > 10 else []
        return structured, summary, warnings, "grep"

    def _compress_failures(self, event: ToolEvent, lines: List[str], event_kind: str) -> tuple[Dict[str, Any], str, List[str], str]:
        failures: List[str] = []
        tail: List[str] = []
        for line in lines:
            lowered = line.lower()
            if any(pattern in lowered for pattern in self.ERROR_PATTERNS) and len(failures) < 12:
                failures.append(line[:220])
            if len(tail) < 8:
                tail.append(line[:220])
            else:
                tail = tail[1:] + [line[:220]]
        selected = failures or tail
        summary = f"{event_kind} run exited with code {event.exit_code}; captured {len(selected)} notable line(s) from {len(lines)} total line(s)."
        structured = {"failures": selected, "failure_count": len(failures), "line_count": len(lines), "exit_code": event.exit_code}
        warnings = [f"{event_kind} failures truncated"] if len(failures) > 12 else []
        return structured, summary, warnings, event_kind

    def _compress_operational(self, event: ToolEvent, lines: List[str], event_kind: str) -> tuple[Dict[str, Any], str, List[str], str]:
        unique: List[str] = []
        seen = set()
        for line in lines:
            trimmed = line[:220]
            if trimmed in seen:
                continue
            seen.add(trimmed)
            unique.append(trimmed)
        kept = unique[:8]
        summary = f"{event_kind} command exited with code {event.exit_code}; {len(lines)} line(s) reduced to {len(kept)} operational signal line(s)."
        structured = {"signals": kept, "line_count": len(lines), "exit_code": event.exit_code}
        warnings = [f"{event_kind} output truncated"] if len(unique) > 8 else []
        return structured, summary, warnings, event_kind

    def _compress_generic(self, event: ToolEvent, lines: List[str]) -> tuple[Dict[str, Any], str, List[str], str]:
        unique: List[str] = []
        seen = set()
        for line in lines:
            trimmed = line[:220]
            if trimmed in seen:
                continue
            seen.add(trimmed)
            unique.append(trimmed)
        kept = unique[:8]
        summary = f"{event.tool_name} exited with code {event.exit_code}; {len(lines)} line(s) reduced to {len(kept)} concise signal line(s)."
        structured = {"signals": kept, "line_count": len(lines), "exit_code": event.exit_code}
        warnings = ["generic output truncated"] if len(unique) > 8 else []
        return structured, summary, warnings, "generic"

    def _score_salience(self, event: ToolEvent, event_kind: str, combined: str, structured: Dict[str, Any]) -> float:
        lowered = combined.lower()
        score = 0.15
        if event.exit_code != 0:
            score += 0.45
        if event_kind in {"test", "lint", "build"}:
            score += 0.2
        if event_kind == "git_diff":
            score += 0.25 if structured.get("file_count", 0) > 0 else 0.0
        if any(pattern in lowered for pattern in self.ERROR_PATTERNS):
            score += 0.2
        if structured.get("failure_count", 0) > 0:
            score += 0.15
        if structured.get("file_count", 0) > 4:
            score += 0.1
        return min(1.0, score)


class OpenClawToolAdapter:
    def from_hook_context(self, context: Dict[str, Any]) -> ToolEvent:
        payload = dict(context or {})
        result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        command = str(payload.get("command") or payload.get("tool_name") or payload.get("tool") or "").strip()
        args = payload.get("args")
        if not args and command:
            args = command.split()[1:]
        tool_name = str(payload.get("tool_name") or payload.get("tool") or (command.split()[0] if command else "shell")).strip()
        scope = payload.get("scope") if isinstance(payload.get("scope"), dict) else {}
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        return ToolEvent(
            tool_name=tool_name,
            args=_normalize_args(args),
            stdout=_clean_text(payload.get("stdout") or payload.get("output") or result.get("stdout") or result.get("output")),
            stderr=_clean_text(payload.get("stderr") or result.get("stderr")),
            exit_code=_safe_int(payload.get("exit_code", result.get("exit_code", payload.get("code", 0)))),
            duration_ms=_safe_int(payload.get("duration_ms", payload.get("duration", result.get("duration_ms", 0)))),
            cwd=str(payload.get("cwd") or payload.get("workdir") or "").strip(),
            timestamp=str(payload.get("timestamp") or _now_iso()),
            source_runtime="openclaw",
            scope={str(key): str(value) for key, value in scope.items() if str(key).strip()},
            metadata=metadata,
            event_id=str(payload.get("event_id") or ""),
        ).normalized()


def read_runtime_middleware_metrics_summary(metrics_path: Optional[str]) -> Dict[str, Any]:
    path = str(metrics_path or "").strip()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = [line.strip() for line in fh.readlines() if line.strip()]
        if not lines:
            return {}
        payload = json.loads(lines[-1])
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


class RuntimeMiddlewarePlugin(NexusPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = PluginMetadata(
            name="runtime_middleware",
            version="3.0.0",
            description="RTK-style runtime middleware for tool output capture",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self._config: Dict[str, Any] = {}
        self._transformer = RtkTransformer()
        self._mem_v5_service: Optional[MemoryV5Service] = None
        self._enabled = True
        self._fail_open = True
        self._metrics_path: Optional[str] = None
        self._evidence_dir: Optional[str] = None
        self._adapter = OpenClawToolAdapter()
        self._stats: Dict[str, Any] = {
            "processed": 0,
            "stored": 0,
            "skipped": 0,
            "aggregated": 0,
            "fallbacks": 0,
            "token_before": 0,
            "token_after": 0,
            "last_event": {},
        }
        self._repeat_cache: Dict[str, Dict[str, Any]] = {}

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config if isinstance(config, dict) else {}
        middleware_cfg = self._config.get("runtime_middleware", {}) if isinstance(self._config, dict) else {}
        self._enabled = bool(middleware_cfg.get("enabled", True))
        self._fail_open = bool(middleware_cfg.get("fail_open", True))
        self._metrics_path = resolve_log_path(
            self._config,
            "runtime_middleware_metrics.log",
            allow_nexus_base=True,
            default_base=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
        if self._metrics_path:
            self._evidence_dir = os.path.join(os.path.dirname(self._metrics_path), "runtime_middleware_evidence")
            os.makedirs(self._evidence_dir, exist_ok=True)
        try:
            self._mem_v5_service = MemoryV5Service(self._config)
        except Exception as exc:
            logger.warning("runtime_middleware memory_v5 init degraded: %s", exc)
            self._mem_v5_service = None
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True

    def get_health_summary(self) -> Dict[str, Any]:
        token_before = max(0, int(self._stats.get("token_before", 0)))
        token_after = max(0, int(self._stats.get("token_after", 0)))
        saved_ratio = 0.0
        if token_before > 0:
            saved_ratio = round(max(0.0, (token_before - token_after) / float(token_before)), 3)
        return {
            "enabled": bool(self._enabled),
            "metrics_path": self._metrics_path or "",
            "processed": int(self._stats.get("processed", 0)),
            "stored": int(self._stats.get("stored", 0)),
            "skipped": int(self._stats.get("skipped", 0)),
            "aggregated": int(self._stats.get("aggregated", 0)),
            "fallbacks": int(self._stats.get("fallbacks", 0)),
            "token_before": token_before,
            "token_after": token_after,
            "saved_ratio": saved_ratio,
            "last_event": dict(self._stats.get("last_event", {}) or {}),
            "last_metrics": read_runtime_middleware_metrics_summary(self._metrics_path),
        }

    def process_openclaw_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        event = self._adapter.from_hook_context(context)
        scope = self._scope_from_context(context)
        return self.process_tool_event(event, scope=scope)

    def process_tool_event(self, event: ToolEvent | Dict[str, Any], scope: Optional[MemoryScope] = None) -> Dict[str, Any]:
        if not self._enabled:
            return {"enabled": False, "stored": False, "reason": "disabled"}

        self._stats["processed"] += 1
        normalized_event = event if isinstance(event, ToolEvent) else ToolEvent(**dict(event or {}))
        normalized_event = normalized_event.normalized()
        scope = scope or self._scope_from_context(normalized_event.scope)

        force_store = False
        try:
            compressed = self._transformer.transform(normalized_event)
        except Exception as exc:
            if not self._fail_open:
                self._record_metric({"event": "transform_failed", "error": str(exc), "tool_name": normalized_event.tool_name})
                raise
            compressed = self._fallback_transform(normalized_event, str(exc))
            self._stats["fallbacks"] += 1
            force_store = True

        self._stats["token_before"] += compressed.token_before
        self._stats["token_after"] += compressed.token_after

        decision = {"action": "store", "mode": "fallback"} if force_store else self._capture_decision(compressed)
        if decision["action"] == "skip":
            self._stats["skipped"] += 1
            self._record_metric(
                {
                    "event": "tool_event_skipped",
                    "tool_name": compressed.tool_name,
                    "event_kind": compressed.event_kind,
                    "reduction_ratio": compressed.reduction_ratio,
                    "salience_score": compressed.salience_score,
                }
            )
            return {"enabled": True, "stored": False, "reason": "low_signal"}

        if decision["action"] == "aggregate":
            self._stats["aggregated"] += 1
            self._record_metric(
                {
                    "event": "tool_event_aggregated",
                    "tool_name": compressed.tool_name,
                    "event_kind": compressed.event_kind,
                    "signature": decision["signature"],
                    "count": decision["count"],
                }
            )
            if not decision.get("flush_digest"):
                return {"enabled": True, "stored": False, "reason": "aggregated"}
            compressed = decision["flush_digest"]

        evidence_path = self._write_evidence_snapshot(normalized_event, compressed)
        compressed.evidence_ref = evidence_path
        stored = self._persist_compressed_event(compressed, scope)
        payload = {
            "event": "tool_event_stored",
            "tool_name": compressed.tool_name,
            "event_kind": compressed.event_kind,
            "token_before": compressed.token_before,
            "token_after": compressed.token_after,
            "reduction_ratio": compressed.reduction_ratio,
            "salience_score": compressed.salience_score,
            "compression_mode": compressed.compression_mode,
            "evidence_ref": evidence_path,
            "stored": bool(stored.get("stored")),
        }
        self._stats["stored"] += 1 if stored.get("stored") else 0
        self._stats["last_event"] = payload
        self._record_metric(payload)
        return stored

    def _capture_decision(self, event: CompressedToolEvent) -> Dict[str, Any]:
        cfg = self._config.get("runtime_middleware", {}) if isinstance(self._config, dict) else {}
        token_gate = cfg.get("token_gate", {}) if isinstance(cfg.get("token_gate", {}), dict) else {}
        capture_policy = cfg.get("capture_policy", {}) if isinstance(cfg.get("capture_policy", {}), dict) else {}
        min_ratio = float(token_gate.get("min_reduction_ratio", 0.15))
        high_salience = float(token_gate.get("high_salience_threshold", 0.7))
        low_salience = float(token_gate.get("low_salience_threshold", 0.35))
        digest_threshold = max(2, int(token_gate.get("digest_repeat_threshold", 3)))
        policy = capture_policy.get(event.event_kind, {}) if isinstance(capture_policy.get(event.event_kind, {}), dict) else {}
        if bool(policy.get("force_store", False)) or event.salience_score >= high_salience:
            return {"action": "store", "mode": "full" if event.reduction_ratio >= min_ratio else "light"}

        signature = hashlib.sha1(
            "|".join([event.tool_name, event.event_kind, event.summary, str(event.structured.get("exit_code", ""))]).encode("utf-8")
        ).hexdigest()[:12]
        if event.salience_score < low_salience and (event.reduction_ratio >= min_ratio or event.token_before >= 10):
            entry = self._repeat_cache.setdefault(
                signature,
                {"count": 0, "tool_name": event.tool_name, "event_kind": event.event_kind, "summary": event.summary},
            )
            entry["count"] = int(entry.get("count", 0)) + 1
            if entry["count"] < digest_threshold:
                return {"action": "aggregate", "signature": signature, "count": entry["count"], "flush_digest": None}

            digest_summary = (
                f"Repeated low-signal {event.event_kind} output from {event.tool_name} "
                f"aggregated {entry['count']} time(s); latest summary: {event.summary}"
            )
            digest_event = CompressedToolEvent(
                event_id=f"digest_{signature}",
                tool_name=event.tool_name,
                event_kind="runtime_digest",
                summary=digest_summary,
                structured={"repeat_count": entry["count"], "event_kind": event.event_kind, "latest_summary": event.summary},
                token_before=event.token_before,
                token_after=self._transformer.estimate_tokens(digest_summary) if isinstance(self._transformer, RtkTransformer) else event.token_after,
                reduction_ratio=event.reduction_ratio,
                salience_score=max(0.4, event.salience_score),
                compression_mode="digest",
                warnings=["aggregated low-signal tool output"],
                source_runtime=event.source_runtime,
            )
            self._repeat_cache.pop(signature, None)
            return {"action": "aggregate", "signature": signature, "count": digest_threshold, "flush_digest": digest_event}

        if event.reduction_ratio >= min_ratio and event.salience_score >= (low_salience + 0.1):
            return {"action": "store", "mode": "light"}
        return {"action": "skip"}

    def _persist_compressed_event(self, event: CompressedToolEvent, scope: MemoryScope) -> Dict[str, Any]:
        if self._mem_v5_service is None:
            return {"enabled": False, "stored": False, "reason": "memory_v5_unavailable"}
        try:
            content = self._build_memory_content(event)
            result = self._mem_v5_service.ingest_tool_event(
                title=f"{event.event_kind}:{event.tool_name}",
                summary=content,
                structured=event.structured,
                scope=scope,
                metadata={
                    "tool_name": event.tool_name,
                    "event_kind": event.event_kind,
                    "exit_code": event.structured.get("exit_code", 0),
                    "token_before": event.token_before,
                    "token_after": event.token_after,
                    "reduction_ratio": event.reduction_ratio,
                    "salience_score": event.salience_score,
                    "compression_mode": event.compression_mode,
                    "source_runtime": event.source_runtime,
                    "warnings": list(event.warnings),
                    "evidence_ref": event.evidence_ref,
                },
            )
            return {"enabled": True, "stored": bool(result.get("stored")), "item_id": result.get("item_id", ""), "evidence_ref": event.evidence_ref}
        except Exception as exc:
            logger.warning("runtime_middleware persist degraded: %s", exc)
            self._record_metric({"event": "tool_event_store_failed", "error": str(exc), "tool_name": event.tool_name})
            return {"enabled": True, "stored": False, "reason": str(exc)}

    def _build_memory_content(self, event: CompressedToolEvent) -> str:
        lines = [event.summary.strip()]
        for key in ("failures", "signals", "matches", "preview"):
            values = event.structured.get(key)
            if not isinstance(values, list):
                continue
            for value in values[:6]:
                text = str(value).strip()
                if text:
                    lines.append(text)
        return "\n".join([line for line in lines if line]).strip()

    def _write_evidence_snapshot(self, event: ToolEvent, compressed: CompressedToolEvent) -> str:
        if not self._evidence_dir:
            return ""
        evidence_path = os.path.join(self._evidence_dir, f"{event.event_id}.json")
        payload = {"event": asdict(event), "compressed": asdict(compressed)}
        try:
            os.makedirs(self._evidence_dir, exist_ok=True)
            with open(evidence_path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return evidence_path
        except Exception as exc:
            logger.warning("runtime_middleware evidence write degraded: %s", exc)
            return ""

    def _fallback_transform(self, event: ToolEvent, error: str) -> CompressedToolEvent:
        output = event.combined_output()
        preview = "\n".join(output.split("\n")[:8]).strip()
        token_before = self._transformer.estimate_tokens(output) if isinstance(self._transformer, RtkTransformer) else 0
        token_after = self._transformer.estimate_tokens(preview) if isinstance(self._transformer, RtkTransformer) else 0
        reduction = 0.0
        if token_before > 0:
            reduction = max(0.0, min(1.0, (token_before - token_after) / float(token_before)))
        return CompressedToolEvent(
            event_id=event.event_id,
            tool_name=event.tool_name,
            event_kind="shell",
            summary=preview or f"{event.tool_name} exited with code {event.exit_code}",
            structured={"signals": [preview] if preview else [], "exit_code": event.exit_code},
            token_before=token_before,
            token_after=token_after,
            reduction_ratio=round(reduction, 3),
            salience_score=0.75 if event.exit_code != 0 else 0.55,
            compression_mode="fallback",
            warnings=[f"transform failed: {error}"],
            source_runtime=event.source_runtime,
        )

    def _scope_from_context(self, payload: Any) -> MemoryScope:
        raw = payload if isinstance(payload, dict) else {}
        service_scope = self._mem_v5_service.scope if self._mem_v5_service is not None else MemoryScope()
        return MemoryScope(
            agent_id=str(raw.get("agent_id") or os.environ.get("OPENCLAW_AGENT_ID") or os.environ.get("CODEX_AGENT_ID") or service_scope.agent_id or "default"),
            user_id=str(raw.get("user_id") or os.environ.get("OPENCLAW_USER_ID") or os.environ.get("CODEX_USER_ID") or service_scope.user_id or "default"),
            run_id=str(raw.get("run_id") or service_scope.run_id or ""),
            app_id=str(raw.get("app_id") or service_scope.app_id or ""),
            workspace=str(raw.get("workspace") or os.environ.get("OPENCLAW_WORKSPACE") or service_scope.workspace or ""),
        ).normalized()

    def _record_metric(self, payload: Dict[str, Any]) -> None:
        if not self._metrics_path:
            return
        try:
            os.makedirs(os.path.dirname(self._metrics_path), exist_ok=True)
            record = dict(payload)
            record.setdefault("schema_version", "5.0.1")
            record.setdefault("component", "runtime_middleware")
            record.setdefault("ts", _now_iso())
            with open(self._metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            return
