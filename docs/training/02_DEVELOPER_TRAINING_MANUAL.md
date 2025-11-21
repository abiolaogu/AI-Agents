# AI Agents Platform - Developer Training Manual

## Course Information
- **Target Audience**: Software Developers, Integration Engineers
- **Duration**: 3-4 hours
- **Prerequisites**: REST APIs, Python/JavaScript basics, API authentication
- **Certification**: Available upon completion

---

## Module 1: Getting Started (30 minutes)

### 1.1 What is the AI Agents Platform?

The AI Agents Platform provides 1,500 specialized AI agents as microservices. Each agent is an expert in a specific business domain and can be accessed via REST API.

**Key Benefits:**
- No AI/ML expertise required
- Production-ready agents
- Consistent API across all agents
- Automatic scaling
- Built-in monitoring

### 1.2 Agent Categories

**Business Functions (750+ agents):**
- Business Planning & Strategy
- Financial Analysis
- Marketing & Content
- Sales & CRM
- Customer Support
- HR & Recruiting

**Technical Functions (400+ agents):**
- Code Generation & Review
- Data Analysis
- DevOps Automation
- Security & Compliance

**Industry Specific (350+ agents):**
- Healthcare
- Real Estate
- Finance & Banking
- Retail & E-commerce
- Manufacturing

### 1.3 Quick Start Example

**Your First API Call:**
```bash
# Using curl
curl -X POST https://api.agents.your-domain.com/api/v1/agents/business-plan-agent-009/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a business plan for a SaaS startup in the education sector",
    "context": {
      "industry": "education",
      "target_market": "K-12 teachers",
      "budget": 100000
    }
  }'
```

**Response:**
```json
{
  "result": "# Executive Summary\n\nBusiness Name: EduTech Solutions...",
  "metadata": {
    "agent_id": "business-plan-agent-009",
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 2847
  },
  "processing_time_ms": 4235.67
}
```

---

## Module 2: Authentication (30 minutes)

### 2.1 Getting API Credentials

**Option 1: JWT Tokens (Interactive Users)**
```bash
# Login to get token
curl -X POST https://api.agents.your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Option 2: API Keys (Programmatic Access)**
```bash
# Contact your admin to generate an API key
# API keys don't expire and are ideal for server-to-server
```

### 2.2 Using Authentication

**With JWT Token:**
```python
import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.agents.your-domain.com/api/v1/agents/marketing-agent-001/execute",
    headers=headers,
    json={"task_description": "Create a marketing campaign"}
)
```

**With API Key:**
```python
headers = {
    "Authorization": "Bearer sk-your-api-key-here",
    "Content-Type": "application/json"
}
```

### 2.3 Rate Limits

**Default Limits:**
- 100 requests per minute per user
- 10,000 requests per day per user
- Rate limit headers included in responses

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642598400
```

**Handling Rate Limits:**
```python
def call_agent_with_retry(agent_id, task, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=task)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:  # Rate limit
            wait_time = int(response.headers.get('Retry-After', 60))
            time.sleep(wait_time)
        else:
            raise Exception(f"Request failed: {response.status_code}")

    raise Exception("Max retries exceeded")
```

---

## Module 3: API Reference (60 minutes)

### 3.1 Core Endpoints

#### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "agent_id": "business-plan-agent-009",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Execute Task
```
POST /api/v1/execute
```

**Request Body:**
```json
{
  "task_description": "string (required)",
  "context": {
    "key": "value"  // Optional context
  }
}
```

**Response:**
```json
{
  "result": "string - The agent's response",
  "metadata": {
    "agent_id": "string",
    "model": "string",
    "tokens_used": 0
  },
  "processing_time_ms": 0.0
}
```

#### Get Agent Info
```
GET /
```

**Response:**
```json
{
  "agent_id": "business-plan-agent-009",
  "name": "Business Plan Agent",
  "version": "1.0.0",
  "status": "operational",
  "category": "business_ops",
  "capabilities": ["business_planning", "strategy", "analysis"]
}
```

### 3.2 Agent Discovery

**List All Agents:**
```
GET /api/v1/agents
```

**Response:**
```json
{
  "total": 1500,
  "agents": [
    {
      "agent_id": "business-plan-agent-009",
      "name": "Business Plan Agent",
      "category": "business_ops",
      "description": "Creates comprehensive business plans"
    },
    ...
  ]
}
```

**Search Agents:**
```
GET /api/v1/agents?category=marketing&search=content
```

**Filter by Category:**
```
GET /api/v1/agents?category=healthcare
```

### 3.3 Error Handling

**Standard Error Response:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Task description is required",
    "details": {
      "field": "task_description",
      "issue": "missing_required_field"
    }
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Malformed request |
| UNAUTHORIZED | 401 | Invalid credentials |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Agent not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Agent temporarily unavailable |

---

## Module 4: SDK Usage (45 minutes)

### 4.1 Python SDK

**Installation:**
```bash
pip install ai-agents-sdk
```

**Basic Usage:**
```python
from ai_agents import AgentsClient

# Initialize client
client = AgentsClient(
    api_key="your-api-key",
    base_url="https://api.agents.your-domain.com"
)

# Execute task
result = client.execute(
    agent_id="business-plan-agent-009",
    task="Create a business plan for a coffee shop",
    context={
        "location": "San Francisco",
        "budget": 50000
    }
)

print(result.text)
print(f"Tokens used: {result.metadata.tokens_used}")
print(f"Processing time: {result.processing_time_ms}ms")
```

**Async Support:**
```python
import asyncio
from ai_agents import AsyncAgentsClient

async def main():
    client = AsyncAgentsClient(api_key="your-api-key")

    # Execute multiple agents concurrently
    tasks = [
        client.execute("marketing-agent-001", "Create social media campaign"),
        client.execute("content-agent-002", "Write blog post about AI"),
        client.execute("seo-agent-003", "Optimize for keyword 'AI agents'")
    ]

    results = await asyncio.gather(*tasks)
    for result in results:
        print(result.text)

asyncio.run(main())
```

**Error Handling:**
```python
from ai_agents import AgentsClient, AgentError, RateLimitError

client = AgentsClient(api_key="your-api-key")

try:
    result = client.execute("agent-id", "task")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except AgentError as e:
    print(f"Agent error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 4.2 JavaScript SDK

**Installation:**
```bash
npm install @ai-agents/sdk
```

**Basic Usage:**
```javascript
const { AgentsClient } = require('@ai-agents/sdk');

const client = new AgentsClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.agents.your-domain.com'
});

// Execute task
async function createBusinessPlan() {
  const result = await client.execute({
    agentId: 'business-plan-agent-009',
    task: 'Create a business plan for a SaaS startup',
    context: {
      industry: 'technology',
      targetMarket: 'SMBs'
    }
  });

  console.log(result.text);
  console.log(`Tokens: ${result.metadata.tokensUsed}`);
}

createBusinessPlan();
```

**TypeScript:**
```typescript
import { AgentsClient, ExecuteResponse } from '@ai-agents/sdk';

const client = new AgentsClient({
  apiKey: process.env.AI_AGENTS_API_KEY!
});

interface BusinessPlanContext {
  industry: string;
  budget: number;
}

async function execute(task: string, context: BusinessPlanContext): Promise<ExecuteResponse> {
  return await client.execute({
    agentId: 'business-plan-agent-009',
    task,
    context
  });
}
```

### 4.3 Other Languages

**cURL (Shell):**
```bash
#!/bin/bash

API_KEY="your-api-key"
AGENT_ID="business-plan-agent-009"
BASE_URL="https://api.agents.your-domain.com"

curl -X POST "${BASE_URL}/api/v1/agents/${AGENT_ID}/execute" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "task_description": "Create a business plan",
  "context": {
    "industry": "retail"
  }
}
EOF
```

**Go:**
```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type ExecuteRequest struct {
    TaskDescription string                 `json:"task_description"`
    Context         map[string]interface{} `json:"context"`
}

func executeAgent(agentID, task string) (*http.Response, error) {
    url := "https://api.agents.your-domain.com/api/v1/agents/" + agentID + "/execute"

    reqBody := ExecuteRequest{
        TaskDescription: task,
        Context:         map[string]interface{}{"key": "value"},
    }

    jsonData, _ := json.Marshal(reqBody)

    req, _ := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
    req.Header.Set("Authorization", "Bearer your-api-key")
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{}
    return client.Do(req)
}
```

---

## Module 5: Best Practices (45 minutes)

### 5.1 Task Design

**Good Task Descriptions:**
```python
# ✅ GOOD - Specific and clear
task = "Create a 12-month marketing plan for a B2B SaaS company targeting enterprise clients in the healthcare sector. Include budget allocation, channel strategy, and KPIs."

# ✅ GOOD - Provides context
task = "Analyze this customer support ticket and suggest a resolution"
context = {
    "ticket": "Customer cannot login after password reset",
    "customer_tier": "enterprise",
    "previous_tickets": 2
}

# ❌ BAD - Too vague
task = "Help with marketing"

# ❌ BAD - Too complex for single request
task = "Create full business strategy, marketing plan, financial projections, and website copy"
```

**Breaking Down Complex Tasks:**
```python
# Instead of one complex request, use multiple agents:

# Step 1: Research
research = client.execute(
    "market-research-agent",
    "Analyze the SaaS market in healthcare"
)

# Step 2: Strategy (using research results)
strategy = client.execute(
    "strategy-agent",
    f"Create strategy based on: {research.text}"
)

# Step 3: Implementation plan
plan = client.execute(
    "planning-agent",
    f"Create implementation plan for: {strategy.text}"
)
```

### 5.2 Context Management

**Providing Effective Context:**
```python
# ✅ GOOD - Structured context
context = {
    "company": {
        "name": "TechCorp",
        "industry": "SaaS",
        "size": "50 employees",
        "revenue": "$2M ARR"
    },
    "goal": "increase customer retention",
    "constraints": {
        "budget": "$50K",
        "timeline": "Q1 2025"
    },
    "preferences": {
        "tone": "professional",
        "format": "markdown"
    }
}

result = client.execute("strategy-agent", "Create retention strategy", context=context)
```

### 5.3 Performance Optimization

**Caching Results:**
```python
import hashlib
import redis

cache = redis.Redis(host='localhost', port=6379)

def execute_with_cache(agent_id, task, context, ttl=3600):
    # Create cache key
    cache_key = hashlib.md5(
        f"{agent_id}:{task}:{json.dumps(context)}".encode()
    ).hexdigest()

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Execute agent
    result = client.execute(agent_id, task, context)

    # Cache result
    cache.setex(cache_key, ttl, json.dumps(result.dict()))

    return result
```

**Parallel Execution:**
```python
import asyncio
from ai_agents import AsyncAgentsClient

async def execute_parallel(tasks):
    client = AsyncAgentsClient(api_key="your-key")

    # Execute all tasks concurrently
    results = await asyncio.gather(*[
        client.execute(task['agent_id'], task['description'])
        for task in tasks
    ])

    return results

# Usage
tasks = [
    {"agent_id": "agent-1", "description": "task 1"},
    {"agent_id": "agent-2", "description": "task 2"},
    {"agent_id": "agent-3", "description": "task 3"}
]

results = asyncio.run(execute_parallel(tasks))
```

### 5.4 Error Handling & Retries

**Robust Error Handling:**
```python
import time
from typing import Optional

def execute_with_retry(
    client,
    agent_id: str,
    task: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Optional[dict]:
    """Execute agent with exponential backoff retry"""

    for attempt in range(max_retries):
        try:
            result = client.execute(agent_id, task)
            return result

        except RateLimitError as e:
            # Respect rate limit
            wait_time = e.retry_after
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)

        except ServiceUnavailableError:
            # Exponential backoff
            wait_time = backoff_factor ** attempt
            print(f"Service unavailable. Retry in {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            # Log and fail
            print(f"Unexpected error: {e}")
            return None

    print(f"Failed after {max_retries} attempts")
    return None
```

---

## Module 6: Integration Patterns (45 minutes)

### 6.1 Web Application Integration

**Flask Example:**
```python
from flask import Flask, request, jsonify
from ai_agents import AgentsClient

app = Flask(__name__)
client = AgentsClient(api_key="your-key")

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    data = request.json
    topic = data.get('topic')

    # Call agent
    result = client.execute(
        "content-writer-agent",
        f"Write blog post about: {topic}",
        context=data.get('context', {})
    )

    return jsonify({
        "content": result.text,
        "tokens_used": result.metadata.tokens_used
    })

if __name__ == '__main__':
    app.run()
```

**Express.js Example:**
```javascript
const express = require('express');
const { AgentsClient } = require('@ai-agents/sdk');

const app = express();
const client = new AgentsClient({ apiKey: process.env.API_KEY });

app.use(express.json());

app.post('/api/generate-content', async (req, res) => {
  const { topic, context } = req.body;

  try {
    const result = await client.execute({
      agentId: 'content-writer-agent',
      task: `Write blog post about: ${topic}`,
      context
    });

    res.json({
      content: result.text,
      tokensUsed: result.metadata.tokensUsed
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000);
```

### 6.2 Workflow Orchestration

**Multi-Agent Workflow:**
```python
class ContentWorkflow:
    def __init__(self, client):
        self.client = client

    def execute(self, topic, target_audience):
        # Step 1: Research
        print("Step 1: Researching...")
        research = self.client.execute(
            "research-agent",
            f"Research {topic} for {target_audience}"
        )

        # Step 2: Outline
        print("Step 2: Creating outline...")
        outline = self.client.execute(
            "outline-agent",
            f"Create outline based on: {research.text}"
        )

        # Step 3: Write content
        print("Step 3: Writing content...")
        content = self.client.execute(
            "content-writer-agent",
            f"Write article following outline: {outline.text}"
        )

        # Step 4: SEO optimization
        print("Step 4: Optimizing for SEO...")
        optimized = self.client.execute(
            "seo-agent",
            f"Optimize this content: {content.text}"
        )

        return optimized.text

# Usage
workflow = ContentWorkflow(client)
result = workflow.execute("AI in healthcare", "healthcare professionals")
```

### 6.3 Background Jobs

**Celery Integration:**
```python
from celery import Celery
from ai_agents import AgentsClient

app = Celery('tasks', broker='redis://localhost:6379')
client = AgentsClient(api_key="your-key")

@app.task
def process_content_async(topic, user_id):
    """Process content generation in background"""

    result = client.execute(
        "content-writer-agent",
        f"Write about: {topic}"
    )

    # Save to database
    save_to_db(user_id, result.text)

    # Notify user
    send_notification(user_id, "Content ready!")

    return result.text

# Trigger from web app
task = process_content_async.delay("AI trends", user_id=123)
```

---

## Module 7: Monitoring & Debugging (30 minutes)

### 7.1 Request Logging

**Log All Requests:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_agent_request(agent_id, task, result, duration):
    logger.info({
        "agent_id": agent_id,
        "task": task[:100],  # First 100 chars
        "tokens_used": result.metadata.tokens_used,
        "duration_ms": duration,
        "success": True
    })

# Usage
start = time.time()
result = client.execute("agent-id", "task")
duration = (time.time() - start) * 1000
log_agent_request("agent-id", "task", result, duration)
```

### 7.2 Performance Monitoring

**Track Metrics:**
```python
from prometheus_client import Counter, Histogram

request_counter = Counter('agent_requests', 'Agent requests', ['agent_id', 'status'])
request_duration = Histogram('agent_duration', 'Request duration', ['agent_id'])

def execute_with_metrics(agent_id, task):
    with request_duration.labels(agent_id=agent_id).time():
        try:
            result = client.execute(agent_id, task)
            request_counter.labels(agent_id=agent_id, status='success').inc()
            return result
        except Exception as e:
            request_counter.labels(agent_id=agent_id, status='error').inc()
            raise
```

### 7.3 Debugging Tips

**Enable Debug Mode:**
```python
from ai_agents import AgentsClient

client = AgentsClient(
    api_key="your-key",
    debug=True  # Prints request/response details
)
```

**Inspect Raw Responses:**
```python
response = client.execute("agent-id", "task", raw=True)
print(response.status_code)
print(response.headers)
print(response.text)
```

---

## Module 8: Sample Projects

### Project 1: Content Generator Bot

**Requirements:**
- Generate blog posts from topics
- Save to CMS
- Schedule publishing

**Code:**
```python
from ai_agents import AgentsClient
import schedule
import time

client = AgentsClient(api_key="your-key")

def generate_and_publish(topic):
    # Generate content
    result = client.execute(
        "content-writer-agent",
        f"Write SEO-optimized blog post about: {topic}"
    )

    # Publish to CMS (pseudo-code)
    publish_to_cms(
        title=extract_title(result.text),
        content=result.text
    )

    print(f"Published: {topic}")

# Schedule weekly posts
topics = ["AI trends", "Machine Learning", "Data Science"]
for i, topic in enumerate(topics):
    schedule.every().monday.at("09:00").do(generate_and_publish, topic)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Project 2: Customer Support Assistant

**Requirements:**
- Analyze support tickets
- Suggest responses
- Track resolution time

**Code:**
```python
def handle_support_ticket(ticket_id, ticket_text, customer_info):
    # Analyze ticket
    analysis = client.execute(
        "support-analysis-agent",
        f"Analyze support ticket: {ticket_text}",
        context={"customer_info": customer_info}
    )

    # Generate response
    response = client.execute(
        "support-response-agent",
        f"Create response based on analysis: {analysis.text}"
    )

    # Return to agent
    return {
        "ticket_id": ticket_id,
        "analysis": analysis.text,
        "suggested_response": response.text,
        "priority": extract_priority(analysis.text)
    }
```

---

## Module 9: Certification Test

### Knowledge Check (20 questions)

**API Basics:**
1. What HTTP method is used to execute an agent?
2. What header is required for authentication?
3. What is the default rate limit?
4. What HTTP status code indicates rate limiting?

**Integration:**
5. How do you handle retries?
6. What's the best way to cache results?
7. How do you execute multiple agents in parallel?
8. What's exponential backoff?

**Best Practices:**
9. How should you structure task descriptions?
10. What context should you provide?
11. When should you break down tasks?
12. How do you handle errors gracefully?

**Practical Exercise:**
Build a simple application that:
1. Accepts user input
2. Calls an appropriate agent
3. Displays the result
4. Handles errors
5. Logs requests

### Passing Score
- **Written**: 80% (16/20 correct)
- **Practical**: Working application

---

## Additional Resources

- API Documentation: https://docs.agents.your-domain.com
- SDK GitHub: https://github.com/your-org/ai-agents-sdk
- Community Forum: https://community.agents.your-domain.com
- Support: developers@your-company.com

---

**Training Manual Version**: 1.0
**Last Updated**: 2025-01-15
