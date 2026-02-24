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
    new_text = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    if path.exists():
        old_text = path.read_text(encoding="utf-8")
        if old_text == new_text:
            return False
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


def build_override(deepsea_config: Dict[str, Any]) -> Dict[str, Any]:
    smart = deepsea_config.get("smart_context") if isinstance(deepsea_config.get("smart_context"), dict) else {}
    preserve_recent = to_positive_int(smart.get("full_rounds"), 8)
    compression_threshold = to_positive_int(smart.get("summary_rounds"), 20)
    token_trigger_estimate = to_positive_int(smart.get("full_tokens_max"), 8000)
    return {
        "schema_version": "1.0",
        "source": "deepsea-nexus/config.json",
        "generated_at": now_iso(),
        "preserveRecent": preserve_recent,
        "compressionThreshold": compression_threshold,
        "tokenTriggerEstimate": token_trigger_estimate,
        "enabled": True,
        "verbose": False,
        "mapping": {
            "preserveRecent": "smart_context.full_rounds",
            "compressionThreshold": "smart_context.summary_rounds",
            "tokenTriggerEstimate": "smart_context.full_tokens_max",
        },
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
        override_changed = existing_override != override

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
            "tokenTriggerEstimate": override["tokenTriggerEstimate"],
        },
        "handler": handler_result,
        "ts": now_iso(),
    }
    print(json.dumps(result, ensure_ascii=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
