"""
Nexus Core Plugin v3.0

Refactored NexusCore using Plugin architecture.
Simplified core with storage abstraction and unified compression.
"""

import importlib.util
import json
import os
import re
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

from ..core.plugin_system import NexusPlugin, PluginMetadata, PluginState
from ..core.event_bus import EventTypes
from ..storage.base import RecallResult

import logging
logger = logging.getLogger(__name__)


class NexusCorePlugin(NexusPlugin):
    """
    Nexus Core Plugin - Semantic Memory System
    
    Provides:
    - Semantic search/recall
    - Incremental document indexing
    - Unified API for memory operations
    
    Note: Compression is now handled by CompressionManager (storage.compression)
    No duplicate compression code in this module!
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="nexus_core",
            version="3.0.0",
            description="Semantic memory and RAG recall",
            dependencies=["config_manager"],
            hot_reloadable=True,
        )
        self._vector_backend = None
        self._config = None
        self._available = False
        self._vector_available = False
        self._vector_reason = ""

        # Runtime capabilities and observability
        self._capabilities: Dict[str, Any] = {}
        self._metrics_path: Optional[str] = None

        # Hybrid retrieval controls
        self._hybrid_enabled = True
        self._hybrid_min_hits = 2
        self._hybrid_lexical_boost = 0.15

        # In-memory lexical cache (degraded mode + hybrid补全)
        self._lexical_docs: Dict[str, Dict[str, Any]] = {}
        self._lexical_order: List[str] = []
        self._lexical_max_docs = 5000

        # Optional vNext brain hook (feature-flagged)
        self._brain_enabled = False
        self._brain_available = False
        self._brain_mode = "facts"
        self._brain_min_score = 0.2
        self._brain_merge = "append"  # append|replace

    def _detect_capabilities(self) -> Dict[str, Any]:
        def _has_module(name: str) -> bool:
            try:
                return importlib.util.find_spec(name) is not None
            except Exception:
                return False

        return {
            "chromadb": _has_module("chromadb"),
            "sentence_transformers": _has_module("sentence_transformers"),
            "yaml": _has_module("yaml"),
        }

    def _resolve_metrics_path(self, config: Dict[str, Any]) -> Optional[str]:
        base_path = ""
        if isinstance(config, dict):
            paths = config.get("paths", {}) if isinstance(config.get("paths", {}), dict) else {}
            nexus_cfg = config.get("nexus", {}) if isinstance(config.get("nexus", {}), dict) else {}
            base_path = (
                paths.get("base")
                or config.get("base_path")
                or config.get("workspace_root")
                or nexus_cfg.get("base_path", "")
            )
        if not base_path:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            base_path = os.path.expanduser(str(base_path))
            log_dir = os.path.join(base_path, "logs")
            os.makedirs(log_dir, exist_ok=True)
            return os.path.join(log_dir, "nexus_core_metrics.log")
        except Exception:
            return None

    def _append_metrics(self, payload: Dict[str, Any]) -> None:
        if not self._metrics_path:
            return
        try:
            payload.setdefault("schema_version", "4.4.0")
            payload.setdefault("component", "nexus_core")
            payload.setdefault("event", "unknown")
            payload.setdefault("ts", time.time())
            payload.setdefault("ts_iso", datetime.now().isoformat())
            with open(self._metrics_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            return

    def _tokenize(self, text: str) -> Set[str]:
        return {t for t in re.findall(r"[\w\u4e00-\u9fff]+", (text or "").lower()) if t}

    def _remember_lexical(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]]) -> None:
        did = (doc_id or str(uuid.uuid4())[:8]).strip()
        meta = metadata or {}
        self._lexical_docs[did] = {
            "doc_id": did,
            "content": content or "",
            "metadata": meta,
            "tokens": self._tokenize(content or ""),
            "source": str(meta.get("title", did)),
        }
        self._lexical_order.append(did)
        if len(self._lexical_order) > self._lexical_max_docs:
            stale = self._lexical_order.pop(0)
            self._lexical_docs.pop(stale, None)

    def _lexical_recall(self, query: str, n: int) -> List[RecallResult]:
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []
        scored: List[RecallResult] = []
        for item in self._lexical_docs.values():
            overlap = len(q_tokens & item["tokens"])
            if overlap <= 0:
                continue
            base = overlap / float(max(1, len(q_tokens)))
            if query and query.lower() in item["content"].lower():
                base = min(1.0, base + self._hybrid_lexical_boost)
            scored.append(
                RecallResult(
                    content=item["content"],
                    source=item["source"],
                    relevance=round(float(base), 3),
                    metadata={"origin": "lexical", **(item.get("metadata") or {})},
                    doc_id=item["doc_id"],
                )
            )
        scored.sort(key=lambda r: r.relevance, reverse=True)
        return scored[: max(0, int(n))]
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Nexus Core"""
        try:
            self._available = True
            self._capabilities = self._detect_capabilities()
            self._metrics_path = self._resolve_metrics_path(config if isinstance(config, dict) else {})

            nexus_cfg = config.get("nexus", {}) if isinstance(config.get("nexus", {}), dict) else {}
            recall_cfg = config.get("recall", {}) if isinstance(config.get("recall", {}), dict) else {}
            retrieval_cfg = config.get("retrieval", {}) if isinstance(config.get("retrieval", {}), dict) else {}

            # Load configuration
            self._config = {
                "vector_db_path": nexus_cfg.get("vector_db_path"),
                "embedder_name": nexus_cfg.get("embedder_name", "all-MiniLM-L6-v2"),
                "cache_size": recall_cfg.get("cache_size", 128),
            }
            self._hybrid_enabled = bool(retrieval_cfg.get("hybrid_enabled", True))
            self._hybrid_min_hits = max(1, int(retrieval_cfg.get("hybrid_min_hits", 2)))
            self._hybrid_lexical_boost = float(retrieval_cfg.get("hybrid_lexical_boost", 0.15))
            self._lexical_max_docs = max(200, int(retrieval_cfg.get("lexical_cache_max_docs", 5000)))

            # Prefer in-repo implementation (no extra sys.path surgery).
            create_vector_store = None
            try:
                from ..vector_store_legacy import create_vector_store as _create_vector_store
                create_vector_store = _create_vector_store
            except Exception as e:
                self._vector_reason = f"vector_store_legacy import failed: {e}"
                logger.warning(self._vector_reason)

            # Optional brain hook config
            brain_cfg = config.get("brain", {}) if isinstance(config, dict) else {}
            self._brain_enabled = bool(brain_cfg.get("enabled", False))
            self._brain_mode = str(brain_cfg.get("mode", "facts"))
            self._brain_min_score = float(brain_cfg.get("min_score", 0.2))
            self._brain_merge = str(brain_cfg.get("merge", "append"))
            brain_scorer_type = str(brain_cfg.get("scorer_type", "keyword"))
            brain_base_path = brain_cfg.get("base_path") or config.get("workspace_root") or "."
            brain_max_snapshots = int(brain_cfg.get("max_snapshots", 20))
            brain_backfill_on_start = bool(brain_cfg.get("backfill_on_start", False))
            brain_backfill_limit = int(brain_cfg.get("backfill_limit", 0))
            brain_dedupe_on_write = bool(brain_cfg.get("dedupe_on_write", False))
            brain_dedupe_recent_max = int(brain_cfg.get("dedupe_recent_max", 5000))
            brain_track_usage = bool(brain_cfg.get("track_usage", True))
            brain_decay_on_checkpoint_days = int(brain_cfg.get("decay_on_checkpoint_days", 14))
            brain_decay_floor = float(brain_cfg.get("decay_floor", 0.1))
            brain_decay_step = float(brain_cfg.get("decay_step", 0.05))
            brain_tiered_recall = bool(brain_cfg.get("tiered_recall", False))
            brain_tiered_order = brain_cfg.get("tiered_order")
            brain_tiered_limits = brain_cfg.get("tiered_limits")
            brain_dedupe_on_recall = bool(brain_cfg.get("dedupe_on_recall", True))
            brain_novelty_cfg = brain_cfg.get("novelty", {}) if isinstance(brain_cfg, dict) else {}
            brain_novelty_enabled = bool(brain_novelty_cfg.get("enabled", False))
            brain_novelty_min_similarity = float(brain_novelty_cfg.get("min_similarity", 0.92))
            brain_novelty_window_seconds = int(brain_novelty_cfg.get("window_seconds", 3600))

            if self._brain_enabled:
                try:
                    from ..brain.api import configure_brain, backfill_embeddings
                    import threading

                    configure_brain(
                        enabled=True,
                        base_path=str(brain_base_path),
                        scorer_type=brain_scorer_type,
                        max_snapshots=brain_max_snapshots,
                        dedupe_on_write=brain_dedupe_on_write,
                        dedupe_recent_max=brain_dedupe_recent_max,
                        track_usage=brain_track_usage,
                        decay_on_checkpoint_days=brain_decay_on_checkpoint_days,
                        decay_floor=brain_decay_floor,
                        decay_step=brain_decay_step,
                        novelty_enabled=brain_novelty_enabled,
                        novelty_min_similarity=brain_novelty_min_similarity,
                        novelty_window_seconds=brain_novelty_window_seconds,
                        tiered_recall=brain_tiered_recall,
                        tiered_order=brain_tiered_order,
                        tiered_limits=brain_tiered_limits,
                        dedupe_on_recall=brain_dedupe_on_recall,
                    )
                    self._brain_available = True
                    logger.info("✓ Brain hook enabled")

                    if brain_backfill_on_start:
                        def _backfill_task():
                            try:
                                stats = backfill_embeddings(limit=brain_backfill_limit)
                                logger.info(f"✓ Brain backfill complete: {stats}")
                            except Exception as e:
                                logger.warning(f"Brain backfill failed: {e}")

                        threading.Thread(target=_backfill_task, daemon=True).start()
                except Exception as e:
                    self._brain_available = False
                    logger.warning(f"Brain hook enable failed; continuing without brain: {e}")

            if create_vector_store is not None:
                logger.info("🔄 Initializing vector store...")
                try:
                    store = create_vector_store(config)
                    self._vector_backend = store
                    self._vector_available = not bool(getattr(store, "is_fallback", False))
                    fallback_reason = str(getattr(store, "reason", "") or "").strip()
                    if fallback_reason:
                        self._vector_reason = fallback_reason
                    stats = await self._get_stats()
                    if self._vector_available:
                        logger.info(f"✓ Nexus Core ready ({stats.get('total_documents', 0)} documents)")
                    else:
                        logger.warning(
                            "Nexus Core running in degraded vector mode: "
                            f"{self._vector_reason or 'fallback backend'}"
                        )
                except Exception as e:
                    self._vector_backend = None
                    self._vector_available = False
                    self._vector_reason = str(e)
                    logger.warning(f"Vector store init failed, degraded mode enabled: {e}")

            self._append_metrics(
                {
                    "event": "nexus_init",
                    "vector_available": bool(self._vector_available),
                    "vector_reason": self._vector_reason,
                    "brain_enabled": bool(self._brain_enabled and self._brain_available),
                    "hybrid_enabled": bool(self._hybrid_enabled),
                    "capabilities": self._capabilities,
                }
            )

            return True
            
        except Exception as e:
            logger.exception("✗ Nexus Core init failed")
            return False
    
    async def start(self) -> bool:
        """Start the plugin"""
        logger.info("✓ Nexus Core started")
        return True
    
    async def stop(self) -> bool:
        """Stop the plugin"""
        if self._vector_backend:
            # Cleanup if needed
            pass
        logger.info("✓ Nexus Core stopped")
        return True
    
    # Core API Methods
    
    async def search_recall(self, query: str, n: int = 5) -> List[RecallResult]:
        """Semantic search with optional brain augmentation and lexical fallback."""
        started_at = time.time()
        query = (query or "").strip()
        if not query:
            return []

        out: List[RecallResult] = []
        vector_results: List[RecallResult] = []
        lexical_results: List[RecallResult] = []
        vector_error = ""

        # 1) Brain recall (optional)
        if self._brain_enabled and self._brain_available:
            try:
                from ..brain.api import brain_retrieve

                brain_limit = max(1, n)
                for rec in brain_retrieve(
                    query=query,
                    mode=self._brain_mode,
                    limit=brain_limit,
                    min_score=self._brain_min_score,
                ):
                    brain_score = float(rec.get("score", 0.65))
                    relevance = min(0.85, brain_score * 1.2)
                    out.append(
                        RecallResult(
                            content=str(rec.get("content", "")),
                            source=f"🧠 {rec.get('source', 'brain')}",
                            relevance=round(relevance, 3),
                            metadata={
                                "origin": "brain",
                                "brain": True,
                                "brain_kind": rec.get("kind", "fact"),
                                "brain_priority": rec.get("priority", "P1"),
                                "brain_score": brain_score,
                                **{k: v for k, v in rec.items() if k not in {"content", "kind", "priority", "source"}},
                            },
                            doc_id=str(rec.get("id", "")),
                        )
                    )
            except Exception as e:
                logger.warning(f"Brain recall failed; continuing without brain: {e}")

        # 2) Vector recall
        backend = self._vector_backend
        if backend is not None:
            try:
                if isinstance(backend, dict) and "recall" in backend:
                    recall = backend["recall"]
                    results = recall.search(query, n_results=n)
                    vector_results = [
                        RecallResult(
                            content=r.content,
                            source=r.metadata.get("title", r.doc_id),
                            relevance=r.relevance_score,
                            metadata={"origin": "vector", **(r.metadata or {})},
                            doc_id=r.doc_id,
                        )
                        for r in results
                    ]
                else:
                    raw = backend.search(query=query, n_results=n)
                    docs = (raw or {}).get("documents") or [[]]
                    metas = (raw or {}).get("metadatas") or [[]]
                    ids = (raw or {}).get("ids") or [[]]
                    dists = (raw or {}).get("distances") or [[]]

                    count = min(n, len(docs[0]) if docs else 0)
                    for i in range(count):
                        content = docs[0][i]
                        meta = metas[0][i] if metas and metas[0] and i < len(metas[0]) else {}
                        doc_id = ids[0][i] if ids and ids[0] and i < len(ids[0]) else ""
                        dist = dists[0][i] if dists and dists[0] and i < len(dists[0]) else None
                        relevance = 0.5 if dist is None else max(0.0, 1.0 - float(dist))
                        vector_results.append(
                            RecallResult(
                                content=str(content),
                                source=str((meta or {}).get("title", doc_id or "doc")),
                                relevance=float(relevance),
                                metadata={"origin": "vector", **(meta or {})},
                                doc_id=str(doc_id),
                            )
                        )
            except Exception as e:
                vector_error = str(e)
                logger.warning(f"Vector search failed; fallback continues: {e}")

        # 3) Lexical fallback/hybrid补全
        need_lexical = self._hybrid_enabled and (
            (not self._vector_available)
            or len(vector_results) < min(self._hybrid_min_hits, max(1, n))
        )
        if need_lexical:
            lexical_results = self._lexical_recall(query, n=max(1, n))

        # Merge strategy:
        # - replace: brain-only
        # - append: vector/lexical primary, brain fills gaps
        merged: List[RecallResult]
        if self._brain_enabled and self._brain_available and self._brain_merge == "replace":
            merged = out
        else:
            merged = list(vector_results)
            for r in lexical_results:
                if len(merged) >= n:
                    break
                merged.append(r)
            if len(merged) < n:
                merged.extend(out)
            elif not merged:
                merged = out

        dedup: Dict[str, RecallResult] = {}
        for r in merged:
            key = (r.doc_id or "").strip()
            if not key:
                key = f"{r.source}\n{r.content}".strip()
            existing = dedup.get(key)
            if existing is None or r.relevance > existing.relevance:
                dedup[key] = r

        final_results = sorted(dedup.values(), key=lambda r: r.relevance, reverse=True)[:n]
        self._append_metrics(
            {
                "event": "recall",
                "query_len": len(query),
                "n": int(n),
                "vector_hits": len(vector_results),
                "lexical_hits": len(lexical_results),
                "brain_hits": len(out),
                "final_hits": len(final_results),
                "vector_available": bool(self._vector_available),
                "vector_error": vector_error,
                "used_lexical": bool(need_lexical),
                "duration_ms": int((time.time() - started_at) * 1000),
            }
        )
        return final_results
    
    # Alias for backward compatibility
    search = search_recall
    recall = search_recall
    
    async def add_document(self, content: str, 
                          title: str = "",
                          tags: str = "",
                          doc_id: Optional[str] = None) -> Optional[str]:
        """
        Add a document to the index
        
        Args:
            content: Document content
            title: Document title
            tags: Comma-separated tags
            doc_id: Optional document ID
            
        Returns:
            str: Document ID on success, None on failure
        """
        resolved_id = (doc_id or str(uuid.uuid4())[:8]).strip()
        metadata = {"title": title or "Untitled"}
        if tags:
            metadata["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

        # Always keep an in-memory lexical copy for hybrid fallback.
        self._remember_lexical(resolved_id, content, metadata)

        # Optional brain write (best-effort; does not block vector write)
        if self._brain_enabled and self._brain_available:
            try:
                from ..brain.api import brain_write

                # Infer kind from tags/content hints
                tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
                content_lower = (content or "").lower()
                # Simple heuristic for kind inference
                if any(k in content_lower for k in ["strategy", "plan", "roadmap", "goal"]):
                    inferred_kind = "strategy"
                elif any(k in content_lower for k in ["step", "how", "guide", "tutorial"]):
                    inferred_kind = "guide"
                else:
                    inferred_kind = "fact"

                # Priority inference: P0 for critical tags, P1 for normal, P2 for low-priority
                priority = "P1"
                if any(t.lower() in {"important", "critical", "urgent", "p0"} for t in tag_list):
                    priority = "P0"
                elif any(t in content_lower for t in ["draft", "todo", "maybe", "low"]):
                    priority = "P2"

                brain_write(
                    {
                        "id": resolved_id,
                        "kind": inferred_kind,
                        "priority": priority,
                        "source": title or resolved_id or "nexus",
                        "tags": tag_list,
                        "content": content,
                    }
                )
            except Exception as e:
                logger.warning(f"Brain write failed; continuing without brain: {e}")

        backend = self._vector_backend
        vector_written = False
        write_error = ""

        try:
            if backend is not None:
                if isinstance(backend, dict) and "manager" in backend:
                    manager = backend["manager"]
                    new_id = manager.add_note(
                        content=content,
                        metadata=metadata,
                        note_id=resolved_id,
                    )
                    if new_id:
                        resolved_id = str(new_id)
                    vector_written = True
                else:
                    backend.add(
                        documents=[content],
                        ids=[resolved_id],
                        metadatas=[metadata],
                    )
                    vector_written = True

            # Emit event
            await self.emit(EventTypes.DOCUMENT_ADDED, {
                "doc_id": resolved_id,
                "title": title,
                "tags": tags,
            })

            self._append_metrics(
                {
                    "event": "add_document",
                    "doc_id": resolved_id,
                    "vector_written": bool(vector_written),
                    "vector_available": bool(self._vector_available),
                }
            )
            return resolved_id
            
        except Exception as e:
            write_error = str(e)
            logger.warning(f"Add document degraded to lexical-only mode: {e}")
            self._append_metrics(
                {
                    "event": "add_document",
                    "doc_id": resolved_id,
                    "vector_written": False,
                    "vector_available": bool(self._vector_available),
                    "error": write_error,
                }
            )
            return resolved_id
    
    async def add_documents(self, documents: List[Dict[str, str]], 
                           batch_size: int = 10) -> List[str]:
        """
        Add multiple documents in batch
        
        Args:
            documents: List of {content, title, tags, doc_id}
            batch_size: Batch size
            
        Returns:
            List of document IDs
        """
        results = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            for doc in batch:
                doc_id = await self.add_document(
                    content=doc.get("content", ""),
                    title=doc.get("title", ""),
                    tags=doc.get("tags", ""),
                    doc_id=doc.get("doc_id"),
                )
                if doc_id:
                    results.append(doc_id)
        
        return results
    
    # Backward compatibility alias
    add = add_document
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        if doc_id in self._lexical_docs:
            item = self._lexical_docs[doc_id]
            return {
                "id": item["doc_id"],
                "content": item["content"],
                "metadata": item.get("metadata", {}),
            }
        return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        deleted = False
        try:
            if doc_id in self._lexical_docs:
                self._lexical_docs.pop(doc_id, None)
                deleted = True
            backend = self._vector_backend
            if backend is not None and hasattr(backend, "delete"):
                backend.delete(ids=[doc_id])
                deleted = True
            await self.emit(EventTypes.DOCUMENT_DELETED, {"doc_id": doc_id})
            self._append_metrics({"event": "delete_document", "doc_id": doc_id, "deleted": bool(deleted)})
            return deleted
        except Exception as e:
            logger.error(f"Delete document error: {e}")
            return deleted
    
    def _collect_stats(self) -> Dict[str, Any]:
        """Collect internal stats synchronously."""
        lexical_count = len(self._lexical_docs)
        if not self._vector_backend:
            return {
                "total_documents": lexical_count,
                "vector_documents": 0,
                "lexical_documents": lexical_count,
                "status": "degraded" if lexical_count else "unavailable",
            }

        backend = self._vector_backend
        try:
            if isinstance(backend, dict) and "recall" in backend:
                recall = backend["recall"]
                stats = recall.get_recall_stats()
                return {
                    "total_documents": int(stats.get("total_documents", 0)) or lexical_count,
                    "vector_documents": int(stats.get("total_documents", 0)),
                    "lexical_documents": lexical_count,
                    "collection_name": stats.get("collection_name", "N/A"),
                    "status": "active" if self.state == PluginState.ACTIVE else "inactive",
                }

            # VectorStore wrapper
            return {
                "total_documents": int(getattr(backend, "count", 0)) or lexical_count,
                "vector_documents": int(getattr(backend, "count", 0)),
                "lexical_documents": lexical_count,
                "collection_name": getattr(backend, "collection_name", "deepsea_nexus"),
                "status": (
                    "degraded"
                    if bool(getattr(backend, "is_fallback", False))
                    else "active" if self.state == PluginState.ACTIVE else "inactive"
                ),
            }
        except Exception:
            return {
                "total_documents": lexical_count,
                "vector_documents": 0,
                "lexical_documents": lexical_count,
                "status": "error",
            }

    async def _get_stats(self) -> Dict[str, Any]:
        """Async wrapper for compatibility with async callers."""
        return self._collect_stats()
    
    def stats(self) -> Dict[str, Any]:
        """Get public stats"""
        return self._collect_stats()
    
    def health(self) -> Dict[str, Any]:
        """Get health status"""
        return {
            "available": self._available,
            "vector_available": self._vector_available,
            "vector_reason": self._vector_reason,
            "initialized": self._vector_backend is not None,
            "documents": self.stats().get("total_documents", 0),
            "state": self.state.name,
            "version": "3.0.0",
            "capabilities": self._capabilities,
            "hybrid_enabled": self._hybrid_enabled,
        }
    
    # NOTE: Compression methods REMOVED
    # Use storage.compression.CompressionManager instead
    # 
    # Old methods (removed):
    # - compress_session() -> use CompressionManager.compress_file()
    # - decompress_session() -> use CompressionManager.decompress_file()
    
    async def get_health(self) -> Dict[str, Any]:
        """Get detailed health"""
        base_health = super().get_health()
        base_health.update(self.health())
        return base_health
