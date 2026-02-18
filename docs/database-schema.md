# Data Model

**Project**: AI-Agents Platform
**Last Updated**: 2026-02-17

---

## 1. Overview

The AI-Agents platform uses PostgreSQL 15 as its primary data store and Redis 7 for caching,
rate limiting, and task brokering. This document describes all persistent data models, their
relationships, and the migration strategy.

---

## 2. PostgreSQL Schema

### 2.1 Users Table

Defined in `services/orchestration_engine/orchestration_engine/database.py`.

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | PRIMARY KEY | Auto-incrementing user ID |
| `username` | `VARCHAR(255)` | UNIQUE, NOT NULL | Login identifier |
| `password_hash` | `VARCHAR(255)` | NOT NULL | bcrypt-hashed password |
| `created_at` | `TIMESTAMP` | DEFAULT now() | Account creation timestamp |

### 2.2 Workflows Table

```sql
CREATE TABLE workflows (
    id          VARCHAR(36) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    tasks       TEXT NOT NULL,
    status      VARCHAR(50) DEFAULT 'pending',
    results     TEXT DEFAULT '[]',
    user_id     INTEGER REFERENCES users(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | UUID v4 workflow identifier |
| `name` | `VARCHAR(255)` | NOT NULL | Human-readable workflow name |
| `tasks` | `TEXT` | NOT NULL | JSON-serialised list of task definitions |
| `status` | `VARCHAR(50)` | DEFAULT 'pending' | One of: pending, running, completed, failed |
| `results` | `TEXT` | DEFAULT '[]' | JSON-serialised list of agent responses |
| `user_id` | `INTEGER` | FOREIGN KEY -> users(id) | Owner of the workflow |
| `created_at` | `TIMESTAMP` | DEFAULT now() | Workflow creation timestamp |

### 2.3 Entity Relationship Diagram

```
+----------+       1:N       +------------+
|  users   |--------------->| workflows  |
+----------+                +------------+
| id (PK)  |                | id (PK)    |
| username |                | name       |
| password |                | tasks      |
| created  |                | status     |
+----------+                | results    |
                            | user_id(FK)|
                            | created    |
                            +------------+
```

---

## 3. JSON Data Structures

### 3.1 Workflow Tasks (stored in `workflows.tasks`)

```json
[
  {
    "agent_id": "sales_leadgen_agent_001",
    "task_details": {
      "task_description": "Generate leads for fintech vertical",
      "context": {
        "industry": "fintech",
        "region": "US"
      }
    }
  }
]
```

### 3.2 Workflow Results (stored in `workflows.results`)

```json
[
  {
    "result": "Generated 50 qualified leads...",
    "metadata": {
      "agent_id": "sales_leadgen_agent_001",
      "model": "claude-3-5-sonnet-20241022",
      "tokens_used": 1523
    },
    "processing_time_ms": 2340.5
  }
]
```

---

## 4. Agent Definition Schema

### 4.1 JSON Definitions (`agents/definitions/*.json`)

```json
{
  "id": "sales_leadgen_agent_001",
  "name": "Lead Generation Agent",
  "description": "Identifies and qualifies potential leads using AI",
  "category": "sales",
  "version": "1.0.0",
  "url": "http://lead-scoring-agent:5002",
  "capabilities": ["lead_scoring", "prospect_research"],
  "system_prompt": "You are an expert lead generation specialist...",
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

### 4.2 YAML Definitions (`agents/definitions/<category>/*.yaml`)

```yaml
name: Dynamic Pricing Engine
category: hospitality_tourism
description: Optimises room and service pricing based on demand signals
version: 1.0.0
model: claude-3-5-sonnet-20241022
temperature: 0.7
max_tokens: 4096
system_prompt: |
  You are an expert in dynamic pricing for the hospitality industry...
capabilities:
  - demand_forecasting
  - price_optimization
  - competitor_monitoring
```

---

## 5. Redis Data Structures

### 5.1 Rate Limiting

```
Key:    rate_limit:{user_id}
Type:   String (counter)
TTL:    60 seconds
Value:  Integer (request count in current window)
```

### 5.2 Token Blacklist

```
Key:    blacklist:{jwt_token}
Type:   String
TTL:    Remaining token lifetime (max 3600s)
Value:  "1"
```

### 5.3 API Keys

```
Key:    api_key:sk-{random_token}
Type:   Hash
Fields: user_id, name, permissions, created_at
TTL:    None (persistent until revoked)
```

### 5.4 Celery Task Queue

```
Key:    celery (default queue name)
Type:   List (FIFO queue)
Value:  Serialised Celery task messages
```

### 5.5 Cache Entries (via CacheManager)

```
Key:    cache:{cache_key}
Type:   String
TTL:    Configurable (default 3600s)
Value:  JSON-serialised response data
```

---

## 6. Redpanda / Kafka Topics

### 6.1 Analytics Events Topic

```
Topic:      agent-analytics
Partitions: 1 (default, scale as needed)
Retention:  7 days (default)
```

**Event Schema**:
```json
{
  "event_type": "agent_task_completed",
  "workflow_id": "uuid",
  "agent_id": "string",
  "user_id": 123,
  "duration": 2.34,
  "status": "success",
  "timestamp": "2026-02-17T10:30:00Z"
}
```

**Event Types**:
- `workflow_created`
- `workflow_started`
- `workflow_finished`
- `agent_task_completed`
- `agent_task_failed`

---

## 7. OPA Policy Data

Location: `policies/data/roles.json`

```json
{
  "roles": {
    "admin": {
      "permissions": ["*"]
    },
    "developer": {
      "permissions": ["agent:execute", "workflow:create", "workflow:read"]
    },
    "viewer": {
      "permissions": ["workflow:read", "agent:list"]
    }
  }
}
```

---

## 8. Consul Configuration Store

Location: `config-management/config_service.py`

Key-value pairs stored in Consul for dynamic runtime configuration:

```
ai-agents/config/log_level         -> "INFO"
ai-agents/config/rate_limit        -> "100"
ai-agents/config/feature/workflows -> "true"
ai-agents/config/feature/analytics -> "true"
ai-agents/config/feature/teams     -> "true"
```

---

## 9. Migration Strategy

### Current State

The database schema is created via SQLAlchemy's `create_all()` at application startup in
`database.py`. There is no migration tooling.

### Recommended Approach

1. **Install Alembic**: `pip install alembic`
2. **Initialise**: `alembic init migrations`
3. **Configure**: Point `alembic.ini` at `DATABASE_URL` from environment.
4. **Auto-generate initial migration**:
   ```bash
   alembic revision --autogenerate -m "initial schema"
   ```
5. **Remove `create_all()`** from application startup.
6. **Add migration step** to deployment scripts:
   ```bash
   alembic upgrade head
   ```

### Future Schema Additions (Planned)

| Table | Purpose |
|-------|---------|
| `teams` | RBAC team management |
| `agent_executions` | Persistent execution history (currently in Redpanda) |
| `api_keys` | Move from Redis to PostgreSQL for durability |
| `audit_log` | Immutable security audit trail |

---

## 10. Data Flow Summary

```
User Input -> Frontend -> Orchestration Engine
  -> PostgreSQL (workflow record created)
  -> Celery (task dispatched via Redis)
  -> Worker -> Agent -> Claude API -> Response
  -> PostgreSQL (results updated)
  -> Redpanda (analytics event published)
  -> User polls for results via REST API
```

---

*See `services/orchestration_engine/orchestration_engine/database.py` for the SQLAlchemy model
definitions.*
