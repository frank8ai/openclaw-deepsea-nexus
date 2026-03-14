#!/usr/bin/env python3
"""
Audit OpenClaw system compactions and write to smart_context_metrics.log.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path


def resolve_openclaw_home() -> Path:
    return Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser().resolve()


def resolve_workspace_root() -> Path:
    return Path(
        os.environ.get("OPENCLAW_WORKSPACE", resolve_openclaw_home() / "workspace")
    ).expanduser().resolve()


GATEWAY_LOG = (resolve_openclaw_home() / "logs" / "gateway.log").resolve()
STATE_PATH = (resolve_workspace_root() / "logs" / "compaction_audit_state.json").resolve()
SMART_LOG = (resolve_workspace_root() / "logs" / "smart_context_metrics.log").resolve()


COMPACTION_PAT = re.compile(r"auto-compaction succeeded.*", re.IGNORECASE)


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"last_line": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"last_line": 0}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_metric(event: dict) -> None:
    SMART_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SMART_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> None:
    if not GATEWAY_LOG.exists():
        raise SystemExit(f"gateway.log not found: {GATEWAY_LOG}")

    state = load_state()
    last_line = int(state.get("last_line", 0))

    lines = GATEWAY_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    new_lines = lines[last_line:]
    if not new_lines:
        return

    for idx, line in enumerate(new_lines, start=last_line + 1):
        if COMPACTION_PAT.search(line):
            append_metric(
                {
                    "event": "system_compaction",
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "line": line.strip(),
                }
            )

    state["last_line"] = len(lines)
    save_state(state)


if __name__ == "__main__":
    main()
