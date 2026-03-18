"""deepsea-nexus skill package.

This file exists so local tools can import modules using package-relative imports.

Public API expected by the test suite lives here.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Pytest may import this file as a top-level ``__init__`` module while collecting
# ``tests/``. Bootstrap a synthetic package name so relative imports still work.
if not __package__:
    _REPO_ROOT = Path(__file__).resolve().parent
    _BOOTSTRAP_PACKAGE = "deepsea_nexus_repo_root"
    __package__ = _BOOTSTRAP_PACKAGE
    __path__ = [str(_REPO_ROOT)]
    if __spec__ is not None:
        __spec__.submodule_search_locations = [str(_REPO_ROOT)]
    _current_module = sys.modules.get(__name__)
    if _current_module is not None:
        sys.modules.setdefault(_BOOTSTRAP_PACKAGE, _current_module)


def _prefer_repo_shell_wrappers() -> None:
    if os.name != "nt":
        return
    repo_root = Path(__file__).resolve().parent
    path_entries = os.environ.get("PATH", "").split(os.pathsep) if os.environ.get("PATH") else []
    repo_root_str = str(repo_root)
    if repo_root_str not in path_entries:
        os.environ["PATH"] = os.pathsep.join([repo_root_str] + path_entries)


_prefer_repo_shell_wrappers()

from ._version import __version__
from .auto_summary import StructuredSummary, SummaryParser
from .app import NexusApplication, create_app, get_app, set_app
from .compat import (
    brain_checkpoint,
    brain_retrieve,
    brain_rollback,
    brain_write,
    close_session,
    get_flush_manager,
    get_session,
    get_session_manager,
    get_version,
    manual_flush,
    nexus_add,
    nexus_add_document,
    nexus_add_documents,
    nexus_compress_session,
    nexus_decompress_session,
    nexus_init,
    nexus_recall,
    nexus_search,
    nexus_stats,
    nexus_health,
    nexus_write,
    resolve_default_config_path,
    start_session,
)
from .core.config_manager import ConfigManager, get_config_manager
from .core.event_bus import EventBus, get_event_bus
from .core.plugin_system import (
    PluginRegistry,
    get_plugin_registry,
    reset_plugin_registry,
    clear_plugin_registry,
)
from .session_manager import SessionManager
from .storage.compression import (
    CompressionManager,
    GzipBackend,
    ZstdBackend,
    Lz4Backend,
)
from .memory_v5 import MemoryV5Service, MemoryScope

create_summary_prompt = SummaryParser.create_structured_summary_prompt


def parse_summary(response: str):
    """Backward-compatible helper around ``SummaryParser.parse``."""
    return SummaryParser.parse(response)


try:
    from .plugins.context_engine import (
        ContextEngine,
        ContextEnginePlugin,
        detect_trigger,
        get_engine,
        inject_context,
        smart_retrieve,
        store_summary,
    )
except Exception:  # pragma: no cover - keep package import resilient
    ContextEngine = None
    ContextEnginePlugin = None

    def _context_engine_unavailable(*_args, **_kwargs):
        raise ImportError("context_engine exports are unavailable in this runtime")

    get_engine = _context_engine_unavailable
    smart_retrieve = _context_engine_unavailable
    inject_context = _context_engine_unavailable
    detect_trigger = _context_engine_unavailable
    store_summary = _context_engine_unavailable

__all__ = [
    "__version__",
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
    "nexus_search",
    "nexus_add",
    "nexus_add_document",
    "nexus_add_documents",
    "nexus_health",
    "nexus_stats",
    "nexus_write",
    "resolve_default_config_path",
    "SessionManager",
    "get_session_manager",
    "start_session",
    "get_session",
    "close_session",
    "get_flush_manager",
    "manual_flush",
    "nexus_compress_session",
    "nexus_decompress_session",
    "CompressionManager",
    "GzipBackend",
    "ZstdBackend",
    "Lz4Backend",
    "StructuredSummary",
    "SummaryParser",
    "create_summary_prompt",
    "parse_summary",
    "ContextEngine",
    "ContextEnginePlugin",
    "get_engine",
    "smart_retrieve",
    "inject_context",
    "detect_trigger",
    "store_summary",
    "brain_retrieve",
    "brain_write",
    "brain_checkpoint",
    "brain_rollback",
    "get_version",
    "MemoryV5Service",
    "MemoryScope",
]
