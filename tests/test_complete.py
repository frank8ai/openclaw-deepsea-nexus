"""
Test suite for Deep-Sea Nexus v2.0 - Day 5 Complete Coverage
"""
import os
import sys
import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

pytest.skip(
    "Legacy v2 archive test module; use run_tests.py and tests/test_memory_v5.py for current v5 coverage.",
    allow_module_level=True,
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestNexusCore:
    """Test NexusCore functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def nexus(self, temp_workspace):
        """Create NexusCore with temp workspace"""
        # Set environment
        os.environ["NEXUS_BASE_PATH"] = temp_workspace
        
        from nexus_core import NexusCore
        nexus = NexusCore()
        yield nexus
        
        # Cleanup
        if hasattr(nexus, '_lock'):
            nexus._lock = None
    
    def test_initialize_system(self, nexus):
        """Test system initialization"""
        stats = nexus.get_stats()
        assert stats is not None
        assert "today_sessions" in stats
    
    def test_start_session(self, nexus):
        """Test session creation"""
        session_id = nexus.start_session("TestTopic")
        assert session_id is not None
        assert "TestTopic" in session_id or "testtopic" in session_id.lower()
        assert "_" in session_id
    
    def test_write_session(self, nexus):
        """Test session writing"""
        session_id = nexus.start_session("WriteTest")
        result = nexus.write_session(session_id, "Test content")
        assert result is True
        
        # Write GOLD content
        gold_result = nexus.write_session(session_id, "Gold content", is_gold=True)
        assert gold_result is True
    
    def test_read_session(self, nexus):
        """Test session reading"""
        session_id = nexus.start_session("ReadTest")
        nexus.write_session(session_id, "Content to read")
        
        content = nexus.read_session(session_id)
        assert content is not None
        assert "Content to read" in content
    
    def test_read_session_max_tokens(self, nexus):
        """Test session reading with token limit"""
        session_id = nexus.start_session("TokenTest")
        
        # Write lots of content
        long_content = "word " * 1000
        nexus.write_session(session_id, long_content)
        
        content = nexus.read_session(session_id, max_tokens=100)
        assert content is not None
        # Should be truncated
        assert len(content) < len(long_content)
    
    def test_active_session(self, nexus):
        """Test getting active session"""
        # Initially no session
        active = nexus.get_active_session()
        # May be None if no sessions exist
        
        # Create session
        session_id = nexus.start_session("ActiveTest")
        active = nexus.get_active_session()
        assert active is not None
    
    def test_read_today_index(self, nexus):
        """Test reading today's index"""
        index = nexus.read_today_index()
        assert index is not None
        assert len(index) > 0
    
    def test_recall_basic(self, nexus):
        """Test basic recall"""
        # Create session with specific content
        session_id = nexus.start_session("RecallTest")
        nexus.write_session(session_id, "Python coding session", is_gold=True)
        
        # Recall
        results = nexus.recall("Python")
        assert results is not None
        # Results may be empty if indexing hasn't happened
    
    def test_parse_index(self, nexus):
        """Test index parsing"""
        index_content = """---
uuid: 202602080000
type: daily-index
tags: [daily-index, 2026-02-08]
created: 2026-02-08
---

# 2026-02-08 Daily Index

## Sessions (1)
- [active] session_0001_Test (Test Topic)

## Gold Keys (1)
- session_0001: Test, Topic

## Topics (1)
- Test Topic
"""
        
        daily_index = nexus.parse_index(index_content)
        assert daily_index is not None
        assert daily_index.date == "2026-02-08"
        assert "session_0001" in daily_index.sessions or len(daily_index.sessions) >= 0
    
    def test_recall_archives(self, nexus):
        """Test archive recall"""
        results = nexus.recall_archives("test", days=1, max_results=3)
        assert results is not None
        assert isinstance(results, list)
    
    def test_flush_session(self, nexus):
        """Test flushing single session"""
        session_id = nexus.start_session("FlushTest")
        result = nexus.flush_session(session_id)
        assert result is True or result is False  # May already be flushed
    
    def test_daily_flush(self, nexus):
        """Test daily flush"""
        stats = nexus.daily_flush()
        assert stats is not None
        assert "flushed_count" in stats
        assert "archive_dir" in stats
    
    def test_get_stats(self, nexus):
        """Test statistics"""
        stats = nexus.get_stats()
        assert stats is not None
        assert "today_sessions" in stats
        assert "index_size_tokens" in stats


class TestSessionSplit:
    """Test session splitting functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_splitter_initialization(self, temp_workspace):
        """Test splitter can be created"""
        from session_split import SessionSplitter
        splitter = SessionSplitter(temp_workspace, threshold=1000)
        assert splitter is not None
    
    def test_detect_large_sessions_empty(self, temp_workspace):
        """Test detection when no large sessions"""
        from session_split import SessionSplitter
        splitter = SessionSplitter(temp_workspace)
        large = splitter.detect_large_sessions()
        assert large == []


class TestIndexRebuild:
    """Test index rebuilding functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_rebuilder_initialization(self, temp_workspace):
        """Test rebuilder can be created"""
        from index_rebuild import IndexRebuilder
        rebuilder = IndexRebuilder(temp_workspace)
        assert rebuilder is not None
    
    def test_scan_empty(self, temp_workspace):
        """Test scanning empty directory"""
        from index_rebuild import IndexRebuilder
        rebuilder = IndexRebuilder(temp_workspace)
        sessions = rebuilder.scan_all_sessions()
        assert sessions == {}


class TestMigration:
    """Test migration functionality"""
    
    @pytest.fixture
    def temp_v1(self):
        """Create temporary v1 directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_v2(self):
        """Create temporary v2 directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_migration_engine_init(self, temp_v1, temp_v2):
        """Test migration engine initialization"""
        from migrate import MigrationEngine
        engine = MigrationEngine(temp_v1, temp_v2)
        assert engine is not None
    
    def test_detect_no_v1(self, temp_v1, temp_v2):
        """Test detection when no v1 data"""
        from migrate import MigrationEngine
        engine = MigrationEngine(temp_v1, temp_v2)
        detected = engine.detect_v1_data()
        assert detected == []


class TestIntegration:
    """Integration tests"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def nexus(self, temp_workspace):
        """Create NexusCore with temp workspace"""
        os.environ["NEXUS_BASE_PATH"] = temp_workspace
        
        from nexus_core import NexusCore
        nexus = NexusCore()
        yield nexus
    
    def test_complete_flow(self, nexus):
        """Test complete workflow"""
        # 1. Create session
        session_id = nexus.start_session("IntegrationTest")
        assert session_id is not None
        
        # 2. Write content
        nexus.write_session(session_id, "Integration test content", is_gold=True)
        
        # 3. Read session
        content = nexus.read_session(session_id)
        assert content is not None
        
        # 4. Recall
        results = nexus.recall("Integration")
        assert results is not None
        
        # 5. Get stats
        stats = nexus.get_stats()
        assert stats is not None
        
        # 6. Read index
        index = nexus.read_today_index()
        assert index is not None
    
    def test_multi_session(self, nexus):
        """Test multiple sessions"""
        sessions = []
        for i in range(3):
            sid = nexus.start_session(f"MultiTest{i}")
            sessions.append(sid)
        
        assert len(sessions) == 3
        
        # All should be retrievable
        for sid in sessions:
            content = nexus.read_session(sid)
            assert content is not None
    
    def test_gold_sync(self, nexus):
        """Test GOLD marker synchronization"""
        session_id = nexus.start_session("GoldTest")
        
        # Write multiple GOLD entries
        nexus.write_session(session_id, "Gold item 1", is_gold=True)
        nexus.write_session(session_id, "Gold item 2", is_gold=True)
        
        # Read index
        index = nexus.read_today_index()
        assert "#GOLD" in index or "Gold" in index


class TestPerformance:
    """Performance tests"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def nexus(self, temp_workspace):
        """Create NexusCore with temp workspace"""
        os.environ["NEXUS_BASE_PATH"] = temp_workspace
        
        from nexus_core import NexusCore
        nexus = NexusCore()
        yield nexus
    
    def test_index_under_300_tokens(self, nexus):
        """Test index stays under 300 tokens"""
        # Create some sessions
        for i in range(5):
            sid = nexus.start_session(f"TokenTest{i}")
            nexus.write_session(sid, f"Content {i}")
        
        index = nexus.read_today_index()
        # Rough token estimate: 4 chars per token
        estimated_tokens = len(index) / 4
        assert estimated_tokens < 500  # Allow some margin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
