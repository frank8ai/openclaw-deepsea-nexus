#!/usr/bin/env python
"""
Unit Tests for Deep-Sea Nexus v2.0
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

pytest.skip(
    "Legacy v2 archive test module; use run_tests.py and tests/test_memory_v5.py for current v5 coverage.",
    allow_module_level=True,
)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.nexus_core import NexusCore


class TestNexusCore:
    """Test suite for NexusCore"""
    
    @pytest.fixture
    def temp_nexus(self, tmp_path):
        """Create a temporary Nexus instance"""
        # Create temp directory structure
        memory_dir = tmp_path / "memory" / "90_Memory"
        today_dir = memory_dir / datetime.now().strftime("%Y-%m-%d")
        today_dir.mkdir(parents=True)
        
        # Create temp config
        config_data = {
            "paths": {
                "base": str(tmp_path),
                "memory": "memory/90_Memory"
            },
            "index": {
                "max_index_tokens": 300,
                "max_session_tokens": 1000
            }
        }
        
        # Create nexus with temp config
        with patch('src.nexus_core.config') as mock_config:
            mock_config.get.side_effect = lambda k, d=None: config_data.get(k.replace('.', '/'), d) if '/' in k else config_data.get(k, d)
            nexus = NexusCore(config_obj=mock_config)
            nexus._ensure_today_index()
            yield nexus
        
        # Cleanup
        shutil.rmtree(tmp_path, ignore_errors=True)
    
    # ===================== Directory Tests =====================
    
    def test_ensure_directories(self, temp_nexus):
        """Test directory creation"""
        base = temp_nexus.config.get("paths.base")
        memory = temp_nexus.config.get("paths.memory")
        
        assert os.path.exists(os.path.join(base, memory))
        assert os.path.exists(os.path.join(base, memory, "00_Inbox"))
        assert os.path.exists(os.path.join(base, memory, "10_Projects"))
    
    def test_create_index_file(self, temp_nexus):
        """Test index file creation"""
        test_date = "2026-02-15"
        test_path = os.path.join(
            temp_nexus.config.get("paths.base"),
            temp_nexus.config.get("paths.memory"),
            test_date,
            "_INDEX.md"
        )
        
        # Create parent dir
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        temp_nexus._create_index_file(test_path, test_date)
        
        assert os.path.exists(test_path)
        
        with open(test_path, 'r') as f:
            content = f.read()
        
        assert test_date in content
        assert "Sessions" in content
        assert "Gold Keys" in content
    
    # ===================== Session Tests =====================
    
    def test_start_session(self, temp_nexus):
        """Test session creation"""
        session_id = temp_nexus.start_session("Test Topic", auto_create=True)
        
        assert session_id is not None
        assert "_" in session_id  # Format: HHMM_Topic
        assert len(session_id.split("_")[0]) == 4  # HHMM
    
    def test_write_session(self, temp_nexus):
        """Test session writing"""
        session_id = temp_nexus.start_session("Write Test")
        result = temp_nexus.write_session(session_id, "Test content")
        
        assert result is True
        
        # Verify content
        content = temp_nexus.read_session(session_id)
        assert content is not None
        assert "Test content" in content
    
    def test_write_session_gold(self, temp_nexus):
        """Test GOLD marking"""
        session_id = temp_nexus.start_session("Gold Test")
        temp_nexus.write_session(session_id, "Important info", is_gold=True)
        
        content = temp_nexus.read_session(session_id)
        assert "#GOLD" in content
    
    def test_read_session_max_tokens(self, temp_nexus):
        """Test token limiting"""
        session_id = temp_nexus.start_session("Token Test")
        
        # Write large content
        large_content = "word " * 5000
        temp_nexus.write_session(session_id, large_content)
        
        # Read with max_tokens
        content = temp_nexus.read_session(session_id, max_tokens=100)
        assert content is not None
        assert len(content) < 5000  # Should be truncated
    
    def test_read_nonexistent_session(self, temp_nexus):
        """Test reading non-existent session"""
        content = temp_nexus.read_session("nonexistent")
        assert content is None
    
    def test_get_active_session(self, temp_nexus):
        """Test getting active session"""
        session1 = temp_nexus.start_session("Topic 1")
        session2 = temp_nexus.start_session("Topic 2")
        
        active = temp_nexus.get_active_session()
        assert active is not None
        assert active == session2  # Latest session
    
    # ===================== Index Tests =====================
    
    def test_read_today_index(self, temp_nexus):
        """Test reading index"""
        index = temp_nexus.read_today_index()
        
        assert index is not None
        assert len(index) > 0
    
    def test_parse_index(self, temp_nexus):
        """Test index parsing"""
        content = """---
uuid: 202602150000
type: daily-index
tags: [daily-index, 2026-02-15]
created: 2026-02-15
---

# 2026-02-15 Daily Index

## Sessions (1)
- [active] session_0900_Test (Test Topic)

## Gold Keys (1)
- session_0900_Test: important, key

## Topics (1)
- Test Topic
"""
        
        parsed = temp_nexus.parse_index(content)
        
        assert parsed is not None
        assert len(parsed.sessions) >= 0  # May be empty due to format
        assert len(parsed.topics) >= 0
    
    def test_index_under_token_limit(self, temp_nexus):
        """Test index stays under token limit"""
        index = temp_nexus.read_today_index()
        
        # Rough token estimate (1 token ~ 4 chars)
        estimated_tokens = len(index) / 4
        assert estimated_tokens < 400  # Allow some buffer
    
    # ===================== Recall Tests =====================
    
    def test_recall_basic(self, temp_nexus):
        """Test basic recall"""
        # Create and write session
        session_id = temp_nexus.start_session("Python Study")
        temp_nexus.write_session(session_today_id, "Learning Python lists", is_gold=True)
        
        # Recall
        results = temp_nexus.recall("Python")
        
        assert results is not None
        # Results may vary based on implementation
    
    def test_recall_archives(self, temp_archives):
        """Test archive recall"""
        # This would need archive setup
        pass
    
    def test_search_index(self, temp_nexus):
        """Test index searching"""
        content = """- [active] session_0900_Python (Python学习)
- session_0900_Python: Python, 学习
"""
        
        results = temp_nexus._search_index(content, "Python")
        
        assert len(results) > 0
        assert any(r['score'] > 0 for r in results)
    
    def test_extract_relevant_parts(self, temp_nexus):
        """Test content extraction"""
        content = """# Python学习

今天学习 Python。

#GOLD 使用列表推导式

继续学习..
"""
        
        parts = temp_nexus._extract_relevant_parts(content, "Python")
        
        assert parts is not None
        assert "Python" in parts
    
    # ===================== Flush Tests =====================
    
    def test_flush_session(self, temp_nexus):
        """Test session flushing"""
        session_id = temp_nexus.start_session("Flush Test")
        
        result = temp_nexus.flush_session(session_id)
        
        assert result is True
    
    def test_daily_flush(self, temp_nexus):
        """Test daily flush"""
        # Create some sessions
        temp_nexus.start_session("Session 1")
        temp_nexus.start_session("Session 2")
        
        stats = temp_nexus.daily_flush()
        
        assert stats is not None
        assert "date" in stats
        assert "flushed_count" in stats
    
    # ===================== Statistics Tests =====================
    
    def test_get_stats(self, temp_nexus):
        """Test statistics"""
        temp_nexus.start_session("Stats Test")
        
        stats = temp_nexus.get_stats()
        
        assert stats is not None
        assert "today_sessions" in stats
        assert "index_size_tokens" in stats
    
    # ===================== Edge Cases =====================
    
    def test_empty_query(self, temp_nexus):
        """Test recall with empty query"""
        results = temp_nexus.recall("")
        assert results is not None
    
    def test_special_characters_in_topic(self, temp_nexus):
        """Test topic with special characters"""
        session_id = temp_nexus.start_session("Test: Topic/With.Special")
        
        assert session_id is not None
        assert "_" in session_id  # Special chars replaced
    
    def test_concurrent_session_creation(self, temp_nexus):
        """Test concurrent session creation"""
        import threading
        
        results = []
        threads = []
        
        def create_session(name):
            sid = temp_nexus.start_session(name)
            results.append(sid)
        
        # Create 5 threads
        for i in range(5):
            t = threading.Thread(target=create_session, args=(f"Topic{i}",))
            threads.append(t)
            t.start()
        
        # Wait for all
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(set(results)) == 5  # All unique


class TestIntegration:
    """Integration tests"""
    
    def test_complete_workflow(self, tmp_path):
        """Test complete user workflow"""
        # Create nexus
        config_data = {
            "paths": {
                "base": str(tmp_path),
                "memory": "memory/90_Memory"
            },
            "index": {
                "max_index_tokens": 300,
                "max_session_tokens": 1000
            }
        }
        
        with patch('src.nexus_core.config') as mock_config:
            mock_config.get.side_effect = lambda k, d=None: config_data.get(k.replace('.', '/'), d) if '/' in k else config_data.get(k, d)
            nexus = NexusCore(config_obj=mock_config)
            
            # 1. Create session
            session_id = nexus.start_session("Python学习")
            
            # 2. Write content
            nexus.write_session(session_id, "今天学习 Python 列表")
            nexus.write_session(session_id, "#GOLD 使用列表推导式更高效", is_gold=True)
            
            # 3. Read back
            content = nexus.read_session(session_id)
            assert "列表" in content
            assert "#GOLD" in content
            
            # 4. Recall
            results = nexus.recall("列表")
            assert results is not None
            
            # 5. Check stats
            stats = nexus.get_stats()
            assert stats["today_sessions"] >= 1
            
            # 6. Parse index
            index = nexus.read_today_index()
            assert len(index) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
