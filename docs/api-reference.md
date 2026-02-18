# API Reference

**Project**: AI-Agents Platform
**Base URL**: `http://localhost:8000` (local) / `https://api.agents.your-domain.com` (production)
**Last Updated**: 2026-02-17

---

## 1. Authentication Endpoints

### POST /auth/register

Create a new user account.

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 201**:
```json
{
  "message": "User registered successfully"
}
```

**Response 409**:
```json
{
  "detail": "Username already exists"
}
```

---

### POST /auth/login

Authenticate and receive a JWT token.

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 401**:
```json
{
  "detail": "Invalid credentials"
}
```

**Token Details**:
- Algorithm: HS256
- Expiry: 3600 seconds (1 hour)
- Payload: `user_id`, `roles`, `permissions`, `iat`, `exp`

---

## 2. Agent Library Endpoints

### GET /agents/library

Retrieve the full catalogue of available agents for the Agent Marketplace.

**Authentication**: None required.

**Response 200**:
```json
[
  {
    "id": "sales_leadgen_agent_001",
    "name": "Lead Generation Agent",
    "description": "Identifies and qualifies potential leads",
    "category": "sales",
    "version": "1.0.0",
    "url": "http://lead-scoring-agent:5002"
  }
]
```

**Notes**:
- Returns all agents registered in the `AgentManager`.
- Currently loads from JSON definitions in `agents/definitions/`.
- YAML-based agents in category subdirectories are not yet loaded (see gap analysis).

---

## 3. Workflow Endpoints

All workflow endpoints require a valid JWT token in the `Authorization: Bearer <token>` header.

### POST /workflows

Create a new multi-step workflow and dispatch it for execution.

**Request Body**:
```json
{
  "name": "Q1 Sales Pipeline",
  "tasks": [
    {
      "agent_id": "sales_leadgen_agent_001",
      "task_details": {
        "task_description": "Generate 50 leads in the fintech vertical",
        "context": {
          "industry": "fintech",
          "region": "US"
        }
      }
    },
    {
      "agent_id": "marketing_contentcreation_agent_001",
      "task_details": {
        "task_description": "Create email campaign copy for the generated leads"
      }
    }
  ]
}
```

**Response 202**:
```json
{
  "message": "Workflow created and dispatched for execution.",
  "workflow_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_url": "/workflows/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### GET /workflows

List all workflows for the authenticated user.

**Response 200**:
```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Q1 Sales Pipeline",
    "status": "completed"
  }
]
```

**Possible statuses**: `pending`, `running`, `completed`, `failed`

---

### GET /workflows/{workflow_id}

Get detailed status and results of a specific workflow.

**Response 200**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Q1 Sales Pipeline",
  "status": "completed",
  "results": [
    {
      "result": "Generated 50 qualified leads in fintech...",
      "metadata": {
        "agent_id": "sales_leadgen_agent_001",
        "model": "claude-3-5-sonnet-20241022",
        "tokens_used": 1523
      },
      "processing_time_ms": 2340.5
    }
  ]
}
```

**Response 404**:
```json
{
  "detail": "Workflow not found or access denied"
}
```

---

## 4. Analytics Endpoints

### GET /analytics/events

Retrieve analytics events for the authenticated user.

**Response 200**:
```json
[
  {
    "event_type": "workflow_created",
    "workflow_id": "a1b2c3d4",
    "timestamp": "2026-02-17T10:30:00Z"
  },
  {
    "event_type": "agent_task_completed",
    "workflow_id": "a1b2c3d4",
    "agent_id": "sales_leadgen_agent_001",
    "duration": 2.34,
    "status": "success"
  }
]
```

---

## 5. Individual Agent API

Each of the 1,500 agents exposes the following endpoints on its own port (range 8200-9000).

### POST /api/v1/execute

Execute the agent's primary task.

**Request Body**:
```json
{
  "task_description": "Analyse competitor pricing strategies for Q1 2026",
  "context": {
    "industry": "SaaS",
    "competitors": ["CompA", "CompB"]
  }
}
```

**Response 200**:
```json
{
  "result": "Based on my analysis of competitor pricing...",
  "metadata": {
    "agent_id": "competitor-analysis-agent",
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 2048
  },
  "processing_time_ms": 1856.3
}
```

---

### GET /health

Agent liveness check.

**Response 200**:
```json
{
  "status": "healthy",
  "agent_id": "ab-testing-agent-078",
  "version": "1.0.0",
  "timestamp": "2026-02-17T10:30:00Z"
}
```

---

### GET /metrics

Prometheus-formatted metrics.

**Response 200** (text/plain):
```
# HELP agent_requests_total Total requests
# TYPE agent_requests_total counter
agent_requests_total{agent_id="ab-testing-agent-078"} 142

# HELP agent_processing_seconds Processing duration
# TYPE agent_processing_seconds histogram
agent_processing_seconds_bucket{le="0.5"} 10
agent_processing_seconds_bucket{le="1.0"} 45
agent_processing_seconds_bucket{le="2.5"} 120
agent_processing_seconds_bucket{le="5.0"} 140
agent_processing_seconds_bucket{le="+Inf"} 142
agent_processing_seconds_sum 284.6
agent_processing_seconds_count 142
```

---

### GET /

Agent identity and status.

**Response 200**:
```json
{
  "agent_id": "ab-testing-agent-078",
  "name": "A/B Testing Agent",
  "version": "1.0.0",
  "status": "operational",
  "category": "sales_marketing"
}
```

---

## 6. API Key Authentication

For programmatic access, API keys can be used instead of JWT tokens.

**Header**: `Authorization: Bearer sk-<api-key>`

API keys are managed via the `APIKeyAuth` class in `security/api-gateway/auth-middleware.py`.
They are stored in Redis with associated user ID, name, and permissions.

---

## 7. Rate Limiting

| Parameter | Default |
|-----------|---------|
| Requests per window | 100 |
| Window duration | 60 seconds |
| Scope | Per user ID |
| Storage | Redis key: `rate_limit:{user_id}` |

**Response 429** when exceeded:
```json
{
  "detail": "Rate limit exceeded"
}
```

---

## 8. Error Responses

All endpoints return standard HTTP error codes with JSON bodies:

| Code | Meaning |
|------|---------|
| 400 | Bad Request -- Invalid input |
| 401 | Unauthorised -- Missing or invalid token |
| 403 | Forbidden -- Insufficient permissions |
| 404 | Not Found -- Resource does not exist |
| 409 | Conflict -- Resource already exists (registration) |
| 429 | Too Many Requests -- Rate limit exceeded |
| 500 | Internal Server Error -- Agent execution failure |

---

## 9. Pydantic Schemas

Defined in `services/orchestration_engine/orchestration_engine/schemas.py`:

```python
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TaskCreate(BaseModel):
    agent_id: str
    task_details: dict

class WorkflowCreate(BaseModel):
    name: str
    tasks: list[TaskCreate]
```

Defined in each generated agent `app.py`:

```python
class AgentRequest(BaseModel):
    task_description: str
    context: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]
    processing_time_ms: float
```

---

*See the orchestration engine source at `services/orchestration_engine/` for implementation details.*
