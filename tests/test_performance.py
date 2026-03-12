"""
Performance benchmarks for Deep-Sea Nexus.

Benchmark the new architecture performance vs. expected metrics.
"""

import asyncio
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from dataclasses import dataclass
from typing import List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("NEXUS_TEST_MODE", "1")


def _load_local_package():
    spec = importlib.util.spec_from_file_location(
        "deepsea_nexus_local_performance",
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
nexus_init = deepsea_nexus.nexus_init
nexus_recall = deepsea_nexus.nexus_recall
nexus_add = deepsea_nexus.nexus_add
CompressionManager = deepsea_nexus.CompressionManager
storage_base_module = importlib.import_module(f"{deepsea_nexus.__name__}.storage.base")
event_bus_module = importlib.import_module(f"{deepsea_nexus.__name__}.core.event_bus")


@dataclass
class BenchmarkResult:
    """Benchmark result container"""
    name: str
    duration: float
    operations: int
    ops_per_second: float
    memory_used: float  # MB
    success: bool
    details: dict


class PerformanceBenchmark(unittest.TestCase):
    """Performance benchmark tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.results: List[BenchmarkResult] = []
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def benchmark(self, name: str, func, *args, **kwargs) -> BenchmarkResult:
        """Generic benchmark function"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            success = True
            details = {"result": result}
        except Exception as e:
            success = False
            details = {"error": str(e)}
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        ops_per_second = kwargs.get("operations", 0) / duration if duration > 0 else 0
        
        benchmark_result = BenchmarkResult(
            name=name,
            duration=duration,
            operations=kwargs.get("operations", 0),
            ops_per_second=ops_per_second,
            memory_used=memory_used,
            success=success,
            details=details,
        )
        
        self.results.append(benchmark_result)
        return benchmark_result
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def test_application_startup_performance(self):
        """Benchmark application startup time"""
        def startup_func():
            config_path = os.path.join(self.temp_dir, "perf_config.json")
            config = {
                "base_path": self.temp_dir,
                "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
                "session": {"auto_archive_days": 30},
                "flush": {"enabled": False},
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            app = create_app(config_path)
            init_success = asyncio.run(app.initialize())
            start_success = asyncio.run(app.start())
            
            # Stop immediately to measure startup only
            asyncio.run(app.stop())
            
            return init_success and start_success
        
        result = self.benchmark(
            "Application Startup",
            startup_func,
            operations=1
        )
        
        # Should start up quickly (< 2 seconds for minimal config)
        self.assertLess(result.duration, 5.0, f"Startup took {result.duration}s, expected < 5s")
        print(f"✓ {result.name}: {result.duration:.2f}s")
    
    def test_compression_performance(self):
        """Benchmark compression performance"""
        test_data = b"A" * 1024 * 100  # 100KB of test data
        
        for algo in ["gzip", "zstd", "lz4"]:
            try:
                cm = CompressionManager(algo)
                
                def compress_func(*, operations: int = 1):
                    # Accept `operations` kwarg because `benchmark()` forwards it.
                    compressed = cm.compress(test_data)
                    decompressed = cm.decompress(compressed)
                    return len(test_data), len(compressed)

                result = self.benchmark(
                    f"Compression {algo}",
                    compress_func,
                    operations=1
                )
                
                if not result.success or "result" not in result.details:
                    self.fail(f"Compression benchmark failed: {result.details}")

                original_len, compressed_len = result.details["result"]
                compression_ratio = compressed_len / original_len
                
                print(f"✓ {result.name}: {result.duration:.3f}s, "
                      f"ratio={compression_ratio:.2f}, "
                      f"speed={result.ops_per_second:.1f} ops/s")
                
                # Verify correctness
                self.assertEqual(result.details["result"][0], len(test_data))
                
            except ImportError:
                print(f"⚠️  Skipping {algo} (not available)")
    
    def test_concurrent_operations(self):
        """Benchmark concurrent operations"""
        # Initialize for concurrent testing (use a temp config so plugin deps load deterministically)
        config_path = os.path.join(self.temp_dir, "perf_concurrent_config.json")
        config = {
            "base_path": self.temp_dir,
            "nexus": {"vector_db_path": os.path.join(self.temp_dir, "vector_db")},
            "session": {"auto_archive_days": 30},
            "flush": {"enabled": False},
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
        with open(config_path, "w") as f:
            json.dump(config, f)

        self.assertTrue(nexus_init(config_path))
        
        async def concurrent_add_tasks():
            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        nexus_add,
                        f"Test content {i}",
                        f"Title {i}",
                        f"tag{i}"
                    )
                )
                tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        def concurrent_func():
            return asyncio.run(concurrent_add_tasks())
        
        result = self.benchmark(
            "Concurrent Adds (10 parallel)",
            concurrent_func,
            operations=10
        )
        
        print(f"✓ {result.name}: {result.duration:.3f}s, "
              f"speed={result.ops_per_second:.1f} ops/s")
    
    def test_large_search_performance(self):
        """Benchmark search performance with simulated data"""
        # Simulate search without requiring actual vector store
        def mock_search():
            # Simulate search that takes some time
            time.sleep(0.01)  # Simulate processing
            # Return mock results
            results = [
                storage_base_module.RecallResult(
                    content=f"Mock result {i}",
                    source=f"source_{i}",
                    relevance=0.9 - (i * 0.1),
                    metadata={"test": True},
                    doc_id=f"id_{i}"
                )
                for i in range(5)
            ]
            return results
        
        result = self.benchmark(
            "Search Performance (mock)",
            mock_search,
            operations=1
        )
        
        print(f"✓ {result.name}: {result.duration:.3f}s")
    
    def test_plugin_communication_overhead(self):
        """Benchmark plugin communication overhead"""
        async def publish_many_events():
            event_bus = event_bus_module.get_event_bus()
            received_events = []
            
            def handler(event):
                received_events.append(event)
            
            event_bus.subscribe("benchmark.test", handler)
            
            # Publish many events
            for i in range(100):
                event_bus.publish("benchmark.test", {"id": i, "data": f"test_{i}"})
            
            # Wait for processing
            await asyncio.sleep(0.01)
            
            return len(received_events)
        
        def event_func():
            return asyncio.run(publish_many_events())
        
        result = self.benchmark(
            "Event Communication (100 events)",
            event_func,
            operations=100
        )
        
        print(f"✓ {result.name}: {result.duration:.3f}s, "
              f"speed={result.ops_per_second:.1f} events/s")
    
    def test_session_operations(self):
        """Benchmark session operations"""
        # Initialize session manager
        nexus_init()

        def session_ops():
            session_ids = []
            
            # Create 10 sessions
            for i in range(10):
                sid = deepsea_nexus.start_session(f"Benchmark Session {i}")
                session_ids.append(sid)
            
            # Close all sessions
            for sid in session_ids:
                deepsea_nexus.close_session(sid)
            
            return len(session_ids)
        
        result = self.benchmark(
            "Session Operations (10 create/close)",
            session_ops,
            operations=20  # 10 creates + 10 closes
        )
        
        print(f"✓ {result.name}: {result.duration:.3f}s, "
              f"speed={result.ops_per_second:.1f} ops/s")
    
    def print_summary(self):
        """Print benchmark summary"""
        print(f"\n📊 Performance Benchmark Summary")
        print("=" * 60)
        
        total_duration = sum(r.duration for r in self.results)
        total_ops = sum(r.operations for r in self.results)
        
        print(f"Total tests: {len(self.results)}")
        print(f"Total duration: {total_duration:.3f}s")
        print(f"Total operations: {total_ops}")
        
        if total_duration > 0:
            print(f"Overall throughput: {total_ops / total_duration:.1f} ops/s")
        
        print("\nIndividual Results:")
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.name}: {result.duration:.3f}s "
                  f"({result.ops_per_second:.1f} ops/s)")


class CompressionBenchmark(unittest.TestCase):
    """Specific compression benchmarks"""
    
    def test_compression_ratios(self):
        """Test compression ratios for different data types"""
        import json
        
        # Different types of test data
        test_datasets = {
            "random_bytes": bytes([i % 256 for i in range(1024 * 50)]),  # 50KB random
            "repeated_text": b"Hello World! " * (1024 * 4),  # 48KB repeated
            "json_data": json.dumps({
                "items": [{"id": i, "data": f"item_{i}"} for i in range(1000)]
            }).encode() * 2,  # JSON-like data
            "mixed_content": (
                b"Line 1: This is some sample text.\n" * 500 +
                b"Line 2: More content with numbers 123456789.\n" * 500 +
                b"Line 3: Special chars !@#$%^&*()\n" * 500
            ),
        }
        
        print(f"\n📦 Compression Ratio Analysis")
        print("=" * 60)
        
        for dataset_name, data in test_datasets.items():
            print(f"\nDataset: {dataset_name} ({len(data)} bytes)")
            print("-" * 40)
            
            for algo in ["gzip", "zstd", "lz4"]:
                try:
                    cm = CompressionManager(algo)
                    compressed = cm.compress(data)
                    ratio = len(compressed) / len(data)
                    
                    print(f"  {algo:4s}: {len(compressed):6d} bytes, "
                          f"ratio={ratio:.3f}, time={cm.backend.__class__.__name__}")
                except ImportError:
                    print(f"  {algo:4s}: N/A (not installed)")
    
    def test_compression_speed_vs_ratio(self):
        """Compare speed vs compression ratio tradeoffs"""
        test_data = b"The quick brown fox jumps over the lazy dog. " * 1000  # 48KB
        
        print(f"\n⚡ Speed vs Compression Analysis")
        print("=" * 60)
        print(f"{'Algorithm':<10} {'Size':<8} {'Ratio':<8} {'Time(s)':<10} {'Speed':<12}")
        print("-" * 60)
        
        for algo in ["gzip", "zstd", "lz4"]:
            try:
                start = time.time()
                cm = CompressionManager(algo)
                compressed = cm.compress(test_data)
                duration = time.time() - start
                
                ratio = len(compressed) / len(test_data)
                speed = len(test_data) / duration / 1024 / 1024  # MB/s
                
                print(f"{algo:<10} {len(compressed):<8,d} {ratio:<8.3f} "
                      f"{duration:<10.4f} {speed:<12.2f}")
            except ImportError:
                print(f"{algo:<10} {'N/A':<8} {'N/A':<8} {'N/A':<10} {'N/A':<12}")


def run_performance_benchmarks():
    """Run all performance benchmarks"""
    print("⚡ Running Deep-Sea Nexus performance benchmarks...")
    
    # Run performance tests
    loader = unittest.TestLoader()
    perf_suite = loader.loadTestsFromTestCase(PerformanceBenchmark)
    compression_suite = loader.loadTestsFromTestCase(CompressionBenchmark)
    
    # Combine suites
    all_tests = unittest.TestSuite([perf_suite, compression_suite])
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(all_tests)
    
    # Print summary for performance tests specifically
    perf_test = PerformanceBenchmark()
    perf_test.setUp()
    
    # Run individual benchmarks to get timing data
    methods = [method for method in dir(perf_test) if method.startswith('test_')]
    for method_name in methods:
        method = getattr(perf_test, method_name)
        try:
            method()
        except:
            pass  # Expected for some tests that require optional dependencies
    
    perf_test.print_summary()
    
    print(f"\n📈 Performance Results:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    success = result.wasSuccessful()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Performance benchmarks {'passed' if success else 'failed'}")
    
    return success


if __name__ == "__main__":
    success = run_performance_benchmarks()
    exit(0 if success else 1)
