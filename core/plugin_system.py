"""
Plugin System - Hot-Pluggable Architecture for Deep-Sea Nexus

Provides lifecycle management, dependency injection, and hot-reload support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import asyncio
import logging
import importlib

from .event_bus import get_event_bus, EventBus, EventTypes

logger = logging.getLogger(__name__)


class _AsyncNullLock:
    """No-op async lock used when no event loop is available yet."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class PluginState(Enum):
    """Plugin lifecycle states"""
    REGISTERED = auto()      # Registered but not initialized
    INITIALIZING = auto()    # Initialization in progress
    ACTIVE = auto()          # Fully operational
    PAUSED = auto()          # Temporarily paused
    ERROR = auto()           # Error state
    UNLOADING = auto()       # Unload in progress
    UNLOADED = auto()        # Fully unloaded


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    hot_reloadable: bool = True  # Whether plugin supports hot reload
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class PluginHealth:
    """Plugin health status"""
    state: PluginState
    last_error: Optional[str] = None
    error_count: int = 0
    start_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.name,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": self.uptime_seconds,
        }


class NexusPlugin(ABC):
    """
    Base class for all Deep-Sea Nexus plugins
    
    To create a plugin:
    1. Inherit from NexusPlugin
    2. Set metadata in __init__
    3. Implement initialize(), start(), stop()
    4. Optionally implement reload() for hot-reload support
    """
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self.state = PluginState.REGISTERED
        self.config: Dict[str, Any] = {}
        self._event_bus: Optional[EventBus] = None
        self._health = PluginHealth(state=PluginState.REGISTERED)
        self._init_time: Optional[datetime] = None
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the plugin service
        
        Returns:
            bool: True if started successfully
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the plugin service (for hot-unload)
        
        Returns:
            bool: True if stopped successfully
        """
        pass
    
    async def reload(self, new_config: Dict[str, Any]) -> bool:
        """
        Hot-reload configuration
        
        Default implementation: stop -> reinitialize -> start
        Override for custom reload logic.
        
        Args:
            new_config: New configuration
            
        Returns:
            bool: True if reloaded successfully
        """
        if not self.metadata or not self.metadata.hot_reloadable:
            logger.warning(f"Plugin {self.metadata.name if self.metadata else 'unknown'} does not support hot reload")
            return False
        
        logger.info(f"Reloading plugin: {self.metadata.name}")
        
        # Stop current instance
        await self.stop()
        
        # Reinitialize
        success = await self.initialize(new_config)
        if not success:
            self.state = PluginState.ERROR
            return False
        
        # Restart
        success = await self.start()
        if success:
            self.state = PluginState.ACTIVE
            await self._emit_plugin_event("reloaded")
        else:
            self.state = PluginState.ERROR
        
        return success
    
    def get_health(self) -> PluginHealth:
        """Get current health status"""
        if self._health.start_time and self.state == PluginState.ACTIVE:
            self._health.uptime_seconds = (datetime.now() - self._health.start_time).total_seconds()
        return self._health
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for this plugin"""
        self._event_bus = event_bus
    
    async def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Emit an event through the plugin's event bus
        
        Automatically adds plugin name as source.
        """
        if self._event_bus:
            source = self.metadata.name if self.metadata else None
            await self._event_bus.emit(event_type, payload, source)
    
    async def _emit_plugin_event(self, action: str) -> None:
        """Emit plugin lifecycle event"""
        await self.emit(EventTypes.PLUGIN_LOADED if action == "loaded" else 
                       EventTypes.PLUGIN_UNLOADED if action == "unloaded" else
                       "plugin.reloaded", {
            "plugin": self.metadata.name if self.metadata else "unknown",
            "version": self.metadata.version if self.metadata else "unknown",
            "action": action,
            "state": self.state.name,
        })
    
    def _record_error(self, error: Exception) -> None:
        """Record an error in health status"""
        self._health.last_error = str(error)
        self._health.error_count += 1
        self.state = PluginState.ERROR


class PluginRegistry:
    """
    Plugin registry managing all plugin lifecycles
    
    Features:
    - Plugin registration and discovery
    - Dependency resolution
    - Lifecycle management
    - Hot-reload support
    """
    
    def __init__(self):
        self._plugins: Dict[str, NexusPlugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        self._states: Dict[str, PluginState] = {}
        self._event_bus: Optional[EventBus] = None
        self._lock: Optional[asyncio.Lock] = None
        self._null_lock = _AsyncNullLock()

    def _get_lock(self):
        """Create asyncio lock lazily in an active event loop."""
        if self._lock is not None:
            return self._lock
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # Some sync test paths construct the registry before creating an event loop.
            return self._null_lock
        self._lock = asyncio.Lock()
        return self._lock
    
    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the global event bus"""
        self._event_bus = event_bus
        for plugin in self._plugins.values():
            plugin.set_event_bus(event_bus)
    
    def register(self, plugin: NexusPlugin, metadata: PluginMetadata) -> bool:
        """
        Register a plugin
        
        Args:
            plugin: Plugin instance
            metadata: Plugin metadata
            
        Returns:
            bool: True if registered successfully
        """
        if metadata.name in self._plugins:
            logger.warning(f"Plugin {metadata.name} is already registered")
            return False
        
        # Set up plugin
        plugin.metadata = metadata
        if self._event_bus:
            plugin.set_event_bus(self._event_bus)
        
        # Store
        self._plugins[metadata.name] = plugin
        self._metadata[metadata.name] = metadata
        self._states[metadata.name] = PluginState.REGISTERED
        
        logger.info(f"✓ Plugin registered: {metadata.name} v{metadata.version}")
        return True
    
    async def load(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Load and initialize a plugin
        
        Args:
            name: Plugin name
            config: Configuration dictionary
            
        Returns:
            bool: True if loaded successfully
        """
        async with self._get_lock():
            if name not in self._plugins:
                logger.error(f"Plugin {name} is not registered")
                return False
            
            plugin = self._plugins[name]
            metadata = self._metadata[name]
            
            # Check dependencies
            for dep in metadata.dependencies:
                if dep not in self._plugins:
                    logger.error(f"Dependency {dep} not found for {name}")
                    return False
                if self._states.get(dep) != PluginState.ACTIVE:
                    logger.error(f"Dependency {dep} is not active for {name}")
                    return False
            
            # Initialize
            try:
                self._states[name] = PluginState.INITIALIZING
                plugin.state = PluginState.INITIALIZING
                
                success = await plugin.initialize(config)
                if not success:
                    self._states[name] = PluginState.ERROR
                    plugin.state = PluginState.ERROR
                    return False
                
                # Start
                success = await plugin.start()
                if success:
                    self._states[name] = PluginState.ACTIVE
                    plugin.state = PluginState.ACTIVE
                    plugin._health.start_time = datetime.now()
                    await plugin._emit_plugin_event("loaded")
                    logger.info(f"✓ Plugin loaded: {name}")
                    return True
                else:
                    self._states[name] = PluginState.ERROR
                    plugin.state = PluginState.ERROR
                    return False
                    
            except Exception as e:
                logger.error(f"✗ Failed to load plugin {name}: {e}")
                plugin._record_error(e)
                self._states[name] = PluginState.ERROR
                plugin.state = PluginState.ERROR
                return False
    
    async def unload(self, name: str) -> bool:
        """
        Unload a plugin (hot-unload support)
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if unloaded successfully
        """
        async with self._get_lock():
            if name not in self._plugins:
                return False
            
            plugin = self._plugins[name]
            
            # Check if other plugins depend on this
            for other_name, metadata in self._metadata.items():
                if name in metadata.dependencies and self._states.get(other_name) == PluginState.ACTIVE:
                    logger.error(f"Cannot unload {name}: {other_name} depends on it")
                    return False
            
            try:
                self._states[name] = PluginState.UNLOADING
                plugin.state = PluginState.UNLOADING
                
                success = await plugin.stop()
                if success:
                    self._states[name] = PluginState.UNLOADED
                    plugin.state = PluginState.UNLOADED
                    await plugin._emit_plugin_event("unloaded")
                    logger.info(f"✓ Plugin unloaded: {name}")
                    return True
                else:
                    self._states[name] = PluginState.ERROR
                    plugin.state = PluginState.ERROR
                    return False
                    
            except Exception as e:
                logger.error(f"✗ Error unloading plugin {name}: {e}")
                plugin._record_error(e)
                self._states[name] = PluginState.ERROR
                plugin.state = PluginState.ERROR
                return False
    
    async def reload(self, name: str, new_config: Dict[str, Any]) -> bool:
        """
        Hot-reload a plugin
        
        Args:
            name: Plugin name
            new_config: New configuration
            
        Returns:
            bool: True if reloaded successfully
        """
        if name not in self._plugins:
            return False
        
        plugin = self._plugins[name]
        success = await plugin.reload(new_config)
        
        if success:
            self._states[name] = PluginState.ACTIVE
            plugin.state = PluginState.ACTIVE
        
        return success
    
    def get(self, name: str) -> Optional[NexusPlugin]:
        """Get a plugin by name"""
        return self._plugins.get(name)
    
    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata"""
        return self._metadata.get(name)
    
    def get_state(self, name: str) -> Optional[PluginState]:
        """Get plugin state"""
        return self._states.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins"""
        return [
            {
                "name": name,
                "version": meta.version,
                "state": self._states[name].name,
                "description": meta.description,
            }
            for name, meta in self._metadata.items()
        ]
    
    def list_active(self) -> List[str]:
        """List names of all active plugins"""
        return [
            name for name, state in self._states.items()
            if state == PluginState.ACTIVE
        ]
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status of all plugins"""
        return {
            name: {
                "state": self._states[name].name,
                "health": plugin.get_health().to_dict(),
            }
            for name, plugin in self._plugins.items()
        }
    
    async def load_all(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """
        Load multiple plugins in dependency order
        
        Args:
            configs: Dictionary of {plugin_name: config}
            
        Returns:
            Dictionary of {plugin_name: success}
        """
        results = {}
        loaded = set()
        
        async def load_with_deps(name: str) -> bool:
            if name in loaded:
                return results.get(name, False)
            
            if name not in self._plugins:
                results[name] = False
                return False
            
            # Load dependencies first
            metadata = self._metadata[name]
            for dep in metadata.dependencies:
                if not await load_with_deps(dep):
                    logger.error(f"Cannot load {name}: dependency {dep} failed")
                    results[name] = False
                    return False
            
            # Load this plugin
            config = configs.get(name, {})
            success = await self.load(name, config)
            results[name] = success
            loaded.add(name)
            return success
        
        for name in configs:
            await load_with_deps(name)
        
        return results
    
    async def unload_all(self) -> Dict[str, bool]:
        """Unload all plugins in reverse dependency order"""
        results = {}
        
        # Sort by dependency (reverse order)
        unload_order = []
        unloaded = set()
        
        def add_to_unload(name: str):
            if name in unloaded:
                return
            # Find plugins that depend on this
            for other_name, meta in self._metadata.items():
                if name in meta.dependencies:
                    add_to_unload(other_name)
            unload_order.append(name)
            unloaded.add(name)
        
        for name in list(self._plugins.keys()):
            add_to_unload(name)
        
        # Unload in order
        for name in unload_order:
            results[name] = await self.unload(name)
        
        return results


# Global registry instance
_registry_instance: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance


def reset_plugin_registry() -> PluginRegistry:
    """Reset and recreate the global plugin registry"""
    global _registry_instance
    _registry_instance = PluginRegistry()
    return _registry_instance


# Backward-compat test helper
def clear_plugin_registry() -> PluginRegistry:
    """Alias for reset_plugin_registry (used by tests)."""
    return reset_plugin_registry()


# Convenience decorator for plugin registration
def plugin(metadata: PluginMetadata):
    """
    Decorator to register a plugin class
    
    Usage:
        @plugin(PluginMetadata(name="my_plugin", version="1.0.0"))
        class MyPlugin(NexusPlugin):
            pass
    """
    def decorator(cls: Type[NexusPlugin]):
        registry = get_plugin_registry()
        instance = cls()
        registry.register(instance, metadata)
        return cls
    return decorator
