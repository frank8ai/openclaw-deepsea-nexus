"""
Session Manager Plugin v3.0

Refactored SessionManager using Plugin architecture.
Provides session lifecycle management with event-driven communication.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from ..core.plugin_system import NexusPlugin, PluginMetadata, PluginState
from ..core.event_bus import EventTypes
from ..core.config_manager import get_config_manager
from ..runtime_paths import resolve_openclaw_workspace

import logging
logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    topic: str
    created_at: str
    last_active: str
    status: str  # active, paused, archived
    chunk_count: int = 0
    gold_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionInfo':
        return cls(**data)
    
    def is_active(self) -> bool:
        return self.status == "active"
    
    def days_since_active(self) -> int:
        """Days since last activity"""
        try:
            last = datetime.fromisoformat(self.last_active)
            return (datetime.now() - last).days
        except:
            return 0


class SessionManagerPlugin(NexusPlugin):
    """
    Session Manager Plugin
    
    Manages conversation sessions with full lifecycle:
    - Creation
    - Activity tracking
    - Pausing/Closing
    - Archival
    
    Emits events for all state changes (decoupled from consumers).
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="session_manager",
            version="3.0.0",
            description="Session lifecycle management with event support",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self.sessions: Dict[str, SessionInfo] = {}
        self._storage = None
        self._config = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize session manager"""
        try:
            # Get configuration
            config_mgr = get_config_manager()
            default_base_path = os.path.join(resolve_openclaw_workspace(), "memory")
            self._config = {
                "base_path": config.get("base_path", default_base_path),
                "auto_archive_days": config.get("session", {}).get("auto_archive_days", 30),
                "index_file": config.get("session", {}).get("index_file", "_sessions_index.json"),
            }
            
            # Expand path
            self._config["base_path"] = os.path.expanduser(self._config["base_path"])
            os.makedirs(self._config["base_path"], exist_ok=True)
            
            # Initialize storage backend
            storage_type = config.get("storage", {}).get("session_backend", "json")
            if storage_type == "json":
                from ..storage.json_backend import JsonSessionStorage
                self._storage = JsonSessionStorage(self._config["base_path"])
            else:
                logger.error(f"Unknown storage backend: {storage_type}")
                return False
            
            await self._storage.initialize()
            
            # Load existing sessions
            result = await self._storage.get_all_sessions()
            if result.success and result.data:
                for sid, data in result.data.items():
                    self.sessions[sid] = SessionInfo.from_dict(data)
            
            logger.info(f"✓ SessionManager initialized: {len(self.sessions)} sessions loaded")
            return True
            
        except Exception as e:
            logger.error(f"✗ SessionManager init failed: {e}")
            return False

    def _run_async_safely(self, coro):
        """Run/schedule a coroutine from both sync and async call paths."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        loop.create_task(coro)
        return None
    
    async def start(self) -> bool:
        """Start the plugin"""
        # Subscribe to config reload events
        if self._event_bus:
            self._event_bus.subscribe(EventTypes.CONFIG_RELOADED, self._on_config_reload)
        
        logger.info("✓ SessionManager started")
        return True
    
    async def stop(self) -> bool:
        """Stop the plugin"""
        # Save all sessions
        await self._save_all()
        
        # Close storage
        if self._storage:
            await self._storage.close()
        
        logger.info("✓ SessionManager stopped")
        return True
    
    async def reload(self, new_config: Dict[str, Any]) -> bool:
        """Hot-reload configuration"""
        # Save current state
        await self._save_all()
        
        # Reinitialize with new config
        return await self.initialize(new_config)
    
    def start_session(self, topic: str, auto_create: bool = True) -> str:
        """
        Create a new session
        
        Args:
            topic: Session topic/name
            auto_create: Whether to create if not exists
            
        Returns:
            str: Session ID
        """
        # Generate session ID (HHMM_Topic format)
        now = datetime.now()
        time_str = now.strftime("%H%M")
        
        # Clean topic for safe filename
        clean_topic = "".join(c for c in topic if c.isalnum() or c in "_- ")
        safe_topic = clean_topic[:20].strip() if clean_topic else "Unknown"
        session_id = f"{time_str}_{safe_topic}"
        
        # Handle duplicates
        original_id = session_id
        counter = 1
        while session_id in self.sessions:
            session_id = f"{original_id}_{counter}"
            counter += 1
        
        # Create session
        now_str = now.isoformat()
        self.sessions[session_id] = SessionInfo(
            session_id=session_id,
            topic=topic,
            created_at=now_str,
            last_active=now_str,
            status="active"
        )

        # Persist + emit in sync/async-safe mode.
        self._run_async_safely(self._save_session(session_id))
        self._run_async_safely(self.emit(EventTypes.SESSION_CREATED, {
            "session_id": session_id,
            "topic": topic,
            "timestamp": now_str,
        }))
        
        logger.info(f"✓ Session created: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_session_by_topic(self, topic: str) -> Optional[SessionInfo]:
        """Find session by topic (exact match)"""
        for session in self.sessions.values():
            if session.topic == topic:
                return session
        return None
    
    def update_activity(self, session_id: str) -> bool:
        """Update session activity timestamp"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].last_active = datetime.now().isoformat()
        self._run_async_safely(self._save_session(session_id))

        # Emit event
        self._run_async_safely(self.emit(EventTypes.SESSION_UPDATED, {
            "session_id": session_id,
            "field": "last_active",
        }))
        
        return True
    
    def close_session(self, session_id: str) -> bool:
        """
        Close (pause) a session
        
        Note: Session data is preserved, just marked as inactive.
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.status = "paused"
        session.last_active = datetime.now().isoformat()

        self._run_async_safely(self._save_session(session_id))

        # Emit event
        self._run_async_safely(self.emit(EventTypes.SESSION_CLOSED, {
            "session_id": session_id,
            "topic": session.topic,
            "chunks": session.chunk_count,
            "gold": session.gold_count,
        }))
        
        logger.info(f"✓ Session closed: {session_id}")
        return True
    
    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session
        
        Marks session for archival. Actual file movement handled by FlushManager.
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.status = "archived"
        session.last_active = datetime.now().isoformat()

        self._run_async_safely(self._save_session(session_id))

        # Emit event
        self._run_async_safely(self.emit(EventTypes.SESSION_ARCHIVED, {
            "session_id": session_id,
            "topic": session.topic,
            "total_chunks": session.chunk_count,
        }))
        
        logger.info(f"✓ Session archived: {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session"""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        
        # Delete from storage
        if self._storage:
            self._run_async_safely(self._storage.delete_session(session_id))
        
        logger.info(f"✓ Session deleted: {session_id}")
        return True
    
    def list_active_sessions(self) -> List[SessionInfo]:
        """List all active sessions"""
        return [s for s in self.sessions.values() if s.status == "active"]
    
    def list_paused_sessions(self) -> List[SessionInfo]:
        """List all paused sessions"""
        return [s for s in self.sessions.values() if s.status == "paused"]
    
    def list_archived_sessions(self) -> List[SessionInfo]:
        """List all archived sessions"""
        return [s for s in self.sessions.values() if s.status == "archived"]
    
    def list_recent_sessions(self, days: int = 7) -> List[SessionInfo]:
        """List sessions active in last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return [s for s in self.sessions.values() if s.last_active > cutoff_str]
    
    def list_sessions_to_archive(self) -> List[SessionInfo]:
        """List sessions that should be archived based on policy"""
        to_archive = []
        days = self._config.get("auto_archive_days", 30)
        
        for session in self.sessions.values():
            if session.status == "active" and session.days_since_active() > days:
                to_archive.append(session)
        
        return to_archive
    
    def add_chunk(self, session_id: str) -> bool:
        """Increment chunk count for a session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].chunk_count += 1
        self.update_activity(session_id)
        return True
    
    def add_gold(self, session_id: str) -> bool:
        """Increment gold count for a session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].gold_count += 1
        self.update_activity(session_id)
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        active = len(self.list_active_sessions())
        paused = len(self.list_paused_sessions())
        archived = len(self.list_archived_sessions())
        total_chunks = sum(s.chunk_count for s in self.sessions.values())
        total_gold = sum(s.gold_count for s in self.sessions.values())
        
        return {
            "total_sessions": len(self.sessions),
            "active": active,
            "paused": paused,
            "archived": archived,
            "total_chunks": total_chunks,
            "total_gold": total_gold,
        }
    
    # Private methods
    
    async def _save_session(self, session_id: str):
        """Save single session to storage"""
        if not self._storage or session_id not in self.sessions:
            return
        
        try:
            await self._storage.save_session(self.sessions[session_id].to_dict())
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
    
    async def _save_all(self):
        """Save all sessions to storage"""
        if not self._storage:
            return
        
        try:
            for session_id in self.sessions:
                await self._save_session(session_id)
            logger.debug(f"Saved {len(self.sessions)} sessions")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    async def _on_config_reload(self, event):
        """Handle config reload event"""
        logger.info("Config reloaded, updating SessionManager settings")
        # Reload config from config manager
        config_mgr = get_config_manager()
        self._config["auto_archive_days"] = config_mgr.get("session.auto_archive_days", 30)
