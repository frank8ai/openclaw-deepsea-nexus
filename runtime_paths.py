"""
Shared runtime path resolution helpers.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional


def resolve_openclaw_home(default: Optional[str] = None) -> str:
    candidate = os.environ.get("OPENCLAW_HOME")
    if candidate:
        return os.path.expanduser(str(candidate))
    return os.path.expanduser(str(default or "~/.openclaw"))


def resolve_openclaw_workspace(default: Optional[str] = None) -> str:
    candidate = os.environ.get("OPENCLAW_WORKSPACE")
    if candidate:
        return os.path.expanduser(str(candidate))
    if default:
        return os.path.expanduser(str(default))
    return os.path.join(resolve_openclaw_home(), "workspace")


def resolve_workspace_base(
    config: Optional[Dict[str, Any]] = None,
    *,
    allow_nexus_base: bool = False,
    default: Optional[str] = None,
) -> str:
    cfg = config if isinstance(config, dict) else {}
    paths = cfg.get("paths", {}) if isinstance(cfg.get("paths", {}), dict) else {}
    nexus_cfg = cfg.get("nexus", {}) if isinstance(cfg.get("nexus", {}), dict) else {}

    candidates = [
        paths.get("base"),
        cfg.get("base_path"),
        cfg.get("workspace_root"),
        os.environ.get("OPENCLAW_WORKSPACE"),
    ]
    if allow_nexus_base:
        candidates.append(nexus_cfg.get("base_path"))
    candidates.append(default)

    for candidate in candidates:
        if candidate:
            return os.path.expanduser(str(candidate))
    return os.getcwd()


def _is_posix_absolute(path: str) -> bool:
    text = str(path or "")
    return text.startswith("/") and not re.match(r"^[A-Za-z]:[\\/]", text)


def _join_preserving_style(base_path: str, *parts: str) -> str:
    if _is_posix_absolute(base_path):
        suffix = "/".join([str(part).strip("/\\") for part in parts if str(part).strip("/\\")])
        if not suffix:
            return base_path
        return base_path.rstrip("/\\") + "/" + suffix
    return os.path.join(base_path, *parts)


def resolve_log_path(
    config: Optional[Dict[str, Any]],
    filename: str,
    *,
    allow_nexus_base: bool = False,
    default_base: Optional[str] = None,
) -> Optional[str]:
    base_path = resolve_workspace_base(
        config,
        allow_nexus_base=allow_nexus_base,
        default=default_base,
    )
    if not base_path:
        return None
    try:
        log_dir = _join_preserving_style(base_path, "logs")
        if not (_is_posix_absolute(log_dir) and os.name == "nt"):
            os.makedirs(log_dir, exist_ok=True)
        return _join_preserving_style(log_dir, filename)
    except Exception:
        return None


def resolve_memory_root(
    config: Optional[Dict[str, Any]],
    *,
    default_root: str = "memory/95_MemoryV5",
    default_base: Optional[str] = None,
) -> str:
    cfg = config if isinstance(config, dict) else {}
    mem_cfg = cfg.get("memory_v5", {}) if isinstance(cfg.get("memory_v5", {}), dict) else {}
    root = os.path.expanduser(str(mem_cfg.get("root") or default_root))
    if os.path.isabs(root):
        if _is_posix_absolute(root):
            return root
        return os.path.normpath(root)
    base_path = resolve_workspace_base(cfg, default=default_base)
    joined = _join_preserving_style(os.path.expanduser(str(base_path)), root)
    if _is_posix_absolute(joined):
        return joined
    return os.path.normpath(joined)
