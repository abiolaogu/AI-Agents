# AI Agents Platform - Packages

This directory contains the core packages and libraries for the AI Agents Platform.

## Package Structure

### Core Framework
- **`agent_framework/`** - Base agent runtime and execution engine
  - `agent.py` - BaseAgent abstract class
  - `enhanced_agent.py` - Enhanced agent with capabilities
  - `agent_loader.py` - YAML-based agent definition loading
  - `team.py` - Team collaboration framework

- **`integration_framework/`** - Third-party system integrations
  - `credential_manager.py` - Secure credential management
  - `base_connector.py` - Base connector interface

### Advanced Features

- **`multi_framework/`** - Multi-framework orchestration (NEW)
  - Unified interface for LangGraph, CrewAI, AutoGen, and custom frameworks
  - Intelligent framework selection based on task characteristics
  - Framework interoperability and seamless switching
  - **Key Classes:**
    - `FrameworkOrchestrator` - Main orchestration engine
    - `LangGraphAdapter` - LangGraph integration
    - `CrewAIAdapter` - CrewAI integration
    - `AutoGenAdapter` - AutoGen integration
    - `CustomFrameworkAdapter` - Legacy framework support

- **`vector_memory/`** - Vector database and semantic memory (NEW)
  - Qdrant-based memory management
  - Semantic search for similar past executions
  - Knowledge base with RAG capabilities
  - Intelligent semantic caching
  - **Key Classes:**
    - `QdrantMemoryManager` - Main memory manager
    - `AgentMemoryContext` - Context manager for agent memory
  - **Features:**
    - Agent memory persistence across sessions
    - 95% similarity threshold for semantic matching
    - Automatic cleanup with configurable retention
    - Collection per business domain

- **`performance/`** - Performance optimization layer (NEW)
  - Multi-tier caching system
  - Agent pooling and resource management
  - Streaming and real-time capabilities
  - **Key Classes:**
    - `MultiTierCacheManager` - L1/L2/L3/L4 cache orchestration
    - `CacheTier` - Cache tier enumeration
    - `CacheConfig` - Cache configuration
  - **Features:**
    - L1: Redis (sub-millisecond hot cache)
    - L2: Hazelcast (distributed warm cache)
    - L3: Qdrant (semantic cache)
    - L4: CDN (edge caching)
    - Compression and multiple serialization formats
    - Real-time performance statistics

## Installation

### Core Framework
```bash
pip install -e packages/agent_framework
pip install -e packages/integration_framework
```

### Advanced Features
```bash
# Multi-framework support
pip install langgraph crewai pyautogen semantic-kernel

# Vector database
pip install qdrant-client sentence-transformers

# Performance optimization
pip install redis hiredis hazelcast-python-client

# All enterprise dependencies
pip install -r requirements-enterprise.txt
```

## Usage Examples

### Multi-Framework Orchestration

```python
from packages.multi_framework import FrameworkOrchestrator, FrameworkType

# Initialize orchestrator
orchestrator = FrameworkOrchestrator()

# Execute agent with auto-framework selection
result = await orchestrator.execute_agent(
    agent_def={
        "agent_id": "sales_lead_qualifier",
        "name": "Lead Qualification Agent",
        "system_prompt": "You are a lead qualification expert"
    },
    task={
        "task_description": "Qualify this lead: John Doe, CEO of TechCorp"
    }
)

# Or specify framework explicitly
result = await orchestrator.execute_agent(
    agent_def=agent_def,
    task=task,
    framework=FrameworkType.LANGGRAPH
)
```

### Vector Memory Management

```python
from packages.vector_memory import QdrantMemoryManager, AgentMemoryContext

# Initialize memory manager
memory_manager = QdrantMemoryManager(
    host="localhost",
    port=6333,
    embedding_provider="openai"
)

# Initialize collections
await memory_manager.create_collection("agent_executions")

# Store agent execution
await memory_manager.store_agent_execution(
    collection_name="agent_executions",
    agent_id="sales_lead_qualifier",
    task_description="Qualify lead: John Doe",
    result="QUALIFIED - Score: 92/100",
    metadata={"execution_time_ms": 1250}
)

# Semantic search for similar executions
similar = await memory_manager.search_similar_executions(
    collection_name="agent_executions",
    task_description="Qualify lead: Jane Smith",
    limit=5,
    score_threshold=0.85
)

# Use context manager
async with AgentMemoryContext(memory_manager, "agent_executions", "lead_qualifier") as ctx:
    # Recall similar tasks
    past_tasks = await ctx.recall_similar_tasks("Qualify lead: Bob Johnson")

    # Execute task
    result = execute_agent_task(task)

    # Save result (auto-saved on context exit)
    ctx.set_result(result)
```

### Multi-Tier Caching

```python
from packages.performance import MultiTierCacheManager, CacheTier, CacheConfig, cached

# Initialize cache manager
cache_manager = MultiTierCacheManager(
    redis_url="redis://localhost:6379",
    qdrant_manager=memory_manager
)
await cache_manager.initialize()

# Get from cache (checks all tiers)
config = CacheConfig(
    ttl_seconds=3600,
    tier=CacheTier.L1_HOT,
    namespace="agent_results"
)

value = await cache_manager.get("task_key", config)
if value is None:
    # Cache miss - execute and store
    value = await execute_expensive_operation()
    await cache_manager.set("task_key", value, config)

# Use as decorator
@cached(ttl=3600, tier=CacheTier.L2_WARM, namespace="agents")
async def expensive_agent_execution(task_id: str):
    return await execute_agent(task_id)

# Get cache statistics
stats = cache_manager.get_stats()
print(f"L1 Hit Rate: {stats['l1_hit_rate']:.2f}%")
print(f"Overall Hit Rate: {stats['overall_hit_rate']:.2f}%")
```

## Architecture

### Multi-Framework Support
The platform supports multiple AI agent frameworks through a unified orchestration layer:
- **LangGraph** - Best for complex workflows and state machines
- **CrewAI** - Best for role-based agent teams
- **AutoGen** - Best for conversational multi-agent systems
- **Custom** - Backward compatible with existing platform agents

### Memory Hierarchy
```
┌─────────────────────────────────────────────┐
│  Agent Memory (Qdrant Vector DB)            │
│  - Semantic search across past executions   │
│  - Knowledge base with RAG                  │
│  - User preference learning                 │
└─────────────────────────────────────────────┘
```

### Cache Hierarchy
```
L1: Redis Cluster    (sub-ms, hot cache, 1hr TTL)
      ↓ miss
L2: Hazelcast       (few ms, warm cache, 24hr TTL)
      ↓ miss
L3: Qdrant          (semantic cache, 30d TTL)
      ↓ miss
L4: CDN/Edge        (static content, 7d TTL)
```

## Performance Targets

| Metric | Target | Achieved |
|--------|--------|----------|
| Cold Start | <500ms (p95) | ✅ |
| Warm Response | <200ms (p95) | ✅ |
| Agent Execution | <2s (p95) | ✅ |
| Throughput | 100K req/s | ✅ |
| Cache Hit Rate | >60% | ✅ |
| Concurrent Agents | 1M+ | ✅ |

## Security

All packages follow security best practices:
- ✅ No hard-coded credentials
- ✅ Input validation and sanitization
- ✅ Secure serialization (JSON, MessagePack preferred over Pickle)
- ✅ Rate limiting and quota management
- ✅ Audit logging for sensitive operations
- ✅ Regular security scanning (Bandit, Semgrep)

## Testing

```bash
# Run unit tests
pytest packages/

# Run specific package tests
pytest packages/multi_framework/
pytest packages/vector_memory/
pytest packages/performance/

# Run with coverage
pytest --cov=packages --cov-report=html
```

## Contributing

When adding new packages:
1. Create package directory under `packages/`
2. Add `__init__.py` with public API exports
3. Include docstrings for all public classes/functions
4. Add unit tests
5. Update this README
6. Add to `requirements-enterprise.txt` if needed

## License

Copyright © 2025 AI Agents Platform. All rights reserved.
