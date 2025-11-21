# AI Agents Platform - Complete Technical Documentation

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Agent Implementation](#agent-implementation)
3. [API Reference](#api-reference)
4. [Infrastructure](#infrastructure)
5. [Security](#security)
6. [Monitoring](#monitoring)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## 1. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer / CDN                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   Nginx API Gateway                          │
│    (SSL Termination, Rate Limiting, Auth Middleware)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌─────▼──────┐  ┌───────▼────────┐
│  Agent Pool    │  │  Agent Pool │  │  Agent Pool    │
│   (500 agents) │  │  (500 agents│  │  (500 agents)  │
└────────┬───────┘  └──────┬──────┘  └────────┬───────┘
         │                 │                   │
         └─────────────────┼───────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌─────▼──────┐  ┌───────▼────────┐
│    Redis       │  │ PostgreSQL │  │   Vault        │
│    Cache       │  │    DB      │  │   Secrets      │
└────────────────┘  └────────────┘  └────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Monitoring │
                    │  (Prometheus│
                    │   + Grafana)│
                    └─────────────┘
```

### Component Descriptions

**Agent Layer:**
- 1,500 FastAPI microservices
- Each agent is stateless and independently scalable
- Horizontal pod autoscaling based on CPU/memory
- Health checks: /health endpoint

**Data Layer:**
- PostgreSQL: Persistent storage for audit logs, user data
- Redis: Caching layer, session storage, rate limiting
- Vault: Secrets management, API keys

**Infrastructure Layer:**
- Kubernetes: Container orchestration
- Docker: Containerization
- Consul: Service discovery, configuration
- Nginx: API gateway, load balancing

**Monitoring Layer:**
- Prometheus: Metrics collection
- Grafana: Visualization and dashboards
- Loki: Log aggregation
- AlertManager: Alert routing

---

## 2. Agent Implementation

### Agent Structure

Each agent is a FastAPI application with standardized structure:

```python
# app.py - Agent Implementation
class AgentService:
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        # 1. Format prompt from template
        prompt = self.prompt_template.format(**request.context)

        # 2. Call Anthropic API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=config.MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )

        # 3. Process and return response
        return AgentResponse(
            result=response.content[0].text,
            metadata=self._extract_metadata(response)
        )
```

### Agent Files

Each agent consists of 4 files:

1. **app.py** (~135 lines)
   - FastAPI application
   - Business logic
   - API endpoints
   - Metrics collection

2. **Dockerfile** (Multi-stage build)
   ```dockerfile
   FROM python:3.11-alpine as builder
   # Build dependencies
   FROM python:3.11-alpine
   # Production image
   ```

3. **requirements.txt**
   ```
   fastapi==0.109.0
   anthropic==0.18.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.3
   prometheus-client==0.19.0
   ```

4. **README.md**
   - Agent description
   - Usage examples
   - Configuration options

### Agent Configuration

**Environment Variables:**
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Optional
MAX_TOKENS=4096
TEMPERATURE=0.7
PORT=8xxx
LOG_LEVEL=INFO
```

**Resource Limits:**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## 3. API Reference

### Base URL
```
Production: https://api.agents.your-domain.com
Staging: https://staging-api.agents.your-domain.com
Development: http://localhost:8xxx
```

### Authentication

**JWT Bearer Token:**
```bash
curl -H "Authorization: Bearer eyJhbGci..." \
  https://api.agents.your-domain.com/api/v1/execute
```

**API Key:**
```bash
curl -H "Authorization: Bearer sk-your-api-key" \
  https://api.agents.your-domain.com/api/v1/execute
```

### Endpoints

#### Execute Agent Task
```
POST /api/v1/execute
```

**Request:**
```json
{
  "task_description": "string (required, max 5000 chars)",
  "context": {
    "key": "value",  // Optional context
    "another_key": "another_value"
  }
}
```

**Response (200 OK):**
```json
{
  "result": "string - The agent's response",
  "metadata": {
    "agent_id": "business_plan_agent_009",
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 2847,
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "processing_time_ms": 4235.67
}
```

**Error Response (4xx/5xx):**
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

#### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "agent_id": "business_plan_agent_009",
  "version": "1.0.0",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Agent Metrics
```
GET /metrics
```

**Response:** Prometheus-formatted metrics
```
# HELP agent_requests_total Total number of requests
# TYPE agent_requests_total counter
agent_requests_total{agent_id="business_plan_agent_009"} 1234

# HELP agent_processing_seconds Request processing time
# TYPE agent_processing_seconds histogram
agent_processing_seconds_bucket{le="1.0"} 856
agent_processing_seconds_bucket{le="5.0"} 1180
agent_processing_seconds_bucket{le="+Inf"} 1234
agent_processing_seconds_sum 4567.89
agent_processing_seconds_count 1234
```

### Rate Limits

- **Default**: 100 requests/minute per user
- **Enterprise**: Custom limits available

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705318200
```

**Rate Limit Error (429):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 42 seconds",
    "retry_after": 42
  }
}
```

---

## 4. Infrastructure

### Kubernetes Resources

**Namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-agents
```

**Deployment (per agent):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: business-plan-agent-009
  namespace: ai-agents
spec:
  replicas: 2
  selector:
    matchLabels:
      app: business-plan-agent-009
  template:
    spec:
      containers:
      - name: business-plan-agent-009
        image: ghcr.io/your-org/business-plan-agent-009:latest
        ports:
        - containerPort: 8209
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**HorizontalPodAutoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: business-plan-agent-009-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: business-plan-agent-009
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Infrastructure as Code

**Terraform Structure:**
```
terraform/
├── aws/
│   ├── main.tf          # EKS cluster
│   ├── variables.tf     # Input variables
│   ├── outputs.tf       # Outputs
│   └── modules/
│       ├── eks/         # EKS module
│       ├── vpc/         # VPC module
│       └── rds/         # RDS module
├── gcp/
│   └── main.tf          # GKE cluster
└── azure/
    └── main.tf          # AKS cluster
```

---

## 5. Security

### Authentication Flow

```
1. User → POST /auth/login (username, password)
2. Server validates credentials
3. Server generates JWT token
4. Server returns token (expires in 1 hour)
5. User includes token in Authorization header
6. Server validates token on each request
7. Token can be refreshed before expiration
```

### Network Security

**Network Policies:**
- Default deny all ingress
- Explicit allow rules for required traffic
- Pod-to-pod isolation
- Egress control

**Example Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-agent-traffic
spec:
  podSelector:
    matchLabels:
      role: agent
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: api-gateway
    ports:
    - protocol: TCP
      port: 8080
```

### Secrets Management

**Vault Integration:**
```python
import hvac

# Initialize Vault client
vault = hvac.Client(url='http://vault:8200', token=vault_token)

# Retrieve secret
secret = vault.secrets.kv.v2.read_secret_version(
    path='agents/anthropic'
)
api_key = secret['data']['data']['api_key']
```

### Security Checklist

- [ ] All secrets in Vault, not in code
- [ ] TLS/SSL for all external traffic
- [ ] JWT tokens with short expiration
- [ ] Rate limiting enabled
- [ ] Network policies enforced
- [ ] Pod security policies applied
- [ ] Container images scanned
- [ ] Dependencies updated
- [ ] Audit logging enabled
- [ ] Backup and recovery tested

---

## 6. Monitoring

### Key Metrics

**Application Metrics:**
- `agent_requests_total`: Total requests by agent
- `agent_errors_total`: Total errors by agent
- `agent_processing_seconds`: Request duration histogram
- `agent_tokens_used_total`: Total tokens consumed

**Infrastructure Metrics:**
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage
- `kube_pod_status_ready`: Pod readiness
- `kube_deployment_replicas`: Replica counts

### Grafana Dashboards

**Platform Overview Dashboard:**
- Total request rate (all agents)
- Global error rate
- Average response time (P50, P95, P99)
- Active agent count
- Top 10 most-used agents
- Cost estimate (daily/monthly)

**Agent Detail Dashboard:**
- Request rate (specific agent)
- Error rate (specific agent)
- Response time distribution
- Token usage
- Resource usage (CPU/Memory)
- Recent errors

### Alerts

**Critical Alerts:**
- AgentDown: Agent not responding for 2+ minutes
- HighErrorRate: Error rate > 5% for 5 minutes
- DatabaseDown: Database unavailable

**Warning Alerts:**
- HighResponseTime: P95 > 10 seconds
- HighCPUUsage: CPU > 80% for 10 minutes
- HighMemoryUsage: Memory > 85% for 10 minutes

### Logging

**Log Levels:**
- DEBUG: Detailed debugging info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

**Log Format (JSON):**
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "agent_id": "business_plan_agent_009",
  "message": "Request completed",
  "duration_ms": 3456.78,
  "tokens_used": 2847
}
```

---

## 7. Deployment

### Deployment Strategies

**Rolling Update (Default):**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

**Blue-Green Deployment:**
```bash
# Deploy new version (green)
kubectl apply -f agent-v2-deployment.yaml

# Test green deployment
curl http://agent-v2-service/health

# Switch traffic
kubectl patch service agent-service \
  -p '{"spec":{"selector":{"version":"v2"}}}'
```

**Canary Deployment:**
```yaml
# 10% traffic to new version
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: agent-canary
spec:
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: agent-v2
      weight: 10
    - destination:
        host: agent-v1
      weight: 90
```

### CI/CD Pipeline

**GitHub Actions Example:**
```yaml
name: Deploy Agent
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build image
        run: docker build -t agent:${{ github.sha }} .

      - name: Push to registry
        run: docker push agent:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/agent \
            agent=agent:${{ github.sha }}
          kubectl rollout status deployment/agent
```

---

## 8. Troubleshooting

### Common Issues

#### Agent Returns 500 Error

**Check logs:**
```bash
kubectl logs -n ai-agents deployment/business-plan-agent-009
```

**Common causes:**
- Invalid API key
- Anthropic API unavailable
- Database connection issues

**Solutions:**
```bash
# Verify API key
kubectl get secret agent-secrets -n ai-agents -o json

# Check Anthropic status
curl https://status.anthropic.com/api/v2/status.json

# Test database connection
kubectl exec -it postgres-0 -n ai-agents -- psql -U agents_admin
```

#### High Latency

**Check metrics:**
```promql
# P95 latency
histogram_quantile(0.95,
  rate(agent_processing_seconds_bucket[5m])
)
```

**Solutions:**
- Scale up replicas
- Increase resource limits
- Check network latency
- Enable caching

#### Memory Leaks

**Monitor memory:**
```bash
kubectl top pods -n ai-agents --sort-by=memory
```

**Solutions:**
- Restart affected pods
- Update to latest version
- Review code for memory leaks
- Increase memory limits

### Debug Mode

**Enable debug logging:**
```bash
kubectl set env deployment/business-plan-agent-009 \
  -n ai-agents LOG_LEVEL=DEBUG
```

**View detailed logs:**
```bash
kubectl logs -n ai-agents -l app=business-plan-agent-009 -f
```

---

## Additional Resources

- **API Documentation**: `docs/api/`
- **Training Manuals**: `docs/training/`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Operations Runbook**: `RUNBOOK.md`
- **Security Guide**: `security/README.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Maintained By**: Platform Engineering Team
