"""
Flush Manager Plugin v3.0

Refactored FlushManager using Plugin architecture.
Uses unified CompressionManager instead of duplicate compression code.
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..core.plugin_system import NexusPlugin, PluginMetadata
from ..core.event_bus import EventTypes
from ..core.config_manager import get_config_manager
from ..runtime_paths import resolve_openclaw_workspace
from ..storage.compression import CompressionManager

import logging
logger = logging.getLogger(__name__)


class FlushManagerPlugin(NexusPlugin):
    """
    Flush Manager Plugin
    
    Manages session archival and cleanup with compression support.
    Uses unified CompressionManager (eliminates code duplication).
    
    Events:
    - FLUSH_STARTED: When flush begins
    - FLUSH_COMPLETED: When flush completes
    - FLUSH_FAILED: When flush fails
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="flush_manager",
            version="3.0.0",
            description="Session archival and cleanup with compression",
            dependencies=["config_manager", "session_manager"],
            hot_reloadable=True,
        )
        self._config = None
        self._session_manager = None
        self._compression = None
        self._archive_path = None
        self._running = False
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize flush manager"""
        try:
            config_mgr = get_config_manager()
            default_base_path = os.path.join(resolve_openclaw_workspace(), "memory")
            
            self._config = {
                "enabled": config.get("flush", {}).get("enabled", True),
                "archive_time": config.get("flush", {}).get("archive_time", "03:00"),
                "compress_enabled": config.get("flush", {}).get("compress_enabled", True),
                "compress_algorithm": config.get("flush", {}).get("compress_algorithm", "gzip"),
                "archive_dir": config.get("flush", {}).get("archive_dir", "archive"),
                "keep_active_days": config.get("session", {}).get("auto_archive_days", 30),
                "keep_archived_days": config.get("flush", {}).get("keep_archived_days", 90),
                "min_chunks_to_archive": config.get("session", {}).get("min_chunks_to_archive", 5),
                "base_path": config.get("base_path", default_base_path),
            }
            
            # Expand path
            self._config["base_path"] = os.path.expanduser(self._config["base_path"])
            self._archive_path = os.path.join(
                self._config["base_path"],
                self._config["archive_dir"]
            )
            os.makedirs(self._archive_path, exist_ok=True)
            
            # Initialize compression manager (UNIFIED - no duplicate code!)
            self._compression = CompressionManager(
                algorithm=self._config["compress_algorithm"]
            )
            
            logger.info(f"✓ FlushManager initialized (compression: {self._config['compress_algorithm']})")
            return True
            
        except Exception as e:
            logger.error(f"✗ FlushManager init failed: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the plugin"""
        # Get session manager reference
        from ..core.plugin_system import get_plugin_registry
        registry = get_plugin_registry()
        self._session_manager = registry.get("session_manager")
        
        if not self._session_manager:
            logger.warning("SessionManager not available, some features disabled")
        
        # Subscribe to events
        if self._event_bus:
            self._event_bus.subscribe(EventTypes.SESSION_CLOSED, self._on_session_closed)
        
        logger.info("✓ FlushManager started")
        return True
    
    async def stop(self) -> bool:
        """Stop the plugin"""
        self._running = False
        logger.info("✓ FlushManager stopped")
        return True
    
    def should_archive(self, session_info: Dict[str, Any]) -> bool:
        """
        Determine if a session should be archived
        
        Args:
            session_info: Session data dict
            
        Returns:
            bool: True if should archive
        """
        # Check chunks threshold
        if session_info.get("chunk_count", 0) < self._config["min_chunks_to_archive"]:
            return False
        
        # Check last active time
        last_active = session_info.get("last_active", "")
        if last_active:
            try:
                last_date = datetime.fromisoformat(last_active)
                days_ago = (datetime.now() - last_date).days
                
                # Don't archive if active in last 7 days
                if days_ago < 7:
                    return False
                
                # Archive if inactive longer than threshold
                if days_ago > self._config["keep_active_days"]:
                    return True
                    
            except Exception:
                pass
        
        return False
    
    async def archive_session(self, session_id: str, session_info: Dict[str, Any]) -> bool:
        """
        Archive a single session
        
        Uses CompressionManager for compression (no duplicate code).
        
        Args:
            session_id: Session ID
            session_info: Session data
            
        Returns:
            bool: True if archived successfully
        """
        try:
            # Create archive directory (by month)
            month_dir = datetime.now().strftime("%Y-%m")
            target_dir = os.path.join(self._archive_path, month_dir)
            os.makedirs(target_dir, exist_ok=True)
            
            # Source file path
            source_file = os.path.join(
                self._config["base_path"],
                "sessions",
                f"{session_id}.json"
            )
            
            target_file = os.path.join(target_dir, f"{session_id}.json")
            
            if os.path.exists(source_file):
                # Move to archive
                shutil.move(source_file, target_file)
                
                # Compress using CompressionManager
                if self._config["compress_enabled"]:
                    result = self._compression.compress_file(target_file)
                    
                    if result.success:
                        # Remove uncompressed file
                        os.remove(target_file)
                        compressed_path = result.data.get("target_path")
                        logger.info(f"✓ Archived and compressed: {session_id} -> {month_dir}/")
                    else:
                        logger.warning(f"Compression failed, keeping uncompressed: {session_id}")
                else:
                    logger.info(f"✓ Archived (no compression): {session_id} -> {month_dir}/")
                
                return True
            else:
                # Create info file even if source doesn't exist
                import json
                info_file = os.path.join(target_dir, f"{session_id}_info.json")
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, ensure_ascii=False, indent=2)
                logger.info(f"✓ Archived (info only): {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"✗ Failed to archive {session_id}: {e}")
            return False
    
    async def daily_flush(self) -> Dict[str, Any]:
        """
        Execute daily flush operation
        
        Returns:
            Stats dict with operation results
        """
        if not self._config["enabled"]:
            logger.info("Flush is disabled, skipping")
            return {"skipped": True}
        
        if not self._session_manager:
            logger.error("SessionManager not available")
            return {"error": "SessionManager not available"}
        
        stats = {
            "started_at": datetime.now().isoformat(),
            "total_sessions": 0,
            "archived": 0,
            "compressed": 0,
            "skipped": 0,
            "errors": 0,
        }
        
        self._running = True
        
        try:
            # Emit start event
            await self.emit(EventTypes.FLUSH_STARTED, {
                "timestamp": stats["started_at"],
            })
            
            logger.info(f"🔄 Starting daily flush")
            
            # Get all sessions
            sessions = self._session_manager.sessions
            stats["total_sessions"] = len(sessions)
            
            for session_id, info in sessions.items():
                if not self._running:
                    logger.info("Flush interrupted")
                    break
                
                try:
                    info_dict = info.to_dict() if hasattr(info, 'to_dict') else info
                    
                    if self.should_archive(info_dict):
                        if await self.archive_session(session_id, info_dict):
                            # Update session status
                            self._session_manager.archive_session(session_id)
                            stats["archived"] += 1
                            if self._config["compress_enabled"]:
                                stats["compressed"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        stats["skipped"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing session {session_id}: {e}")
                    stats["errors"] += 1
            
            # Clean old archives
            cleaned = await self.cleanup_old_archives()
            stats["cleaned"] = cleaned
            
            stats["completed_at"] = datetime.now().isoformat()
            
            # Emit completion event
            await self.emit(EventTypes.FLUSH_COMPLETED, stats)
            
            logger.info(f"✓ Flush completed: archived={stats['archived']}, "
                       f"compressed={stats['compressed']}, skipped={stats['skipped']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"✗ Flush failed: {e}")
            stats["error"] = str(e)
            
            # Emit failure event
            await self.emit(EventTypes.FLUSH_FAILED, {
                "error": str(e),
                "stats": stats,
            })
            
            return stats
            
        finally:
            self._running = False
    
    async def manual_flush(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Manual flush with preview
        
        Args:
            dry_run: If True, only preview what would be archived
            
        Returns:
            Stats or preview dict
        """
        if not self._session_manager:
            return {"error": "SessionManager not available"}
        
        sessions_to_archive = []
        
        for session_id, info in self._session_manager.sessions.items():
            info_dict = info.to_dict() if hasattr(info, 'to_dict') else info
            
            if self.should_archive(info_dict):
                sessions_to_archive.append({
                    "session_id": session_id,
                    "topic": info.topic,
                    "last_active": info.last_active,
                    "chunks": info.chunk_count,
                    "days_inactive": info.days_since_active(),
                })
        
        if dry_run:
            logger.info(f"🔍 Dry run: {len(sessions_to_archive)} sessions would be archived")
            return {
                "dry_run": True,
                "sessions_to_archive": sessions_to_archive,
                "total_sessions": len(self._session_manager.sessions),
            }
        else:
            return await self.daily_flush()
    
    async def cleanup_old_archives(self) -> int:
        """
        Clean up archives older than retention period
        
        Returns:
            int: Number of archives cleaned
        """
        if not self._config["keep_archived_days"]:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=self._config["keep_archived_days"])
        cleaned = 0
        
        try:
            for root, dirs, files in os.walk(self._archive_path):
                for file in files:
                    if file.endswith(("_info.json", ".json.gz", ".zst", ".lz4")):
                        try:
                            file_path = os.path.join(root, file)
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            
                            if mtime < cutoff_date:
                                os.remove(file_path)
                                cleaned += 1
                                logger.debug(f"Cleaned old archive: {file}")
                                
                        except Exception as e:
                            logger.warning(f"Error cleaning {file}: {e}")
            
            if cleaned > 0:
                logger.info(f"🗑️ Cleaned {cleaned} old archives")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error during archive cleanup: {e}")
            return 0
    
    def get_archive_stats(self) -> Dict[str, Any]:
        """Get archive statistics"""
        stats = {
            "total_archives": 0,
            "compressed_count": 0,
            "by_month": {},
        }
        
        if not os.path.exists(self._archive_path):
            return stats
        
        try:
            for item in os.listdir(self._archive_path):
                item_path = os.path.join(self._archive_path, item)
                if os.path.isdir(item_path):
                    files = os.listdir(item_path)
                    json_count = len([f for f in files if f.endswith(".json")])
                    gz_count = len([f for f in files if ".gz" in f or ".zst" in f or ".lz4" in f])
                    
                    stats["by_month"][item] = {
                        "total": json_count + gz_count,
                        "compressed": gz_count,
                    }
                    stats["total_archives"] += json_count + gz_count
                    stats["compressed_count"] += gz_count
                    
        except Exception as e:
            logger.error(f"Error getting archive stats: {e}")
        
        return stats
    
    async def _on_session_closed(self, event):
        """Handle session closed event - trigger flush check"""
        # Optional: Auto-flush when sessions are closed
        pass
    
    # Note: compress_file and decompress_file methods REMOVED
    # These are now handled by CompressionManager (no code duplication!)
