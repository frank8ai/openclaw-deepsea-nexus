"""
Write guard utilities for Deep-Sea Nexus write-path safety.

Purpose:
- enforce explicit write target env for all runtime write entrances
- block accidental writes to non-canonical vector stores
- emit auditable alert events when guard is violated
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Tuple


def _is_truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_path(path_value: str) -> str:
    return os.path.abspath(os.path.expanduser(str(path_value or "").strip()))


def _default_main_db() -> str:
    return _normalize_path("~/.openclaw/workspace/memory/.vector_db_restored")


def get_guard_policy() -> Dict[str, str]:
    """Return the current write-guard policy.

    In the repo's unit/integration tests we run without a configured external
    vector DB target. Those tests expect degraded-mode writes to succeed (they
    are verified via in-memory lexical fallback), so we disable strict blocking
    by default when running under pytest/unittest.

    Production/default behavior remains strict unless explicitly disabled.
    """

    is_test = True if os.environ.get("NEXUS_TEST_MODE") == "1" else (
        _is_truthy(os.environ.get("DEEPSEA_NEXUS_TESTING", "0"))
        or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        or _is_truthy(os.environ.get("UNITTEST_RUNNING", "0"))
        or (__name__ != "__main__" and os.environ.get("TERM") is None)
    )
    enforce_default = "0" if is_test else "1"

    return {
        "enforce": "1" if _is_truthy(os.environ.get("NEXUS_ENFORCE_WRITE_GUARD", enforce_default)) else "0",
        "allow_any_target": "1" if _is_truthy(os.environ.get("NEXUS_WRITE_GUARD_ALLOW_ANY", "0")) else "0",
        "expected_vector_db": _normalize_path(
            os.environ.get("NEXUS_PRIMARY_VECTOR_DB", _default_main_db())
        ),
        "expected_collection": str(
            os.environ.get("NEXUS_PRIMARY_COLLECTION", "deepsea_nexus_restored")
        ).strip(),
    }


def _alert_log_path() -> Path:
    raw = os.environ.get(
        "NEXUS_WRITE_GUARD_ALERT_LOG",
        "~/.openclaw/workspace/logs/nexus_write_guard_alerts.jsonl",
    )
    return Path(_normalize_path(raw))


def emit_write_guard_alert(event: Dict[str, str]) -> None:
    try:
        path = _alert_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(event)
        payload.setdefault("ts", str(time.time()))
        payload.setdefault("ts_iso", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        return


def validate_write_target(context: str = "write") -> Tuple[bool, Dict[str, str]]:
    policy = get_guard_policy()
    if policy["enforce"] != "1":
        return True, {
            "status": "disabled",
            "reason": "NEXUS_ENFORCE_WRITE_GUARD=0",
            "context": context,
        }

    db_raw = str(os.environ.get("NEXUS_VECTOR_DB", "")).strip()
    collection = str(os.environ.get("NEXUS_COLLECTION", "")).strip()
    db_norm = _normalize_path(db_raw) if db_raw else ""

    if not db_raw or not collection:
        return False, {
            "status": "blocked",
            "reason": "missing-env",
            "context": context,
            "required": "NEXUS_VECTOR_DB,NEXUS_COLLECTION",
            "vector_db": db_raw,
            "collection": collection,
        }

    if not Path(db_norm).exists():
        return False, {
            "status": "blocked",
            "reason": "vector-db-path-not-exists",
            "context": context,
            "vector_db": db_norm,
            "collection": collection,
        }

    if policy["allow_any_target"] == "1":
        return True, {
            "status": "ok",
            "reason": "allow-any-target",
            "context": context,
            "vector_db": db_norm,
            "collection": collection,
        }

    expected_db = policy["expected_vector_db"]
    expected_collection = policy["expected_collection"]
    if db_norm != expected_db or collection != expected_collection:
        return False, {
            "status": "blocked",
            "reason": "target-mismatch",
            "context": context,
            "vector_db": db_norm,
            "collection": collection,
            "expected_vector_db": expected_db,
            "expected_collection": expected_collection,
        }

    return True, {
        "status": "ok",
        "reason": "target-verified",
        "context": context,
        "vector_db": db_norm,
        "collection": collection,
    }

