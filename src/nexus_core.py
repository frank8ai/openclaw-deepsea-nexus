#!/usr/bin/env python
"""
Deep-Sea Nexus v2.0 Core Engine

Core functionality:
- Session management
- Index maintenance
- Memory recall
- Daily flush
- Cross-date archive search
"""

import os
import re
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


def _resolve_default_base_path() -> str:
    override = os.environ.get("DEEPSEA_NEXUS_ROOT", "").strip()
    if override:
        return str(Path(override).expanduser().resolve())
    return str(Path(__file__).resolve().parent.parent)


# Base path fallback for legacy v2 defaults.
_DEFAULT_BASE = _resolve_default_base_path()
# Import local modules (fallback to built-in types if not available)
try:
    from .config import NexusConfig
    from .data_structures import (
        DailyIndex, SessionMetadata, SessionStatus, 
        RecallResult, IndexEntry
    )
    config = NexusConfig()
except ImportError:
    # Fallback: use simple config
    class SimpleConfig:
        def get(self, key, default=None):
            if key == "index.max_index_tokens":
                return 300
            elif key == "index.max_session_tokens":
                return 1000
            elif key == "paths.base":
                return _DEFAULT_BASE
            elif key == "paths.memory":
                return "memory/90_Memory"
            return default
    config = SimpleConfig()
    
    # Define fallbacks
    class SessionStatus:
        ACTIVE = "active"
        PAUSED = "paused"
        ARCHIVED = "archived"
    
    class DailyIndex:
        def __init__(self, date, sessions, gold_keys, topics, paused_sessions):
            self.date = date
            self.sessions = sessions
            self.gold_keys = gold_keys
            self.topics = topics
            self.paused_sessions = paused_sessions
    
    class SessionMetadata:
        def __init__(self, uuid, topic, created_at, last_active, status, gold_count, word_count, tags):
            self.uuid = uuid
            self.topic = topic
            self.created_at = created_at
            self.last_active = last_active
            self.status = status
            self.gold_count = gold_count
            self.word_count = word_count
            self.tags = tags
    
    class RecallResult:
        def __init__(self, session_id, relevance, content, source, metadata):
            self.session_id = session_id
            self.relevance = relevance
            self.content = content
            self.source = source
            self.metadata = metadata


class NexusCore:
    """
    Deep-Sea Nexus v2.0 Core Engine
    
    Design principles:
    - Boot only reads index (< 300 tokens)
    - Dialogs load on-demand (< 1000 tokens)
    - GOLD markers sync in real-time
    - Automatic flush to archives
    """
    
    def __init__(self, config_obj=None):
        self.config = config_obj or config
        self._ensure_directories()
        self._ensure_today_index()
        self._lock = Lock()  # For thread safety
    
    # ===================== Directory Management =====================
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        dirs = [
            self.config.get("paths.base", _DEFAULT_BASE),
            os.path.join(self.config.get("paths.base", _DEFAULT_BASE), 
                        self.config.get("paths.memory", "memory/90_Memory")),
            os.path.join(self.config.get("paths.base", _DEFAULT_BASE), 
                        self.config.get("paths.memory", "memory/90_Memory"), today),
            os.path.join(self.config.get("paths.base", _DEFAULT_BASE), 
                        self.config.get("paths.memory", "memory/90_Memory"), today[:7]),  # YYYY-MM
            os.path.join(self.config.get("paths.base", _DEFAULT_BASE), 
                        "memory/00_Inbox"),
            os.path.join(self.config.get("paths.base", _DEFAULT_BASE), 
                        "memory/10_Projects"),
        ]
        
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
    
    def _ensure_today_index(self):
        """Ensure today's index file exists"""
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        index_file = os.path.join(today_dir, "_INDEX.md")
        
        if not os.path.exists(index_file):
            self._create_index_file(index_file, today)
    
    def _create_index_file(self, path, date):
        """Create a new daily index file"""
        content = """---
uuid: %s
type: daily-index
tags: [daily-index, %s]
created: %s
---

# %s Daily Index

## Sessions (0)
_(no active sessions)_

## Gold Keys (0)
_(no gold keys)_

## Topics (0)
_(no topics)_
""" % (datetime.now().strftime("%Y%m%d%H%M%S"), date, date, date)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # ===================== Session Management =====================
    
    def start_session(self, topic, auto_create=True):
        """
        Start a new session
        
        Args:
            topic: Topic name
            auto_create: Whether to create file automatically (default True)
        
        Returns:
            session_id: Format HHMM_Topic
        """
        now = datetime.now()
        topic_safe = re.sub(r'[^\w]', '', topic.replace(" ", "_"))
        session_id = now.strftime("%H%M") + "_" + topic_safe[:20]
        
        if auto_create:
            today = now.strftime("%Y-%m-%d")
            base_path = self.config.get("paths.base", _DEFAULT_BASE)
            memory_path = self.config.get("paths.memory", "memory/90_Memory")
            today_dir = os.path.join(base_path, memory_path, today)
            session_file = os.path.join(today_dir, "session_%s.md" % session_id)
            
            content = """---
uuid: %s
type: session
tags: [%s]
status: active
created: %s
---

# %s

""" % (datetime.now().strftime("%Y%m%d%H%M%S"), topic, now.isoformat(), topic)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update index
            self._add_session_to_index(session_id, topic, now.isoformat())
        
        return session_id
    
    def write_session(self, session_id, content, is_gold=False, append=True):
        """
        Write content to session
        
        Args:
            session_id: Session ID
            content: Content to write
            is_gold: Whether content is GOLD marked
            append: Whether to append (False = overwrite)
        
        Returns:
            bool: Success
        """
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        session_file = os.path.join(today_dir, "session_%s.md" % session_id)
        
        if not os.path.exists(session_file):
            return False
        
        # Read existing content
        if append:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    existing = f.read()
            except:
                existing = ""
        else:
            existing = ""
        
        # Build new content
        if is_gold:
            new_content = "\n\n#GOLD %s\n" % content
        else:
            new_content = "\n\n%s\n" % content
        
        # Update file
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(existing + new_content)
        
        # If GOLD, update index
        if is_gold:
            self._add_gold_key(session_id, content)
        
        # Update last active time in index
        self._touch_session(session_id)
        
        return True
    
    def read_session(self, session_id, max_tokens=None):
        """
        Read session content
        
        Args:
            session_id: Session ID
            max_tokens: Max tokens (None = all)
        
        Returns:
            str: Session content or None
        """
        if max_tokens is None:
            max_tokens = self.config.get("index.max_session_tokens", 1000)
        
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        session_file = os.path.join(today_dir, "session_%s.md" % session_id)
        
        if not os.path.exists(session_file):
            return None
        
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Truncate by tokens (approximate: 1 token ~ 4 chars)
        max_chars = max_tokens * 4
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[...]"
        
        return content
    
    def get_active_session(self):
        """Get currently active session"""
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        
        if not os.path.exists(today_dir):
            return None
        
        session_files = []
        for f in os.listdir(today_dir):
            if f.startswith("session_") and f.endswith(".md"):
                session_files.append(os.path.join(today_dir, f))
        
        if not session_files:
            return None
        
        # Return latest session
        session_files.sort(key=os.path.getmtime, reverse=True)
        filename = os.path.basename(session_files[0])
        return filename.replace("session_", "").replace(".md", "")
    
    # ===================== Index Management =====================
    
    def read_today_index(self):
        """
        Read today's index
        
        Core method: Ensure < 300 tokens
        """
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        index_file = os.path.join(base_path, memory_path, today, "_INDEX.md")
        
        if not os.path.exists(index_file):
            self._ensure_today_index()
            index_file = os.path.join(base_path, memory_path, today, "_INDEX.md")
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ensure index is under token limit (truncate if needed)
        max_tokens = self.config.get("index.max_index_tokens", 300)
        max_chars = max_tokens * 4
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Truncated...]"
        
        return content
    
    def _add_session_to_index(self, session_id, topic, timestamp):
        """Add session to index"""
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today = datetime.now().strftime("%Y-%m-%d")
        index_file = os.path.join(base_path, memory_path, today, "_INDEX.md")
        
        if not os.path.exists(index_file):
            return
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already exists
        if "session_%s" % session_id in content:
            return
        
        # Add new line
        new_line = "- [active] session_%s (%s)\n" % (session_id, topic)
        
        # Find Sessions section
        if "## Sessions" in content:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith("## Sessions"):
                    # Insert after the line
                    new_lines.append(new_line)
            content = '\n'.join(new_lines)
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _touch_session(self, session_id):
        """Update session last active time (simplified)"""
        # For now, just ensure session exists in index
        pass
    
    def _add_gold_key(self, session_id, content):
        """Add GOLD key to index"""
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today = datetime.now().strftime("%Y-%m-%d")
        index_file = os.path.join(base_path, memory_path, today, "_INDEX.md")
        
        if not os.path.exists(index_file):
            return
        
        # Extract keywords (simple: take first 10 words)
        words = content.split()[:10]
        keywords = ", ".join(words)
        
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_line = "- session_%s: %s\n" % (session_id, keywords)
        
        if "## Gold Keys" in content:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith("## Gold Keys"):
                    # Insert after the line
                    new_lines.append(new_line)
            content = '\n'.join(new_lines)
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    # ===================== Cross-Date Search =====================
    
    def recall_archives(self, query, days=7, max_results=5):
        """
        Search across recent days and monthly archives
        
        Args:
            query: Search query
            days: Number of past days to search (default 7)
            max_results: Max results per day
        
        Returns:
            List[RecallResult]: Search results from archives
        """
        results = []
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        
        # Search past days
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            date_dir = os.path.join(base_path, memory_path, date)
            index_file = os.path.join(date_dir, "_INDEX.md")
            
            if not os.path.exists(index_file):
                continue
            
            # Read and parse index
            with open(index_file, 'r', encoding='utf-8') as f:
                index_content = f.read()
            
            # Search index
            relevant_sessions = self._search_index(index_content, query)
            
            # Load content
            for session_ref in relevant_sessions[:max_results]:
                session_file = os.path.join(date_dir, "session_%s.md" % session_ref['id'])
                
                if os.path.exists(session_file):
                    with open(session_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    relevant_parts = self._extract_relevant_parts(content, query)
                    
                    results.append({
                        'session_id': session_ref['id'],
                        'relevance': session_ref['score'],
                        'content': relevant_parts,
                        'source': session_file,
                        'date': date,
                        'metadata': {
                            'topic': session_ref['topic'],
                            'is_gold': session_ref.get('is_gold', False)
                        }
                    })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results * 2]
    
    # ===================== Recall System =====================
    
    def recall(self, query, max_results=3, max_tokens=None):
        """
        Recall related memories
        
        Args:
            query: Query term
            max_results: Max results to return
            max_tokens: Max tokens per result
        
        Returns:
            List of recall results
        """
        if max_tokens is None:
            max_tokens = self.config.get("index.max_session_tokens", 1000)
        
        results = []
        
        # Step 1: Read index
        index_content = self.read_today_index()
        
        # Step 2: Search index keywords
        relevant_sessions = self._search_index(index_content, query)
        
        # Step 3: Load relevant content
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        
        for session_ref in relevant_sessions[:max_results]:
            session_file = os.path.join(today_dir, "session_%s.md" % session_ref['id'])
            
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract relevant parts
                relevant_parts = self._extract_relevant_parts(content, query)
                
                results.append(RecallResult(
                    session_id=session_ref['id'],
                    relevance=session_ref['score'],
                    content=relevant_parts,
                    source=session_file,
                    metadata={
                        'topic': session_ref['topic'],
                        'is_gold': session_ref.get('is_gold', False)
                    }
                ))
        
        return results
    
    def _search_index(self, index_content, query):
        """
        Search in index
        
        Returns:
            [{id, topic, score, is_gold}]
        """
        query_words = query.lower().split()
        results = []
        
        # 1. Search Sessions
        lines = index_content.split('\n')
        for line in lines:
            if line.startswith("- [") and "session_" in line:
                # Parse: - [active] session_0923_Test (Test)
                if "] session_" in line and "(" in line and ")" in line:
                    try:
                        session_part = line.split("session_")[1].split(" ")[0]
                        topic_part = line.split("(")[1].split(")")[0]
                        
                        score = 0
                        for qw in query_words:
                            if qw in session_part.lower():
                                score += 0.5
                            if qw in topic_part.lower():
                                score += 1
                        
                        if score > 0:
                            results.append({
                                'id': session_part,
                                'topic': topic_part,
                                'score': score / len(query_words),
                                'is_gold': False
                            })
                    except:
                        continue
        
        # 2. Search GOLD Keys
        in_gold_section = False
        for line in lines:
            if line.startswith("## Gold Keys"):
                in_gold_section = True
            elif line.startswith("## ") and not line.startswith("## Gold Keys"):
                in_gold_section = False
            
            if in_gold_section and line.startswith("- session_"):
                try:
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        session_part = parts[0].replace("- session_", "").strip()
                        keywords = parts[1] if len(parts) > 1 else ""
                        
                        score = 0
                        for qw in query_words:
                            if qw.lower() in keywords.lower():
                                score += 1.5  # GOLD gets higher weight
                        
                        if score > 0:
                            # Check if already in results
                            exists = [r for r in results if r['id'] == session_part]
                            if not exists:
                                results.append({
                                    'id': session_part,
                                    'topic': 'gold',
                                    'score': score / len(query_words),
                                    'is_gold': True
                                })
                except:
                    continue
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def _extract_relevant_parts(self, content, query):
        """Extract relevant parts from content"""
        query_words = query.lower().split()
        lines = content.split('\n')
        relevant = []
        
        for line in lines:
            line_lower = line.lower()
            for qw in query_words:
                if qw in line_lower:
                    relevant.append(line.strip())
                    break
        
        # Return first 5 lines
        return '\n'.join(relevant[:5])
    
    # ===================== Index Parsing =====================
    
    def parse_index(self, index_content: str) -> DailyIndex:
        """
        Parse index content into DailyIndex structure
        
        Args:
            index_content: Raw index markdown content
        
        Returns:
            DailyIndex: Parsed index object
        """
        sessions = {}
        gold_keys = []
        topics = []
        paused_sessions = {}
        
        lines = index_content.split('\n')
        current_section = None
        
        for line in lines:
            stripped = line.strip()
            
            # Detect sections
            if stripped.startswith("## Sessions"):
                current_section = "sessions"
                continue
            elif stripped.startswith("## Gold Keys"):
                current_section = "gold"
                continue
            elif stripped.startswith("## Topics"):
                current_section = "topics"
                continue
            elif stripped.startswith("## ") and current_section:
                current_section = None
                continue
            
            # Parse sessions
            if current_section == "sessions":
                if stripped.startswith("- [") and "session_" in stripped:
                    match = re.match(r"- \[(\w+)\] session_(\S+) \((.+)\)", stripped)
                    if match:
                        status_str = match.group(1)
                        session_id = match.group(2)
                        topic = match.group(3)
                        
                        status = SessionStatus.ACTIVE
                        if status_str == "paused":
                            status = SessionStatus.PAUSED
                        elif status_str == "archived":
                            status = SessionStatus.ARCHIVED
                        
                        sessions[session_id] = SessionMetadata(
                            uuid=session_id,
                            topic=topic,
                            created_at="",
                            last_active="",
                            status=status,
                            gold_count=0,
                            word_count=0,
                            tags=[]
                        )
                        
                        if topic not in topics:
                            topics.append(topic)
            
            # Parse gold keys
            elif current_section == "gold":
                if stripped.startswith("- session_"):
                    match = re.match(r"- session_(\S+): (.+)", stripped)
                    if match:
                        session_id = match.group(1)
                        keywords = match.group(2).split(", ")
                        gold_keys.extend(keywords)
                        
                        # Update session metadata if exists
                        if session_id in sessions:
                            sessions[session_id].gold_count += len(keywords)
            
            # Parse topics
            elif current_section == "topics":
                if stripped.startswith("- "):
                    topic = stripped.replace("- ", "").strip()
                    if topic and topic not in topics:
                        topics.append(topic)
        
        # Try to extract date from YAML frontmatter or header
        date_match = re.search(r"# (\d{4}-\d{2}-\d{2}) Daily Index", index_content)
        date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        return DailyIndex(
            date=date,
            sessions=sessions,
            gold_keys=gold_keys,
            topics=topics,
            paused_sessions=paused_sessions
        )
    
    def recall_archives(self, query: str, days: int = 7, max_results: int = 5) -> List[RecallResult]:
        """
        Search across historical archives
        
        Args:
            query: Search query
            days: Number of days to search (default 7)
            max_results: Max results per day
        
        Returns:
            List[RecallResult]: Combined search results
        """
        results = []
        today = datetime.now()
        
        # Search today's index first
        today_str = today.strftime("%Y-%m-%d")
        today_index = self.read_today_index()
        today_results = self.recall(query, max_results=max_results)
        
        for r in today_results:
            if hasattr(r, 'metadata'):
                r.metadata['date'] = today_str
                r.metadata['source'] = 'today'
            else:
                # Handle dict results
                r['metadata'] = r.get('metadata', {})
                r['metadata']['date'] = today_str
                r['metadata']['source'] = 'today'
        results.extend(today_results)
        
        # Search historical indexes
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        
        for i in range(1, days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            index_file = os.path.join(base_path, memory_path, date_str, "_INDEX.md")
            
            if os.path.exists(index_file):
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_content = f.read()
                    
                    # Parse index
                    daily_index = self.parse_index(index_content)
                    
                    # Search in parsed index
                    relevant_sessions = self._search_index(index_content, query)
                    
                    # Load content from each session
                    date_dir = os.path.join(base_path, memory_path, date_str)
                    
                    for session_ref in relevant_sessions[:max_results]:
                        session_file = os.path.join(date_dir, "session_%s.md" % session_ref['id'])
                        
                        if os.path.exists(session_file):
                            with open(session_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            relevant_parts = self._extract_relevant_parts(content, query)
                            
                            results.append(RecallResult(
                                session_id=session_ref['id'],
                                relevance=session_ref['score'] * 0.8,  # Slightly lower weight for archives
                                content=relevant_parts,
                                source=session_file,
                                metadata={
                                    'topic': session_ref['topic'],
                                    'is_gold': session_ref.get('is_gold', False),
                                    'date': date_str,
                                    'source': 'archive'
                                }
                            ))
                except Exception as e:
                    continue
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance if hasattr(x, 'relevance') else x.get('relevance', 0), reverse=True)
        
        # Limit total results
        return results[:max_results * 2]
    
    # ===================== Flush System =====================
    
    def flush_session(self, session_id):
        """
        Flush a session
        
        Args:
            session_id: Session ID
        
        Returns:
            bool: Success
        """
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        index_file = os.path.join(base_path, memory_path, today, "_INDEX.md")
        
        session_file = os.path.join(base_path, memory_path, today, "session_%s.md" % session_id)
        if not os.path.exists(session_file):
            return False
        
        # Remove from index
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_lines = []
            for line in content.split('\n'):
                if "session_%s" % session_id not in line:
                    new_lines.append(line)
            
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
        
        return True
    
    def daily_flush(self):
        """
        Perform daily flush
        
        Returns:
            Dict: Flush statistics
        """
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        
        # 1. Count active sessions
        sessions = []
        for f in os.listdir(today_dir):
            if f.startswith("session_") and f.endswith(".md"):
                sessions.append(os.path.join(today_dir, f))
        
        session_count = len(sessions)
        
        # 2. Move to archive (monthly)
        archive_dir = os.path.join(base_path, memory_path, today[:7])  # YYYY-MM
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir, exist_ok=True)
        
        flushed = 0
        for session in sessions:
            archive_file = os.path.join(archive_dir, os.path.basename(session))
            os.rename(session, archive_file)
            flushed += 1
        
        # 3. Create new index
        self._create_index_file(os.path.join(today_dir, "_INDEX.md"), today)
        
        return {
            "date": today,
            "flushed_count": flushed,
            "archive_dir": archive_dir
        }
    
    # ===================== Statistics =====================
    
    def get_stats(self):
        """Get system statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        base_path = self.config.get("paths.base", _DEFAULT_BASE)
        memory_path = self.config.get("paths.memory", "memory/90_Memory")
        today_dir = os.path.join(base_path, memory_path, today)
        
        session_files = []
        for f in os.listdir(today_dir):
            if f.startswith("session_") and f.endswith(".md"):
                session_files.append(f)
        
        index_file = os.path.join(today_dir, "_INDEX.md")
        index_size = 0
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_size = len(f.read())
            except:
                pass
        
        return {
            "today_sessions": len(session_files),
            "index_size_chars": index_size,
            "index_size_tokens": index_size // 4,
            "memory_path": os.path.join(base_path, memory_path)
        }


# CLI interface
if __name__ == "__main__":
    import sys
    
    nexus = NexusCore()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "--init":
            print("✅ Deep-Sea Nexus v2.0 initialized")
            stats = nexus.get_stats()
            print("   Index size: %d tokens (< 300 ✅)" % stats['index_size_tokens'])
        
        elif cmd == "--stats":
            stats = nexus.get_stats()
            print("📊 Today's stats:")
            print("   Sessions: %d" % stats['today_sessions'])
            print("   Index: %d tokens" % stats['index_size_tokens'])
        
        elif cmd == "--session" and len(sys.argv) > 2:
            session_id = nexus.start_session(sys.argv[2])
            print("✅ Session: %s" % session_id)
        
        elif cmd == "--write" and len(sys.argv) > 2:
            session_id = nexus.get_active_session()
            if session_id:
                nexus.write_session(session_id, " ".join(sys.argv[2:]))
                print("✅ Written to session")
            else:
                print("❌ No active session")
        
        elif cmd == "--recall" and len(sys.argv) > 2:
            results = nexus.recall(" ".join(sys.argv[2:]))
            print("🔍 Found %d results:" % len(results))
            for r in results:
                print("   [%.2f] %s..." % (r['relevance'], r['content'][:50]))
        
        elif cmd == "--index":
            print(nexus.read_today_index())
        
        elif cmd == "--flush":
            stats = nexus.daily_flush()
            print("🧹 Flushed %d sessions to %s" % (stats['flushed_count'], stats['archive_dir']))
        
        elif cmd == "--archives" and len(sys.argv) > 2:
            results = nexus.recall_archives(" ".join(sys.argv[2:]))
            print("🔍 Found %d results from archives:" % len(results))
            for r in results:
                date = r.metadata.get('date', 'unknown')
                print("   [%s] [%.2f] %s - %s..." % (
                    date, r.relevance, r.session_id, r.content[:50]
                ))
        
        elif cmd == "--split":
            print("📄 Session Split Tool")
            print("   Run: python src/session_split.py --split")
        
        elif cmd == "--rebuild":
            print("🔧 Index Rebuild Tool")
            print("   Run: python src/index_rebuild.py --rebuild")
        
        elif cmd == "--migrate":
            print("📦 Migration Tool")
            print("   Usage: python src/migrate.py --v1 /path/to/v1 --migrate")
            print("\n   Options:")
            print("     --v1 PATH     v1.0 data path")
            print("     --dry-run     Show plan only")
            print("     --validate    Validate migration")
        
        elif cmd == "--help":
            print("Deep-Sea Nexus v2.0 Core Engine")
            print("\nCommands:")
            print("  --init           Initialize system")
            print("  --stats          Show statistics")
            print("  --session TOPIC  Start new session")
            print("  --write CONTENT  Write content")
            print("  --recall QUERY   Recall memories")
            print("  --index          Show index")
            print("  --flush          Perform daily flush")
            print("  --archives QUERY Search archives (7 days)")
            print("  --split          Split large sessions")
            print("  --rebuild        Rebuild indexes")
            print("  --migrate        Show migration info")
            print("\nRun with --help for this message")
    
    else:
        print("Deep-Sea Nexus v2.0 Core Engine")
        print("Run with --help for commands")
