"""
Deep-Sea Nexus v2.0 - Vector Store Manager
Phase 3: Vector Storage Management

This module provides CRUD operations for the ChromaDB vector store.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any
import json
import uuid
import os
from pathlib import Path
import yaml
from datetime import datetime

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


class VectorStoreManager:
    """Manage vector storage operations for Deep-Sea Nexus."""
    
    def __init__(self, embedder, collection, config_path: str = None):
        """Initialize with embedder and collection."""
        self.embedder = embedder
        self.collection = collection
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON/YAML file."""
        return load_config_file(config_path)
    
    def add_note(
        self,
        content: str,
        metadata: Dict[str, Any],
        note_id: str = None
    ) -> str:
        """
        Add a single note to the vector store.
        
        Args:
            content: The text content to embed
            metadata: Additional metadata (title, tags, date, etc.)
            note_id: Optional custom ID (generates UUID if not provided)
            
        Returns:
            The document ID
        """
        if note_id is None:
            note_id = str(uuid.uuid4())
        
        # Add timestamp if not present
        if 'created_at' not in metadata:
            metadata['created_at'] = datetime.now().isoformat()
        
        # Generate embedding
        embedding = self.embedder.encode([content]).tolist()
        
        # Add to collection
        self.collection.add(
            documents=[content],
            embeddings=embedding,
            metadatas=[metadata],
            ids=[note_id]
        )
        
        return note_id
    
    def add_notes_batch(
        self,
        notes: List[Dict[str, Any]],
        chunk_size: int = 32
    ) -> List[str]:
        """
        Add multiple notes to the vector store in batches.
        
        Args:
            notes: List of dicts with 'content' and 'metadata' keys
            chunk_size: Batch size for processing
            
        Returns:
            List of document IDs
        """
        ids = []
        
        for i in range(0, len(notes), chunk_size):
            batch = notes[i:i + chunk_size]
            
            contents = [n['content'] for n in batch]
            metadatas = [n['metadata'] for n in batch]
            ids_batch = [
                n.get('id', str(uuid.uuid4())) 
                for n in batch
            ]
            
            # Generate embeddings
            embeddings = self.embedder.encode(contents).tolist()
            
            # Add batch
            self.collection.add(
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids_batch
            )
            
            ids.extend(ids_batch)
            
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filters: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Search results with documents, distances, and metadata
        """
        # Generate query embedding
        query_embedding = self.embedder.encode([query]).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=filters
        )
        
        return results
    
    def search_by_metadata(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search with metadata filters.
        
        Args:
            query: Search query
            metadata_filter: Metadata filter conditions
            n_results: Number of results
            
        Returns:
            Filtered search results
        """
        return self.search(query, n_results, metadata_filter)
    
    def delete_by_id(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    def delete_by_metadata(self, filters: Dict[str, str]) -> int:
        """
        Delete documents matching metadata filter.
        
        Returns:
            Number of deleted documents
        """
        # Get matching IDs
        results = self.collection.get(where=filters)
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])
        
        return 0
    
    def update_note(
        self,
        doc_id: str,
        content: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update an existing document."""
        try:
            update_kwargs = {}
            
            if content is not None:
                update_kwargs['documents'] = [content]
                update_kwargs['embeddings'] = [
                    self.embedder.encode([content]).tolist()[0]
                ]
            
            if metadata is not None:
                update_kwargs['metadatas'] = [metadata]
            
            if update_kwargs:
                update_kwargs['ids'] = [doc_id]
                self.collection.update(**update_kwargs)
            
            return True
        except Exception:
            return False
    
    def get_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Get a document by ID."""
        results = self.collection.get(ids=[doc_id])
        
        if results['documents']:
            return {
                'id': doc_id,
                'content': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        
        return None
    
    def get_all_metadata(self, limit: int = 100) -> List[Dict]:
        """Get all document metadata."""
        results = self.collection.get(limit=limit)
        
        return [
            {'id': rid, 'metadata': rm}
            for rid, rm in zip(results['ids'], results['metadatas'])
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        
        return {
            'total_documents': count,
            'collection_name': self.collection.name,
            'embedding_dimension': self.embedder.get_sentence_embedding_dimension()
        }
    
    def reset_collection(self):
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                metadata=self.collection.metadata
            )
            print("✓ Collection reset complete")
        except Exception as e:
            print(f"Error resetting collection: {e}")


def create_manager(embedder, collection, config_path: str = None) -> VectorStoreManager:
    """Factory function to create vector store manager."""
    return VectorStoreManager(embedder, collection, config_path)


if __name__ == "__main__":
    # Test the manager
    from init_chroma import create_vector_store
    
    store = create_vector_store()
    manager = create_manager(
        store.embedder, 
        store.collection
    )
    
    # Test add
    test_id = manager.add_note(
        content="This is a test note for Deep-Sea Nexus v2.0",
        metadata={
            "title": "Test Note",
            "tags": "test, demo",
            "type": "test"
        }
    )
    print(f"Added test note: {test_id}")
    
    # Test search
    results = manager.search("Deep Sea Nexus memory", n_results=3)
    print(f"Search results: {results}")
    
    # Stats
    stats = manager.get_stats()
    print(f"Stats: {stats}")
