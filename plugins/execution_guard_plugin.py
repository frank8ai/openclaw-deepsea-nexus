"""
Execution guard plugin for tool-risk classification and report-first recommendations.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..memory_v5 import MemoryScope
from ..runtime_paths import resolve_log_path, resolve_openclaw_home

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_pathish(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def resolve_execution_governor_guardrails_path(config: Optional[Dict[str, Any]] = None) -> str:
    cfg = config if isinstance(config, dict) else {}
    guard_cfg = cfg.get("execution_guard", {}) if isinstance(cfg.get("execution_guard", {}), dict) else {}
    bridge_cfg = guard_cfg.get("host_bridge", {}) if isinstance(guard_cfg.get("host_bridge", {}), dict) else {}
    override = str(bridge_cfg.get("guardrails_path") or "").strip()
    if override:
        return str(Path(override).expanduser())
    return os.path.join(resolve_openclaw_home(), "state", "execution-governor-guardrails.json")


@dataclass
class GuardFinding:
    kind: str
    severity: str
    evidence: str
    location: str = ""
    rule_id: str = ""


@dataclass
class GuardDecision:
    decision: str
    risk_level: str
    risk_score: float
    reasons: List[str] = field(default_factory=list)
    matched_rules: List[str] = field(default_factory=list)
    sensitive_targets: List[str] = field(default_factory=list)
    recommended_action: str = "allow"
    findings: List[GuardFinding] = field(default_factory=list)
    mode: str = "report_only"
    enforced: bool = False
    context_hint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["risk_score"] = round(float(self.risk_score), 3)
        return payload


class ExecutionGuardPlugin(NexusPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.metadata = PluginMetadata(
            name="execution_guard",
            version="3.0.0",
            description="Report-first tool risk classification for execution-governor",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self._config: Dict[str, Any] = {}
        self._enabled = True
        self._mode = "report_only"
        self._metrics_path: Optional[str] = None
        self._guardrails_path: Optional[str] = None
        self._stats: Dict[str, Any] = {
            "processed": 0,
            "allow": 0,
            "context": 0,
            "ask": 0,
            "block": 0,
            "last_decision": {},
        }

    async def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config if isinstance(config, dict) else {}
        guard_cfg = self._guard_cfg()
        self._enabled = bool(guard_cfg.get("enabled", True))
        self._mode = str(guard_cfg.get("mode", "report_only") or "report_only").strip() or "report_only"
        self._metrics_path = resolve_log_path(
            self._config,
            "execution_guard_metrics.log",
            allow_nexus_base=True,
            default_base=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        )
        self._guardrails_path = resolve_execution_governor_guardrails_path(self._config)
        return True

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True

    def get_health_summary(self) -> Dict[str, Any]:
        return {
            "enabled": self._enabled,
            "mode": self._mode,
            "metrics_path": self._metrics_path or "",
            "guardrails_path": self._guardrails_path or "",
            "processed": int(self._stats.get("processed", 0)),
            "allow": int(self._stats.get("allow", 0)),
            "context": int(self._stats.get("context", 0)),
            "ask": int(self._stats.get("ask", 0)),
            "block": int(self._stats.get("block", 0)),
            "last_decision": dict(self._stats.get("last_decision", {}) or {}),
            "last_metrics": read_execution_guard_metrics_summary(self._metrics_path),
        }

    def analyze_tool_event(self, event: Any, compressed: Optional[Any] = None, scope: Optional[MemoryScope] = None) -> Dict[str, Any]:
        if not self._enabled:
            return GuardDecision(decision="allow", risk_level="low", risk_score=0.0, mode=self._mode).to_dict()

        command_text = self._command_text(event)
        findings: List[GuardFinding] = []
        sensitive_targets: List[str] = []
        matched_rules: List[str] = []
        workspace_root = self._workspace_root(scope, event)

        findings.extend(self._shell_findings(command_text))
        path_findings, path_targets = self._path_findings(event, workspace_root)
        findings.extend(path_findings)
        sensitive_targets.extend(path_targets)
        findings.extend(self._second_brain_findings(event, workspace_root))

        risk_score = 0.05
        if self._is_low_risk_dev_command(event, command_text, findings):
            risk_score = max(risk_score, 0.1)
        for finding in findings:
            matched_rules.append(finding.rule_id or finding.kind)
            risk_score = max(risk_score, self._severity_score(finding.severity))
            if finding.location and finding.location not in sensitive_targets:
                sensitive_targets.append(finding.location)
        risk_level = self._risk_level(risk_score)
        decision = self._decision_for_score(risk_score, sensitive_targets)
        recommended_action = self._recommended_action(decision)
        reasons = [finding.evidence for finding in findings[:8]]
        context_hint = ""
        if decision == "context":
            context_hint = "Sensitive asset access should be reviewed in context before execution."
        payload = GuardDecision(
            decision=decision,
            risk_level=risk_level,
            risk_score=risk_score,
            reasons=reasons,
            matched_rules=matched_rules[:12],
            sensitive_targets=sensitive_targets[:12],
            recommended_action=recommended_action,
            findings=findings[:12],
            mode=self._mode,
            enforced=self._mode in {"ask_enforced", "block_enforced"},
            context_hint=context_hint,
        ).to_dict()
        self._record_decision(payload, event)
        return payload

    def _guard_cfg(self) -> Dict[str, Any]:
        cfg = self._config.get("execution_guard", {}) if isinstance(self._config, dict) else {}
        if not isinstance(cfg, dict):
            return {}
        return cfg

    def _command_text(self, event: Any) -> str:
        tool_name = str(getattr(event, "tool_name", "") or event.get("tool_name", "")).strip()
        args = getattr(event, "args", None)
        if args is None and isinstance(event, dict):
            args = event.get("args", [])
        parts = [tool_name] + [str(arg).strip() for arg in (args or []) if str(arg).strip()]
        return " ".join(parts).strip()

    def _workspace_root(self, scope: Optional[MemoryScope], event: Any) -> str:
        if scope and getattr(scope, "workspace", ""):
            return _clean_pathish(scope.workspace)
        raw_scope = getattr(event, "scope", None)
        if isinstance(raw_scope, dict) and raw_scope.get("workspace"):
            return _clean_pathish(raw_scope.get("workspace"))
        cwd = _clean_pathish(getattr(event, "cwd", "") if not isinstance(event, dict) else event.get("cwd", ""))
        if cwd:
            return cwd
        return _clean_pathish(os.environ.get("OPENCLAW_WORKSPACE", ""))

    def _severity_score(self, severity: str) -> float:
        mapping = {
            "low": 0.2,
            "medium": 0.55,
            "high": 0.8,
            "critical": 0.95,
        }
        return mapping.get(str(severity or "").lower(), 0.2)

    def _risk_level(self, score: float) -> str:
        if score >= 0.9:
            return "critical"
        if score >= 0.7:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"

    def _decision_for_score(self, score: float, sensitive_targets: Sequence[str]) -> str:
        thresholds = self._guard_cfg().get("thresholds", {}) if isinstance(self._guard_cfg().get("thresholds", {}), dict) else {}
        ask_score = _safe_float(thresholds.get("ask_score"), 0.7)
        block_score = _safe_float(thresholds.get("block_score"), 0.9)
        if score >= block_score:
            return "block"
        if score >= ask_score:
            return "ask"
        context_targets = {
            "workspace_sensitive",
            "outside_workspace",
            "system_sensitive",
            "credential_sensitive",
            "second_brain_sensitive",
        }
        if any(target in context_targets for target in sensitive_targets):
            return "context"
        return "allow"

    def _recommended_action(self, decision: str) -> str:
        if self._mode == "report_only":
            if decision == "block":
                return "block_recommended"
            if decision == "ask":
                return "ask_recommended"
            if decision == "context":
                return "context_recommended"
            return "allow"
        if decision == "block" and self._mode == "block_enforced":
            return "block"
        if decision in {"ask", "block"} and self._mode == "ask_enforced":
            return "ask"
        return decision

    def _shell_findings(self, command_text: str) -> List[GuardFinding]:
        lowered = command_text.lower()
        findings: List[GuardFinding] = []
        patterns = [
            (r"curl\s+.+\|\s*(bash|sh)\b", "critical", "network bootstrap piped into shell", "shell.curl_pipe_shell"),
            (r"wget\s+.+\|\s*(bash|sh)\b", "critical", "network bootstrap piped into shell", "shell.wget_pipe_shell"),
            (r"powershell(\.exe)?\s+-enc(odedcommand)?\b", "critical", "encoded PowerShell execution", "shell.powershell_encoded"),
            (r"base64\s+(-d|--decode)\b", "high", "base64 decode execution pattern", "shell.base64_decode"),
            (r"\brm\s+-rf\b", "critical", "recursive shell deletion", "shell.rm_rf"),
            (r"\bdel\s+/s\s+/q\b", "critical", "recursive Windows deletion", "shell.del_sq"),
            (r"remove-item\b.+-recurse.+-force", "critical", "recursive PowerShell deletion", "shell.remove_item_force"),
            (r"\bcurl\b|\bwget\b", "medium", "network execution tool invoked", "shell.network_fetch"),
        ]
        for pattern, severity, evidence, rule_id in patterns:
            if re.search(pattern, lowered):
                findings.append(GuardFinding(kind="execute", severity=severity, evidence=evidence, rule_id=rule_id))
        return findings

    def _path_findings(self, event: Any, workspace_root: str) -> Tuple[List[GuardFinding], List[str]]:
        findings: List[GuardFinding] = []
        targets: List[str] = []
        for path in self._candidate_paths(event):
            target = self._classify_path_target(path, workspace_root)
            if target not in targets:
                targets.append(target)
            operation = self._operation_kind(event, path)
            if target == "credential_sensitive":
                findings.append(GuardFinding(kind="secret_search", severity="critical", evidence="credential-sensitive target matched", location=target, rule_id="path.credential_sensitive"))
            elif target == "system_sensitive" and operation in {"filesystem_write", "filesystem_delete", "execute"}:
                findings.append(GuardFinding(kind=operation, severity="high", evidence="system-sensitive path targeted", location=target, rule_id="path.system_sensitive"))
            elif target == "outside_workspace" and operation in {"filesystem_write", "filesystem_delete", "edit"}:
                findings.append(GuardFinding(kind=operation, severity="high", evidence="path escapes workspace boundary", location=target, rule_id="path.outside_workspace"))
            elif target == "second_brain_sensitive":
                severity = "high" if operation in {"filesystem_write", "filesystem_delete", "edit"} else "medium"
                findings.append(GuardFinding(kind=operation, severity=severity, evidence="second-brain asset targeted", location=target, rule_id="path.second_brain_sensitive"))
            elif target == "workspace_sensitive":
                findings.append(GuardFinding(kind=operation, severity="medium", evidence="workspace-sensitive file targeted", location=target, rule_id="path.workspace_sensitive"))
        return findings, targets

    def _second_brain_findings(self, event: Any, workspace_root: str) -> List[GuardFinding]:
        findings: List[GuardFinding] = []
        for path in self._candidate_paths(event):
            normalized = _clean_pathish(path).lower()
            if "memory.md" in normalized and any(token in normalized for token in ("memory.md", "/memory/", "\\memory\\")):
                findings.append(GuardFinding(kind=self._operation_kind(event, path), severity="medium", evidence="MEMORY.md access", location="second_brain_sensitive", rule_id="memory.memory_md"))
        return findings

    def _candidate_paths(self, event: Any) -> List[str]:
        args = getattr(event, "args", None)
        metadata = getattr(event, "metadata", None)
        if isinstance(event, dict):
            args = event.get("args", args)
            metadata = event.get("metadata", metadata)
        paths: List[str] = []
        for raw in (args or []):
            text = str(raw).strip()
            if not text:
                continue
            if "/" in text or "\\" in text or text.startswith(".") or text.startswith("~"):
                paths.append(text)
        if isinstance(metadata, dict):
            for key in ("path", "file_path", "target_path", "paths"):
                value = metadata.get(key)
                if isinstance(value, list):
                    paths.extend([str(item).strip() for item in value if str(item).strip()])
                elif value:
                    paths.append(str(value).strip())
        return [path for path in paths if path]

    def _operation_kind(self, event: Any, path: str) -> str:
        tool_name = str(getattr(event, "tool_name", "") or event.get("tool_name", "")).lower() if isinstance(event, dict) else str(getattr(event, "tool_name", "")).lower()
        command = self._command_text(event).lower()
        if tool_name in {"read", "glob", "grep", "rg"}:
            return "filesystem_read"
        if tool_name in {"write"}:
            return "filesystem_write"
        if tool_name in {"edit", "multiedit"}:
            return "edit"
        if "rm " in command or " del " in f" {command} " or "remove-item" in command:
            return "filesystem_delete"
        if any(token in command for token in ("chmod", "chown", "mv ", "move-item", "cp ", "copy-item")):
            return "archive_or_copy"
        if tool_name in {"bash", "shell", "powershell", "pwsh"}:
            return "execute"
        return "filesystem_read"

    def _classify_path_target(self, path: str, workspace_root: str) -> str:
        normalized = _clean_pathish(path).lower()
        workspace = _clean_pathish(workspace_root).lower()
        credential_patterns = ["/.ssh", "/.gnupg", "/.aws", "/.config/gcloud", ".env", "credentials", "id_rsa", "id_ed25519"]
        second_brain_patterns = ["memory.md", "/obsidian", "/memory/.vector_db", ".vector_db_restored", "/state/", "/logs/"]
        system_patterns = ["/windows/system32", "/etc/", "/var/", "/usr/", "/program files/"]

        if any(pattern in normalized for pattern in credential_patterns):
            return "credential_sensitive"
        if any(pattern in normalized for pattern in system_patterns):
            return "system_sensitive"
        if any(pattern in normalized for pattern in second_brain_patterns):
            return "second_brain_sensitive"
        if normalized.startswith("../") or normalized.startswith("..\\"):
            return "outside_workspace"
        if workspace and normalized.startswith(workspace.rstrip("/")):
            if normalized.endswith("/config.json") or "/config/" in normalized:
                return "workspace_sensitive"
            return "workspace_safe"
        if re.match(r"^[a-z]:/", normalized) or normalized.startswith("/"):
            return "outside_workspace"
        return "workspace_safe"

    def _is_low_risk_dev_command(self, event: Any, command_text: str, findings: Sequence[GuardFinding]) -> bool:
        if findings:
            return False
        tool_name = str(getattr(event, "tool_name", "") or event.get("tool_name", "")).lower() if isinstance(event, dict) else str(getattr(event, "tool_name", "")).lower()
        command = command_text.lower()
        if tool_name == "git" and "diff" in command:
            return True
        if tool_name in {"rg", "grep"}:
            return True
        if any(token in command for token in ("pytest", "unittest", "go test", "cargo test")):
            return True
        return False

    def _record_decision(self, decision: Dict[str, Any], event: Any) -> None:
        self._stats["processed"] += 1
        decision_name = str(decision.get("decision", "allow"))
        if decision_name in self._stats:
            self._stats[decision_name] += 1
        self._stats["last_decision"] = decision
        if not self._metrics_path:
            return
        try:
            payload = {
                "schema_version": "5.3.0",
                "component": "execution_guard",
                "event": "guard_decision",
                "ts": _now_iso(),
                "tool_name": str(getattr(event, "tool_name", "") or event.get("tool_name", "")) if isinstance(event, dict) else str(getattr(event, "tool_name", "")),
                "decision": decision.get("decision", "allow"),
                "risk_level": decision.get("risk_level", "low"),
                "risk_score": decision.get("risk_score", 0.0),
                "recommended_action": decision.get("recommended_action", "allow"),
                "sensitive_targets": decision.get("sensitive_targets", []),
                "matched_rules": decision.get("matched_rules", []),
            }
            os.makedirs(os.path.dirname(self._metrics_path), exist_ok=True)
            with open(self._metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            return


def read_execution_guard_metrics_summary(metrics_path: Optional[str]) -> Dict[str, Any]:
    path = str(metrics_path or "").strip()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            rows = [json.loads(line) for line in fh if line.strip()]
    except Exception:
        return {}
    if not rows:
        return {}
    summary = {
        "processed": len(rows),
        "allow": 0,
        "context": 0,
        "ask": 0,
        "block": 0,
        "top_rules": {},
        "top_targets": {},
        "last_decision": rows[-1],
    }
    for row in rows:
        decision = str(row.get("decision", "allow"))
        if decision in summary:
            summary[decision] += 1
        for rule in row.get("matched_rules", []) or []:
            summary["top_rules"][rule] = summary["top_rules"].get(rule, 0) + 1
        for target in row.get("sensitive_targets", []) or []:
            summary["top_targets"][target] = summary["top_targets"].get(target, 0) + 1
    return summary
