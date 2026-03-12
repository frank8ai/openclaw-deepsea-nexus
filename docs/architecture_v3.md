# Deep-Sea Nexus v4.1 (built on v3 architecture)
## Hot-Pluggable Architecture Documentation

> Archived: this document describes the earlier v4.1-on-v3 architecture view.
> Current docs:
> - `README.md`
> - `README_EN.md`
> - `docs/ARCHITECTURE_CURRENT.md`
> - `docs/API_CURRENT.md`

**Version:** 4.1.0  
**Status:** Production Ready  
**Release Date:** February 2026

---

## Overview

Deep-Sea Nexus v4.1 builds on the v3 hot-pluggable architecture, keeping 100% backward compatibility while adding associative memory via a light knowledge graph.

### Key Features
- ✅ **Hot-Pluggable Architecture** - Dynamic plugin loading/unloading
- ✅ **Event-Driven Communication** - Decoupled module interaction  
- ✅ **Unified Compression** - Eliminates code duplication
- ✅ **100% Backward Compatible** - Zero breaking changes
- ✅ **Swappable Storage** - Pluggable storage backends
- ✅ **Async First** - Non-blocking operations

---

## Architecture

### Core Components

#### 1. Plugin System
```python
from deepsea_nexus import NexusPlugin, PluginMetadata

class MyPlugin(NexusPlugin):
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            dependencies=["config_manager"],
            hot_reloadable=True
        )
```

#### 2. Event Bus
```python
from deepsea_nexus import get_event_bus

event_bus = get_event_bus()
event_bus.subscribe("nexus.search.completed", my_handler)
event_bus.publish("my.custom.event", {"data": "value"})
```

#### 3. Config Manager
```python
from deepsea_nexus import get_config_manager

config = get_config_manager()
config.set("my.setting", "value")
value = config.get("my.setting", "default")
```

#### 4. Storage Abstraction
```python
from deepsea_nexus import CompressionManager

# Unified compression (no duplicate code!)
cm = CompressionManager("zstd")  # gzip, zstd, lz4
compressed = cm.compress(data)
decompressed = cm.decompress(compressed)
```

---

## API Migration Guide

### New API (Recommended v3.0)
```python
from deepsea_nexus import create_app

# Create and start application
app = create_app("/path/to/config.json")
await app.initialize()
await app.start()

# Use plugins directly
results = await app.plugins["nexus_core"].search_recall("query")

# Graceful shutdown
await app.stop()
```

### Legacy API (Still Works)
```python
from deepsea_nexus import nexus_init, nexus_recall

# Same as before - no changes needed!
nexus_init()
results = nexus_recall("query", n=5)
```

### Mixed Usage (Both APIs Together)
```python
from deepsea_nexus import create_app, nexus_recall

# New API
app = create_app()
await app.initialize()
await app.start()

# Legacy API still works
legacy_results = nexus_recall("query")

# New API also available
new_results = await app.plugins["nexus_core"].search_recall("query")
```

---

## Performance Improvements

### Compression Benchmarks
| Algorithm | Compression Ratio | Speed (MB/s) | Dependencies |
|-----------|------------------|--------------|--------------|
| gzip      | 0.15-0.30        | 50-100       | Built-in     |
| zstd      | 0.10-0.25        | 100-200      | zstandard    |
| lz4       | 0.20-0.40        | 300-500      | lz4          |

### Operation Throughput
- **Search**: 100+ queries/second
- **Add Document**: 50+ operations/second  
- **Session Operations**: 1000+ operations/second
- **Event Processing**: 10,000+ events/second

---

## Configuration

### Sample Configuration
```json
{
  "base_path": "./memory",
  "nexus": {
    "vector_db_path": "./vector_db",
    "embedder_name": "all-MiniLM-L6-v2"
  },
  "session": {
    "auto_archive_days": 30,
    "index_file": "_sessions_index.json"
  },
  "flush": {
    "enabled": true,
    "archive_time": "03:00",
    "compress_enabled": true,
    "compress_algorithm": "zstd"
  },
  "plugins": {
    "auto_load": [
      "nexus_core",
      "session_manager", 
      "flush_manager"
    ]
  }
}
```

---

## Development Guide

### Creating Custom Plugins
```python
from deepsea_nexus.core.plugin_system import NexusPlugin, PluginMetadata

class CustomPlugin(NexusPlugin):
    async def initialize(self, config):
        # Initialize with config
        return True
    
    async def start(self):
        # Start plugin services
        return True
    
    async def stop(self):
        # Cleanup resources
        return True
    
    def my_custom_method(self):
        # Your plugin functionality
        pass
```

### Using the Event System
```python
# Subscribe to events
async def my_handler(event):
    print(f"Received: {event.type} with data: {event.data}")

app.event_bus.subscribe("nexus.*", my_handler)

# Publish custom events
await app.event_bus.publish("my.custom.event", {"key": "value"})
```

---

## Migration Checklist

### Before Deploying v3.0
- [ ] Test with existing code (backward compatibility)
- [ ] Review configuration changes
- [ ] Plan rollout strategy
- [ ] Backup existing data

### Upgrade Process
1. Install v3.0: `pip install deepsea-nexus==3.0.0`
2. Update configuration if needed
3. Test with legacy API
4. Migrate to new API gradually
5. Monitor performance

### Rollback Plan
- Revert to v2.x: `pip install deepsea-nexus==2.x.x`
- Restore previous configuration
- Verify functionality

---

## Best Practices

### For New Development
- Use the new `create_app()` API
- Leverage plugin system for modularity
- Use event bus for loose coupling
- Implement proper error handling

### For Legacy Code
- Existing code continues to work unchanged
- Gradually migrate to new API
- Use mixed approach during transition
- Monitor performance after migration

---

## Support & Maintenance

### Version Support Policy
- v3.0: Full support, active development
- v2.x: Security patches only
- v1.x: End-of-life

### Issue Reporting
- Bug reports: GitHub Issues
- Performance issues: Include benchmarks
- Feature requests: RFC process
- Security issues: Responsible disclosure

---

## Release Notes

### v3.0.0 (February 2026)
**Major Architecture Changes:**
- Hot-pluggable plugin system
- Event-driven architecture
- Unified compression layer
- 100% backward compatibility maintained
- Performance improvements across all operations
- Modular storage backends

**Breaking Changes:** None - 100% backward compatible

**New Features:**
- Dynamic plugin loading/unloading
- Config hot-reload support
- Advanced compression options (zstd, lz4)
- Improved session management
- Enhanced error handling

**Performance Improvements:**
- 2x faster compression/decompression
- 3x faster event processing
- Reduced memory footprint
- Better async support

---

## Contact & Support

- **GitHub:** [frank8ai/deepsea-nexus](https://github.com/frank8ai/deepsea-nexus)
- **Issues:** [Issues](https://github.com/frank8ai/deepsea-nexus/issues)

---

*This documentation covers all aspects of Deep-Sea Nexus v3.0. For additional support, contact the development team.*
