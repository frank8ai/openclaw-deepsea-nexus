"""
Unit tests for Deep-Sea Nexus.

Test the hot-pluggable architecture and ensure all components work correctly.
"""

import asyncio
import importlib
import importlib.util
import os
import sys
import tempfile
import unittest

from unittest.mock import Mock, patch, MagicMock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NEXUS_TEST_MODE", "1")


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_units",
        os.path.join(REPO_ROOT, "__init__.py"),
        submodule_search_locations=[REPO_ROOT],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


deepsea_nexus = _load_local_package()
create_app = deepsea_nexus.create_app
NexusApplication = deepsea_nexus.NexusApplication
get_plugin_registry = deepsea_nexus.get_plugin_registry
get_event_bus = deepsea_nexus.get_event_bus
get_config_manager = deepsea_nexus.get_config_manager
nexus_init = deepsea_nexus.nexus_init
nexus_recall = deepsea_nexus.nexus_recall
nexus_add = deepsea_nexus.nexus_add
CompressionManager = deepsea_nexus.CompressionManager
GzipBackend = deepsea_nexus.GzipBackend
ZstdBackend = deepsea_nexus.ZstdBackend
Lz4Backend = deepsea_nexus.Lz4Backend
plugin_system_module = importlib.import_module(f"{deepsea_nexus.__name__}.core.plugin_system")
storage_base_module = importlib.import_module(f"{deepsea_nexus.__name__}.storage.base")


class TestEventBus(unittest.TestCase):
    """Test Event Bus functionality"""
    
    def setUp(self):
        self.event_bus = get_event_bus()
        self.event_bus.clear_subscribers()  # Clean slate
        self.event_bus.clear_history()
    
    def test_subscribe_and_publish(self):
        """Test basic subscribe/publish"""
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        self.event_bus.subscribe("test.event", handler)
        
        # Publish event
        self.event_bus.publish("test.event", {"data": "test"})
        
        # Process events (async)
        asyncio.run(asyncio.sleep(0.01))  # Allow async processing
        
        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0].data["data"], "test")
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event"""
        received1, received2 = [], []
        
        def handler1(event):
            received1.append(event)
        
        def handler2(event):
            received2.append(event)
        
        self.event_bus.subscribe("test.multi", handler1)
        self.event_bus.subscribe("test.multi", handler2)
        
        self.event_bus.publish("test.multi", {"msg": "hello"})
        asyncio.run(asyncio.sleep(0.01))
        
        self.assertEqual(len(received1), 1)
        self.assertEqual(len(received2), 1)
        self.assertEqual(received1[0].data["msg"], "hello")
        self.assertEqual(received2[0].data["msg"], "hello")

    def test_wildcard_subscriber_receives_matching_events(self):
        """Wildcard subscriptions (e.g. session.*) should receive matching events."""
        received = []

        def handler(event):
            received.append(event.type)

        self.event_bus.subscribe("session.*", handler)
        self.event_bus.publish("session.created", {"session_id": "s1"})
        asyncio.run(asyncio.sleep(0.01))

        self.assertEqual(received, ["session.created"])


class TestCompressionManager(unittest.TestCase):
    """Test Compression Manager functionality"""
    
    def test_gzip_backend(self):
        """Test gzip compression"""
        backend = GzipBackend(level=6)
        
        original = b"Hello, World! This is test data for compression."
        compressed = backend.compress(original)
        decompressed = backend.decompress(compressed)
        
        self.assertEqual(decompressed, original)
        # Small payloads can expand due to headers; round-trip correctness is the guarantee.
        self.assertGreater(len(compressed), 0)
    
    def test_zstd_backend(self):
        """Test zstd compression (if available)"""
        try:
            backend = ZstdBackend(level=3)
            
            original = b"Hello, World! This is test data for compression."
            compressed = backend.compress(original)
            decompressed = backend.decompress(compressed)
            
            self.assertEqual(decompressed, original)
            self.assertGreater(len(compressed), 0)
        except ImportError:
            self.skipTest("zstandard not installed")
    
    def test_lz4_backend(self):
        """Test lz4 compression (if available)"""
        try:
            backend = Lz4Backend()
            
            original = b"Hello, World! This is test data for compression."
            compressed = backend.compress(original)
            decompressed = backend.decompress(compressed)
            
            self.assertEqual(decompressed, original)
            self.assertGreater(len(compressed), 0)
        except ImportError:
            self.skipTest("lz4 not installed")
    
    def test_compression_manager(self):
        """Test compression manager interface"""
        original = b"Test data for compression manager"
        
        # Test gzip
        cm = CompressionManager("gzip")
        compressed = cm.compress(original)
        decompressed = cm.decompress(compressed)
        self.assertEqual(decompressed, original)
        
        # Test file operations
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(original)
            temp.flush()
            temp_path = temp.name
        
        try:
            # Compress file
            result = cm.compress_file(temp_path)
            self.assertTrue(result.success)
            
            # Decompress file
            result = cm.decompress_file(result.data["target_path"])
            self.assertTrue(result.success)
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            compressed_file = temp_path + ".gz"
            if os.path.exists(compressed_file):
                os.unlink(compressed_file)


class TestNexusApplication(unittest.TestCase):
    """Test Nexus Application lifecycle"""
    
    def setUp(self):
        self.temp_config = tempfile.mktemp(suffix=".json")
    
    def tearDown(self):
        if os.path.exists(self.temp_config):
            os.unlink(self.temp_config)
    
    def test_app_creation(self):
        """Test application creation"""
        app = create_app()
        self.assertIsInstance(app, NexusApplication)
    
    def test_app_initialize_start_stop(self):
        """Test full application lifecycle"""
        app = create_app()
        
        # Initialize
        result = asyncio.run(app.initialize())
        self.assertTrue(result)
        
        # Start
        result = asyncio.run(app.start())
        self.assertTrue(result)
        
        # Check plugins are loaded
        self.assertIsNotNone(app.plugins.get("nexus_core"))
        self.assertIsNotNone(app.plugins.get("session_manager"))
        self.assertIsNotNone(app.plugins.get("flush_manager"))
        
        # Stop
        result = asyncio.run(app.stop())
        self.assertTrue(result)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility"""
    
    def test_nexus_init_recall(self):
        """Test backward compatible API"""
        # Should not raise exception
        result = nexus_init()
        self.assertTrue(result)
        
        # Should return list
        results = nexus_recall("test", n=1)
        self.assertIsInstance(results, list)
    
    def test_nexus_add(self):
        """Test backward compatible add"""
        # Should not raise exception
        doc_id = nexus_add("Test content", "Test title", "test,tag")
        
        # May return None if backend not available, but shouldn't crash
        if doc_id is not None:
            self.assertIsInstance(doc_id, str)

    def test_degraded_recall_still_works(self):
        """Recall should still return usable results when vector backend is degraded."""
        self.assertTrue(nexus_init())
        doc_id = nexus_add("Fallback lexical memory for degraded mode", "FallbackDoc", "fallback,test")
        self.assertIsInstance(doc_id, str)
        results = nexus_recall("degraded fallback lexical", n=5)
        self.assertIsInstance(results, list)
        self.assertTrue(any("fallback" in (r.content or "").lower() for r in results))


class TestPluginSystem(unittest.TestCase):
    """Test Plugin System"""
    
    def setUp(self):
        self.registry = plugin_system_module.reset_plugin_registry()  # Clean registry
    
    def test_plugin_registration(self):
        """Test plugin registration"""
        NexusPlugin = plugin_system_module.NexusPlugin
        PluginMetadata = plugin_system_module.PluginMetadata
        
        # Create mock plugin
        class TestPlugin(NexusPlugin):
            def __init__(self):
                super().__init__()
                self.metadata = PluginMetadata(
                    name="test_plugin",
                    version="1.0.0",
                    description="Test plugin",
                    dependencies=[],
                    hot_reloadable=True,
                )

            async def initialize(self, config):
                return True

            async def start(self):
                return True

            async def stop(self):
                return True
        
        plugin = TestPlugin()
        
        # Register
        result = self.registry.register(plugin, plugin.metadata)
        self.assertTrue(result)
        
        # Get plugin
        retrieved = self.registry.get("test_plugin")
        self.assertIs(retrieved, plugin)
    
    def test_dependency_resolution(self):
        """Test dependency resolution"""
        NexusPlugin = plugin_system_module.NexusPlugin
        PluginMetadata = plugin_system_module.PluginMetadata
        
        class DependentPlugin(NexusPlugin):
            def __init__(self):
                super().__init__()
                self.metadata = PluginMetadata(
                    name="dependent_plugin",
                    version="1.0.0",
                    description="Dependent plugin",
                    dependencies=["config_manager"],  # Should exist
                    hot_reloadable=True,
                )

            async def initialize(self, config):
                return True

            async def start(self):
                return True

            async def stop(self):
                return True
        
        plugin = DependentPlugin()
        
        # Register
        result = self.registry.register(plugin, plugin.metadata)
        self.assertTrue(result)


class TestStorageAbstraction(unittest.TestCase):
    """Test storage abstraction layer"""
    
    def test_storage_result(self):
        """Test StorageResult functionality"""
        StorageResult = storage_base_module.StorageResult
        
        # Success result
        success = StorageResult.ok("data")
        self.assertTrue(success.success)
        self.assertEqual(success.data, "data")
        self.assertIsNone(success.error_msg)
        
        # Error result
        error = StorageResult.err("error message")
        self.assertFalse(error.success)
        self.assertEqual(error.error_msg, "error message")
        self.assertIsNone(error.data)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
