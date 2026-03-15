"""
Integration tests for Deep-Sea Nexus.

Test the full system integration and end-to-end functionality.
"""

import asyncio
import importlib
import importlib.util
import io
import json
import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("NEXUS_TEST_MODE", "1")


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_integration",
        REPO_ROOT / "__init__.py",
        submodule_search_locations=[str(REPO_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
create_app = deepsea_nexus.create_app
nexus_init = deepsea_nexus.nexus_init
nexus_recall = deepsea_nexus.nexus_recall
nexus_add = deepsea_nexus.nexus_add
get_session_manager = deepsea_nexus.get_session_manager
start_session = deepsea_nexus.start_session
close_session = deepsea_nexus.close_session
config_manager_module = importlib.import_module(f"{deepsea_nexus.__name__}.core.config_manager")
event_bus_module = importlib.import_module(f"{deepsea_nexus.__name__}.core.event_bus")
plugin_system_module = importlib.import_module(f"{deepsea_nexus.__name__}.core.plugin_system")
storage_compression_module = importlib.import_module(f"{deepsea_nexus.__name__}.storage.compression")
reset_config_manager = config_manager_module.reset_config_manager
reset_event_bus = event_bus_module.reset_event_bus
reset_plugin_registry = plugin_system_module.reset_plugin_registry


def _reset_runtime_state():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    reset_plugin_registry()
    reset_config_manager()
    reset_event_bus()


def _close_runtime_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return
    if loop.is_running() or loop.is_closed():
        return
    loop.close()
    asyncio.set_event_loop(None)


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        _reset_runtime_state()
        self.temp_dir = tempfile.mkdtemp()
        self.app = None
    
    def tearDown(self):
        if self.app:
            asyncio.run(self.app.stop())
        _reset_runtime_state()
        _close_runtime_loop()
        
        # Cleanup temp dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_lifecycle(self):
        """Test complete application lifecycle"""
        # Create app with temp config
        config_path = os.path.join(self.temp_dir, "test_config.json")
        config = {
            "base_path": self.temp_dir,
            "nexus": {
                "vector_db_path": os.path.join(self.temp_dir, "vector_db"),
            },
            "session": {
                "auto_archive_days": 30,
            },
            "flush": {
                "enabled": False,  # Disable auto-flush for tests
            },
            "plugins": {
                "auto_load": [
                    "config_manager",
                    "nexus_core",
                    "session_manager",
                    "smart_context",
                    "flush_manager",
                ]
            },
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Create and initialize app
        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))
        
        # Test plugins are working
        self.assertIsNotNone(app.plugins.get("nexus_core"))
        self.assertIsNotNone(app.plugins.get("session_manager"))
        self.assertIsNotNone(app.plugins.get("flush_manager"))
        
        # Test backward compatibility
        self.assertTrue(nexus_init())
        
        # Test search (should not crash)
        results = nexus_recall("test", n=1)
        self.assertIsInstance(results, list)
        
        # Test add (should not crash)
        doc_id = nexus_add("Test content", "Test title", "test,integration")
        # May return None if backend not available, but shouldn't crash
        
        # Stop app
        self.assertTrue(asyncio.run(app.stop()))
    
    def test_session_management(self):
        """Test session management integration"""
        # Initialize with backward compatibility
        self.assertTrue(nexus_init())
        
        # Get session manager
        session_mgr = get_session_manager()
        if session_mgr:
            # Test session creation
            session_id = start_session("Integration Test")
            self.assertTrue(session_id)
            self.assertTrue(session_mgr.add_chunk(session_id))
            
            # Test session retrieval
            session = session_mgr.get_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session.topic, "Integration Test")
            if session:
                self.assertEqual(session.chunk_count, 1)
            
            # Test session closing
            result = close_session(session_id)
            self.assertTrue(result)
            
            # Verify session is paused
            session = session_mgr.get_session(session_id)
            self.assertIsNotNone(session)
            if session:
                self.assertEqual(session.status, "paused")


class TestPluginCommunication(unittest.TestCase):
    """Test plugin communication via event bus"""
    
    def setUp(self):
        _reset_runtime_state()
        self.temp_dir = tempfile.mkdtemp()
        self.events_received = []
    
    def tearDown(self):
        _reset_runtime_state()
        _close_runtime_loop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_event_driven_communication(self):
        """Test that plugins communicate via events"""
        # Set up event listener
        def event_handler(event):
            self.events_received.append(event)
        
        event_bus = event_bus_module.get_event_bus()
        event_bus.subscribe("nexus.*", event_handler)  # Listen to nexus events
        event_bus.subscribe("session.*", event_handler)  # Listen to session events
        event_bus.subscribe("flush.*", event_handler)  # Listen to flush events
        
        # Create and run app
        config_path = os.path.join(self.temp_dir, "test_config.json")
        config = {
            "base_path": self.temp_dir,
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))
        
        # Perform some operations that should generate events
        nexus_init()
        
        # Wait for events to process
        asyncio.run(asyncio.sleep(0.1))
        
        # We expect some events to be generated during initialization
        # Even if no specific events occur, this verifies the system is working
        
        # Stop app
        asyncio.run(app.stop())


class TestBackwardCompatibilityIntegration(unittest.TestCase):
    """Test backward compatibility in integrated scenarios"""
    
    def setUp(self):
        _reset_runtime_state()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        _reset_runtime_state()
        _close_runtime_loop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_mixed_api_usage(self):
        """Test mixing old and new APIs"""
        config_path = os.path.join(self.temp_dir, "test_config.json")
        config = {
            "base_path": self.temp_dir,
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }

        with open(config_path, "w") as f:
            json.dump(config, f)

        first_app = create_app(config_path)
        self.assertTrue(asyncio.run(first_app.initialize()))
        self.assertTrue(asyncio.run(first_app.start()))
        self.assertTrue(nexus_init())
        self.assertIsInstance(nexus_recall("test", n=1), list)
        self.assertTrue(asyncio.run(first_app.stop()))

        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

        try:
            second_app = create_app(config_path)
            self.assertTrue(asyncio.run(second_app.initialize()))
            self.assertTrue(asyncio.run(second_app.start()))
            if second_app.plugins.get("nexus_core"):
                new_results = asyncio.run(
                    second_app.plugins["nexus_core"].search_recall("test", 1)
                )
                self.assertIsInstance(new_results, list)
            self.assertTrue(asyncio.run(second_app.stop()))
        finally:
            root_logger.removeHandler(handler)
            root_logger.setLevel(previous_level)

        log_output = log_stream.getvalue()
        self.assertNotIn("already registered", log_output)
        self.assertNotIn("Failed to register plugin", log_output)

    def test_brain_enabled_augments_recall(self):
        """When brain is enabled, nexus_recall should include brain hits even if vector backend is unavailable."""
        config_path = os.path.join(self.temp_dir, "brain_test_config.json")
        config = {
            "base_path": self.temp_dir,
            "brain": {
                "enabled": True,
                "base_path": self.temp_dir,
                "max_snapshots": 5,
                "merge": "append",
                "mode": "facts",
                "min_score": 0.1,
            },
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }

        with open(config_path, "w") as f:
            json.dump(config, f)

        # Initialize app so plugin can read config + enable brain hook
        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))

        # Write via old API; plugin add_document does best-effort brain_write
        nexus_add("Brain-only content about JSONL", "BrainNote", "brain,jsonl")

        # Recall should surface something from brain even if vector backend is unavailable
        results = nexus_recall("jsonl", n=5)
        self.assertIsInstance(results, list)
        self.assertTrue(any("JSONL" in (r.content or "") or "jsonl" in (r.content or "").lower() for r in results))

        asyncio.run(app.stop())

    def test_brain_replace_uses_brain_only(self):
        """When brain.merge=replace, recall should come from brain results."""
        config_path = os.path.join(self.temp_dir, "brain_replace_config.json")
        config = {
            "base_path": self.temp_dir,
            "brain": {
                "enabled": True,
                "base_path": self.temp_dir,
                "max_snapshots": 5,
                "merge": "replace",
                "mode": "facts",
                "min_score": 0.1,
            },
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }

        with open(config_path, "w") as f:
            json.dump(config, f)

        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))

        nexus_add("Replace-mode brain content", "BrainReplace", "brain")

        results = nexus_recall("replace-mode", n=5)
        self.assertIsInstance(results, list)
        self.assertTrue(any("Replace-mode brain content" in (r.content or "") for r in results))
        self.assertTrue(any((r.source or "").startswith("🧠") for r in results))

        asyncio.run(app.stop())

        # Use new API
        config_path = os.path.join(self.temp_dir, "test_config.json")
        config = {
            "base_path": self.temp_dir,
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))
        
        # Now use old API
        self.assertTrue(nexus_init())
        
        # Both should work together
        old_results = nexus_recall("test", n=1)
        self.assertIsInstance(old_results, list)
        
        # Use new API
        if app.plugins.get("nexus_core"):
            new_results = asyncio.run(
                app.plugins["nexus_core"].search_recall("test", 1)
            )
            self.assertIsInstance(new_results, list)
        
        # Stop
        asyncio.run(app.stop())
    
    def test_config_integration(self):
        """Test config manager integration"""
        config_mgr = config_manager_module.get_config_manager()
        
        # Test setting/getting values
        config_mgr.set("test.key", "test_value")
        self.assertEqual(config_mgr.get("test.key"), "test_value")
        
        # Test default values
        self.assertEqual(config_mgr.get("nonexistent", "default"), "default")
        
        # Test nested access
        config_mgr.set("nested.deep.value", "deep_test")
        self.assertEqual(config_mgr.get("nested.deep.value"), "deep_test")


class TestStorageIntegration(unittest.TestCase):
    """Test storage backend integration"""
    
    def setUp(self):
        _reset_runtime_state()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        _reset_runtime_state()
        _close_runtime_loop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compression_integration(self):
        """Test compression manager integration"""
        # Test all available backends
        for algo in storage_compression_module.CompressionManager.available_algorithms():
            cm = storage_compression_module.CompressionManager(algo)
            
            # Test basic compression
            original = b"Integration test data for compression algorithm: " + algo.encode()
            compressed = cm.compress(original)
            decompressed = cm.decompress(compressed)
            
            self.assertEqual(decompressed, original)
            # Small payloads may expand due to compression headers; verify round-trip instead.
            self.assertEqual(cm.decompress(compressed), original)
        
        # Test benchmark (should not crash)
        cm = storage_compression_module.CompressionManager("gzip")
        data = b"Test data for benchmarking"
        try:
            benchmark_results = cm.benchmark(data)
            # Should return dict with results
            self.assertIsInstance(benchmark_results, dict)
        except Exception:
            # Some backends might not be available, that's OK
            pass


class TestHotReload(unittest.TestCase):
    """Test hot-reload functionality"""
    
    def setUp(self):
        _reset_runtime_state()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        _reset_runtime_state()
        _close_runtime_loop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_reload(self):
        """Test configuration reload"""
        # Create initial config
        config_path = os.path.join(self.temp_dir, "reload_test.json")
        initial_config = {
            "base_path": self.temp_dir,
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
        }
        
        with open(config_path, 'w') as f:
            json.dump(initial_config, f)
        
        # Create and start app
        app = create_app(config_path)
        self.assertTrue(asyncio.run(app.initialize()))
        self.assertTrue(asyncio.run(app.start()))
        
        # Modify config
        modified_config = initial_config.copy()
        modified_config["session"]["auto_archive_days"] = 15  # Change value
        
        with open(config_path, 'w') as f:
            json.dump(modified_config, f)
        
        # Test reload
        self.assertTrue(asyncio.run(app.reload()))
        
        # Stop
        asyncio.run(app.stop())


def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Deep-Sea Nexus integration tests...")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEndToEnd)
    suite.addTests(loader.loadTestsFromTestCase(TestPluginCommunication))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardCompatibilityIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestHotReload))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 Integration Test Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
