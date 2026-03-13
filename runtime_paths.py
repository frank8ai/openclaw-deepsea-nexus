"""
Shared runtime path resolution helpers.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


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
    ]
    if allow_nexus_base:
        candidates.append(nexus_cfg.get("base_path"))
    candidates.append(default)

    for candidate in candidates:
        if candidate:
            return os.path.expanduser(str(candidate))
    return os.getcwd()


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
        log_dir = os.path.join(base_path, "logs")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, filename)
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
        return root
    base_path = resolve_workspace_base(cfg, default=default_base)
    return os.path.join(os.path.expanduser(str(base_path)), root)
