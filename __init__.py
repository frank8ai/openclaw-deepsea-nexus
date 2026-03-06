"""deepsea-nexus skill package.

This file exists so local tools can import modules using package-relative imports.

Public API expected by the test suite lives here.
"""

from __future__ import annotations

from .app import NexusApplication, create_app, get_app, set_app
from .core.config_manager import ConfigManager, get_config_manager
from .core.event_bus import EventBus, get_event_bus
from .core.plugin_system import (
    PluginRegistry,
    get_plugin_registry,
    reset_plugin_registry,
    clear_plugin_registry,
)
from .nexus_core import nexus_init, nexus_recall, nexus_add, nexus_health, nexus_stats
# Prefer plugin-based session manager via compat layer (works in v3 app).
from .compat import get_session_manager, start_session, close_session
from .session_manager import SessionManager
from .storage.compression import (
    CompressionManager,
    GzipBackend,
    ZstdBackend,
    Lz4Backend,
)
from .memory_v5 import MemoryV5Service, MemoryScope


__all__ = [
    "NexusApplication",
    "create_app",
    "get_app",
    "set_app",
    "ConfigManager",
    "get_config_manager",
    "EventBus",
    "get_event_bus",
    "PluginRegistry",
    "get_plugin_registry",
    "reset_plugin_registry",
    "clear_plugin_registry",
    "nexus_init",
    "nexus_recall",
    "nexus_add",
    "nexus_health",
    "nexus_stats",
    "SessionManager",
    "get_session_manager",
    "start_session",
    "close_session",
    "CompressionManager",
    "GzipBackend",
    "ZstdBackend",
    "Lz4Backend",
    "MemoryV5Service",
    "MemoryScope",
]
