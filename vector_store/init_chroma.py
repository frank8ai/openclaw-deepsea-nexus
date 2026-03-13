"""
Deep-Sea Nexus v2.0 - Vector Store Initialization
Phase 1: Infrastructure Setup

This module initializes the ChromaDB vector database with proper configuration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Patch chromadb persist loader before importing chromadb itself.
# This keeps old on-disk collections readable on newer chromadb.
try:
    import chroma_patch  # noqa: F401
except Exception:
    pass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import yaml
from utils.vector_db_lock import vector_db_write_lock

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_config_path(config_path: str = None) -> Path | None:
    if config_path:
        return Path(config_path).expanduser().resolve()

    env_override = os.environ.get("DEEPSEA_NEXUS_CONFIG") or os.environ.get(
        "DEEP_SEA_NEXUS_CONFIG"
    )
    candidates = []
    if env_override:
        candidates.append(Path(env_override).expanduser())

    candidates.extend(
        [
            Path(os.getcwd()) / "config.json",
            Path(os.getcwd()) / "config.yaml",
            PROJECT_ROOT / "config.json",
            PROJECT_ROOT / "config.yaml",
        ]
    )

    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded.resolve()
    return None


def load_config_file(config_path: str = None) -> dict:
    resolved = resolve_config_path(config_path)
    if resolved is None or not resolved.exists():
        return {}
    with open(resolved, "r", encoding="utf-8") as f:
        if resolved.suffix == ".json":
            return json.load(f)
        return yaml.safe_load(f) or {}


class VectorStoreInit:
    """Initialize and manage ChromaDB vector store.

    Also provides a minimal `add/search` interface for HybridStorage, so the
    summary flush pipeline doesn't need a second wrapper that re-initializes
    Chroma with different settings.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.embedder = None
        self.client = None
        self.collection = None
        self.persist_dir = ""
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON/YAML file."""
        return load_config_file(config_path)
    
    def initialize_embedder(self):
        """Initialize the sentence transformer embedder."""
        model_name = self.config['embedding']['model_name']
        print(f"Loading embedding model: {model_name}")
        
        self.embedder = SentenceTransformer(model_name)
        print(f"✓ Embedding model loaded (dimension: {self.embedder.get_sentence_embedding_dimension()})")
        
    def initialize_vector_store(self):
        """Initialize ChromaDB client and collection."""
        vs_config = self.config['vector_store']
        
        # Resolve persist directory (allow env override for shared multi-agent store)
        env_db = os.environ.get("NEXUS_VECTOR_DB", "").strip()
        if env_db:
            persist_dir = os.path.abspath(os.path.expanduser(env_db))
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            persist_dir = os.path.abspath(os.path.join(base_dir, vs_config['persist_directory']))
        
        print(f"Initializing ChromaDB at: {persist_dir}")
        
        # Create persistent client
        # NOTE: On Python 3.8, Chroma's product telemetry dependency chain
        # (posthog -> TypedDict with PEP585 generics) can raise:
        #   TypeError: 'type' object is not subscriptable
        # even when anonymized_telemetry=False.
        # We disable Chroma's product telemetry explicitly to keep the store usable.
        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
        try:
            # Avoid importing posthog on Python 3.8 (it can crash at import-time).
            # Use our local no-op implementation.
            settings.chroma_product_telemetry_impl = "vector_store.telemetry_nop.NopProductTelemetryClient"
            settings.chroma_telemetry_impl = "vector_store.telemetry_nop.NopProductTelemetryClient"
        except Exception:
            pass

        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=settings,
            tenant="default_tenant",
            database="default_database",
        )
        
        # Get or create collection (allow env override for shared multi-agent store)
        collection_name = os.environ.get("NEXUS_COLLECTION", "").strip() or vs_config['collection_name']
        distance_metric = vs_config.get('distance_metric', 'cosine')
        
        # Attach embedding function so Chroma can embed text inputs.
        class _SentenceTransformerEmbeddingFunction:
            def __init__(self, model):
                self._model = model

            def __call__(self, input):
                if isinstance(input, str):
                    input = [input]
                emb = self._model.encode(input)
                try:
                    return emb.tolist()
                except Exception:
                    return [e.tolist() for e in emb]

        embedding_fn = _SentenceTransformerEmbeddingFunction(self.embedder) if self.embedder else None

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn,
            metadata={
                "description": "Deep-Sea Nexus v2.0 memory store",
                "distance_metric": distance_metric
            }
        )
        
        print(f"✓ Collection '{collection_name}' ready")
        print(f"  - Total documents: {self.collection.count()}")
        
    def initialize_all(self):
        """Initialize both embedder and vector store."""
        print("=" * 50)
        print("Deep-Sea Nexus v2.0 - Initialization")
        print("=" * 50)
        
        self.initialize_embedder()
        self.initialize_vector_store()
        
        print("=" * 50)
        print("✓ Initialization complete!")
        print("=" * 50)
        
        return {
            'embedder': self.embedder,
            'client': self.client,
            'collection': self.collection
        }
    
    def add(self, content: str, title: str = "", tags: str = "") -> str:
        """Add a single document to the collection.

        HybridStorage expects the vector store to provide an `add` method.
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized")

        import uuid
        doc_id = str(uuid.uuid4())[:8]
        metadata = {}
        if title:
            metadata["title"] = title
        if tags:
            metadata["tags"] = tags

        lock_timeout = float(os.environ.get("NEXUS_VECTOR_LOCK_TIMEOUT", "30") or 30)
        with vector_db_write_lock(self.persist_dir, timeout_sec=lock_timeout):
            self.collection.add(documents=[content], ids=[doc_id], metadatas=[metadata])
        return doc_id

    def search(self, query: str, n_results: int = 5, where: dict = None) -> dict:
        """Search the collection."""
        if self.collection is None:
            raise RuntimeError("Collection not initialized")

        return self.collection.query(query_texts=[query], n_results=n_results, where=where)

    def get_collection_stats(self) -> dict:
        """Get collection statistics."""
        if self.collection is None:
            return {'error': 'Collection not initialized'}
        
        count = self.collection.count()
        
        return {
            'total_documents': count,
            'collection_name': self.collection.name,
            'has_documents': count > 0
        }


def create_vector_store(config_path: str = None) -> VectorStoreInit:
    """Factory function to create initialized vector store.

    Important: return VectorStoreInit which now provides `add/search` directly,
    to avoid double-initializing Chroma (which can conflict on settings).
    """
    store = VectorStoreInit(config_path)
    store.initialize_all()
    return store


if __name__ == "__main__":
    # Quick test initialization
    store = create_vector_store()
    stats = store.get_collection_stats()
    print(f"\nCollection Stats: {stats}")
