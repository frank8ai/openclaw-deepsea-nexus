"""
Deep-Sea Nexus v2.0 - Semantic Recall Module
Phase 4: Semantic Retrieval

This module provides semantic search functionality for the vector store.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import os
from pathlib import Path
import yaml
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_config_path(config_path: str = None) -> Optional[Path]:
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


@dataclass
class SearchResult:
    """Represents a semantic search result."""
    content: str
    metadata: Dict[str, Any]
    distance: float
    relevance_score: float
    doc_id: str


class SemanticRecall:
    """
    Semantic search and recall for Deep-Sea Nexus.
    
    Features:
    - Vector similarity search
    - Metadata filtering
    - Relevance scoring
    - Result ranking
    """
    
    def __init__(self, manager, config_path: str = None):
        """
        Initialize with vector store manager.
        
        Args:
            manager: VectorStoreManager instance
            config_path: Optional path to config.json/config.yaml
        """
        self.manager = manager
        self.config = self._load_config(config_path)
        
        # RAG settings
        rag_config = self.config.get('rag', {})
        self.default_top_k = rag_config.get('top_k', 5)
        self.similarity_threshold = rag_config.get('similarity_threshold', 0.5)
        self.max_context_tokens = rag_config.get('max_context_tokens', 2000)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON/YAML file."""
        return load_config_file(config_path)
    
    def search(
        self,
        query: str,
        n_results: int = None,
        filters: Dict[str, Any] = None,
        return_scores: bool = True
    ) -> List[SearchResult]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
            return_scores: Include distance/relevance scores
            
        Returns:
            List of SearchResult objects
        """
        if n_results is None:
            n_results = self.default_top_k
        
        # Get search results from vector store
        results = self.manager.search(
            query=query,
            n_results=n_results,
            filters=filters
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results.get('documents') and results['documents'][0]:
            documents = results['documents'][0]
            distances = results.get('distances')
            distances = distances[0] if (isinstance(distances, list) and distances) else []
            metadatas = results.get('metadatas')
            metadatas = metadatas[0] if (isinstance(metadatas, list) and metadatas) else []
            ids = results.get('ids')
            ids = ids[0] if (isinstance(ids, list) and ids) else []
            
            for i, doc_content in enumerate(documents):
                dist = distances[i] if (isinstance(distances, list) and i < len(distances)) else None
                relevance = 1.0 - dist if dist is not None else 0.0
                
                # Filter by threshold
                if relevance < self.similarity_threshold:
                    continue
                
                result = SearchResult(
                    content=doc_content,
                    metadata=metadatas[i] if metadatas else {},
                    distance=distances[i] if distances else 0.0,
                    relevance_score=relevance,
                    doc_id=ids[i] if ids else f"doc_{i}"
                )
                search_results.append(result)
        
        # Sort by relevance
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return search_results
    
    def search_with_context(
        self,
        query: str,
        n_results: int = None,
        filters: Dict[str, Any] = None,
        max_context_length: int = None
    ) -> Tuple[str, List[SearchResult]]:
        """
        Search and return combined context string.
        
        Args:
            query: Search query
            n_results: Number of results
            filters: Optional metadata filters
            max_context_length: Max length of combined context
            
        Returns:
            Tuple of (combined_context, results_list)
        """
        if max_context_length is None:
            max_context_length = self.max_context_tokens * 4  # Rough token est.
        
        results = self.search(query, n_results, filters)
        
        # Combine contexts
        combined = ""
        for result in results:
            header = f"\n[来源: {result.metadata.get('title', result.doc_id)} | 相关度: {result.relevance_score:.2f}]\n"
            combined += header + result.content
            
            if len(combined) > max_context_length:
                break
        
        return combined.strip(), results
    
    def find_related_notes(
        self,
        note_id: str,
        n_related: int = 3
    ) -> List[SearchResult]:
        """
        Find notes related to a specific note.
        
        Args:
            note_id: ID of the source note
            n_related: Number of related notes to find
            
        Returns:
            List of related SearchResult objects
        """
        # Get the note content
        note = self.manager.get_by_id(note_id)
        
        if not note:
            return []
        
        # Search using the note content as query
        return self.search(note['content'], n_results=n_related + 1)
    
    def search_by_tags(
        self,
        query: str,
        tags: List[str],
        n_results: int = None
    ) -> List[SearchResult]:
        """
        Search with tag filtering.
        
        Args:
            query: Search query
            tags: List of tags to filter by
            n_results: Number of results
            
        Returns:
            Filtered search results
        """
        # Create filter for tags
        # ChromaDB uses $in for array containment
        filters = {"tags": {"$in": tags}}
        
        return self.search(query, n_results, filters)
    
    def search_by_date_range(
        self,
        query: str,
        start_date: str,
        end_date: str,
        n_results: int = None
    ) -> List[SearchResult]:
        """
        Search within a date range.
        
        Args:
            query: Search query
            start_date: ISO date string (e.g., "2026-02-01")
            end_date: ISO date string
            n_results: Number of results
            
        Returns:
            Filtered search results
        """
        # Note: This requires date parsing based on your metadata format
        # Simplified version - adjust based on your date format
        filters = {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        return self.search(query, n_results, filters)
    
    def smart_query(
        self,
        user_query: str,
        context: Dict[str, Any] = None,
        n_results: int = None
    ) -> Dict[str, Any]:
        """
        Enhanced query with context awareness.
        
        Args:
            user_query: Original user query
            context: Additional context (current topic, tags, etc.)
            n_results: Number of results
            
        Returns:
            Dict with 'context', 'results', and 'summary'
        """
        if n_results is None:
            n_results = self.default_top_k
        
        # Build query with context
        enhanced_query = user_query
        
        if context:
            # Add topic context if available
            if 'topic' in context:
                enhanced_query = f"[{context['topic']}] {user_query}"
            
            # Add tags context
            if 'tags' in context:
                tags_str = ", ".join(context['tags'])
                enhanced_query = f"Tags: {tags_str} | {user_query}"
        
        # Perform search
        combined_context, results = self.search_with_context(
            enhanced_query,
            n_results,
            max_context_length=self.max_context_tokens * 4
        )
        
        # Generate summary
        summary_parts = []
        for r in results[:3]:  # Top 3
            title = r.metadata.get('title', 'Unknown')
            summary_parts.append(f"- {title} (相关度: {r.relevance_score:.1%})")
        
        summary = "\n".join(summary_parts) if summary_parts else "未找到相关内容"
        
        return {
            'query': user_query,
            'enhanced_query': enhanced_query,
            'context': combined_context,
            'results': results,
            'summary': summary,
            'total_found': len(results)
        }
    
    def get_recall_stats(self) -> Dict[str, Any]:
        """Get semantic recall statistics."""
        return {
            'total_documents': self.manager.get_stats()['total_documents'],
            'default_top_k': self.default_top_k,
            'similarity_threshold': self.similarity_threshold,
            'max_context_tokens': self.max_context_tokens
        }


def create_semantic_recall(manager, config_path: str = None) -> SemanticRecall:
    """Factory function to create SemanticRecall instance."""
    return SemanticRecall(manager, config_path)


if __name__ == "__main__":
    # Test the semantic recall
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from vector_store.manager import create_manager
    from vector_store.init_chroma import create_vector_store
    
    print("=" * 50)
    print("Testing Semantic Recall")
    print("=" * 50)
    
    # Initialize
    store = create_vector_store()
    manager = create_manager(store.embedder, store.collection)
    recall = create_semantic_recall(manager)
    
    # Test search
    test_query = "Deep Sea Nexus memory system"
    results = recall.search(test_query, n_results=5)
    
    print(f"\nQuery: {test_query}")
    print(f"Found {len(results)} results:")
    
    for i, r in enumerate(results):
        print(f"\n{i+1}. [{r.relevance_score:.2f}] {r.metadata.get('title', 'Unknown')}")
        preview = r.content[:100] + "..." if len(r.content) > 100 else r.content
        print(f"   {preview}")
    
    # Stats
    stats = recall.get_recall_stats()
    print(f"\n\nStats: {stats}")
