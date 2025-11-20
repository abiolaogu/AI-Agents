# Complete API Integration Guide

## Overview

This guide provides comprehensive documentation for integrating with the AI Agents Platform API. The platform exposes REST, GraphQL, and WebSocket APIs for maximum flexibility.

## Base URLs

```
Production:  https://api.aiagents.platform/v1
Staging:     https://api-staging.aiagents.platform/v1
Development: http://localhost:8000/v1
```

## Authentication

### API Keys

```bash
# Get API key from dashboard
curl -X POST https://api.aiagents.platform/v1/auth/api-keys \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["agents:read", "agents:execute", "workflows:manage"]
  }'
```

### JWT Authentication

```python
import requests

# Login
response = requests.post(
    "https://api.aiagents.platform/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "your_password"
    }
)

token = response.json()["access_token"]

# Use token in subsequent requests
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

## Core Endpoints

### List Agents

```bash
GET /v1/agents
```

**Parameters:**
- `category` (optional): Filter by category
- `capability` (optional): Filter by capability
- `page` (default: 1): Page number
- `limit` (default: 50): Results per page

**Example:**
```python
import requests

response = requests.get(
    "https://api.aiagents.platform/v1/agents",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "category": "sales_marketing",
        "limit": 100
    }
)

agents = response.json()["data"]
for agent in agents:
    print(f"{agent['agent_id']}: {agent['name']}")
```

**Response:**
```json
{
  "data": [
    {
      "agent_id": "sales_marketing_lead_qualifier",
      "name": "Lead Qualification Agent",
      "description": "Automatically qualifies leads based on criteria",
      "category": "sales_marketing",
      "capabilities": ["text_analysis", "decision_support"],
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1503,
    "pages": 31
  }
}
```

### Execute Agent

```bash
POST /v1/agents/{agent_id}/execute
```

**Example:**
```python
response = requests.post(
    "https://api.aiagents.platform/v1/agents/sales_marketing_lead_qualifier/execute",
    headers=headers,
    json={
        "task_description": "Qualify this lead: John Doe, CEO of TechCorp, 500 employees, interested in enterprise plan",
        "context": {
            "company_size": "enterprise",
            "budget": "high",
            "timeline": "Q1 2025"
        },
        "parameters": {
            "scoring_model": "advanced",
            "threshold": 0.75
        }
    }
)

result = response.json()
print(f"Lead Score: {result['result']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Execution Time: {result['metadata']['execution_time_ms']}ms")
```

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "agent_id": "sales_marketing_lead_qualifier",
  "result": "QUALIFIED - Score: 92/100. High-value enterprise lead with strong buying intent.",
  "confidence_score": 0.95,
  "metadata": {
    "execution_time_ms": 1250,
    "tokens_used": 450,
    "model": "claude-3-5-sonnet-20241022",
    "cached": false
  },
  "created_at": "2025-01-20T10:30:00Z"
}
```

### Create Workflow

```bash
POST /v1/workflows
```

**Example:**
```python
workflow = {
    "name": "Lead to Customer Workflow",
    "description": "End-to-end lead processing",
    "steps": [
        {
            "id": "qualify",
            "agent_id": "sales_marketing_lead_qualifier",
            "inputs": {"task_description": "{{lead_data}}"}
        },
        {
            "id": "enrich",
            "agent_id": "sales_marketing_lead_enrichment",
            "inputs": {"task_description": "{{qualify.result}}"},
            "condition": "{{qualify.confidence_score}} > 0.7"
        },
        {
            "id": "notify",
            "agent_id": "sales_marketing_sales_notification",
            "inputs": {"task_description": "{{enrich.result}}"}
        }
    ],
    "triggers": {
        "webhook": true,
        "schedule": "0 9 * * *"
    }
}

response = requests.post(
    "https://api.aiagents.platform/v1/workflows",
    headers=headers,
    json=workflow
)

workflow_id = response.json()["workflow_id"]
```

### Execute Workflow

```bash
POST /v1/workflows/{workflow_id}/execute
```

**Example:**
```python
response = requests.post(
    f"https://api.aiagents.platform/v1/workflows/{workflow_id}/execute",
    headers=headers,
    json={
        "inputs": {
            "lead_data": {
                "name": "Jane Smith",
                "company": "InnovateCo",
                "email": "jane@innovateco.com",
                "phone": "+1-555-0123"
            }
        }
    }
)

execution_id = response.json()["execution_id"]
```

## Advanced Features

### Team Collaboration

```python
# Create agent team
team = {
    "team_name": "Quarterly Report Team",
    "agents": [
        {"agent_id": "finance_legal_financial_analyst"},
        {"agent_id": "business_ops_data_analyst"},
        {"agent_id": "sales_marketing_performance_analyst"}
    ],
    "execution_strategy": "sequential",
    "collaboration_config": {
        "shared_context": true,
        "inter_agent_communication": true
    }
}

response = requests.post(
    "https://api.aiagents.platform/v1/teams",
    headers=headers,
    json=team
)

team_id = response.json()["team_id"]

# Execute team
response = requests.post(
    f"https://api.aiagents.platform/v1/teams/{team_id}/execute",
    headers=headers,
    json={
        "task_description": "Generate Q4 2024 quarterly report with financial, operational, and sales insights",
        "context": {
            "quarter": "Q4 2024",
            "format": "executive_summary"
        }
    }
)
```

### Streaming Responses

```python
import requests

# Use streaming for real-time results
response = requests.post(
    "https://api.aiagents.platform/v1/agents/content_writer/execute",
    headers=headers,
    json={
        "task_description": "Write a 1000-word blog post about AI in healthcare",
        "streaming": true
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        print(data["chunk"], end="", flush=True)
```

### Webhooks

```python
# Register webhook
webhook = {
    "url": "https://your-app.com/webhooks/agent-completed",
    "events": ["agent.execution.completed", "agent.execution.failed"],
    "secret": "your_webhook_secret"
}

response = requests.post(
    "https://api.aiagents.platform/v1/webhooks",
    headers=headers,
    json=webhook
)

# Webhook payload example
{
    "event": "agent.execution.completed",
    "execution_id": "exec_abc123",
    "agent_id": "sales_marketing_lead_qualifier",
    "result": "...",
    "timestamp": "2025-01-20T10:30:00Z"
}
```

## SDK Examples

### Python SDK

```python
from aiagents import Client

# Initialize
client = Client(api_key="your_api_key")

# Execute agent
result = await client.agents.execute(
    "sales_marketing_lead_qualifier",
    task="Qualify lead: John Doe, TechCorp CEO",
    context={"budget": "high"}
)

print(result.result)
print(f"Confidence: {result.confidence_score}")

# Create workflow
workflow = client.workflows.create(
    name="Lead Processing",
    steps=[
        {"agent_id": "qualify", "inputs": {"task": "{{input}}"}},
        {"agent_id": "enrich", "inputs": {"task": "{{qualify.result}}"}}
    ]
)

# Execute workflow
execution = await workflow.execute(input="Lead data here")
```

### JavaScript/TypeScript SDK

```typescript
import { AIAgentsClient } from '@aiagents/sdk';

const client = new AIAgentsClient({
  apiKey: process.env.AIAGENTS_API_KEY
});

// Execute agent
const result = await client.agents.execute({
  agentId: 'sales_marketing_lead_qualifier',
  task: 'Qualify lead: John Doe',
  context: { budget: 'high' }
});

console.log(result.result);

// Stream response
const stream = await client.agents.executeStream({
  agentId: 'content_writer',
  task: 'Write blog post about AI'
});

for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

### Java SDK

```java
import com.aiagents.Client;
import com.aiagents.models.*;

// Initialize
Client client = new Client("your_api_key");

// Execute agent
AgentExecution result = client.agents().execute(
    "sales_marketing_lead_qualifier",
    new ExecutionRequest()
        .task("Qualify lead: John Doe")
        .context(Map.of("budget", "high"))
);

System.out.println(result.getResult());
System.out.println("Confidence: " + result.getConfidenceScore());
```

## Rate Limits

| Tier | Requests/Hour | Concurrent | Burst |
|------|---------------|------------|-------|
| Free | 100 | 1 | 10 |
| Starter | 1,000 | 5 | 50 |
| Professional | 10,000 | 25 | 100 |
| Business | 100,000 | 100 | 500 |
| Enterprise | Unlimited | Unlimited | Unlimited |

## Error Handling

```python
from aiagents import Client, exceptions

client = Client(api_key="your_api_key")

try:
    result = await client.agents.execute("invalid_agent", task="test")
except exceptions.AgentNotFoundError as e:
    print(f"Agent not found: {e}")
except exceptions.RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except exceptions.AuthenticationError as e:
    print(f"Authentication failed: {e}")
except exceptions.ValidationError as e:
    print(f"Invalid input: {e.details}")
except exceptions.APIError as e:
    print(f"API error: {e.message}")
```

## Best Practices

### 1. Use Semantic Caching

```python
# Enable semantic caching to reduce costs
result = await client.agents.execute(
    "content_writer",
    task="Write about AI in healthcare",
    cache_config={
        "enabled": true,
        "ttl_seconds": 3600,
        "similarity_threshold": 0.95
    }
)
```

### 2. Implement Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def execute_with_retry(agent_id, task):
    return await client.agents.execute(agent_id, task=task)
```

### 3. Handle Webhooks Securely

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)

# In your webhook handler
@app.post("/webhooks/agent-completed")
async def handle_webhook(request):
    signature = request.headers.get("X-Signature")
    payload = await request.body()

    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook
    data = json.loads(payload)
    # ...
```

### 4. Monitor Performance

```python
import time

# Track execution time
start = time.time()
result = await client.agents.execute("agent_id", task="...")
duration = time.time() - start

# Log metrics
logger.info(f"Agent execution completed in {duration:.2f}s")
logger.info(f"Tokens used: {result.metadata['tokens_used']}")
logger.info(f"Confidence: {result.confidence_score}")
```

---

*Last Updated: 2025-01-20*
*Version: 2.0.0*
