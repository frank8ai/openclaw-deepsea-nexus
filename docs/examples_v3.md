# Deep-Sea Nexus v3.0 Usage Examples

> Archived reference: this file contains v3-era examples and is not the current
> source of truth for the v5 runtime.
> Current docs:
> - `README.md`
> - `README_EN.md`
> - `API_CURRENT.md`
> - `ARCHITECTURE_CURRENT.md`

## Table of Contents
1. [Quick Start](#quick-start)
2. [New API Examples](#new-api-examples)
3. [Legacy API Examples](#legacy-api-examples)
4. [Mixed Usage](#mixed-usage)
5. [Plugin Development](#plugin-development)
6. [Advanced Patterns](#advanced-patterns)

---

## Quick Start

### Installation
```bash
pip install deepsea-nexus==3.0.0
```

### Basic Usage (New API)
```python
from deepsea_nexus import create_app

# Create application
app = create_app()

# Initialize and start
await app.initialize()
await app.start()

# Add a document
doc_id = await app.plugins["nexus_core"].add_document(
    content="Python is a versatile programming language.",
    title="Python Introduction",
    tags="python,programming,basics"
)

# Search for information
results = await app.plugins["nexus_core"].search_recall("Python programming", n=5)
for result in results:
    print(f"[{result.relevance:.2f}] {result.source}: {result.content[:100]}...")

# Shutdown gracefully
await app.stop()
```

### Basic Usage (Legacy API - Still Works!)
```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

# Initialize (same as before!)
nexus_init()

# Add document (same API!)
doc_id = nexus_add(
    content="Python is a versatile programming language.",
    title="Python Introduction", 
    tags="python,programming,basics"
)

# Search (same API!)
results = nexus_recall("Python programming", n=5)
for result in results:
    print(f"[{result.relevance:.2f}] {result.source}: {result.content[:100]}...")
```

---

## New API Examples

### 1. Complete Application Lifecycle
```python
from deepsea_nexus import create_app
import asyncio

async def main():
    # Create with custom config
    app = create_app("/path/to/my_config.json")
    
    try:
        # Initialize application
        if await app.initialize():
            print("✅ Application initialized")
        else:
            print("❌ Initialization failed")
            return
        
        # Start all services
        if await app.start():
            print("✅ Application started")
        else:
            print("❌ Start failed")
            return
        
        # Use plugins
        nexus_core = app.plugins["nexus_core"]
        session_mgr = app.plugins["session_manager"]
        flush_mgr = app.plugins["flush_manager"]
        
        # Example operations
        doc_id = await nexus_core.add_document(
            content="Sample document content",
            title="Sample Title"
        )
        
        session_id = session_mgr.start_session("My Session")
        
        # Perform operations...
        
    finally:
        # Graceful shutdown
        await app.stop()
        print("✅ Application stopped")

# Run the example
asyncio.run(main())
```

### 2. Event-Driven Programming
```python
from deepsea_nexus import create_app
import asyncio

async def event_handler(event):
    """Handle events from the system"""
    print(f"Event: {event.type}")
    print(f"Data: {event.data}")
    
    # Example: Log search events
    if event.type == "nexus.search.completed":
        print(f"Search for '{event.data.get('query')}' returned {len(event.data.get('results', []))} results")

async def main():
    app = create_app()
    await app.initialize()
    await app.start()
    
    # Subscribe to events
    app.event_bus.subscribe("nexus.*", event_handler)  # All nexus events
    app.event_bus.subscribe("session.*", event_handler)  # All session events
    
    # Perform operations that generate events
    nexus_core = app.plugins["nexus_core"]
    await nexus_core.add_document("Test content", "Test title")
    results = await nexus_core.search_recall("test", n=1)
    
    # Let events process
    await asyncio.sleep(0.1)
    
    await app.stop()

asyncio.run(main())
```

### 3. Custom Plugin Development
```python
from deepsea_nexus.core.plugin_system import NexusPlugin, PluginMetadata
from deepsea_nexus.core.event_bus import EventTypes
import asyncio

class AnalyticsPlugin(NexusPlugin):
    """
    Example plugin that tracks usage analytics
    """
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="analytics",
            version="1.0.0",
            description="Usage analytics tracking",
            dependencies=["nexus_core"],  # Depends on nexus_core
            hot_reloadable=True,
        )
        self.stats = {
            "searches": 0,
            "documents_added": 0,
            "session_starts": 0,
        }
    
    async def initialize(self, config):
        """Initialize plugin with configuration"""
        self.enabled = config.get("analytics", {}).get("enabled", True)
        return True
    
    async def start(self):
        """Start the plugin - subscribe to events"""
        if self._event_bus and self.enabled:
            self._event_bus.subscribe(EventTypes.DOCUMENT_ADDED, self._on_document_added)
            self._event_bus.subscribe(EventTypes.SEARCH_COMPLETED, self._on_search_completed)
            self._event_bus.subscribe(EventTypes.SESSION_CREATED, self._on_session_created)
        return True
    
    async def stop(self):
        """Stop the plugin"""
        print(f"Analytics stats: {self.stats}")
        return True
    
    async def _on_document_added(self, event):
        self.stats["documents_added"] += 1
        print(f"Document added: {event.data.get('title')}")
    
    async def _on_search_completed(self, event):
        self.stats["searches"] += 1
        print(f"Search completed: {event.data.get('query')}")
    
    async def _on_session_created(self, event):
        self.stats["session_starts"] += 1
        print(f"Session started: {event.data.get('session_id')}")

# Using the custom plugin
async def main():
    app = create_app()
    
    # Register custom plugin
    app.registry.register(AnalyticsPlugin())
    
    await app.initialize()
    await app.start()
    
    # Use the system - analytics will track
    nexus = app.plugins["nexus_core"]
    await nexus.add_document("Sample content", "Sample title")
    results = await nexus.search_recall("sample", n=1)
    
    await app.stop()

asyncio.run(main())
```

### 4. Advanced Compression Usage
```python
from deepsea_nexus import CompressionManager
import asyncio

async def compression_examples():
    # Different compression algorithms
    data = b"This is sample data that will be compressed using different algorithms." * 100
    
    # Gzip (built-in, good balance)
    gzip_cm = CompressionManager("gzip", level=6)
    gzip_compressed = gzip_cm.compress(data)
    print(f"Gzip: {len(data)} -> {len(gzip_compressed)} bytes ({len(gzip_compressed)/len(data):.2f} ratio)")
    
    # Zstd (high compression, requires: pip install zstandard)
    try:
        zstd_cm = CompressionManager("zstd", level=3)
        zstd_compressed = zstd_cm.compress(data)
        print(f"Zstd: {len(data)} -> {len(zstd_compressed)} bytes ({len(zstd_compressed)/len(data):.2f} ratio)")
    except ImportError:
        print("Zstd not available - install with: pip install zstandard")
    
    # LZ4 (fast compression, requires: pip install lz4)
    try:
        lz4_cm = CompressionManager("lz4")
        lz4_compressed = lz4_cm.compress(data)
        print(f"LZ4: {len(data)} -> {len(lz4_compressed)} bytes ({len(lz4_compressed)/len(data):.2f} ratio)")
    except ImportError:
        print("LZ4 not available - install with: pip install lz4")
    
    # File operations
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(data)
        temp.flush()
        temp_path = temp.name
    
    try:
        # Compress file
        result = gzip_cm.compress_file(temp_path)
        if result.success:
            compressed_path = result.data["target_path"]
            print(f"File compressed: {temp_path} -> {compressed_path}")
            
            # Decompress file
            result = gzip_cm.decompress_file(compressed_path)
            if result.success:
                print(f"File decompressed successfully")
    finally:
        import os
        os.unlink(temp_path)
        compressed_file = temp_path + ".gz"
        if os.path.exists(compressed_file):
            os.unlink(compressed_file)

asyncio.run(compression_examples())
```

---

## Legacy API Examples

### 1. Simple Search and Add
```python
from deepsea_nexus import nexus_init, nexus_recall, nexus_add

# Initialize (exactly as before)
nexus_init()

# Add document (same API as v2.x)
doc_id = nexus_add(
    content="Artificial Intelligence is transforming technology.",
    title="AI Revolution",
    tags="ai,technology,future"
)

# Search (same API as v2.x)
results = nexus_recall("artificial intelligence", n=3)
for result in results:
    print(f"[{result.relevance:.2f}] {result.source}")
    print(f"  {result.content[:150]}...")
    print()
```

### 2. Session Management (Legacy)
```python
from deepsea_nexus import (
    nexus_init, 
    start_session, 
    close_session, 
    get_session_manager
)

# Initialize
nexus_init()

# Start session
session_id = start_session("Python Learning Session")
print(f"Started session: {session_id}")

# Get session info
session_mgr = get_session_manager()
session = session_mgr.get_session(session_id)
if session:
    print(f"Session topic: {session.topic}")
    print(f"Created: {session.created_at}")

# Close session
close_session(session_id)
print(f"Closed session: {session_id}")
```

### 3. Health Checks (Legacy)
```python
from deepsea_nexus import nexus_health, nexus_stats

# Check system health
health = nexus_health()
print(f"Nexus available: {health['available']}")
print(f"Documents: {health['documents']}")
print(f"Version: {health['version']}")

# Get statistics
stats = nexus_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Status: {stats['status']}")
```

---

## Mixed Usage Examples

### 1. Gradual Migration
```python
from deepsea_nexus import create_app, nexus_init, nexus_recall

async def gradual_migration_example():
    # Start with legacy initialization
    nexus_init()  # Still works!
    
    # Create new app for new features
    app = create_app()
    await app.initialize()
    await app.start()
    
    # Use legacy API for existing code
    legacy_results = nexus_recall("existing query", n=3)
    
    # Use new API for enhanced features
    new_results = await app.plugins["nexus_core"].search_recall("new query", n=5)
    
    # Compare results
    print(f"Legacy results: {len(legacy_results)}")
    print(f"New results: {len(new_results)}")
    
    await app.stop()

asyncio.run(gradual_migration_example())
```

### 2. Configuration Sharing
```python
from deepsea_nexus import create_app, get_config_manager

# Create app with config
app = create_app("/path/to/config.json")
await app.initialize()

# Access shared config from anywhere
config = get_config_manager()
base_path = config.get("base_path", "./memory")
archive_days = config.get("session.auto_archive_days", 30)

print(f"Base path: {base_path}")
print(f"Archive after: {archive_days} days")

await app.stop()
```

---

## Advanced Patterns

### 1. Plugin Dependency Injection
```python
from deepsea_nexus.core.plugin_system import NexusPlugin, PluginMetadata

class DependentPlugin(NexusPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="dependent_plugin",
            version="1.0.0",
            description="Plugin that depends on others",
            dependencies=["nexus_core", "session_manager"],  # Specify dependencies
            hot_reloadable=True,
        )
    
    async def initialize(self, config):
        # Dependencies are guaranteed to be available
        nexus_core = self._registry.get("nexus_core")
        session_mgr = self._registry.get("session_manager")
        
        if not nexus_core or not session_mgr:
            raise Exception("Required dependencies not available")
        
        self.nexus_core = nexus_core
        self.session_mgr = session_mgr
        return True
    
    async def enhanced_operation(self, query, session_id):
        """Operation that uses multiple plugins"""
        # Search in nexus
        results = await self.nexus_core.search_recall(query, n=5)
        
        # Track in session
        if self.session_mgr.get_session(session_id):
            self.session_mgr.add_chunk(session_id)  # Increment chunk counter
        
        return results
```

### 2. Hot Configuration Reload
```python
from deepsea_nexus import create_app
import asyncio
import json
import tempfile

async def hot_reload_example():
    # Create temporary config
    config_fd, config_path = tempfile.mkstemp(suffix='.json')
    
    initial_config = {
        "session": {"auto_archive_days": 30},
        "nexus": {"embedder_name": "all-MiniLM-L6-v2"}
    }
    
    with open(config_path, 'w') as f:
        json.dump(initial_config, f)
    
    app = create_app(config_path)
    await app.initialize()
    await app.start()
    
    print(f"Initial archive days: {app.config.get('session.auto_archive_days')}")
    
    # Modify config file
    modified_config = {
        "session": {"auto_archive_days": 7},  # Change to 7 days
        "nexus": {"embedder_name": "all-MiniLM-L6-v2"}
    }
    
    with open(config_path, 'w') as f:
        json.dump(modified_config, f)
    
    # Hot reload
    await app.reload()
    
    print(f"After reload: {app.config.get('session.auto_archive_days')}")
    
    await app.stop()
    import os
    os.unlink(config_path)

asyncio.run(hot_reload_example())
```

### 3. Error Handling Best Practices
```python
from deepsea_nexus import create_app
import asyncio

async def robust_usage():
    app = None
    try:
        app = create_app()
        
        if not await app.initialize():
            print("❌ Failed to initialize application")
            return
        
        if not await app.start():
            print("❌ Failed to start application")
            return
        
        # Use plugins with error handling
        nexus_core = app.plugins.get("nexus_core")
        if not nexus_core:
            print("❌ Nexus core plugin not available")
            return
        
        try:
            results = await nexus_core.search_recall("query", n=5)
            print(f"✅ Found {len(results)} results")
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        if app:
            try:
                await app.stop()
                print("✅ Application stopped")
            except Exception as e:
                print(f"❌ Error stopping app: {e}")

asyncio.run(robust_usage())
```

---

## Performance Tips

### 1. Efficient Batch Operations
```python
async def efficient_batch_processing():
    app = create_app()
    await app.initialize()
    await app.start()
    
    # Batch add documents efficiently
    documents = [
        {"content": f"Content {i}", "title": f"Title {i}", "tags": f"tag{i}"}
        for i in range(100)
    ]
    
    nexus_core = app.plugins["nexus_core"]
    
    # Use batch processing instead of individual calls
    added_ids = []
    batch_size = 10
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        for doc in batch:
            doc_id = await nexus_core.add_document(
                doc["content"], doc["title"], doc["tags"]
            )
            if doc_id:
                added_ids.append(doc_id)
    
    print(f"Added {len(added_ids)} documents efficiently")
    
    await app.stop()
```

### 2. Resource Management
```python
from deepsea_nexus import create_app
import asyncio

async def resource_efficient_usage():
    """Example of efficient resource usage"""
    
    # Use context manager pattern
    async with create_app() as app:
        # App automatically initializes and starts
        nexus_core = app.plugins["nexus_core"]
        
        # Perform operations
        results = await nexus_core.search_recall("query", n=5)
        print(f"Found {len(results)} results")
        
    # App automatically stops when exiting context

asyncio.run(resource_efficient_usage())
```

---

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**
```python
# Check if plugin is registered
app = create_app()
await app.initialize()

if "nexus_core" not in app.plugins:
    print("Plugin not loaded - check dependencies and config")
    print("Available plugins:", app.registry.list_all())
```

2. **Configuration Problems**
```python
# Validate configuration
config = get_config_manager()
errors = config.validate()
if errors:
    print("Config errors:", errors)
```

3. **Performance Issues**
```python
# Enable debug logging to identify bottlenecks
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*These examples demonstrate the flexibility and power of Deep-Sea Nexus v3.0. Choose the approach that best fits your use case and gradually migrate from legacy to new APIs as needed.*
