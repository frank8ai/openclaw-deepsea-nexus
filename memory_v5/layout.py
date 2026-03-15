from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

from .models import MemoryScope


def _safe_segment(value: str, default: str = "default") -> str:
    val = (value or "").strip()
    if not val:
        return default
    # Normalize path-like input and block path traversal / absolute segments.
    pieces = [piece for piece in val.replace("\\", "/").split("/") if piece and piece not in {".", ".."}]
    candidate = "_".join(pieces) if pieces else ""
    if not candidate:
        return default
    sanitized = "".join(ch if (ch.isalnum() or ch in {"_", "-", "."}) else "_" for ch in candidate)
    sanitized = sanitized.strip("._")
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    return sanitized or default


@dataclass
class MemoryLayout:
    base_path: str
    scope: MemoryScope

    def __post_init__(self) -> None:
        self.scope = self.scope.normalized()
        self.base_path = os.path.expanduser(self.base_path)

    def scope_root(self) -> str:
        parts = [
            _safe_segment(self.scope.agent_id),
            _safe_segment(self.scope.user_id),
        ]
        root = os.path.join(self.base_path, *parts)
        os.makedirs(root, exist_ok=True)
        return root

    def resources_dir(self) -> str:
        path = os.path.join(self.scope_root(), "resources")
        os.makedirs(path, exist_ok=True)
        return path

    def items_dir(self) -> str:
        path = os.path.join(self.scope_root(), "items")
        os.makedirs(path, exist_ok=True)
        return path

    def items_archive_dir(self) -> str:
        path = os.path.join(self.scope_root(), "items_archive")
        os.makedirs(path, exist_ok=True)
        return path

    def categories_dir(self) -> str:
        path = os.path.join(self.scope_root(), "categories")
        os.makedirs(path, exist_ok=True)
        return path

    def graphs_dir(self) -> str:
        path = os.path.join(self.scope_root(), "graphs")
        os.makedirs(path, exist_ok=True)
        return path

    def resource_path(self, resource_id: str) -> str:
        return os.path.join(self.resources_dir(), f"{resource_id}.json")

    def item_path(self, item_id: str) -> str:
        return os.path.join(self.items_dir(), f"{item_id}.json")

    def item_archive_path(self, item_id: str) -> str:
        return os.path.join(self.items_archive_dir(), f"{item_id}.json")

    def category_path(self, category_name: str) -> str:
        safe_name = _safe_segment(category_name or "general")
        # When app/run/workspace qualifiers exist, keep per-scope category files
        # distinct even if agent/user are shared.
        qualifiers = [
            (self.scope.app_id or "").strip(),
            (self.scope.run_id or "").strip(),
            (self.scope.workspace or "").strip(),
        ]
        qualifier_key = "|".join([q for q in qualifiers if q])
        if qualifier_key:
            digest = hashlib.sha1(self.scope.scope_key().encode("utf-8")).hexdigest()[:8]
            return os.path.join(self.categories_dir(), f"{safe_name}__{digest}.md")
        return os.path.join(self.categories_dir(), f"{safe_name}.md")

    def index_path(self) -> str:
        return os.path.join(self.scope_root(), "index.sqlite3")

    def ensure_dirs(self) -> None:
        _ = self.scope_root()
        _ = self.resources_dir()
        _ = self.items_dir()
        _ = self.categories_dir()
        _ = self.graphs_dir()
