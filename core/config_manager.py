"""
Configuration Manager - Unified Configuration with Hot-Reload

Features:
- Unified configuration management
- Environment variable support
- File-based configuration with hot-reload
- Schema validation
- Hierarchical configuration (default < file < env)
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import logging

from .event_bus import get_event_bus, EventTypes

logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """Configuration source priority"""
    DEFAULT = 0
    FILE = 1
    ENV = 2
    RUNTIME = 3


@dataclass
class ConfigChange:
    """Configuration change record"""
    key: str
    old_value: Any
    new_value: Any
    source: ConfigSource


class ConfigManager:
    """
    Configuration Manager
    
    Configuration hierarchy (low to high priority):
    1. Default values
    2. Configuration file
    3. Environment variables
    4. Runtime changes
    
    Supports hot-reload of configuration files.
    """
    
    # Default configuration for Deep-Sea Nexus
    DEFAULTS = {
        "nexus": {
            "base_path": "~/.openclaw/workspace/memory",
            "vector_db_path": "~/.openclaw/workspace/memory/.vector_db_restored",
            "collection_name": "deepsea_nexus_restored",
            "embedder_name": "all-MiniLM-L6-v2",
            "embedder_dim": 384,
        },
        "session": {
            "auto_archive_days": 30,
            "keep_active_days": 7,
            "max_concurrent": 10,
            "retention_days": 90,
            "min_chunks_to_archive": 5,
            "index_file": "_sessions_index.json",
        },
        "flush": {
            "enabled": True,
            "archive_time": "03:00",
            "compress_enabled": True,
            "compress_algorithm": "gzip",  # gzip, zstd, lz4
            "archive_dir": "archive",
            "keep_archived_days": 90,
        },
        "storage": {
            "vector_backend": "chromadb",  # chromadb, faiss, milvus
            "session_backend": "json",     # json, sqlite, redis
            "cache_enabled": True,
            "cache_size": 128,
            "batch_size": 10,
        },
        "recall": {
            "default_limit": 5,
            "max_limit": 50,
            "min_relevance": 0.0,
            "cache_enabled": True,
            "cache_size": 128,
        },
        "summary": {
            "enabled": True,
            "pattern": r"---SUMMARY---\s*(.+?)\s*---END---",
            "store_original": True,
            "store_summary": True,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            "file": None,
        },
        "plugins": {
            "auto_load": [
                "config_manager",
                "nexus_core",
                "session_manager",
                "smart_context",
                "flush_manager",
            ],
            "hot_reload": True,
        },
    }
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        "NEXUS_BASE_PATH": ("nexus.base_path", str),
        "NEXUS_VECTOR_DB": ("nexus.vector_db_path", str),
        "NEXUS_COLLECTION": ("nexus.collection_name", str),
        "NEXUS_EMBEDDER": ("nexus.embedder_name", str),
        "NEXUS_SESSION_ARCHIVE_DAYS": ("session.auto_archive_days", int),
        "NEXUS_FLUSH_ENABLED": ("flush.enabled", lambda x: x.lower() in ("true", "1", "yes")),
        "NEXUS_FLUSH_COMPRESS": ("flush.compress_enabled", lambda x: x.lower() in ("true", "1", "yes")),
        "NEXUS_LOG_LEVEL": ("logging.level", str),
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        self._config: Dict[str, Any] = {}
        self._sources: Dict[str, ConfigSource] = {}
        self._callbacks: List[Callable[[ConfigChange], None]] = []
        self._config_path: Optional[Path] = None
        self._file_mtime: Optional[float] = None
        
        # Load defaults
        self._load_defaults()
        
        # Load from file
        if config_path:
            self.load_file(config_path)
        
        # Apply environment variables
        self._apply_env()
    
    def _load_defaults(self):
        """Load default configuration"""
        self._config = self._deep_copy(self.DEFAULTS)
        self._sources = {k: ConfigSource.DEFAULT for k in self._flatten_keys(self.DEFAULTS)}
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy a nested structure"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _flatten_keys(self, obj: Any, prefix: str = "") -> List[str]:
        """Get all dot-notation keys from nested dict"""
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.extend(self._flatten_keys(v, full_key))
                else:
                    keys.append(full_key)
        return keys
    
    def _deep_merge(self, base: Dict, override: Dict, source: ConfigSource):
        """Deep merge override into base, tracking sources"""
        for key, value in override.items():
            full_key = key  # Will be tracked via sources dict
            
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value, source)
            else:
                old_value = base.get(key)
                base[key] = value
                self._sources[key] = source
                
                # Notify if changed
                if old_value != value:
                    self._notify_change(ConfigChange(
                        key=key,
                        old_value=old_value,
                        new_value=value,
                        source=source
                    ))
    
    def load_file(self, path: str) -> bool:
        """
        Load configuration from file
        
        Args:
            path: Path to YAML or JSON file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            path = Path(path).expanduser()
            
            if not path.exists():
                logger.warning(f"Config file not found: {path}")
                return False
            
            # Load based on extension
            if path.suffix in ('.yaml', '.yml'):
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif path.suffix == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                logger.warning(f"Unsupported config format: {path.suffix}")
                return False
            
            # Merge into config
            self._deep_merge(self._config, data, ConfigSource.FILE)
            
            # Track file for hot-reload
            self._config_path = path
            self._file_mtime = path.stat().st_mtime
            
            logger.info(f"✓ Config loaded: {path}")
            
            # Emit event
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                loop.create_task(self._emit_reload_event())
            except RuntimeError:
                # No running event loop (sync context)
                import asyncio
                asyncio.run(self._emit_reload_event())
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to load config: {e}")
            return False
    
    async def _emit_reload_event(self):
        """Emit config reload event"""
        await get_event_bus().emit(EventTypes.CONFIG_RELOADED, {
            "path": str(self._config_path) if self._config_path else None,
            "keys": list(self._config.keys()),
        })
    
    def _apply_env(self):
        """Apply environment variable overrides"""
        for env_key, (config_key, transform) in self.ENV_MAPPINGS.items():
            value = os.environ.get(env_key)
            if value is not None:
                try:
                    transformed = transform(value)
                    self.set(config_key, transformed, source=ConfigSource.ENV)
                except Exception as e:
                    logger.warning(f"Failed to parse env var {env_key}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key
        
        Args:
            key: Dot-notation key (e.g., "session.auto_archive_days")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, 
            source: ConfigSource = ConfigSource.RUNTIME) -> bool:
        """
        Set configuration value
        
        Args:
            key: Dot-notation key
            value: Value to set
            source: Source of the change
            
        Returns:
            bool: True if set successfully
        """
        keys = key.split(".")
        target = self._config
        
        # Navigate/create path
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
            if not isinstance(target, dict):
                logger.error(f"Cannot set {key}: intermediate key is not a dict")
                return False
        
        # Set value
        final_key = keys[-1]
        old_value = target.get(final_key)
        target[final_key] = value
        self._sources[final_key] = source
        
        # Notify if changed
        if old_value != value:
            self._notify_change(ConfigChange(
                key=key,
                old_value=old_value,
                new_value=value,
                source=source
            ))
        
        return True
    
    def get_source(self, key: str) -> Optional[ConfigSource]:
        """Get the source of a configuration value"""
        return self._sources.get(key)
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration (copy)"""
        return self._deep_copy(self._config)
    
    def on_change(self, callback: Callable[[ConfigChange], None]) -> None:
        """
        Register a callback for configuration changes
        
        Args:
            callback: Function(ConfigChange) -> None
        """
        self._callbacks.append(callback)
    
    def _notify_change(self, change: ConfigChange):
        """Notify all callbacks of a change"""
        for callback in self._callbacks:
            try:
                callback(change)
            except Exception as e:
                logger.error(f"Config change callback error: {e}")
    
    def save_file(self, path: Optional[str] = None) -> bool:
        """
        Save current configuration to file
        
        Args:
            path: File path (defaults to loaded path)
            
        Returns:
            bool: True if saved successfully
        """
        path = path or self._config_path
        if not path:
            logger.error("No config path specified")
            return False
        
        try:
            path = Path(path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Config saved: {path}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to save config: {e}")
            return False
    
    def check_reload(self) -> bool:
        """
        Check if config file has changed and reload if necessary
        
        Returns:
            bool: True if reloaded
        """
        if not self._config_path:
            return False
        
        try:
            current_mtime = self._config_path.stat().st_mtime
            if current_mtime != self._file_mtime:
                logger.info("Config file changed, reloading...")
                return self.load_file(str(self._config_path))
        except Exception as e:
            logger.error(f"Error checking config file: {e}")
        
        return False
    
    def validate(self) -> List[str]:
        """
        Validate current configuration
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check required paths
        base_path = self.get("nexus.base_path")
        if base_path:
            path = Path(base_path).expanduser()
            if not path.parent.exists():
                errors.append(f"Base path parent does not exist: {path.parent}")
        
        # Check numeric ranges
        archive_days = self.get("session.auto_archive_days")
        if archive_days is not None and (not isinstance(archive_days, int) or archive_days < 1):
            errors.append("session.auto_archive_days must be a positive integer")
        
        # Check enum values
        compress_algo = self.get("flush.compress_algorithm")
        if compress_algo and compress_algo not in ("gzip", "zstd", "lz4"):
            errors.append(f"Invalid compress_algorithm: {compress_algo}")
        
        return errors
    
    def reset_to_defaults(self):
        """Reset configuration to defaults (clear file and runtime changes)"""
        self._load_defaults()
        self._apply_env()  # Re-apply env vars
        logger.info("Configuration reset to defaults")


# Global config manager instance
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the global configuration manager
    
    Args:
        config_path: Path to config file (only used on first call)
        
    Returns:
        ConfigManager instance
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(config_path)
    return _config_manager_instance


def reset_config_manager() -> ConfigManager:
    """Reset and recreate the global configuration manager"""
    global _config_manager_instance
    _config_manager_instance = ConfigManager()
    return _config_manager_instance


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value (convenience)"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> bool:
    """Set configuration value (convenience)"""
    return get_config_manager().set(key, value)
