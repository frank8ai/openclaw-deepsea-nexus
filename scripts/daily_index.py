"""
Deep-Sea Nexus v2.0 - Daily Index Update Script
Phase 6: Automated Daily Indexing

This script updates the vector index daily and tracks changes.
"""

import os
import sys
import glob
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vector_store.init_chroma import create_vector_store
from vector_store.manager import create_manager
from chunking.text_splitter import create_splitter

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


def resolve_default_index_directory() -> Path:
    nexus_root = resolve_nexus_root()
    candidates = [
        nexus_root / "memory",
        DEFAULT_WORKSPACE_ROOT / "memory",
        nexus_root / "Obsidian",
        DEFAULT_WORKSPACE_ROOT / "Obsidian",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[1].resolve()


@dataclass
class IndexEntry:
    """Represents an indexed document."""
    file_path: str
    content_hash: str
    indexed_at: str
    chunk_count: int
    vector_ids: List[str] = field(default_factory=list)


class DailyIndexUpdater:
    """
    Daily index update manager for Deep-Sea Nexus.
    
    Features:
    - Track indexed files with hashes
    - Detect changes (modified/deleted files)
    - Incremental updates
    - Index status reporting
    """
    
    def __init__(self, config_path: str = None, index_db_path: str = None):
        """
        Initialize the index updater.
        
        Args:
            config_path: Path to config.json/config.yaml
            index_db_path: Path to index state file
        """
        self.config_path = config_path
        self.index_db_path = index_db_path or os.path.join(
            os.path.dirname(__file__),
            '..',
            'index_state.json'
        )
        
        self.state: Dict[str, IndexEntry] = {}
        self.store = None
        self.manager = None
        self.splitter = None
        
    def initialize(self):
        """Initialize components and load state."""
        print("Initializing Daily Index Updater...")
        
        self.store = create_vector_store(self.config_path)
        self.manager = create_manager(
            self.store.embedder,
            self.store.collection,
            self.config_path
        )
        self.splitter = create_splitter(self.config_path)
        
        self._load_state()
        print(f"✓ Loaded {len(self.state)} indexed entries")
        
    def _load_state(self):
        """Load index state from file."""
        if os.path.exists(self.index_db_path):
            with open(self.index_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.state = {
                k: IndexEntry(**v) for k, v in data.items()
            }
    
    def _save_state(self):
        """Save index state to file."""
        data = {
            k: {
                'file_path': v.file_path,
                'content_hash': v.content_hash,
                'indexed_at': v.indexed_at,
                'chunk_count': v.chunk_count,
                'vector_ids': v.vector_ids
            }
            for k, v in self.state.items()
        }
        
        with open(self.index_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _compute_hash(self, content: str) -> str:
        """Compute MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def scan_directory(
        self,
        directory: str,
        pattern: str = "**/*.md"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Scan directory and get file information.
        
        Returns:
            Dict mapping file_path to file info
        """
        files = {}
        
        for path in glob.glob(os.path.join(directory, pattern), recursive=True):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            files[path] = {
                'content': content,
                'hash': self._compute_hash(content),
                'modified': os.path.getmtime(path)
            }
        
        return files
    
    def check_for_changes(
        self,
        directory: str,
        pattern: str = "**/*.md"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Check for file changes.
        
        Returns:
            Dict with 'added', 'modified', 'deleted', 'unchanged' lists
        """
        current_files = self.scan_directory(directory, pattern)
        
        result = {
            'added': [],      # New files
            'modified': [],   # Changed files
            'deleted': [],    # Removed files
            'unchanged': []   # No changes
        }
        
        # Check for added/modified
        for path, info in current_files.items():
            if path in self.state:
                entry = self.state[path]
                if entry.content_hash != info['hash']:
                    result['modified'].append(path)
                else:
                    result['unchanged'].append(path)
            else:
                result['added'].append(path)
        
        # Check for deleted
        indexed_paths = set(self.state.keys())
        current_paths = set(current_files.keys())
        
        for path in indexed_paths - current_paths:
            result['deleted'].append(path)
        
        return result
    
    def add_file(
        self,
        file_path: str,
        content: str,
        tag: str = None
    ) -> IndexEntry:
        """Add a new file to the index."""
        content_hash = self._compute_hash(content)
        
        # Chunk the content
        metadata = {
            "source_file": file_path,
            "title": os.path.basename(file_path),
            "type": "indexed"
        }
        
        if tag:
            metadata["index_tag"] = tag
        
        chunks = self.splitter.chunk_document(
            text=content,
            document_metadata=metadata,
            strategy="hybrid"
        )
        
        # Add to vector store
        ids = self.manager.add_notes_batch(chunks)
        
        entry = IndexEntry(
            file_path=file_path,
            content_hash=content_hash,
            indexed_at=datetime.now().isoformat(),
            chunk_count=len(chunks),
            vector_ids=ids
        )
        
        self.state[file_path] = entry
        self._save_state()
        
        return entry
    
    def update_file(
        self,
        file_path: str,
        content: str,
        tag: str = None
    ) -> IndexEntry:
        """Update an indexed file."""
        old_entry = self.state.get(file_path)
        
        # Delete old vectors
        if old_entry and old_entry.vector_ids:
            for vid in old_entry.vector_ids:
                self.manager.delete_by_id(vid)
        
        # Add updated content
        return self.add_file(file_path, content, tag)
    
    def delete_file(self, file_path: str) -> bool:
        """Remove a file from the index."""
        if file_path in self.state:
            entry = self.state[file_path]
            
            # Delete vectors
            if entry.vector_ids:
                for vid in entry.vector_ids:
                    self.manager.delete_by_id(vid)
            
            # Remove from state
            del self.state[file_path]
            self._save_state()
            
            return True
        
        return False
    
    def run_daily_update(
        self,
        directory: str,
        pattern: str = "**/*.md",
        auto_commit: bool = True
    ) -> Dict[str, Any]:
        """
        Run daily index update.
        
        Args:
            directory: Directory to index
            pattern: File pattern
            auto_commit: Automatically commit changes
            
        Returns:
            Update report
        """
        self.initialize()
        
        # Check for changes
        changes = self.check_for_changes(directory, pattern)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "directory": directory,
            "changes": {
                "added": len(changes['added']),
                "modified": len(changes['modified']),
                "deleted": len(changes['deleted']),
                "unchanged": len(changes['unchanged'])
            },
            "details": changes,
            "actions_taken": []
        }
        
        if not auto_commit:
            return report
        
        print("\n" + "=" * 60)
        print("Daily Index Update Report")
        print("=" * 60)
        print(f"Time: {report['timestamp']}")
        print(f"\nChanges:")
        print(f"  Added: {report['changes']['added']}")
        print(f"  Modified: {report['changes']['modified']}")
        print(f"  Deleted: {report['changes']['deleted']}")
        print(f"  Unchanged: {report['changes']['unchanged']}")
        
        # Process changes
        print("\nProcessing changes...")
        
        # Handle deleted files
        for path in changes['deleted']:
            if self.delete_file(path):
                report['actions_taken'].append(f"Deleted: {path}")
                print(f"  ✗ Deleted: {path}")
        
        # Handle added files
        for path in changes['added']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            entry = self.add_file(path, content, tag="daily-index")
            report['actions_taken'].append(f"Added: {path} ({entry.chunk_count} chunks)")
            print(f"  + Added: {path} ({entry.chunk_count} chunks)")
        
        # Handle modified files
        for path in changes['modified']:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            entry = self.update_file(path, content, tag="daily-index")
            report['actions_taken'].append(f"Updated: {path} ({entry.chunk_count} chunks)")
            print(f"  ~ Updated: {path} ({entry.chunk_count} chunks)")
        
        # Final stats
        stats = self.manager.get_stats()
        print(f"\n" + "-" * 60)
        print(f"Total indexed files: {len(self.state)}")
        print(f"Total vector documents: {stats['total_documents']}")
        
        return report
    
    def get_index_status(self) -> Dict[str, Any]:
        """Get current index status."""
        return {
            "indexed_files": len(self.state),
            "total_vectors": self.manager.get_stats()['total_documents'],
            "index_state_file": self.index_db_path,
            "oldest_entry": self._get_oldest_entry(),
            "recent_entries": self._get_recent_entries(5)
        }
    
    def _get_oldest_entry(self) -> Optional[Dict[str, Any]]:
        """Get the oldest indexed entry."""
        if not self.state:
            return None
        
        oldest = min(self.state.values(), key=lambda x: x.indexed_at)
        return {
            'file': oldest.file_path,
            'indexed_at': oldest.indexed_at
        }
    
    def _get_recent_entries(self, n: int) -> List[Dict[str, Any]]:
        """Get the n most recent entries."""
        sorted_entries = sorted(
            self.state.values(),
            key=lambda x: x.indexed_at,
            reverse=True
        )
        
        return [
            {
                'file': e.file_path,
                'indexed_at': e.indexed_at,
                'chunks': e.chunk_count
            }
            for e in sorted_entries[:n]
        ]


def main():
    """Main entry point for daily index update."""
    import argparse
    default_directory = resolve_default_index_directory()
    
    parser = argparse.ArgumentParser(
        description="Daily index update for Deep-Sea Nexus v2.0"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(default_directory),
        help=f"Directory to index (default: {default_directory})"
    )
    parser.add_argument(
        "--pattern",
        default="**/*.md",
        help="File pattern (default: **/*.md)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for changes, don't update"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current index status"
    )
    parser.add_argument(
        "--config",
        help="Path to config.json/config.yaml"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset index and re-index all files"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Deep-Sea Nexus v2.0 - Daily Index Updater")
    print("=" * 60)
    
    updater = DailyIndexUpdater(args.config)
    
    if args.reset:
        print("\nResetting index...")
        if os.path.exists(updater.index_db_path):
            os.remove(updater.index_db_path)
        updater.state = {}
        print("✓ Index reset")
    
    if args.status:
        updater.initialize()
        status = updater.get_index_status()
        print("\nIndex Status:")
        print(f"  Indexed files: {status['indexed_files']}")
        print(f"  Total vectors: {status['total_vectors']}")
        if status['recent_entries']:
            print("\nRecent entries:")
            for e in status['recent_entries']:
                print(f"  - {e['file']} ({e['indexed_at']})")
    
    elif args.check_only:
        updater.initialize()
        changes = updater.check_for_changes(args.directory, args.pattern)
        print("\nChange Summary:")
        print(f"  Added: {len(changes['added'])}")
        print(f"  Modified: {len(changes['modified'])}")
        print(f"  Deleted: {len(changes['deleted'])}")
        print(f"  Unchanged: {len(changes['unchanged'])}")
    
    else:
        report = updater.run_daily_update(
            args.directory,
            args.pattern
        )
        
        # Save report
        report_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'logs',
            f"index_report_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
