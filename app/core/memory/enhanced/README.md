# Enhanced Memory System for Chat2Graph

This module provides enhanced memory capabilities for Chat2Graph by integrating with the external MemFuse memory service. It enables persistent storage and intelligent retrieval of reasoning logs and operator execution experiences.

## 🎯 Overview

The enhanced memory system consists of three main components:

1. **MemoryService**: Singleton service for MemFuse API integration
2. **Hook System**: Non-intrusive hooks for memory operations
3. **Enhanced Wrappers**: Decorator pattern wrappers for existing components

## 🏗️ Architecture

### Core Components

#### MemoryService (`memory_service.py`)
- Central service for all MemFuse interactions
- Handles HTTP communication, error handling, and caching
- Provides unified interface for memory operations
- Follows Chat2Graph singleton service pattern

#### Hook System (`hook.py`)
- Abstract hook interfaces for extensibility
- Memory-specific hook implementations
- Hook manager for coordinated execution
- Error isolation and graceful failure handling

#### Integration Layer (`integration.py`)
- Enhanced wrappers for Reasoner and Operator
- Context enhancement with retrieved memories
- Decorator pattern maintains interface compatibility
- Integration manager for lifecycle management

#### Configuration (`config.py`)
- Environment-based configuration management
- Feature toggles and performance tuning
- MemFuse service connection settings

## 🔄 Data Flow

### Reasoner Memory Enhancement
```
Reasoner.infer(task)
    ↓
Pre-Reasoning Hook
    ↓
Retrieve Relevant Memories (MemFuse API)
    ↓
Enhance Task Context
    ↓
Execute Original Reasoning
    ↓
Post-Reasoning Hook
    ↓
Write Reasoning Log (MemFuse API)
    ↓
Return Result
```

### Operator Experience Learning
```
Operator.execute(job)
    ↓
Pre-Execution Hook
    ↓
Retrieve Relevant Experiences (MemFuse API)
    ↓
Enhance Job Context
    ↓
Execute Original Operation
    ↓
Post-Execution Hook
    ↓
Write Execution Log (MemFuse API)
    ↓
Return Result
```

## 🔧 Configuration

### Environment Variables

```bash
# Feature Toggles
MEMORY_ENABLED=true                    # Enable/disable memory functionality
MEMORY_RETRIEVAL_ENABLED=true         # Enable/disable memory retrieval
MEMORY_ASYNC_WRITE=true               # Async vs sync memory writes

# MemFuse Service Settings
MEMFUSE_BASE_URL=http://localhost:8001 # MemFuse service endpoint
MEMFUSE_TIMEOUT=30.0                   # HTTP request timeout (seconds)
MEMFUSE_RETRY_COUNT=3                  # Retry attempts for failed requests

# Performance Settings
MEMORY_MAX_CONTENT_LENGTH=10000        # Max content size for memory entries
MEMORY_CACHE_TTL=300                   # Cache TTL in seconds
MEMORY_RETRIEVAL_TOP_K=5               # Number of memories to retrieve
MEMORY_MAX_MEMORIES_IN_CONTEXT=3       # Max memories added to context

# Logging Settings
MEMORY_LOG_LEVEL=INFO                  # Memory operation log level
MEMORY_LOG_OPERATIONS=true             # Enable memory operation logging
```

### Configuration Loading
The system automatically loads configuration from environment variables when the MemoryService is initialized. Default values are provided for all settings.

## 🚀 Usage

### Automatic Integration
The memory enhancement is automatically integrated when:
1. MemoryService is initialized by ServiceFactory
2. Memory functionality is enabled via configuration
3. MemFuse service is accessible at configured URL

### Manual Integration
For custom integration scenarios:

```python
from app.core.memory.enhanced import MemoryService, MemoryConfig
from app.core.memory.enhanced.integration import MemoryIntegrationManager

# Initialize with custom configuration
config = MemoryConfig.from_env()
manager = MemoryIntegrationManager(config.to_memory_service_config())
await manager.initialize()

# Wrap existing components
enhanced_reasoner = manager.wrap_reasoner(base_reasoner)
enhanced_operator = manager.wrap_operator(base_operator)

# Use enhanced components normally
result = await enhanced_reasoner.infer(task)
operator_result = await enhanced_operator.execute(reasoner, job)

# Cleanup when done
await manager.cleanup()
```

## 🧪 Testing

### Running Tests
```bash
# Unit tests
pytest test/unit/test_memory_service.py -v
pytest test/unit/test_memory_hooks.py -v

# Integration tests
pytest test/integration/test_memory_integration.py -v

# All memory-related tests
pytest test/ -k "memory" -v
```

### Test Coverage
- **MemoryService**: API interactions, error handling, caching
- **Hook System**: Hook execution, error isolation, result handling
- **Enhanced Wrappers**: Context enhancement, delegation, compatibility
- **Integration**: End-to-end memory flows, configuration scenarios

## 🔍 Troubleshooting

### Common Issues

#### MemFuse Service Unavailable
**Symptoms**: Memory operations fail, warnings in logs
**Solution**: 
1. Check MemFuse service status: `curl http://localhost:8001/health`
2. Verify network connectivity
3. Temporarily disable memory: `MEMORY_ENABLED=false`

#### High Memory Operation Latency
**Symptoms**: Slow reasoning/execution performance
**Solution**:
1. Check MemFuse service performance
2. Reduce retrieval count: `MEMORY_RETRIEVAL_TOP_K=3`
3. Increase cache TTL: `MEMORY_CACHE_TTL=600`
4. Disable retrieval: `MEMORY_RETRIEVAL_ENABLED=false`

#### Memory Content Too Large
**Symptoms**: HTTP 413 errors, truncation warnings
**Solution**:
1. Reduce content limit: `MEMORY_MAX_CONTENT_LENGTH=5000`
2. Check reasoning message sizes
3. Optimize content formatting

### Debug Mode
Enable detailed logging for debugging:
```bash
MEMORY_LOG_LEVEL=DEBUG
MEMORY_LOG_OPERATIONS=true
```

## 🔒 Security Considerations

### Data Privacy
- Memory content may contain sensitive information
- Ensure MemFuse service has appropriate access controls
- Consider data retention policies for memory storage

### Network Security
- Use HTTPS for production MemFuse connections
- Implement authentication if required by MemFuse
- Monitor network traffic for anomalies

## 📈 Performance Monitoring

### Key Metrics
- Memory operation success rate
- Memory retrieval latency
- Cache hit rate
- MemFuse service availability

### Monitoring Setup
```python
# Example monitoring integration
from app.core.service.memory_service import MemoryService

memory_service = MemoryService.instance
health_status = await memory_service.health_check()
connection_status = await memory_service.test_connection()
```

## 🔮 Future Enhancements

### Planned Features
1. **Local Backup**: Local storage backup when MemFuse unavailable
2. **Batch Operations**: Batch memory writes for better performance
3. **Smart Filtering**: Intelligent filtering of memory content
4. **Memory Analytics**: Analytics dashboard for memory usage
5. **Multi-Backend**: Support for multiple memory backends

### Extension Points
- Additional hook types for other components
- Custom memory backends beyond MemFuse
- Advanced retrieval strategies and ranking
- Memory content preprocessing and enhancement

## 📚 References

- [MemFuse Documentation](../../../memfuse_mvp/docs/)
- [Chat2Graph Architecture](../../../doc/en-us/principle/architecture.md)
- [Service Layer Design](../../../doc/en-us/principle/service.md)
- [Hook Pattern Documentation](https://en.wikipedia.org/wiki/Hooking)
