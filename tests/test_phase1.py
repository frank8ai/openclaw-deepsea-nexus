"""
Phase 1 Testing: Infrastructure
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import NexusConfig
from data_structures import (
    SessionStatus, SessionMetadata, DailyIndex, 
    RecallResult, IndexEntry
)
from exceptions import (
    SessionNotFoundError, IndexFileError, 
    StorageFullError, TimeoutError as NexusTimeoutError
)


class TestConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = NexusConfig()
        
        # Test project info
        assert config.get("project.name") == "Deep-Sea Nexus v2.0"
        assert config.get("project.version") == "2.0.0"
        
        # Test index limits
        assert config.max_index_tokens == 300
        assert config.max_session_tokens == 1000
        
        # Test paths
        assert Path(config.base_path).is_absolute()
        assert "DEEP_SEA_NEXUS_V2" not in str(config.base_path)
    
    def test_config_properties(self):
        """Test config properties"""
        config = NexusConfig()
        
        assert isinstance(config.base_path, Path)
        assert isinstance(config.memory_path, Path)
        assert isinstance(config.max_index_tokens, int)
        assert isinstance(config.max_session_tokens, int)


class TestDataStructures:
    """Test data structures"""
    
    def test_session_status_enum(self):
        """Test SessionStatus enum"""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.ARCHIVED.value == "archived"
    
    def test_session_metadata(self):
        """Test SessionMetadata"""
        metadata = SessionMetadata(
            uuid="test-001",
            topic="Test Topic",
            created_at="2026-02-07T10:00:00",
            last_active="2026-02-07T11:00:00",
            status=SessionStatus.ACTIVE,
            gold_count=5,
            word_count=100,
            tags=["test", "example"]
        )
        
        assert metadata.uuid == "test-001"
        assert metadata.topic == "Test Topic"
        assert metadata.status == SessionStatus.ACTIVE
        assert metadata.gold_count == 5
        assert metadata.word_count == 100
        assert "test" in metadata.tags
    
    def test_daily_index(self):
        """Test DailyIndex"""
        index = DailyIndex(
            date="2026-02-07",
            sessions={},
            gold_keys=["test", "keyword"],
            topics=["topic1", "topic2"]
        )
        
        assert index.date == "2026-02-07"
        assert len(index.gold_keys) == 2
        assert len(index.topics) == 2
    
    def test_recall_result(self):
        """Test RecallResult"""
        result = RecallResult(
            session_id="0923_Test",
            relevance=0.85,
            content="Test content",
            source="/path/to/file",
            metadata={"test": True}
        )
        
        assert result.session_id == "0923_Test"
        assert result.relevance == 0.85
        assert result.content == "Test content"
        assert result.source == "/path/to/file"
        assert result.metadata["test"] is True
    
    def test_index_entry(self):
        """Test IndexEntry"""
        entry = IndexEntry(
            session_id="0923_Test",
            status="active",
            topic="Test Topic",
            gold_keywords=["kw1", "kw2"]
        )
        
        assert entry.session_id == "0923_Test"
        assert entry.status == "active"
        assert entry.topic == "Test Topic"
        assert len(entry.gold_keywords) == 2


class TestExceptions:
    """Test custom exceptions"""
    
    def test_session_not_found_error(self):
        """Test SessionNotFoundError"""
        with pytest.raises(SessionNotFoundError) as exc_info:
            raise SessionNotFoundError("test-session-123")
        
        assert "test-session-123" in str(exc_info.value)
    
    def test_index_file_error(self):
        """Test IndexFileError"""
        with pytest.raises(IndexFileError) as exc_info:
            raise IndexFileError("File not readable", "/path/to/file")
        
        assert "File not readable" in str(exc_info.value)
        assert "/path/to/file" in str(exc_info.value)
    
    def test_storage_full_error(self):
        """Test StorageFullError"""
        with pytest.raises(StorageFullError):
            raise StorageFullError()
    
    def test_timeout_error(self):
        """Test NexusTimeoutError"""
        with pytest.raises(NexusTimeoutError) as exc_info:
            raise NexusTimeoutError("read", 5.0)
        
        assert "read" in str(exc_info.value)
        assert "5.0" in str(exc_info.value)


def test_phase1_completion():
    """Phase 1 completion check"""
    # All modules import successfully
    from config import config
    from logger import logger
    from exceptions import NexusException
    
    # Basic functionality works
    assert config.get("project.name") == "Deep-Sea Nexus v2.0"
    print("✅ Phase 1: Infrastructure components working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
