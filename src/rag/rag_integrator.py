"""
Deep-Sea Nexus v2.0 - RAG Integrator
Phase 5: Retrieval-Augmented Generation Integration

This module provides RAG capabilities for context-aware responses.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import os
from pathlib import Path
import yaml
from dataclasses import dataclass, field

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
class RAGContext:
    """RAG context with sources and reasoning."""
    query: str
    retrieved_context: str
    sources: List[Dict[str, Any]]
    confidence: float
    tokens_used: int = 0
    generation_prompt: str = ""


@dataclass
class RAGResponse:
    """Complete RAG response with metadata."""
    answer: str
    context: RAGContext
    sources_used: List[str]
    confidence_score: float
    needs_human_review: bool = False
    suggested_followups: List[str] = field(default_factory=list)


class RAGIntegrator:
    """
    Retrieval-Augmented Generation Integrator.
    
    Features:
    - Context retrieval and formatting
    - Prompt engineering for RAG
    - Confidence scoring
    - Source citation
    - Follow-up suggestion
    """
    
    def __init__(
        self,
        semantic_recall,
        config_path: str = None,
        prompt_template: str = None
    ):
        """
        Initialize RAG integrator.
        
        Args:
            semantic_recall: SemanticRecall instance
            config_path: Optional path to config.json/config.yaml
            prompt_template: Custom prompt template
        """
        self.recall = semantic_recall
        self.config = self._load_config(config_path)
        
        # RAG settings
        rag_config = self.config.get('rag', {})
        self.max_context_tokens = rag_config.get('max_context_tokens', 2000)
        self.similarity_threshold = rag_config.get('similarity_threshold', 0.5)
        self.default_top_k = rag_config.get('top_k', 5)
        
        # Prompt template
        self.prompt_template = prompt_template or self._default_prompt_template()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration."""
        return load_config_file(config_path)
    
    def _default_prompt_template(self) -> str:
        """Default RAG prompt template."""
        return """You are a helpful AI assistant with access to a knowledge base.

## User Question
{query}

## Relevant Context from Knowledge Base
{context}

## Instructions
1. Use the context above to answer the question
2. If the context doesn't contain enough information, say so clearly
3. Cite relevant sources when possible
4. Keep your answer concise and helpful

## Your Answer
"""
    
    def _format_context(self, context: str, max_length: int = None) -> str:
        """Format retrieved context for the prompt."""
        if max_length is None:
            max_length = self.max_context_tokens * 4
        
        if len(context) > max_length:
            context = context[:max_length] + "\n... (truncated)"
        
        return context
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt for the LLM."""
        return self.prompt_template.format(
            query=query,
            context=context
        )
    
    def retrieve_context(
        self,
        query: str,
        n_results: int = None,
        filters: Dict[str, Any] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            n_results: Number of results to retrieve
            filters: Optional metadata filters
            
        Returns:
            Tuple of (formatted_context, sources_list)
        """
        if n_results is None:
            n_results = self.default_top_k
        
        # Get search results
        results = self.recall.search(query, n_results, filters)
        
        # Format context
        context_parts = []
        sources = []
        
        for r in results:
            source_header = f"\n--- Source: {r.metadata.get('title', r.doc_id)} ---\n"
            context_parts.append(source_header + r.content)
            
            sources.append({
                'id': r.doc_id,
                'title': r.metadata.get('title', 'Unknown'),
                'relevance': r.relevance_score,
                'type': r.metadata.get('type', 'note')
            })
        
        combined_context = "\n".join(context_parts)
        formatted_context = self._format_context(combined_context)
        
        return formatted_context, sources
    
    def generate_response(
        self,
        query: str,
        llm_generator,
        n_results: int = None,
        filters: Dict[str, Any] = None,
        context_overlay: str = None
    ) -> RAGResponse:
        """
        Generate RAG-enhanced response.
        
        Args:
            query: User query
            llm_generator: Function that takes prompt and returns response
            n_results: Number of context results
            filters: Optional metadata filters
            context_overlay: Additional context to include
            
        Returns:
            RAGResponse object
        """
        # Retrieve context
        context, sources = self.retrieve_context(query, n_results, filters)
        
        # Add overlay if provided
        if context_overlay:
            context = f"{context_overlay}\n\n{context}"
        
        # Calculate confidence
        avg_relevance = sum(s['relevance'] for s in sources) / len(sources) if sources else 0
        confidence = min(avg_relevance * 1.2, 1.0)  # Boost slightly
        
        # Check if we have sufficient context
        has_sufficient_context = (
            len(context.strip()) > 50 and
            avg_relevance >= self.similarity_threshold
        )
        
        # Build prompt
        prompt = self._build_prompt(query, context)
        
        # Generate response (if LLM is provided)
        if llm_generator:
            answer = llm_generator(prompt)
        else:
            # Placeholder - in real use, call LLM here
            answer = f"[LLM response would appear here]\n\nContext used: {len(context)} chars from {len(sources)} sources"
        
        # Build RAG context
        rag_context = RAGContext(
            query=query,
            retrieved_context=context,
            sources=sources,
            confidence=confidence,
            generation_prompt=prompt
        )
        
        # Determine if human review needed
        needs_review = (
            confidence < 0.3 or
            len(sources) == 0 or
            not has_sufficient_context
        )
        
        # Generate follow-up suggestions
        followups = self._generate_followups(query, sources)
        
        # Build response
        response = RAGResponse(
            answer=answer,
            context=rag_context,
            sources_used=[s['id'] for s in sources],
            confidence_score=confidence,
            needs_human_review=needs_review,
            suggested_followups=followups
        )
        
        return response
    
    def _generate_followups(
        self,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate suggested follow-up questions."""
        followups = []
        
        if sources:
            # Suggest exploring related topics
            top_source = sources[0]
            title = top_source.get('title', 'this topic')
            followups.append(f"Tell me more about {title}")
            
            # Suggest related searches
            if len(sources) > 1:
                followups.append(f"How are {sources[0].get('title', 'these')} and {sources[1].get('title', 'those')} related?")
        
        # Generic follow-ups
        followups.append("Can you provide more specific examples?")
        followups.append("What are the next steps I should take?")
        
        return followups[:3]  # Limit to 3
    
    def create_system_context(
        self,
        current_session: str = None,
        user_profile: Dict[str, Any] = None
    ) -> str:
        """
        Create system context for RAG.
        
        Args:
            current_session: Current session topic
            user_profile: User preferences and history
            
        Returns:
            Formatted system context string
        """
        context_parts = []
        
        if current_session:
            context_parts.append(f"Current Session: {current_session}")
        
        if user_profile:
            if 'preferences' in user_profile:
                prefs = user_profile['preferences']
                context_parts.append(f"User Preferences: {', '.join(prefs)}")
            
            if 'goals' in user_profile:
                goals = user_profile['goals']
                context_parts.append(f"User Goals: {', '.join(goals)}")
        
        return "\n".join(context_parts)
    
    def hybrid_search(
        self,
        query: str,
        tags: List[str] = None,
        date_range: Tuple[str, str] = None,
        n_results: int = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Perform hybrid search with multiple filters.
        
        Args:
            query: Search query
            tags: Tags to filter by
            date_range: (start_date, end_date) tuple
            n_results: Number of results
            
        Returns:
            Tuple of (context, sources)
        """
        filters = {}
        
        if tags:
            filters['tags'] = {"$in": tags}
        
        if date_range:
            start, end = date_range
            filters['created_at'] = {
                "$gte": start,
                "$lte": end
            }
        
        return self.retrieve_context(query, n_results, filters)
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG integrator statistics."""
        return {
            'max_context_tokens': self.max_context_tokens,
            'similarity_threshold': self.similarity_threshold,
            'default_top_k': self.default_top_k,
            'documents_indexed': self.recall.get_recall_stats()['total_documents']
        }
    
    def set_prompt_template(self, template: str):
        """
        Set custom prompt template.
        
        Template variables:
        - {query}: User question
        - {context}: Retrieved context
        """
        self.prompt_template = template


def create_rag_integrator(
    semantic_recall,
    config_path: str = None,
    prompt_template: str = None
) -> RAGIntegrator:
    """Factory function to create RAGIntegrator instance."""
    return RAGIntegrator(semantic_recall, config_path, prompt_template)


if __name__ == "__main__":
    # Test the RAG integrator
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    from vector_store.init_chroma import create_vector_store
    from vector_store.manager import create_manager
    from retrieval.semantic_recall import create_semantic_recall
    
    print("=" * 50)
    print("Testing RAG Integrator")
    print("=" * 50)
    
    # Initialize
    store = create_vector_store()
    manager = create_manager(store.embedder, store.collection)
    recall = create_semantic_recall(manager)
    rag = create_rag_integrator(recall)
    
    # Test retrieve
    test_query = "Deep Sea Nexus architecture"
    context, sources = rag.retrieve_context(test_query, n_results=3)
    
    print(f"\nQuery: {test_query}")
    print(f"\nRetrieved {len(sources)} sources:")
    for s in sources:
        print(f"  - {s['title']} (relevance: {s['relevance']:.2f})")
    
    print(f"\nContext preview: {context[:200]}...")
    
    # Test response generation (without actual LLM)
    response = rag.generate_response(
        test_query,
        llm_generator=None,  # Pass your LLM function here
        n_results=3
    )
    
    print(f"\n\nConfidence Score: {response.confidence_score:.2f}")
    print(f"Needs Review: {response.needs_human_review}")
    print(f"Follow-ups: {response.suggested_followups}")
    
    # Stats
    stats = rag.get_rag_stats()
    print(f"\n\nStats: {stats}")
