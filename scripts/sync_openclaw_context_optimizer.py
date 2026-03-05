#!/usr/bin/env python3
"""Sync OpenClaw context-optimizer hook from deepsea-nexus as single source of truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def write_json_if_changed(path: Path, payload: Dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_json(path) if path.exists() else None
    if existing and comparable_payload(existing) == comparable_payload(payload):
        return False
    payload_to_write = dict(payload)
    payload_to_write["generated_at"] = now_iso()
    new_text = json.dumps(payload_to_write, ensure_ascii=True, indent=2) + "\n"
    path.write_text(new_text, encoding="utf-8")
    return True


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def to_positive_int(value: Any, fallback: int) -> int:
    try:
        num = int(value)
        if num > 0:
            return num
    except Exception:
        pass
    return fallback


def to_ratio(value: Any, fallback: float, minimum: float, maximum: float) -> float:
    try:
        num = float(value)
    except Exception:
        return fallback
    if num < minimum or num > maximum:
        return fallback
    return num


def build_override(deepsea_config: Dict[str, Any]) -> Dict[str, Any]:
    smart = deepsea_config.get("smart_context") if isinstance(deepsea_config.get("smart_context"), dict) else {}
    preserve_recent = to_positive_int(smart.get("full_rounds"), 8)
    compression_threshold = to_positive_int(smart.get("summary_rounds"), 20)
    compress_after_rounds = to_positive_int(
        smart.get("compress_after_rounds"),
        max(compression_threshold + 8, 35),
    )
    token_trigger_estimate = to_positive_int(smart.get("full_tokens_max"), 8000)
    trigger_soft_ratio = to_ratio(smart.get("trigger_soft_ratio"), 0.7, 0.55, 0.9)
    trigger_hard_ratio = to_ratio(
        smart.get("trigger_hard_ratio"),
        0.85,
        max(trigger_soft_ratio + 0.05, 0.65),
        0.98,
    )
    mode = str(smart.get("mode") or "auto").strip().lower()
    if mode not in {"auto", "coding", "general"}:
        mode = "auto"
    return {
        "schema_version": "1.0",
        "source": "deepsea-nexus/config.json",
        "preserveRecent": preserve_recent,
        "compressionThreshold": compression_threshold,
        "compressAfterRounds": compress_after_rounds,
        "tokenTriggerEstimate": token_trigger_estimate,
        "triggerSoftRatio": trigger_soft_ratio,
        "triggerHardRatio": trigger_hard_ratio,
        "mode": mode,
        "enabled": True,
        "verbose": False,
        "mapping": {
            "preserveRecent": "smart_context.full_rounds",
            "compressionThreshold": "smart_context.summary_rounds",
            "compressAfterRounds": "smart_context.compress_after_rounds",
            "tokenTriggerEstimate": "smart_context.full_tokens_max",
            "triggerSoftRatio": "smart_context.trigger_soft_ratio",
            "triggerHardRatio": "smart_context.trigger_hard_ratio",
            "mode": "smart_context.mode",
        },
    }


def comparable_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "source": payload.get("source"),
        "preserveRecent": payload.get("preserveRecent"),
        "compressionThreshold": payload.get("compressionThreshold"),
        "compressAfterRounds": payload.get("compressAfterRounds"),
        "tokenTriggerEstimate": payload.get("tokenTriggerEstimate"),
        "triggerSoftRatio": payload.get("triggerSoftRatio"),
        "triggerHardRatio": payload.get("triggerHardRatio"),
        "mode": payload.get("mode"),
        "enabled": payload.get("enabled"),
        "verbose": payload.get("verbose"),
        "mapping": payload.get("mapping"),
    }


def ensure_handler(runtime_handler: Path, template_handler: Path, backups_dir: Path, apply: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "changed": False,
        "reason": "already-synced",
    }

    if not template_handler.exists():
        result["reason"] = "template-missing"
        result["ok"] = False
        return result

    if not runtime_handler.exists():
        if not apply:
            result["reason"] = "runtime-missing"
            result["ok"] = False
            return result
        runtime_handler.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_handler, runtime_handler)
        result.update({"changed": True, "reason": "runtime-created", "ok": True})
        return result

    template_hash = sha256_file(template_handler)
    runtime_hash = sha256_file(runtime_handler)
    result["template_hash"] = template_hash
    result["runtime_hash"] = runtime_hash

    if template_hash == runtime_hash:
        result["ok"] = True
        return result

    if not apply:
        result["reason"] = "runtime-drift"
        result["ok"] = False
        return result

    backups_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backups_dir / f"handler.js.bak.{ts}"
    shutil.copy2(runtime_handler, backup_path)
    shutil.copy2(template_handler, runtime_handler)

    result.update(
        {
            "changed": True,
            "reason": "runtime-restored-from-template",
            "backup": str(backup_path),
            "ok": True,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OpenClaw context optimizer from deepsea-nexus config")
    parser.add_argument("--check", action="store_true", help="Check only; do not write")
    parser.add_argument("--apply", action="store_true", help="Apply sync changes")
    args = parser.parse_args()

    apply = bool(args.apply and not args.check)

    home = Path(os.path.expanduser("~"))
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", home / ".openclaw"))
    workspace = Path(os.environ.get("OPENCLAW_WORKSPACE", openclaw_home / "workspace"))
    deepsea_root = Path(os.environ.get("DEEPSEA_NEXUS_ROOT", workspace / "skills" / "deepsea-nexus"))

    deepsea_config_path = Path(os.environ.get("DEEPSEA_CONFIG_PATH", deepsea_root / "config.json"))
    override_path = Path(
        os.environ.get(
            "OPENCLAW_CONTEXT_OPTIMIZER_CONFIG",
            openclaw_home / "state" / "context-optimizer-single-source.json",
        )
    )
    runtime_handler = Path(
        os.environ.get(
            "OPENCLAW_CONTEXT_OPTIMIZER_HANDLER",
            openclaw_home / "hooks" / "context-optimizer" / "handler.js",
        )
    )
    template_handler = Path(
        os.environ.get(
            "OPENCLAW_CONTEXT_OPTIMIZER_TEMPLATE",
            deepsea_root / "resources" / "openclaw" / "context-optimizer" / "handler.single-source.js",
        )
    )
    backups_dir = Path(
        os.environ.get(
            "OPENCLAW_CONTEXT_OPTIMIZER_BACKUP_DIR",
            openclaw_home / "backups" / "hooks" / "context-optimizer",
        )
    )

    deepsea_config = read_json(deepsea_config_path)
    if not deepsea_config:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "deepsea config missing or invalid",
                    "path": str(deepsea_config_path),
                },
                ensure_ascii=True,
            )
        )
        return 2

    override = build_override(deepsea_config)
    override_changed = False
    if apply:
        override_changed = write_json_if_changed(override_path, override)
    else:
        existing_override = read_json(override_path)
        override_changed = comparable_payload(existing_override or {}) != comparable_payload(override)

    handler_result = ensure_handler(runtime_handler, template_handler, backups_dir, apply=apply)
    ok = bool(handler_result.get("ok", False))

    result = {
        "ok": ok,
        "mode": "apply" if apply else "check",
        "deepsea_config": str(deepsea_config_path),
        "override_path": str(override_path),
        "override_changed": override_changed,
        "derived": {
            "preserveRecent": override["preserveRecent"],
            "compressionThreshold": override["compressionThreshold"],
            "compressAfterRounds": override["compressAfterRounds"],
            "tokenTriggerEstimate": override["tokenTriggerEstimate"],
            "triggerSoftRatio": override["triggerSoftRatio"],
            "triggerHardRatio": override["triggerHardRatio"],
            "mode": override["mode"],
        },
        "handler": handler_result,
        "ts": now_iso(),
    }
    print(json.dumps(result, ensure_ascii=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
