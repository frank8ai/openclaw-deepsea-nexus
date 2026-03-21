"""
Backward compatibility layer for Deep-Sea Nexus.

Maintains the legacy sync API while the package evolves independently from the
plugin runtime protocol version.
"""

import asyncio
import os
from pathlib import Path

try:
    from .compat_async import run_coro_sync
except ImportError:
    from compat_async import run_coro_sync

try:
    from ._version import __version__ as PACKAGE_VERSION
except ImportError:
    from _version import __version__ as PACKAGE_VERSION
from typing import List, Dict, Any, Optional
import logging

try:
    from .core.plugin_system import get_plugin_registry, PluginState
    from .core.config_manager import get_config_manager
    from .plugins.nexus_core_plugin import RecallResult
    from .write_guard import validate_write_target, emit_write_guard_alert
except ImportError:
    from core.plugin_system import get_plugin_registry, PluginState
    from core.config_manager import get_config_manager
    from plugins.nexus_core_plugin import RecallResult
    from write_guard import validate_write_target, emit_write_guard_alert

logger = logging.getLogger(__name__)


def _enforce_write_guard(context: str) -> bool:
    # In test mode we allow lexical-only writes so degraded-mode can be exercised
    # without requiring external vector DB env vars.
    if os.environ.get("NEXUS_TEST_MODE") == "1":
        return True

    ok, detail = validate_write_target(context=context)
    if ok:
        return True

    alert = {
        "event": "write_guard_blocked",
        "context": context,
        "reason": detail.get("reason", "unknown"),
        "vector_db": detail.get("vector_db", ""),
        "collection": detail.get("collection", ""),
        "expected_vector_db": detail.get("expected_vector_db", ""),
        "expected_collection": detail.get("expected_collection", ""),
    }
    emit_write_guard_alert(alert)
    logger.error(
        "[NEXUS_WRITE_GUARD_BLOCK] context=%s reason=%s vector_db=%s collection=%s",
        context,
        detail.get("reason", "unknown"),
        detail.get("vector_db", ""),
        detail.get("collection", ""),
    )
    return False


def _verify_write_hit(plugin: Any, doc_id: str, context: str) -> bool:
    if not doc_id:
        return False

    if os.environ.get("NEXUS_TEST_MODE") == "1":
        return True
    backend = getattr(plugin, "_vector_backend", None)
    if backend is None:
        emit_write_guard_alert(
            {
                "event": "write_verify_backend_missing",
                "context": context,
                "doc_id": str(doc_id),
            }
        )
        logger.error("[NEXUS_WRITE_VERIFY_BACKEND_MISSING] context=%s doc_id=%s", context, doc_id)
        return False

    # Fallback backend is memory-only and should not be treated as durable write success.
    if bool(getattr(backend, "is_fallback", False)):
        emit_write_guard_alert(
            {
                "event": "write_verify_fallback_backend",
                "context": context,
                "doc_id": str(doc_id),
            }
        )
        logger.error("[NEXUS_WRITE_VERIFY_FALLBACK_BACKEND] context=%s doc_id=%s", context, doc_id)
        return False

    try:
        verify_ids: List[str] = []
        # legacy dict backend: {manager, recall, ...}
        if isinstance(backend, dict) and "manager" in backend:
            manager = backend.get("manager")
            collection = getattr(manager, "collection", None)
            if collection is not None and hasattr(collection, "get"):
                data = collection.get(ids=[doc_id], include=[])
                verify_ids = data.get("ids") or []
        # vector store wrapper (vector_store.py / vector_store_legacy.py)
        elif hasattr(backend, "get"):
            data = backend.get(ids=[doc_id], limit=1)
            verify_ids = data.get("ids") or []

        if doc_id in verify_ids:
            return True

        emit_write_guard_alert(
            {
                "event": "write_verify_vector_miss",
                "context": context,
                "doc_id": str(doc_id),
            }
        )
        logger.error("[NEXUS_WRITE_VERIFY_VECTOR_MISS] context=%s doc_id=%s", context, doc_id)
        return False
    except Exception as exc:
        emit_write_guard_alert(
            {
                "event": "write_verify_error",
                "context": context,
                "doc_id": str(doc_id),
                "reason": str(exc),
            }
        )
        logger.error("[NEXUS_WRITE_VERIFY_ERROR] context=%s doc_id=%s error=%s", context, doc_id, exc)
        return False


def resolve_default_config_path() -> Optional[str]:
    """
    Resolve default Deep-Sea Nexus config path when caller does not pass one.

    This prevents "config written but not applied" when hooks invoke nexus_init()
    without an explicit config_path.
    """
    candidates = []
    try:
        candidates.append(Path(__file__).resolve().with_name("config.json"))
    except Exception:
        pass

    home = Path(os.environ.get("HOME", "~")).expanduser()
    candidates.extend([
        home / ".openclaw" / "workspace" / "skills" / "deepsea-nexus" / "config.json",
        home / ".openclaw" / "skills" / "deepsea-nexus" / "config.json",
    ])

    for path in candidates:
        try:
            if path.exists():
                return str(path)
        except Exception:
            continue
    return None

try:
    from .brain import configure_brain, brain_retrieve as _brain_retrieve, brain_write as _brain_write, checkpoint as _brain_checkpoint, rollback as _brain_rollback, list_versions as _brain_list_versions, backfill_embeddings as _brain_backfill_embeddings
except ImportError:
    from brain import configure_brain, brain_retrieve as _brain_retrieve, brain_write as _brain_write, checkpoint as _brain_checkpoint, rollback as _brain_rollback, list_versions as _brain_list_versions, backfill_embeddings as _brain_backfill_embeddings

# =============================================================================
# Backward Compatible API Functions
# =============================================================================

def nexus_init(config_path: Optional[str] = None) -> bool:
    """
    Initialize Nexus (v2.x compatible)
    
    This function provides 100% backward compatibility with v2.x code.
    It automatically initializes the plugin system if not already done.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        bool: True if initialized successfully
        
    Example (v2.x style - still works):
        from deepsea_nexus import nexus_init, nexus_recall
        nexus_init()
        results = nexus_recall("Python")
    """
    registry = get_plugin_registry()
    
    # Check if already initialized
    plugin = registry.get("nexus_core")
    if plugin and plugin.state == PluginState.ACTIVE:
        return True
    
    # Load configuration (prefer explicit path; otherwise auto-discover config.json)
    resolved_config_path = config_path or resolve_default_config_path()
    config = get_config_manager(resolved_config_path)
    if resolved_config_path:
        config.load_file(resolved_config_path)

    cfg = config.get_all()
    if not isinstance(cfg, dict):
        cfg = {}

    # Ensure plugin auto-load order includes config_manager (dependency root)
    plugins_cfg = cfg.get("plugins", {}) if isinstance(cfg.get("plugins", {}), dict) else {}
    auto_load = plugins_cfg.get("auto_load")
    if not auto_load:
        plugins_cfg["auto_load"] = [
            "config_manager",
            "nexus_core",
            "session_manager",
            "smart_context",
            "flush_manager",
        ]
    cfg["plugins"] = plugins_cfg
    brain_cfg = cfg.get("brain", {}) if isinstance(cfg, dict) else {}
    env_enabled = os.environ.get("DEEPSEA_BRAIN_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    brain_enabled = bool(brain_cfg.get("enabled", False) or env_enabled)
    brain_base_path = brain_cfg.get("base_path", ".") if isinstance(brain_cfg, dict) else "."
    brain_max_snapshots = brain_cfg.get("max_snapshots", 20) if isinstance(brain_cfg, dict) else 20
    configure_brain(enabled=brain_enabled, base_path=brain_base_path, max_snapshots=brain_max_snapshots)
    
    # Register plugins if needed
    if not plugin:
        try:
            from .app import create_app
        except ImportError:
            from app import create_app

        # Create and initialize app (handles plugin registration + dependency order)
        app = create_app(resolved_config_path)
        return bool(run_coro_sync(app.initialize()))
    
    # Initialize existing plugin
    config_dict = config.get_all()
    # Ensure dependency order includes config_manager
    auto_load = config_dict.get("plugins", {}).get("auto_load")
    if not auto_load:
        config_dict.setdefault("plugins", {})["auto_load"] = [
            "config_manager",
            "nexus_core",
            "session_manager",
            "smart_context",
            "flush_manager",
        ]

    ok = bool(run_coro_sync(registry.load("config_manager", config_dict)))
    ok2 = bool(run_coro_sync(registry.load("nexus_core", config_dict)))
    return bool(ok and ok2)


def nexus_recall(query: str, n: int = 5) -> List[RecallResult]:
    """
    Semantic recall/search (v2.x compatible)
    
    Args:
        query: Search query
        n: Number of results to return
        
    Returns:
        List of RecallResult objects
        
    Example (v2.x style - still works):
        results = nexus_recall("Python decorators", 5)
        for r in results:
            print(f"[{r.relevance:.2f}] {r.source}")
    """
    registry = get_plugin_registry()
    plugin = registry.get("nexus_core")
    
    # Auto-initialize if needed
    if plugin is None or plugin.state != PluginState.ACTIVE:
        if not nexus_init():
            logger.error("Failed to initialize Nexus")
            return []
        plugin = registry.get("nexus_core")
    
    if plugin is None:
        return []
    
    # Run async search
    try:
        return run_coro_sync(plugin.search_recall(query, n))
    except Exception as e:
        logger.error(f"Recall error: {e}")
        return []


# Alias for compatibility
nexus_search = nexus_recall


def nexus_add(content: str, title: str, tags: Any = "") -> Optional[str]:
    """
    Add document to index (v2.x compatible)
    
    Args:
        content: Document content
        title: Document title
        tags: Comma-separated tags (str) or list[str]
        
    Returns:
        str: Document ID on success, None on failure
        
    Example (v2.x style - still works):
        doc_id = nexus_add(
            content="Python is great...",
            title="Python Notes",
            tags="python, programming"
        )
    """
    registry = get_plugin_registry()
    plugin = registry.get("nexus_core")

    if not _enforce_write_guard("compat.nexus_add"):
        return None
    
    # Auto-initialize if needed
    if plugin is None or plugin.state != PluginState.ACTIVE:
        if not nexus_init():
            return None
        plugin = registry.get("nexus_core")
    
    if plugin is None:
        return None
    
    try:
        normalized_tags = tags
        if isinstance(normalized_tags, list):
            normalized_tags = ",".join([str(t).strip() for t in normalized_tags if str(t).strip()])
        elif normalized_tags is None:
            normalized_tags = ""
        else:
            normalized_tags = str(normalized_tags)

        doc_id = run_coro_sync(plugin.add_document(content, title, normalized_tags))
        if not doc_id:
            return None
        if not _verify_write_hit(plugin, str(doc_id), "compat.nexus_add"):
            return None
        return str(doc_id)
    except Exception as e:
        logger.error(f"Add error: {e}")
        return None


# Alias for compatibility
nexus_add_document = nexus_add


def nexus_write(
    content: str,
    title: str = "",
    *,
    priority: str = "P1",
    kind: str = "fact",
    source: str = "",
    tags: str = "",
    strict: bool = False,
) -> Optional[str]:
    """Tiered write contract (recommended).

    Encodes structured fields into tags so all agents share the same schema while
    keeping the underlying storage API backward compatible.

    strict:
        - True: invalid priority/kind => reject (return None)
        - False: invalid values are normalized to safe defaults
    """

    if not _enforce_write_guard("compat.nexus_write"):
        return None

    pr = str(priority or "P1").strip().upper()
    if pr == "#GOLD":
        pr = "GOLD"
    if pr not in {"P0", "P1", "P2", "GOLD"}:
        if strict:
            return None
        pr = "P1"

    kd = str(kind or "fact").strip().lower()
    if kd not in {"fact", "decision", "strategy", "pitfall", "code_pattern", "summary", "task"}:
        if strict:
            return None
        kd = "fact"

    src = str(source or "").strip()

    tag_parts = []
    if tags:
        tag_parts.append(str(tags))
    tag_parts.append(f"priority:{pr}")
    tag_parts.append(f"kind:{kd}")
    if src:
        tag_parts.append(f"source:{src}")

    merged_tags = ",".join([p for p in tag_parts if p])
    return nexus_add(content=content, title=title or (kd + ":"), tags=merged_tags)


def nexus_add_documents(documents: List[Dict[str, str]], batch_size: int = 10) -> List[str]:
    """
    Add multiple documents (v2.x compatible)
    
    Args:
        documents: List of {content, title, tags} dicts
        batch_size: Processing batch size
        
    Returns:
        List of document IDs
    """
    results = []
    
    for doc in documents:
        doc_id = nexus_add(
            content=doc.get("content", ""),
            title=doc.get("title", ""),
            tags=doc.get("tags", ""),
        )
        if doc_id:
            results.append(doc_id)
    
    return results


def nexus_stats() -> Dict[str, Any]:
    """
    Get statistics (v2.x compatible)
    
    Returns:
        Dict with stats including total_documents
        
    Example (v2.x style - still works):
        stats = nexus_stats()
        print(f"Documents: {stats['total_documents']}")
    """
    registry = get_plugin_registry()
    plugin = registry.get("nexus_core")
    
    if plugin is None or plugin.state != PluginState.ACTIVE:
        return {
            "total_documents": 0,
            "status": "not_initialized",
            "version": "3.0.0",
        }
    
    return plugin.stats()


def nexus_health() -> Dict[str, Any]:
    """
    Get health status (v2.x compatible)
    
    Returns:
        Dict with health information
        
    Example (v2.x style - still works):
        health = nexus_health()
        if health['available']:
            print("Nexus is ready")
    """
    registry = get_plugin_registry()
    
    health = {
        "available": False,
        "initialized": False,
        "documents": 0,
        "version": "3.0.0",
        "plugins": {},
    }
    
    for name in ["nexus_core", "session_manager", "execution_guard", "runtime_middleware", "flush_manager"]:
        plugin = registry.get(name)
        if plugin:
            health["plugins"][name] = {
                "state": plugin.state.name,
                "version": plugin.metadata.version if plugin.metadata else "unknown",
            }
            if hasattr(plugin, "get_health_summary"):
                try:
                    health["plugins"][name]["summary"] = plugin.get_health_summary()
                except Exception:
                    pass
            if name == "nexus_core":
                health["available"] = True
                health["initialized"] = plugin.state == PluginState.ACTIVE
                health["documents"] = plugin.stats().get("total_documents", 0)
    
    return health


# =============================================================================
# Session Manager Compatibility
# =============================================================================

def get_session_manager():
    """Get SessionManager instance (v2.x compatible).

    Ensures Nexus is initialized so the session_manager plugin is active.
    """
    registry = get_plugin_registry()
    mgr = registry.get("session_manager")
    if mgr is not None and mgr.state == PluginState.ACTIVE:
        return mgr

    # Auto-initialize if needed
    if not nexus_init():
        return registry.get("session_manager")

    mgr = registry.get("session_manager")
    if mgr is not None and mgr.state == PluginState.ACTIVE:
        return mgr
    return mgr


def start_session(topic: str) -> str:
    """Create new session (v2.x compatible)."""
    mgr = get_session_manager()
    if mgr and hasattr(mgr, "start_session"):
        return mgr.start_session(topic)
    return ""


def get_session(session_id: str):
    """Get session by ID (v2.x compatible)"""
    mgr = get_session_manager()
    if mgr:
        return mgr.get_session(session_id)
    return None


def close_session(session_id: str) -> bool:
    """Close session (v2.x compatible)."""
    mgr = get_session_manager()
    if mgr and hasattr(mgr, "close_session"):
        return bool(mgr.close_session(session_id))
    return False


# =============================================================================
# Flush Manager Compatibility
# =============================================================================

def get_flush_manager():
    """
    Get FlushManager instance (v2.x compatible)
    
    Returns:
        FlushManagerPlugin instance or None
    """
    registry = get_plugin_registry()
    return registry.get("flush_manager")


def manual_flush(dry_run: bool = True) -> Dict[str, Any]:
    """
    Manual flush (v2.x compatible)
    
    Note: Now returns coroutine - use asyncio.run() or await
    
    Args:
        dry_run: If True, only preview
        
    Returns:
        Dict with flush results
    """
    mgr = get_flush_manager()
    if mgr:
        # Return coroutine for async execution
        return mgr.manual_flush(dry_run)
    return {"error": "FlushManager not available"}


# =============================================================================
# Compression Compatibility
# =============================================================================

def nexus_compress_session(session_path: str, compressed_path: str = None) -> str:
    """
    Compress session file (v2.x compatible)
    
    Now uses unified CompressionManager instead of duplicate code.
    
    Args:
        session_path: Source file path
        compressed_path: Target file path (optional)
        
    Returns:
        str: Compressed file path
    """
    try:
        from .storage.compression import compress_file
    except ImportError:
        from storage.compression import compress_file
    result = compress_file(session_path, compressed_path)
    return result.data.get("target_path", "") if result.success else ""


def nexus_decompress_session(compressed_path: str, output_path: str = None) -> str:
    """
    Decompress session file (v2.x compatible)
    
    Now uses unified CompressionManager instead of duplicate code.
    
    Args:
        compressed_path: Compressed file path
        output_path: Output file path (optional)
        
    Returns:
        str: Decompressed file path
    """
    try:
        from .storage.compression import decompress_file
    except ImportError:
        from storage.compression import decompress_file
    result = decompress_file(compressed_path, output_path)
    return result.data.get("target_path", "") if result.success else ""


# =============================================================================
# Version Info
# =============================================================================

def brain_retrieve(query: str, mode: str = "facts", limit: int = 5, min_score: float = 0.2, priority_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Optional brain-layer retrieval hook (MVP)."""
    return _brain_retrieve(
        query=query,
        mode=mode,
        limit=limit,
        min_score=min_score,
        priority_filter=priority_filter,
    )


def brain_write(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Optional brain-layer write hook (MVP)."""
    out = _brain_write(record)
    return out.to_dict() if out else None


def brain_checkpoint() -> Dict[str, int]:
    """Optional brain-layer checkpoint hook (MVP)."""
    return _brain_checkpoint()


def brain_rollback(version: str) -> bool:
    """Optional brain-layer rollback hook (MVP)."""
    return bool(_brain_rollback(version))


def brain_list_versions() -> List[str]:
    """Optional brain-layer versions listing hook (MVP)."""
    return list(_brain_list_versions())


def brain_backfill_embeddings(limit: int = 0) -> Dict[str, int]:
    """Optional brain-layer embedding backfill hook (MVP)."""
    return _brain_backfill_embeddings(limit=limit)


def get_version() -> str:
    """Get the current package version."""
    return PACKAGE_VERSION


# Export all backward compatible functions
__all__ = [
    # Core API (v2.x compatible)
    "nexus_init",
    "nexus_recall",
    "nexus_search",
    "nexus_add",
    "nexus_add_document",
    "nexus_add_documents",
    "nexus_stats",
    "nexus_health",
    
    # Session API (v2.x compatible)
    "get_session_manager",
    "start_session",
    "get_session",
    "close_session",
    
    # Flush API (v2.x compatible)
    "get_flush_manager",
    "manual_flush",
    
    # Compression API (v2.x compatible)
    "nexus_compress_session",
    "nexus_decompress_session",
    
    # Brain API (optional MVP)
    "brain_retrieve",
    "brain_write",
    "brain_checkpoint",
    "brain_rollback",
    "brain_list_versions",
    "brain_backfill_embeddings",

    # Utilities
    "get_version",
]
