from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_str(value: Optional[str], default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


@dataclass
class MemoryScope:
    agent_id: str = "default"
    user_id: str = "default"
    run_id: str = ""
    app_id: str = ""
    workspace: str = ""

    def normalized(self) -> "MemoryScope":
        return MemoryScope(
            agent_id=_clean_str(self.agent_id, "default") or "default",
            user_id=_clean_str(self.user_id, "default") or "default",
            run_id=_clean_str(self.run_id, ""),
            app_id=_clean_str(self.app_id, ""),
            workspace=_clean_str(self.workspace, ""),
        )

    def scope_key(self) -> str:
        scope = self.normalized()
        return ":".join(
            [
                scope.agent_id,
                scope.user_id,
                scope.app_id,
                scope.run_id,
                scope.workspace,
            ]
        )


@dataclass
class MemoryResource:
    id: str
    kind: str
    source: str
    content: str
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    metadata: Dict[str, str] = field(default_factory=dict)
    scope: MemoryScope = field(default_factory=MemoryScope)
    path: str = ""


@dataclass
class MemoryItem:
    id: str
    title: str
    content: str
    kind: str = "note"
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    project: str = ""
    category: str = ""
    source_id: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    confidence: str = "medium"
    archived: int = 0
    usage_count: int = 0
    last_used: str = ""
    ttl_days: int = 0
    decay_half_life_days: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    scope: MemoryScope = field(default_factory=MemoryScope)
    path: str = ""


@dataclass
class MemoryCategory:
    id: str
    name: str
    summary: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    scope: MemoryScope = field(default_factory=MemoryScope)
    path: str = ""


@dataclass
class MemoryEdge:
    id: str
    src_id: str
    dst_id: str
    relation: str
    weight: float = 1.0
    created_at: str = field(default_factory=now_iso)
    scope: MemoryScope = field(default_factory=MemoryScope)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class MemoryHit:
    id: str
    title: str
    content: str
    source: str
    relevance: float
    origin: str
    metadata: Dict[str, str] = field(default_factory=dict)
