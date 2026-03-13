"""
Deep-Sea Nexus v2.0 - Text Splitter
Phase 2: Intelligent Text Chunking

This module provides smart text segmentation for vector storage.
"""

from __future__ import annotations

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml
import os

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


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    content: str
    start_position: int
    end_position: int
    chunk_index: int
    metadata: Dict[str, Any]


class TextSplitter:
    """
    Intelligent text splitter with multiple strategies.
    
    Strategies:
    - fixed_size: Fixed character count chunks
    - sentence: Split by sentence boundaries
    - paragraph: Split by paragraph breaks
    - semantic: Split by semantic section headers
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self._setup_chunking_params()
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON/YAML file."""
        return load_config_file(config_path)
    
    def _setup_chunking_params(self):
        """Setup chunking parameters from config."""
        chunking = self.config.get('chunking', {})
        self.chunk_size = chunking.get('chunk_size', 1000)
        self.chunk_overlap = chunking.get('chunk_overlap', 100)
        self.min_chunk_size = chunking.get('min_chunk_size', 50)
        
    def split_fixed_size(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[str]:
        """
        Split text into fixed-size chunks.
        
        Args:
            text: Input text
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
            
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to split at word boundary
            if end < len(text):
                # Find last space within chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
                chunk_index += 1
            
            start = end - overlap
            
            if start >= len(text):
                break
                
        return chunks
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text by sentence boundaries.
        
        Returns:
            List of sentences
        """
        # Common sentence endings
        sentence_endings = r'[.!?]\s+'
        
        sentences = re.split(sentence_endings, text)
        
        # Filter empty and very short sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return sentences
    
    def split_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text by paragraph breaks.
        
        Returns:
            List of paragraphs
        """
        # Split by double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def split_semantic(
        self,
        text: str,
        headers: List[str] = None
    ) -> List[tuple]:
        """
        Split text by semantic sections (headers).
        
        Args:
            text: Input text
            headers: List of header patterns to split on
            
        Returns:
            List of (section_header, section_content) tuples
        """
        if headers is None:
            # Common markdown/structural headers
            headers = [
                r'^#+\s+.+$',           # Markdown headers
                r'^[A-Z][A-Z\s]+:$',    # ALL CAPS headers
                r'^\d+\.\s+.+$',         # Numbered sections
            ]
        
        sections = []
        current_header = "Introduction"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            is_header = False
            
            for pattern in headers:
                if re.match(pattern, line, re.MULTILINE):
                    # Save previous section
                    if current_content:
                        sections.append((current_header, '\n'.join(current_content)))
                    current_header = line.strip()
                    current_content = []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Don't forget the last section
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))
        
        return sections
    
    def smart_split(
        self,
        text: str,
        strategy: str = "hybrid",
        chunk_size: int = None,
        overlap: int = None
    ) -> List[TextChunk]:
        """
        Smart splitting with multiple strategies.
        
        Strategy options:
        - hybrid: Use semantic splitting first, then fixed-size
        - sentence: Split by sentences
        - paragraph: Split by paragraphs
        - fixed: Pure fixed-size splitting
        """
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
            
        chunks = []
        chunk_index = 0
        start_position = 0
        
        if strategy == "hybrid":
            # Try semantic splitting first
            sections = self.split_semantic(text)
            
            for header, content in sections:
                # Split each section into chunks
                section_chunks = self.split_fixed_size(
                    content, chunk_size, overlap
                )
                
                for chunk_content in section_chunks:
                    chunks.append(TextChunk(
                        content=chunk_content,
                        start_position=start_position,
                        end_position=start_position + len(chunk_content),
                        chunk_index=chunk_index,
                        metadata={
                            "section": header,
                            "strategy": "hybrid"
                        }
                    ))
                    chunk_index += 1
                    
        elif strategy == "sentence":
            sentences = self.split_by_sentences(text)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(TextChunk(
                            content=current_chunk.strip(),
                            start_position=start_position,
                            end_position=start_position + len(current_chunk),
                            chunk_index=chunk_index,
                            metadata={"strategy": "sentence"}
                        ))
                        chunk_index += 1
                        start_position += len(current_chunk)
                    current_chunk = sentence + ". "
            
            if current_chunk.strip():
                chunks.append(TextChunk(
                    content=current_chunk.strip(),
                    start_position=start_position,
                    end_position=start_position + len(current_chunk),
                    chunk_index=chunk_index,
                    metadata={"strategy": "sentence"}
                ))
                
        elif strategy == "paragraph":
            paragraphs = self.split_by_paragraphs(text)
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(TextChunk(
                            content=current_chunk.strip(),
                            start_position=start_position,
                            end_position=start_position + len(current_chunk),
                            chunk_index=chunk_index,
                            metadata={"strategy": "paragraph"}
                        ))
                        chunk_index += 1
                        start_position += len(current_chunk)
                    current_chunk = para + "\n\n"
            
            if current_chunk.strip():
                chunks.append(TextChunk(
                    content=current_chunk.strip(),
                    start_position=start_position,
                    end_position=start_position + len(current_chunk),
                    chunk_index=chunk_index,
                    metadata={"strategy": "paragraph"}
                ))
                
        else:  # Fixed size
            raw_chunks = self.split_fixed_size(text, chunk_size, overlap)
            
            for chunk_content in raw_chunks:
                chunks.append(TextChunk(
                    content=chunk_content,
                    start_position=start_position,
                    end_position=start_position + len(chunk_content),
                    chunk_index=chunk_index,
                    metadata={"strategy": "fixed"}
                ))
                chunk_index += 1
                start_position += len(chunk_content)
        
        return chunks
    
    def chunk_document(
        self,
        text: str,
        document_metadata: Dict[str, Any],
        strategy: str = "hybrid",
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk a complete document with metadata.
        
        Args:
            text: Document text
            document_metadata: Metadata to attach to each chunk
            strategy: Splitting strategy
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries ready for vector store
        """
        chunks = self.smart_split(text, strategy, chunk_size, overlap)
        
        result = []
        
        for chunk in chunks:
            # Combine document metadata with chunk metadata
            combined_metadata = {
                **document_metadata,
                "chunk_index": chunk.chunk_index,
                "chunk_strategy": chunk.metadata.get("strategy", "unknown"),
                "section": chunk.metadata.get("section", "")
            }
            
            result.append({
                "content": chunk.content,
                "metadata": combined_metadata
            })
        
        return result


def create_splitter(config_path: str = None) -> TextSplitter:
    """Factory function to create text splitter."""
    return TextSplitter(config_path)


if __name__ == "__main__":
    # Test the splitter
    splitter = create_splitter()
    
    test_text = """
# Deep-Sea Nexus v2.0

## Overview
This is a test document for the Deep-Sea Nexus v2.0 memory system. 
It contains multiple sections to test the text splitting capabilities.

## Architecture
The system uses ChromaDB for vector storage and Sentence-Transformers 
for embeddings. This provides semantic search capabilities.

### Components
1. Vector Store - ChromaDB
2. Embedding Model - all-MiniLM-L6-v2
3. Text Splitter - Custom implementation

## Features
The system supports:
- Semantic search
- Automatic chunking
- RAG integration

This is a longer paragraph to test the fixed-size splitting functionality.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, 
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Conclusion
Deep-Sea Nexus v2.0 provides a powerful memory system for AI agents.
    """
    
    print("=" * 50)
    print("Testing Text Splitter")
    print("=" * 50)
    
    # Test hybrid splitting
    chunks = splitter.smart_split(test_text, strategy="hybrid")
    print(f"\nHybrid splitting produced {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks):
        preview = chunk.content[:80] + "..." if len(chunk.content) > 80 else chunk.content
        print(f"Chunk {i}: [{chunk.metadata.get('section', 'N/A')}]")
        print(f"  {preview}")
        print()
    
    # Test document chunking
    print("=" * 50)
    doc_chunks = splitter.chunk_document(
        test_text,
        {"title": "Test Document", "type": "test"},
        strategy="hybrid"
    )
    print(f"\nDocument chunking produced {len(doc_chunks)} chunks")
