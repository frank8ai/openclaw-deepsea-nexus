"""
Data structures and type definitions for Deep-Sea Nexus v2.0
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


def _resolve_default_base_path() -> str:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return str(Path(override).expanduser().resolve())
    return str(Path(__file__).resolve().parent.parent)


class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class SessionMetadata:
    """Session metadata"""
    uuid: str                           # Unique identifier
    topic: str                          # Topic name
    created_at: str                     # Creation time
    last_active: str                    # Last active time
    status: SessionStatus = SessionStatus.ACTIVE
    gold_count: int = 0                 # Number of GOLD markers
    word_count: int = 0                 # Word count
    tags: List[str] = field(default_factory=list)


@dataclass
class Session:
    """Complete session"""
    metadata: SessionMetadata
    content: str                        # Content


@dataclass
class DailyIndex:
    """Daily index"""
    date: str                           # Date YYYY-MM-DD
    sessions: Dict[str, SessionMetadata]  # Session list
    gold_keys: List[str]                # GOLD keywords
    topics: List[str]                   # Topic list
    paused_sessions: Dict[str, str] = field(default_factory=dict)  # Paused sessions


@dataclass
class RecallResult:
    """Recall result"""
    session_id: str
    relevance: float                    # Relevance 0-1
    content: str                        # Retrieved content
    source: str                         # Source
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexEntry:
    """Index entry"""
    session_id: str
    status: str                         # active/paused
    topic: str                         # Topic
    gold_keywords: List[str] = field(default_factory=list)
    last_active: str = ""


@dataclass
class NexusConfig:
    """Nexus configuration"""
    base_path: str = field(default_factory=_resolve_default_base_path)
    memory_path: str = "memory/90_Memory"
    max_index_tokens: int = 300
    max_session_tokens: int = 1000
