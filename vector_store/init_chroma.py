"""
Deep-Sea Nexus v2.0 - Vector Store Initialization
Phase 1: Infrastructure Setup

This module initializes the ChromaDB vector database with proper configuration.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import yaml
import os


class VectorStoreInit:
    """Initialize and manage ChromaDB vector store."""
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.embedder = None
        self.client = None
        self.collection = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'config.yaml'
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
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
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            ),
            tenant="default_tenant",
            database="default_database",
        )
        
        # Get or create collection (allow env override for shared multi-agent store)
        collection_name = os.environ.get("NEXUS_COLLECTION", "").strip() or vs_config['collection_name']
        distance_metric = vs_config.get('distance_metric', 'cosine')
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
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
    
    def get_collection_stats(self) -> dict:
        """Get collection statistics."""
        if self.collection is None:
            return {'error': 'Collection not initialized'}
        
        count = self.collection.count()
        
        # Get sample documents
        sample = self.collection.get(limit=1)
        
        return {
            'total_documents': count,
            'collection_name': self.collection.name,
            'has_documents': count > 0
        }


def create_vector_store(config_path: str = None) -> VectorStoreInit:
    """Factory function to create initialized vector store."""
    store = VectorStoreInit(config_path)
    store.initialize_all()
    return store


if __name__ == "__main__":
    # Quick test initialization
    store = create_vector_store()
    stats = store.get_collection_stats()
    print(f"\nCollection Stats: {stats}")
