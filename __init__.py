"""
Deep-Sea Nexus v4.4.0
AI Agent Long-term Memory System - Hot-Pluggable Architecture

v4.4.0 patch highlights:
- Degraded vector mode when chromadb is unavailable
- Hybrid recall (vector + lexical fallback + optional brain merge)
- Runtime capability/recall telemetry for fast diagnosis
- Python 3.8-safe plugin registry lock behavior
- Stable test gate under missing optional dependencies
- Smart Context artifacts templates + validator + safe digest cron

New API (v4.x - Recommended):
    from deepsea_nexus import create_app
    
    app = create_app()
    await app.initialize()
    await app.start()
    
    # Use plugins
    results = await app.plugins["nexus_core"].search_recall("query")

Backward Compatible API (v2.x - Still Works):
    from deepsea_nexus import nexus_init, nexus_recall
    
    nexus_init()
    results = nexus_recall("query")

Features:
- Hot-pluggable architecture
- Event-driven communication
- Unified compression (no code duplication)
- Structured summaries for smarter brain
- 100% backward compatible
"""

__version__ = "4.4.0"
__author__ = "Deep-Sea Nexus Team"

# =============================================================================
# v3.2 Enhancement - Layered Config Loader (89% Token Saving)
# =============================================================================

try:
    from .v3_2_enhancement.v3_2_core.config_loader import (
        get_config_loader,
        get_resident_config,
        load_task_config,
        list_capabilities,
    )
    from .v3_2_enhancement.v3_2_core.nexus_v3 import Nexus
    V3_2_AVAILABLE = True
except ImportError:
    V3_2_AVAILABLE = False

# =============================================================================
# New API (v3.0) - Recommended
# =============================================================================

from .app import (
    create_app,
    NexusApplication,
    get_app,
    set_app,
)

from .core.plugin_system import (
    NexusPlugin,
    PluginMetadata,
    PluginRegistry,
    PluginState,
    get_plugin_registry,
)

from .core.event_bus import (
    EventBus,
    EventTypes,
    EventPriority,
    Event,
    get_event_bus,
)

from .core.config_manager import (
    ConfigManager,
    ConfigChange,
    get_config_manager,
)

from .storage.compression import (
    CompressionManager,
    GzipBackend,
    ZstdBackend,
    Lz4Backend,
    compress_file,
    decompress_file,
    read_compressed,
)

from .storage.base import (
    RecallResult,
    StorageResult,
    VectorStorageBackend,
    SessionStorageBackend,
    CompressionBackend,
)

# =============================================================================
# Context Engine (v3.1) - Smart Context System
# =============================================================================

from .plugins.smart_context import (
    SmartContextPlugin,
    store_conversation,
    inject_memory_context,
)

from .plugins.context_engine import (
    ContextEngine,
    get_engine,
    smart_retrieve,
    inject_context,
    detect_trigger,
    store_summary,
    ContextEnginePlugin,
    StructuredSummary,
    parse_summary,
)

# Backward-compatible SummaryParser + prompt helper (v3.1 legacy API)
from .auto_summary import SummaryParser

# Backward-compatible helper: create_summary_prompt
create_summary_prompt = SummaryParser.create_structured_summary_prompt

# =============================================================================
# Backward Compatible API (v2.x)
# =============================================================================

from .compat import (
    # Core
    nexus_init,
    nexus_recall,
    nexus_search,
    nexus_add,
    nexus_add_document,
    nexus_add_documents,
    nexus_write,
    nexus_stats,
    nexus_health,
    
    # Session
    get_session_manager,
    start_session,
    get_session,
    close_session,
    
    # Flush
    get_flush_manager,
    manual_flush,
    
    # Compression
    nexus_compress_session,
    nexus_decompress_session,

    # Brain (optional MVP)
    brain_retrieve,
    brain_write,
    brain_checkpoint,
    brain_rollback,

    # Utils
    get_version,
)

# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Version
    "__version__",
    
    # New API (v3.0)
    "create_app",
    "NexusApplication",
    "get_app",
    "set_app",
    
    # Core Components
    "NexusPlugin",
    "PluginMetadata",
    "PluginRegistry",
    "PluginState",
    "get_plugin_registry",
    
    # Event Bus
    "EventBus",
    "EventTypes",
    "EventPriority",
    "Event",
    "get_event_bus",
    
    # Config
    "ConfigManager",
    "ConfigChange",
    "get_config_manager",
    
    # Storage
    "RecallResult",
    "StorageResult",
    "VectorStorageBackend",
    "SessionStorageBackend",
    "CompressionBackend",
    
    # Compression
    "CompressionManager",
    "GzipBackend",
    "ZstdBackend",
    "Lz4Backend",
    "compress_file",
    "decompress_file",
    "read_compressed",
    
    # Context Engine (v3.1)
    "SmartContextPlugin",
    "store_conversation",
    "inject_memory_context",
    "rescue_before_compress",
    "get_rescue_context",
    "clear_rescue",
    "ContextEngine",
    "get_engine",
    "smart_retrieve",
    "inject_context",
    "detect_trigger",
    "store_summary",
    "ContextEngine",
    "get_engine",
    "smart_retrieve",
    "inject_context",
    "detect_trigger",
    "store_summary",
    "StructuredSummary",
    "SummaryParser",
    "parse_summary",
    "create_summary_prompt",
    
    # Backward Compatible API (v2.x)
    "nexus_init",
    "nexus_recall",
    "nexus_search",
    "nexus_add",
    "nexus_add_document",
    "nexus_add_documents",
    "nexus_write",
    "nexus_stats",
    "nexus_health",
    "get_session_manager",
    "start_session",
    "get_session",
    "close_session",
    "get_flush_manager",
    "manual_flush",
    "nexus_compress_session",
    "nexus_decompress_session",

    # Brain API (optional MVP)
    "brain_retrieve",
    "brain_write",
    "brain_checkpoint",
    "brain_rollback",

    "get_version",
]

# =============================================================================
# Module Info
# =============================================================================

def info():
    """Print module information"""
    print(f"Deep-Sea Nexus v{__version__}")
    print("Hot-Pluggable Architecture")
    print("\nQuick Start:")
    print("  from deepsea_nexus import create_app")
    print("  app = create_app()")
    print("  await app.initialize()")
    print("  await app.start()")
