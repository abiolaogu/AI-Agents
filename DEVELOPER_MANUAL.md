# Developer Manual
## Multi-Framework Super-Agent Platform - API & Integration Guide

**Version:** 1.0  
**Audience:** Developers, DevOps, System Integrators  
**Last Updated:** November 2025

---

## Table of Contents

1. [API Overview & Authentication](#api-overview)
2. [REST API Reference](#rest-api)
3. [WebSocket Real-Time Connection](#websocket)
4. [Building Custom Tools](#custom-tools)
5. [Database Integration](#database-integration)
6. [Webhook Configuration](#webhooks)
7. [CI/CD Integration](#cicd)
8. [Performance Optimization](#performance)
9. [Error Handling & Retry Logic](#error-handling)
10. [Code Examples & Libraries](#code-examples)

---

## API Overview & Authentication {#api-overview}

### Getting Your API Key

1. Log into platform
2. Go to **Settings** > **API** > **API Keys**
3. Click **"Generate New Key"**
4. Choose permissions and expiration
5. Copy key immediately (won't be shown again)

### API Endpoints

**Base URL**: `https://api.superagent.com/v1`

**Available Endpoints**:
- `POST /tasks` - Create and execute task
- `GET /tasks/{id}` - Get task result
- `GET /tasks` - List tasks (paginated)
- `POST /workflows` - Create workflow
- `GET /workflows/{id}` - Get workflow
- `POST /knowledge-base/upload` - Upload document
- `POST /webhooks` - Register webhook
- (See detailed reference below)

### Authentication Methods

**Bearer Token (Recommended)**:
```
Authorization: Bearer YOUR_API_KEY
```

**API Key Header**:
```
X-API-Key: YOUR_API_KEY
```

**Rate Limiting**:
- Default: 100 requests per minute per API key
- Check headers for current limits:
  - `X-RateLimit-Limit`: Max requests
  - `X-RateLimit-Remaining`: Requests left
  - `X-RateLimit-Reset`: Time until reset

### CORS Configuration

For browser-based clients, CORS headers included:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

---

## REST API Reference {#rest-api}

### Create Task

**Endpoint**: `POST /tasks`

**Request**:
```json
{
  "query": "Summarize our Q3 performance report",
  "framework": "auto",  // or "langgraph", "crewyai", "autogen"
  "context": {
    "documents": ["doc_id_1", "doc_id_2"],
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "webhook_url": "https://your-api.com/webhooks/super-agent",
  "metadata": {
    "user_id": "user_123",
    "project_id": "proj_456"
  }
}
```

**Response** (immediate):
```json
{
  "task_id": "task_abc123def456",
  "status": "queued",
  "created_at": "2025-11-14T10:30:00Z",
  "estimated_completion": 15  // seconds
}
```

**Response** (when polled later):
```json
{
  "task_id": "task_abc123def456",
  "status": "completed",
  "result": {
    "content": "Q3 showed 25% revenue growth...",
    "confidence": 0.94,
    "framework_used": "crewyai"
  },
  "execution": {
    "duration": 12.5,
    "tokens_used": 1450,
    "cost": 0.025
  },
  "metadata": {
    "user_id": "user_123"
  }
}
```

**Status Values**:
- `queued`: Waiting to start
- `executing`: In progress
- `completed`: Finished successfully
- `failed`: Error occurred
- `cancelled`: Cancelled by user

### Get Task Result

**Endpoint**: `GET /tasks/{task_id}`

**Query Parameters**:
- `include_trace`: true/false (include execution trace)
- `format`: json/xml (response format)

**Response**:
```json
{
  "task_id": "task_abc123def456",
  "status": "completed",
  "result": { ... },
  "trace": [  // if include_trace=true
    {
      "step": 1,
      "action": "Route decision",
      "result": "Selected CrewAI",
      "duration_ms": 150
    },
    {
      "step": 2,
      "action": "Researcher agent",
      "result": "Found relevant documents",
      "duration_ms": 5000
    }
    // ... more steps
  ]
}
```

### List Tasks

**Endpoint**: `GET /tasks`

**Query Parameters**:
- `limit`: 10-100 (default: 20)
- `offset`: 0-N (pagination)
- `status`: queued/executing/completed/failed
- `framework`: langgraph/crewyai/autogen
- `created_after`: ISO 8601 date
- `created_before`: ISO 8601 date

**Response**:
```json
{
  "tasks": [
    { "task_id": "...", "status": "completed", ... },
    { "task_id": "...", "status": "completed", ... }
  ],
  "total": 245,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Create Workflow

**Endpoint**: `POST /workflows`

**Request**:
```json
{
  "name": "Market Analysis Workflow",
  "agents": [
    {
      "id": "researcher",
      "type": "researcher",
      "system_prompt": "You are a research expert...",
      "tools": ["search", "fetch_url", "read_pdf"],
      "instructions": "Find information about top 5 AI companies"
    },
    {
      "id": "writer",
      "type": "writer",
      "depends_on": ["researcher"],
      "instructions": "Create a professional report from research"
    }
  ],
  "timeout": 300  // seconds
}
```

**Response**:
```json
{
  "workflow_id": "wf_xyz789",
  "name": "Market Analysis Workflow",
  "status": "created",
  "agents": [ ... ],
  "created_at": "2025-11-14T10:30:00Z"
}
```

### Execute Workflow

**Endpoint**: `POST /workflows/{workflow_id}/execute`

**Request**:
```json
{
  "input": {
    "query": "Analyze AI market",
    "companies": ["OpenAI", "Anthropic", "Google", "Meta", "Tesla"]
  },
  "webhook_url": "https://your-api.com/webhooks/result"
}
```

**Response**:
```json
{
  "execution_id": "exec_456xyz",
  "workflow_id": "wf_xyz789",
  "status": "executing",
  "created_at": "2025-11-14T10:35:00Z"
}
```

### Upload Document

**Endpoint**: `POST /knowledge-base/upload`

**Request** (multipart/form-data):
```
File: research_paper.pdf
Collection: ai_research
Metadata: {"source": "arxiv", "year": 2025}
```

**Response**:
```json
{
  "document_id": "doc_abc123",
  "filename": "research_paper.pdf",
  "collection": "ai_research",
  "chunks": 45,
  "embeddings_created": 45,
  "status": "indexed",
  "created_at": "2025-11-14T10:30:00Z"
}
```

### Search Knowledge Base

**Endpoint**: `POST /knowledge-base/search`

**Request**:
```json
{
  "query": "How to implement OAuth authentication?",
  "collection": "engineering_docs",
  "limit": 5,
  "min_score": 0.6
}
```

**Response**:
```json
{
  "results": [
    {
      "document_id": "doc_001",
      "chunk_id": "chunk_042",
      "score": 0.92,
      "content": "OAuth 2.0 is an authorization protocol...",
      "source": "oauth_guide.pdf",
      "page": 3
    },
    // ... more results
  ],
  "total": 3,
  "search_duration_ms": 156
}
```

---

## WebSocket Real-Time Connection {#websocket}

### Connecting

```javascript
// JavaScript example
const ws = new WebSocket('wss://api.superagent.com/ws');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'YOUR_API_KEY'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

### Subscribing to Events

```javascript
// Subscribe to task updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'task:task_abc123def456'
}));

// Subscribe to all your tasks
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'user:all'
}));
```

### Event Messages

Task progress update:
```json
{
  "type": "task_update",
  "task_id": "task_abc123def456",
  "status": "executing",
  "progress": 0.45,
  "current_step": "Researcher agent analyzing documents",
  "timestamp": "2025-11-14T10:30:15Z"
}
```

Task completion:
```json
{
  "type": "task_complete",
  "task_id": "task_abc123def456",
  "status": "completed",
  "result": { ... },
  "timestamp": "2025-11-14T10:30:45Z"
}
```

---

## Building Custom Tools {#custom-tools}

### Tool Definition

Custom tools extend agent capabilities. Define in your agent:

```python
from typing import Any, Dict
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    """Input schema for the tool"""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=5, description="Max results to return")

class CustomSearchTool:
    """Custom search tool for your agents"""
    
    name = "custom_search"
    description = "Search your internal knowledge base"
    input_schema = ToolInput
    
    async def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute the tool"""
        # Your implementation
        results = await self.search_internal_db(query, max_results)
        return {
            "results": results,
            "count": len(results),
            "query": query
        }
```

### Registering Tool with Agent

```python
from crewyai import Agent, Task, Crew

# Create custom tool
search_tool = CustomSearchTool()

# Create agent with tool
researcher = Agent(
    role="Research Specialist",
    goal="Find relevant information",
    tools=[search_tool],  # Add your custom tool
    verbose=True
)

# Use in task
research_task = Task(
    description="Search for AI trends",
    agent=researcher,
    expected_output="Summary of AI trends"
)
```

### Tool Best Practices

**Error Handling**:
```python
async def execute(self, query: str) -> Dict[str, Any]:
    try:
        results = await self.search_internal_db(query)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback": "Consider using general search instead"
        }
```

**Rate Limiting**:
```python
from datetime import datetime, timedelta

class RateLimitedTool:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_timestamps = []
    
    async def execute(self, **kwargs):
        # Check rate limit
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        self.call_timestamps = [
            ts for ts in self.call_timestamps 
            if ts > minute_ago
        ]
        
        if len(self.call_timestamps) >= self.calls_per_minute:
            return {"error": "Rate limit exceeded"}
        
        self.call_timestamps.append(now)
        # Execute tool...
```

---

## Database Integration {#database-integration}

### Connection Strings

**PostgreSQL** (Control Plane):
```
postgresql://user:password@host:5432/super_agent_db
```

**ScyllaDB** (Events & State):
```
cassandra://user:password@host:9042/super_agent
```

**Milvus** (Vector Memory):
```
http://host:19530
```

**DragonflyDB** (Cache):
```
redis://host:6379
```

### Query Examples

**PostgreSQL**:
```python
import asyncpg

async def get_user_quota(user_id: str):
    conn = await asyncpg.connect('postgresql://...')
    try:
        result = await conn.fetchval(
            'SELECT api_quota FROM users WHERE id = $1',
            user_id
        )
        return result
    finally:
        await conn.close()
```

**Milvus**:
```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")

# Search similar documents
results = client.search(
    collection_name="documents",
    data=[[0.1, 0.2, 0.3]],  # Your embedding
    limit=5,
    output_fields=["text", "source"]
)
```

**DragonflyDB**:
```python
import redis

cache = redis.Redis(host='localhost', port=6379)

# Cache tool results
key = f"tool:search:{query}"
cached = cache.get(key)
if cached:
    return json.loads(cached)

# Store result
result = await tool.execute(query)
cache.setex(key, 3600, json.dumps(result))  # 1 hour TTL
return result
```

---

## Webhook Configuration {#webhooks}

### Webhook URL Requirements

Your webhook endpoint must:
- Accept POST requests
- Return HTTP 200 within 5 seconds
- Handle retry attempts (with backoff)
- Verify request signature

### Webhook Payload

When event occurs, platform sends:

```json
{
  "event_type": "task_completed",
  "timestamp": "2025-11-14T10:30:45Z",
  "data": {
    "task_id": "task_abc123def456",
    "status": "completed",
    "result": { ... }
  },
  "signature": "sha256=abc123..."  // HMAC-SHA256
}
```

### Signature Verification

```python
import hmac
import hashlib
from flask import request

def verify_webhook(request):
    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature', '')
    
    # Get raw body
    body = request.get_data()
    
    # Compute expected signature
    secret = 'YOUR_WEBHOOK_SECRET'
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare
    if not hmac.compare_digest(signature, expected):
        return False
    return True

@app.route('/webhooks/super-agent', methods=['POST'])
def handle_webhook():
    if not verify_webhook(request):
        return {'error': 'Invalid signature'}, 401
    
    data = request.json
    # Process event...
    
    return {'status': 'ok'}, 200
```

### Webhook Retry Logic

Platform retries failed webhooks:
- 1st retry: 5 seconds after failure
- 2nd retry: 5 minutes after failure
- 3rd retry: 1 hour after failure
- 4th retry: 24 hours after failure

After 4 failures, webhook disabled.

---

## CI/CD Integration {#cicd}

### Jenkins Integration

```groovy
pipeline {
    agent any
    
    stages {
        stage('Deploy') {
            steps {
                script {
                    // Deploy to platform
                    sh '''
                        curl -X POST https://api.superagent.com/v1/deployments \
                        -H "Authorization: Bearer ${API_KEY}" \
                        -H "Content-Type: application/json" \
                        -d '{
                            "service": "my-agent",
                            "version": "${BUILD_NUMBER}",
                            "image": "myrepo/myservice:${BUILD_NUMBER}",
                            "replicas": 3
                        }'
                    '''
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    // Run integration tests
                    sh '''
                        python -m pytest tests/ \
                            --superagent-api="${API_ENDPOINT}" \
                            --superagent-key="${API_KEY}"
                    '''
                }
            }
        }
    }
}
```

### GitHub Actions Integration

```yaml
name: Deploy to Super-Agent Platform

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy Agents
        run: |
          curl -X POST https://api.superagent.com/v1/agents/deploy \
            -H "Authorization: Bearer ${{ secrets.SUPER_AGENT_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d @deployment.json
      
      - name: Run Tests
        run: |
          pytest tests/integration/ \
            --api-key=${{ secrets.SUPER_AGENT_API_KEY }} \
            --api-endpoint=https://api.superagent.com/v1
```

---

## Performance Optimization {#performance}

### Caching Strategy

```python
from functools import wraps
from datetime import timedelta
import redis

cache = redis.Redis(host='localhost')

def cache_result(ttl_seconds=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = cache.get(key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.setex(key, ttl_seconds, json.dumps(result))
            return result
        
        return wrapper
    return decorator

# Usage
@cache_result(ttl_seconds=3600)
async def expensive_query(query: str):
    return await api.execute_task(query)
```

### Batch Processing

```python
async def batch_process_tasks(tasks: List[Dict], batch_size: int = 10):
    """Process multiple tasks efficiently"""
    results = []
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        
        # Process batch in parallel
        batch_results = await asyncio.gather(*[
            api.execute_task(task)
            for task in batch
        ])
        
        results.extend(batch_results)
    
    return results
```

### Connection Pooling

```python
import asyncpg
from asyncpg import Pool

class DatabasePool:
    def __init__(self):
        self.pool: Optional[Pool] = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            'postgresql://user:password@host/db',
            min_size=10,
            max_size=50,  # Adjust based on load
            max_cached_statement_lifetime=300,
            max_cacheable_statement_size=15000
        )
    
    async def query(self, sql: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(sql, *args)
```

---

## Error Handling & Retry Logic {#error-handling}

### Exponential Backoff

```python
import asyncio
import random
from typing import Coroutine

async def retry_with_backoff(
    coroutine: Coroutine,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Retry with exponential backoff and jitter"""
    
    for attempt in range(max_retries):
        try:
            return await coroutine
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Calculate delay with jitter
            delay = min(
                base_delay * (2 ** attempt) + random.uniform(0, 1),
                max_delay
            )
            
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s")
            await asyncio.sleep(delay)
```

### Error Classification

```python
class APIError(Exception):
    """Base error class"""
    pass

class RetryableError(APIError):
    """Can be retried"""
    pass

class NonRetryableError(APIError):
    """Should not be retried"""
    pass

def should_retry(error: Exception) -> bool:
    """Determine if error is retryable"""
    if isinstance(error, RetryableError):
        return True
    
    # HTTP status codes
    if hasattr(error, 'status_code'):
        # Retry on 429, 5xx
        return error.status_code in [429, 500, 502, 503, 504]
    
    return False
```

---

## Code Examples & Libraries {#code-examples}

### Python SDK

```python
from superagent import SuperAgentClient

client = SuperAgentClient(api_key="YOUR_API_KEY")

# Create and execute task
task = client.tasks.create(
    query="Summarize recent AI breakthroughs",
    framework="auto"
)

# Poll for result
result = client.tasks.wait_for_completion(task.id, timeout=60)
print(f"Result: {result.content}")
print(f"Cost: ${result.cost}")

# Search knowledge base
docs = client.knowledge_base.search(
    query="OAuth implementation",
    collection="tech_docs",
    limit=5
)

# Create workflow
workflow = client.workflows.create(
    name="Analysis Pipeline",
    agents=[...]
)

# Execute workflow
execution = client.workflows.execute(workflow.id, input={"query": "..."})
```

### JavaScript/Node.js SDK

```javascript
import { SuperAgentClient } from '@superagent/client';

const client = new SuperAgentClient({
  apiKey: process.env.SUPER_AGENT_API_KEY
});

// Execute task
const task = await client.tasks.create({
  query: 'Generate Python script for data processing',
  framework: 'autogen'  // Code generation
});

// Real-time updates via WebSocket
task.on('progress', (progress) => {
  console.log(`Progress: ${progress}%`);
});

task.on('complete', (result) => {
  console.log('Task completed!');
  console.log(result.content);
});

// Wait for completion
const result = await task.wait();
```

### cURL Examples

```bash
# Create task
curl -X POST https://api.superagent.com/v1/tasks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "framework": "langgraph"
  }'

# Get task result
curl -X GET https://api.superagent.com/v1/tasks/task_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search knowledge base
curl -X POST https://api.superagent.com/v1/knowledge-base/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database optimization",
    "limit": 5
  }'
```

---

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from superagent import SuperAgentClient

@pytest.mark.asyncio
async def test_create_task():
    client = SuperAgentClient(api_key="test_key")
    
    with patch.object(client.tasks, '_execute') as mock_execute:
        mock_execute.return_value = {"task_id": "test_123"}
        
        result = await client.tasks.create(query="Test query")
        
        assert result.id == "test_123"
        mock_execute.assert_called_once()
```

### Integration Tests

```python
import pytest
from superagent import SuperAgentClient

@pytest.fixture
def client():
    return SuperAgentClient(
        api_key=os.environ['TEST_API_KEY'],
        base_url='https://test.superagent.com'
    )

@pytest.mark.integration
async def test_full_workflow(client):
    # Create task
    task = await client.tasks.create(
        query="Test query",
        framework="langgraph"
    )
    
    # Wait for completion
    result = await task.wait(timeout=30)
    
    # Verify result
    assert result.status == "completed"
    assert result.content is not None
    assert result.cost > 0
```

---

## Support & Resources

**Documentation**: https://docs.superagent.com  
**API Reference**: https://api.superagent.com/docs  
**GitHub**: https://github.com/superagent-ai  
**Community**: Slack workspace (invite link in dashboard)  
**Support Email**: support@superagent.com

---

**Last Updated**: November 2025  
**API Version**: v1  
**SDK Latest**: 1.0.0
