"""
Deep-Sea Nexus v2.0 - Batch Chunk Script
Phase 4: Batch Processing

This script processes multiple markdown files and indexes them into the vector store.
"""

from __future__ import annotations

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import yaml

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chunking.text_splitter import create_splitter
from vector_store.init_chroma import create_vector_store
from vector_store.manager import create_manager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = Path(
    os.environ.get(
        "OPENCLAW_WORKSPACE",
        os.path.join(os.path.expanduser("~"), ".openclaw", "workspace"),
    )
).expanduser()


def resolve_nexus_root() -> Path:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return PROJECT_ROOT


def resolve_default_input_path() -> Path:
    nexus_root = resolve_nexus_root()
    candidates = [
        nexus_root / "Obsidian",
        DEFAULT_WORKSPACE_ROOT / "Obsidian",
        nexus_root / "memory",
        DEFAULT_WORKSPACE_ROOT / "memory",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[1].resolve()


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


class BatchChunkProcessor:
    """
    Batch processor for chunking and indexing markdown files.
    
    Features:
    - Process all files in a directory
    - Preserve frontmatter metadata
    - Progress tracking with tqdm
    - Error handling and recovery
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the batch processor."""
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.splitter = create_splitter(config_path)
        self.store = create_vector_store(config_path)
        self.manager = create_manager(
            self.store.embedder,
            self.store.collection,
            config_path
        )
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'chunks_created': 0,
            'tokens_processed': 0
        }
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON/YAML file."""
        return load_config_file(config_path)
    
    def parse_frontmatter(self, content: str) -> tuple:
        """
        Parse YAML frontmatter from markdown.
        
        Returns:
            Tuple of (metadata_dict, body_content)
        """
        import re
        
        # Match frontmatter between --- markers
        frontmatter_pattern = r'^---\n(.*?)\n---\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            frontmatter_text = match.group(1)
            body = match.group(2)
            
            # Parse YAML
            metadata = yaml.safe_load(frontmatter_text) or {}
            
            return metadata, body
        else:
            # No frontmatter - return empty metadata
            return {}, content
    
    def extract_metadata(self, file_path: str, frontmatter: Dict) -> Dict[str, Any]:
        """
        Extract metadata for vector storage.
        
        Args:
            file_path: Path to the file
            frontmatter: Parsed frontmatter metadata
            
        Returns:
            Metadata dict for vector store
        """
        path = Path(file_path)
        
        # Base metadata from frontmatter
        metadata = {
            'source_file': str(file_path),
            'file_name': path.name,
            'file_stem': path.stem,
            'file_extension': path.suffix,
            'indexed_at': datetime.now().isoformat()
        }
        
        # Add frontmatter fields
        for key, value in frontmatter.items():
            if key in ['tags', 'related_projects']:
                # Convert list to comma-separated string for ChromaDB
                if isinstance(value, list):
                    metadata[key] = ','.join(str(v) for v in value)
                else:
                    metadata[key] = str(value)
            else:
                metadata[key] = str(value)
        
        return metadata
    
    def process_file(
        self,
        file_path: str,
        strategy: str = "hybrid",
        chunk_size: int = None,
        overlap: int = None
    ) -> Dict[str, Any]:
        """
        Process a single markdown file.
        
        Args:
            file_path: Path to markdown file
            strategy: Chunking strategy
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            Processing result statistics
        """
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter
            frontmatter, body = self.parse_frontmatter(content)
            
            # Extract metadata
            metadata = self.extract_metadata(file_path, frontmatter)
            metadata['content_type'] = 'markdown'
            
            # Chunk the body
            chunks = self.splitter.chunk_document(
                body,
                metadata,
                strategy=strategy,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
            # Add to vector store
            if chunks:
                ids = self.manager.add_notes_batch(chunks)
                
                self.stats['chunks_created'] += len(chunks)
                self.stats['files_processed'] += 1
                
                return {
                    'status': 'success',
                    'file': file_path,
                    'chunks': len(chunks),
                    'ids': ids
                }
            else:
                return {
                    'status': 'empty',
                    'file': file_path,
                    'message': 'No content to chunk'
                }
                
        except Exception as e:
            self.stats['files_failed'] += 1
            return {
                'status': 'error',
                'file': file_path,
                'error': str(e)
            }
    
    def process_directory(
        self,
        input_dir: str,
        pattern: str = "*.md",
        recursive: bool = True,
        strategy: str = "hybrid",
        chunk_size: int = None,
        overlap: int = None
    ) -> Dict[str, Any]:
        """
        Process all markdown files in a directory.
        
        Args:
            input_dir: Directory to scan
            pattern: File pattern to match
            recursive: Process subdirectories
            strategy: Chunking strategy
            chunk_size: Characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            Processing summary
        """
        from tqdm import tqdm
        
        input_path = Path(input_dir)
        
        # Find files
        if recursive:
            files = list(input_path.rglob(pattern))
        else:
            files = list(input_path.glob(pattern))
        
        # Sort for consistent ordering
        files.sort()
        
        print(f"Found {len(files)} markdown files")
        print(f"Processing with strategy: {strategy}")
        print("-" * 50)
        
        results = []
        
        for file_path in tqdm(files, desc="Processing files"):
            result = self.process_file(
                str(file_path),
                strategy=strategy,
                chunk_size=chunk_size,
                overlap=overlap
            )
            results.append(result)
            
            if result['status'] == 'error':
                tqdm.write(f"✗ Error: {file_path.name} - {result['error']}")
        
        # Summary
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        summary = {
            'total_files': len(files),
            'successful': len(successful),
            'failed': len(failed),
            'total_chunks': self.stats['chunks_created'],
            'results': results
        }
        
        return summary
    
    def reset_index(self, confirm: bool = False) -> bool:
        """
        Clear all indexed documents.
        
        Args:
            confirm: Confirmation flag for safety
            
        Returns:
            True if reset, False if cancelled
        """
        if not confirm:
            print("Use --reset flag to confirm clearing the index")
            return False
        
        print("Clearing vector index...")
        self.manager.reset_collection()
        
        # Reset stats
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'chunks_created': 0,
            'tokens_processed': 0
        }
        
        print("Index cleared successfully")
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            'statistics': self.stats,
            'collection_stats': self.manager.get_stats(),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """CLI entry point."""
    default_input = resolve_default_input_path()
    parser = argparse.ArgumentParser(
        description="Deep-Sea Nexus v2.0 - Batch Chunk Processor"
    )
    
    parser.add_argument(
        'input',
        nargs='?',
        default=str(default_input),
        help=f'Input directory or file (default: {default_input})'
    )
    
    parser.add_argument(
        '--pattern',
        default='*.md',
        help='File pattern to match (default: *.md)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Disable recursive directory scanning'
    )
    
    parser.add_argument(
        '--strategy',
        default='hybrid',
        choices=['hybrid', 'sentence', 'paragraph', 'fixed'],
        help='Chunking strategy (default: hybrid)'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=None,
        help='Chunk size in characters'
    )
    
    parser.add_argument(
        '--overlap',
        type=int,
        default=None,
        help='Chunk overlap in characters'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Clear index before processing'
    )
    
    parser.add_argument(
        '--config',
        default=None,
        help='Path to config.json/config.yaml'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show index statistics'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = BatchChunkProcessor(args.config)
    
    if args.stats:
        summary = processor.get_summary()
        print("\nIndex Statistics:")
        print(f"  Total documents: {summary['collection_stats']['total_documents']}")
        print(f"  Total chunks created: {summary['statistics']['chunks_created']}")
        sys.exit(0)
    
    # Reset index if requested
    if args.reset:
        processor.reset_index(confirm=True)
    
    # Process input
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file
        result = processor.process_file(
            str(input_path),
            strategy=args.strategy,
            chunk_size=args.chunk_size,
            overlap=args.overlap
        )
        
        print(f"\nProcessing: {input_path.name}")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Chunks created: {result['chunks']}")
    else:
        # Directory
        summary = processor.process_directory(
            str(input_path),
            pattern=args.pattern,
            recursive=not args.no_recursive,
            strategy=args.strategy,
            chunk_size=args.chunk_size,
            overlap=args.overlap
        )
        
        print("\n" + "=" * 50)
        print("Processing Complete!")
        print("=" * 50)
        print(f"Total files: {summary['total_files']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Total chunks created: {summary['total_chunks']}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
