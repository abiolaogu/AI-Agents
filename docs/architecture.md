# Architecture

**Project**: AI-Agents Platform
**Last Updated**: 2026-02-17

---

## 1. High-Level Overview

The AI-Agents platform is a cloud-native, microservices-based system that hosts 1,500
specialised AI agents across 29 business categories. The system is designed around four
primary layers: the Agent Layer, the Orchestration Layer, the Infrastructure Layer, and the
Presentation Layer.

```
+-------------------------------------------------------------+
|                    PRESENTATION LAYER                        |
|  React/TypeScript Frontend (Vite)                           |
|  - Agent Marketplace    - Dashboard    - Analytics           |
+-------------------------------------------------------------+
           |                    |                    |
           v                    v                    v
+-------------------------------------------------------------+
|                   ORCHESTRATION LAYER                        |
|  FastAPI Orchestration Engine                                |
|  - AgentManager          - WorkflowManager                   |
|  - AnalyticsManager      - Auth (JWT + API Key)              |
|  - Celery Workers        - Redpanda Event Streaming          |
+-------------------------------------------------------------+
           |                    |                    |
           v                    v                    v
+-------------------------------------------------------------+
|                      AGENT LAYER                             |
|  1,500 FastAPI Microservices (generated-agents/)             |
|  - POST /api/v1/execute  - GET /health  - GET /metrics       |
|  - Anthropic Claude 3.5 Sonnet integration                   |
|  - Prometheus counters + histograms                          |
+-------------------------------------------------------------+
           |                    |                    |
           v                    v                    v
+-------------------------------------------------------------+
|                  INFRASTRUCTURE LAYER                        |
|  PostgreSQL 15  |  Redis 7  |  Redpanda  |  OPA  |  Vault   |
|  Prometheus  |  Grafana  |  Loki  |  AlertManager            |
|  Docker  |  Kubernetes  |  Consul                            |
+-------------------------------------------------------------+
```

---

## 2. Component Architecture

### 2.1 Orchestration Engine

Location: `services/orchestration_engine/`

The orchestration engine is the central nervous system. It is a FastAPI application that:

- **AgentManager**: Loads agent definitions from `agents/definitions/`, registers metadata,
  and provides agent URL resolution for workflow routing.
- **WorkflowManager**: Creates multi-step workflows persisted in PostgreSQL, dispatches
  execution to Celery, and tracks status through completion or failure.
- **AnalyticsManager**: Logs workflow and agent events to Redpanda for downstream analytics.
- **Auth Module**: Handles user registration and login with bcrypt password hashing and
  JWT token issuance.
- **Celery Worker**: Async task execution for workflows via Redis-backed Celery.
- **RedpandaManager**: Kafka-compatible event producer for analytics telemetry.

Key endpoints:
```
POST /auth/register           -- User registration
POST /auth/login              -- JWT token issuance
GET  /agents/library          -- Agent marketplace catalogue
POST /workflows               -- Create and dispatch workflow
GET  /workflows               -- List user workflows
GET  /workflows/{id}          -- Workflow status
GET  /analytics/events        -- User analytics events
```

### 2.2 Agent Microservices

Location: `generated-agents/` (1,500 agents), `services/` (10 hand-crafted agents),
`examples/` (30 reference agents)

Each agent follows an identical structure:
```
agent-name/
  app.py              -- FastAPI application (~135 lines)
  requirements.txt    -- Pinned Python dependencies
  Dockerfile          -- Multi-stage container build
  README.md           -- Agent-specific documentation
```

Every agent exposes:
- `POST /api/v1/execute` -- Main task execution (accepts `AgentRequest`, returns `AgentResponse`)
- `GET /health` -- Liveness probe
- `GET /metrics` -- Prometheus metrics endpoint
- `GET /` -- Agent metadata (ID, name, version, category, status)

Agent code uses the Anthropic Python SDK to call Claude 3.5 Sonnet with a domain-specific
system prompt and configurable temperature/max-tokens.

### 2.3 Shared Packages

Location: `packages/`

| Package | Purpose |
|---------|---------|
| `agent_framework` | `BaseAgent` ABC, `EnhancedAgent`, `AgentTeam`, `AgentLoader` |
| `multi_framework` | `FrameworkOrchestrator` with adapters for LangGraph, CrewAI, AutoGen |
| `integration_framework` | `BaseConnector`, `CredentialManager` for third-party integrations |
| `vector_memory` | Qdrant vector database manager for agent memory |
| `performance` | `CacheManager` for Redis-based response caching |

### 2.4 Frontend

Location: `web/`

React 18 + TypeScript application built with Vite. Routes:

| Route | Component | Auth Required |
|-------|-----------|---------------|
| `/` | `AgentMarketplace` | No |
| `/login` | `LoginPage` | No |
| `/register` | `RegisterPage` | No |
| `/dashboard` | `DashboardPage` | Yes |
| `/analytics` | `AnalyticsPage` | Yes |

State management uses React Context (`AuthContext`). API calls go through `authService.ts`.

---

## 3. Data Flow

### 3.1 Agent Execution Flow

```
User -> Frontend -> Orchestration Engine -> WorkflowManager
  -> Celery Task Queue -> Celery Worker -> Agent Microservice
  -> Anthropic Claude API -> Response -> Celery Worker
  -> WorkflowManager (DB update) -> AnalyticsManager (Redpanda event)
  -> User polls GET /workflows/{id} for results
```

### 3.2 Authentication Flow

```
User -> POST /auth/register (username, password)
  -> bcrypt hash -> PostgreSQL users table -> 201 Created

User -> POST /auth/login (username, password)
  -> bcrypt verify -> JWT token (HS256, 1hr expiry) -> 200 {token}

User -> Any protected endpoint (Authorization: Bearer <token>)
  -> JWT decode -> User context injected via FastAPI Depends
```

### 3.3 Event Streaming Flow

```
Agent execution event -> AnalyticsManager -> Redpanda topic
  -> Consumer (future) -> Analytics dashboard / Data warehouse
```

---

## 4. Infrastructure Components

### 4.1 Databases

| Service | Purpose | Configuration |
|---------|---------|---------------|
| PostgreSQL 15 | Workflow state, user accounts | `ai_agents` database, Alpine image |
| Redis 7 | Celery broker, caching, rate limiting, token blacklist | Alpine image, 512MB limit |

### 4.2 Event Streaming

Redpanda (Kafka-compatible) handles analytics event streaming. Single-node configuration
with 1GB memory limit. Kafka protocol on port 9092, Pandaproxy on 8082.

### 4.3 Policy Engine

Open Policy Agent (OPA) runs as a sidecar service on port 8181. Rego policies in
`policies/agents/access_control.rego` define role-based access. Roles data is in
`policies/data/roles.json`.

### 4.4 Secrets Management

HashiCorp Vault stores production secrets (API keys, DB credentials). Initialised via
`security/vault-config/vault-init.sh`. Kubernetes integration via external-secrets operator.

### 4.5 Configuration Management

Consul-based config service (`config-management/config_service.py`) provides dynamic
configuration updates, feature flags, and multi-environment support.

---

## 5. Deployment Architecture

### 5.1 Local Development (Docker Compose)

```
docker-compose.yml defines:
  - orchestration-engine (port 8000)
  - 5 legacy agents (ports 5001-5006)
  - redpanda (port 9092)
  - redis (port 6379)
  - postgres (port 5432)
  - opa (port 8181)
  - prometheus (port 9090)
  - grafana (port 3000)
  - worker (Celery)
  - frontend (port 5173)
  - adminer (port 8080)
  - redis-commander (port 8081)
```

### 5.2 Production (Kubernetes)

Namespace: `ai-agents` (agents), `ai-agents-monitoring` (observability)

Components:
- Agent deployments with HPA (2-10 replicas, 70% CPU target)
- Redis cluster (6 nodes)
- PostgreSQL StatefulSet
- Prometheus + Grafana + Loki + AlertManager
- Ingress controller (nginx)
- cert-manager for SSL
- Network policies for pod isolation

---

## 6. Security Architecture

```
Internet -> WAF -> Load Balancer -> Ingress Controller
  -> API Gateway (JWT/API Key auth + rate limiting)
  -> OPA Policy Check -> Agent Microservice
  -> Vault (secret retrieval) -> Anthropic API
```

Layers:
1. **Network**: Kubernetes NetworkPolicy isolates namespaces and pods.
2. **Authentication**: JWT tokens (1hr TTL) with Redis-backed blacklist.
3. **Authorisation**: OPA Rego policies with role-based permissions.
4. **Rate Limiting**: Per-user sliding window (100 req/60s default).
5. **Secrets**: Vault KV store with policy-based access control.
6. **Audit**: Analytics events logged to Redpanda for every agent execution.

---

## 7. Scalability Model

| Dimension | Strategy |
|-----------|----------|
| Horizontal agent scaling | Kubernetes HPA per agent deployment |
| Cluster scaling | Cluster Autoscaler (AWS/GCP/Azure) |
| Database scaling | Read replicas, connection pooling |
| Cache scaling | Redis cluster with 6 nodes |
| Event processing | Redpanda partition-based scaling |
| LLM throughput | Multiple Anthropic API keys, request queuing |

### Capacity Estimates

| Metric | Target |
|--------|--------|
| Concurrent users | 1M+ (distributed across 1,500 agents) |
| Daily agent executions | 100M+ |
| P95 response time | < 2 seconds |
| Availability | 99.9% |

---

## 8. Technology Decisions

| Decision | Rationale |
|----------|-----------|
| FastAPI over Flask | Native async, Pydantic validation, OpenAPI generation |
| Claude 3.5 Sonnet | Best balance of capability, cost, and speed for agent tasks |
| Redpanda over Kafka | Lower resource footprint, Kafka-compatible, no JVM dependency |
| OPA over custom RBAC | Declarative policies, industry standard, Kubernetes-native |
| Celery over native async | Proven at scale, Redis broker, retry/dead-letter support |
| React + Vite | Fast HMR, TypeScript support, ecosystem maturity |

---

*This document reflects the architecture as implemented in the codebase. See the gap analysis
for known issues and planned improvements.*
