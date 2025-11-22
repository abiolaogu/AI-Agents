# AI Agents Platform - Administrator Training Manual

## Course Information
- **Target Audience**: Platform Administrators, DevOps Engineers, SRE
- **Duration**: 4-6 hours
- **Prerequisites**: Kubernetes basics, Linux command line, Docker
- **Certification**: Available upon completion

---

## Module 1: Platform Overview (30 minutes)

### 1.1 Introduction to AI Agents Platform

**What You'll Learn:**
- Platform architecture
- Core components
- Agent categories and capabilities

**Platform Overview:**
The AI Agents Platform consists of 1,500 specialized AI agents across 29 business categories, each powered by Anthropic's Claude 3.5 Sonnet model.

**Key Components:**
1. **Agent Layer**: 1,500 containerized FastAPI applications
2. **Infrastructure Layer**: Kubernetes, load balancers, storage
3. **Data Layer**: PostgreSQL, Redis
4. **Security Layer**: Vault, authentication, network policies
5. **Monitoring Layer**: Prometheus, Grafana, Loki

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│              Load Balancer / Ingress            │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              API Gateway                        │
│         (Auth, Rate Limiting)                   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          1,500 AI Agents                        │
│    (Business Ops, Marketing, Finance, etc.)     │
└──┬─────────────┬──────────────┬─────────────┬───┘
   │             │              │             │
┌──▼───┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
│Vault │   │ Redis   │   │Postgres │   │ Consul  │
│      │   │ Cache   │   │   DB    │   │ Config  │
└──────┘   └─────────┘   └─────────┘   └─────────┘
```

### 1.3 Agent Categories (29 Total)

**Business & Operations:**
- Business Operations (40 agents)
- Finance & Accounting (35 agents)
- HR & People Ops (30 agents)
- Legal & Compliance (25 agents)

**Marketing & Sales:**
- Sales & Marketing (50 agents)
- Customer Support (45 agents)
- Content & Creators (40 agents)

**Technical:**
- Product & Technology (55 agents)
- Data Science & Analytics (60 agents)
- DevOps & Infrastructure (96 agents)

**Industry Specific:**
- Healthcare & Wellness (50 agents)
- Real Estate (35 agents)
- Retail & E-commerce (40 agents)
- Agriculture & Food (50 agents)
- Construction & Engineering (50 agents)
- And 14 more categories...

---

## Module 2: Installation & Setup (60 minutes)

### 2.1 Prerequisites Checklist

**Infrastructure Requirements:**
```bash
# Verify Kubernetes cluster
kubectl version --short
# Client Version: v1.24+
# Server Version: v1.24+

# Check cluster resources
kubectl get nodes
# Should show at least 3 nodes with Ready status

# Verify Helm
helm version --short
# v3.10+

# Check Docker
docker version
# 20.10+
```

**Required Credentials:**
- [ ] Kubernetes cluster admin access
- [ ] Docker registry credentials (ghcr.io)
- [ ] Anthropic API key
- [ ] Cloud provider credentials (AWS/GCP/Azure)

### 2.2 Quick Installation

**Step 1: Clone Repository**
```bash
git clone https://github.com/your-org/AI-Agents.git
cd AI-Agents
```

**Step 2: Configure Environment**
```bash
# Copy environment template
cp config-management/.env.template .env

# Edit with your values
nano .env
```

**Required Environment Variables:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
ENVIRONMENT=production
CONSUL_HOST=consul-service
VAULT_ADDR=http://vault-service:8200
REDIS_HOST=redis-service
DB_HOST=postgres-service
DB_PASSWORD=your-secure-password
```

**Step 3: Deploy Infrastructure**
```bash
cd infrastructure/scripts

# Deploy everything
./deploy.sh production full
```

**What This Does:**
1. Creates Kubernetes namespaces
2. Deploys Vault for secrets
3. Deploys monitoring stack (Prometheus, Grafana)
4. Deploys supporting services (Redis, PostgreSQL)
5. Generates manifests for 1,500 agents
6. Deploys all agents
7. Configures ingress
8. Runs health checks

**Expected Duration:** 20-30 minutes

### 2.3 Verify Installation

**Check All Pods:**
```bash
kubectl get pods -n ai-agents
# Should show all agents with STATUS: Running

# Count running agents
kubectl get pods -n ai-agents | grep Running | wc -l
# Should show close to 1500
```

**Run Health Checks:**
```bash
python3 infrastructure/scripts/health_check.py
```

**Expected Output:**
```
✓ business_plan_agent_009: OK
✓ marketing_agent_001: OK
✓ sales_agent_002: OK
...
========================================
Health Check Summary
========================================
Total agents checked: 1500
Healthy: 1500
Unhealthy: 0
Health percentage: 100.00%
========================================
```

### 2.4 Access Monitoring

**Grafana Dashboard:**
```bash
# Port-forward Grafana
kubectl port-forward -n ai-agents-monitoring svc/grafana 3000:3000

# Open in browser: http://localhost:3000
# Username: admin
# Password: admin (change on first login)
```

**Prometheus:**
```bash
kubectl port-forward -n ai-agents-monitoring svc/prometheus 9090:9090
# Open: http://localhost:9090
```

---

## Module 3: Daily Operations (45 minutes)

### 3.1 Morning Checklist (10 minutes)

**Daily Health Check:**
```bash
# 1. Check platform health
./infrastructure/scripts/health_check.py

# 2. Review overnight alerts
kubectl logs -n ai-agents-monitoring deployment/alertmanager --since=12h

# 3. Check resource usage
kubectl top nodes
kubectl top pods -n ai-agents --sort-by=memory | head -20

# 4. Review error rates in Grafana
# Visit: https://grafana.your-domain.com/d/agents-overview
```

**Key Metrics to Monitor:**
- **Request Rate**: Should be steady during business hours
- **Error Rate**: Should be < 1%
- **Response Time**: P95 should be < 3 seconds
- **Resource Usage**: Should be < 70% average

### 3.2 Managing Agents

**Scale Specific Agent:**
```bash
# Scale up
kubectl scale deployment business-plan-agent-009-deployment \
  -n ai-agents --replicas=5

# Scale down
kubectl scale deployment business-plan-agent-009-deployment \
  -n ai-agents --replicas=2

# Check HPA status
kubectl get hpa -n ai-agents
```

**Restart Agent:**
```bash
kubectl rollout restart deployment/business-plan-agent-009-deployment \
  -n ai-agents

# Watch status
kubectl rollout status deployment/business-plan-agent-009-deployment \
  -n ai-agents
```

**View Agent Logs:**
```bash
# Recent logs
kubectl logs -n ai-agents -l app=business-plan-agent-009 --tail=100

# Follow logs
kubectl logs -n ai-agents -l app=business-plan-agent-009 -f

# Logs from specific pod
kubectl logs <pod-name> -n ai-agents
```

### 3.3 Monitoring & Alerts

**Understanding Alerts:**

1. **HighErrorRate** (Critical)
   - Trigger: Error rate > 5% for 5 minutes
   - Action: Check agent logs, verify API keys, check Anthropic status

2. **AgentDown** (Critical)
   - Trigger: Agent not responding to health checks
   - Action: Check pod status, review events, restart if needed

3. **HighResponseTime** (Warning)
   - Trigger: Average response time > 10 seconds
   - Action: Check resource usage, scale if needed

**Silencing Alerts:**
```bash
# Silence alert during maintenance
amtool silence add alertname=HighErrorRate \
  --duration=1h \
  --comment="Maintenance window"
```

### 3.4 Backup & Recovery

**Daily Backups (Automated):**
- Kubernetes manifests → Git
- Vault snapshots → S3
- PostgreSQL dumps → S3
- Redis snapshots → Configured

**Manual Backup:**
```bash
# Backup platform
./infrastructure/scripts/backup_platform.sh

# Verify backup
./infrastructure/scripts/verify_backup.sh
```

---

## Module 4: Troubleshooting (60 minutes)

### 4.1 Common Issues

#### Issue 1: Agent Won't Start

**Symptoms:**
- Pod in CrashLoopBackOff
- Container restarting frequently

**Diagnosis:**
```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-agents

# Check logs
kubectl logs <pod-name> -n ai-agents --previous

# Common causes:
# - Missing environment variable
# - Invalid API key
# - Resource limits too low
```

**Solution:**
```bash
# If missing environment variable
kubectl set env deployment/<agent-id>-deployment \
  -n ai-agents MISSING_VAR=value

# If resource limits too low
kubectl patch deployment <agent-id>-deployment -n ai-agents \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","resources":{"limits":{"memory":"2Gi"}}}]}}}}'

# Restart
kubectl rollout restart deployment/<agent-id>-deployment -n ai-agents
```

#### Issue 2: High Error Rate

**Diagnosis:**
```bash
# Check error rate by agent
# In Prometheus: sum by (agent_id) (rate(agent_errors_total[5m]))

# Check logs for errors
kubectl logs -n ai-agents -l role=agent | grep ERROR

# Check Anthropic API status
curl https://status.anthropic.com/api/v2/status.json
```

**Solutions:**
- **Invalid API Key**: Rotate in Vault, restart agents
- **Rate Limiting**: Scale down temporarily, request limit increase
- **Database Issues**: Check PostgreSQL health, restart if needed

#### Issue 3: Performance Degradation

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n ai-agents --sort-by=cpu
kubectl top nodes

# Check response times in Grafana
# Query: histogram_quantile(0.95, sum(rate(agent_processing_seconds_bucket[5m])) by (le))
```

**Solutions:**
```bash
# Scale horizontally
kubectl scale deployment <agent-id>-deployment -n ai-agents --replicas=10

# Scale vertically (increase resources)
kubectl patch deployment <agent-id>-deployment -n ai-agents \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","resources":{"requests":{"cpu":"1","memory":"1Gi"}}}]}}}}'
```

### 4.2 Emergency Procedures

**Emergency Shutdown:**
```bash
# Scale all agents to zero
kubectl scale deployment --all -n ai-agents --replicas=0

# Stop accepting new requests
kubectl scale deployment nginx-gateway -n ai-agents --replicas=0
```

**Emergency Rollback:**
```bash
# Rollback specific agent
kubectl rollout undo deployment/<agent-id>-deployment -n ai-agents

# Rollback to specific revision
kubectl rollout undo deployment/<agent-id>-deployment \
  -n ai-agents --to-revision=2
```

**Complete Platform Recovery:**
```bash
# If complete cluster failure, follow disaster recovery:
# 1. Provision new cluster
# 2. Restore Vault from snapshot
# 3. Restore database from backup
# 4. Redeploy platform
# See RUNBOOK.md for detailed steps
```

---

## Module 5: Security Management (45 minutes)

### 5.1 Secrets Management with Vault

**Initialize Vault:**
```bash
cd security/vault-config
./vault-init.sh

# Save root token and unseal keys securely!
```

**Add Secrets:**
```bash
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='your-root-token'

# Add API key
vault kv put secret/agents/anthropic \
  api_key="${ANTHROPIC_API_KEY}"

# Add database credentials
vault kv put secret/agents/database \
  password="${DB_PASSWORD}"
```

**Retrieve Secrets:**
```bash
# Get API key
vault kv get secret/agents/anthropic

# Get specific field
vault kv get -field=api_key secret/agents/anthropic
```

**Rotate Secrets:**
```bash
# Update secret
vault kv put secret/agents/anthropic \
  api_key="${NEW_API_KEY}"

# Restart agents to pick up new secret
kubectl rollout restart deployment -n ai-agents --all
```

### 5.2 User Authentication

**Create User Token:**
```python
from auth_middleware import AuthManager

auth = AuthManager(jwt_secret="your-secret", redis_client=redis_client)

token = auth.create_token(
    user_id="user123",
    roles=["developer"],
    permissions=["agent:execute", "agent:view"]
)
```

**Create API Key:**
```python
from auth_middleware import APIKeyAuth

api_key_auth = APIKeyAuth(redis_client)

api_key = api_key_auth.create_api_key(
    user_id="user123",
    name="Production API Key",
    permissions=["agent:execute"]
)
```

### 5.3 Security Audit

**Review Access Logs:**
```bash
# Check authentication failures
kubectl logs -n ai-agents -l app=api-gateway | grep "401\|403"

# Review Vault audit logs
vault audit list
```

**Run Security Scan:**
```bash
cd security/scans
./run_vulnerability_scan.sh
```

---

## Module 6: Advanced Operations (60 minutes)

### 6.1 Updating Agents

**Rolling Update:**
```bash
# Build new image
cd generated-agents/business_plan_agent_009
docker build -t ghcr.io/your-org/business-plan-agent-009:v2.0.0 .
docker push ghcr.io/your-org/business-plan-agent-009:v2.0.0

# Update deployment
kubectl set image deployment/business-plan-agent-009-deployment \
  business-plan-agent-009=ghcr.io/your-org/business-plan-agent-009:v2.0.0 \
  -n ai-agents

# Watch rollout
kubectl rollout status deployment/business-plan-agent-009-deployment -n ai-agents
```

**Blue-Green Deployment:**
```bash
# Deploy new version alongside old
kubectl apply -f agent-v2-deployment.yaml

# Test new version
curl http://agent-v2-service/health

# Switch traffic
kubectl patch ingress agents-ingress -n ai-agents \
  --type=json -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "agent-v2-service"}]'
```

### 6.2 Scaling Strategies

**Horizontal Pod Autoscaling:**
```yaml
# HPA is pre-configured, but can be adjusted:
kubectl patch hpa business-plan-agent-009-hpa -n ai-agents \
  -p '{"spec":{"minReplicas":3,"maxReplicas":20}}'
```

**Cluster Autoscaling:**
```bash
# Configure cluster autoscaler for AWS
kubectl apply -f infrastructure/kubernetes/cluster-autoscaler.yaml
```

### 6.3 Performance Optimization

**Database Optimization:**
```bash
# Connect to database
kubectl exec -it -n ai-agents postgres-0 -- psql -U agents_admin agents_db

# Check slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

# Vacuum and analyze
VACUUM ANALYZE;
```

**Cache Optimization:**
```bash
# Check Redis cache hit rate
kubectl exec -it -n ai-agents redis-0 -- redis-cli INFO stats | grep hit

# Clear cache if needed
kubectl exec -it -n ai-agents redis-0 -- redis-cli FLUSHALL
```

---

## Module 7: Cost Management (30 minutes)

### 7.1 Monitoring Costs

**View Cost Dashboard:**
- Grafana Dashboard: "Cost Analysis"
- Shows: API costs, infrastructure costs, trends

**Cost Breakdown:**
- **Infrastructure**: $3,100-5,100/month (fixed)
- **API Calls**: Variable based on usage
  - $0.012 per request (Claude 3.5 Sonnet)
  - Monitor in Grafana

### 7.2 Cost Optimization

**Strategies:**
1. **Caching**: Reduce repeated API calls
2. **Rate Limiting**: Prevent abuse
3. **Right-sizing**: Optimize resource requests
4. **Scheduling**: Scale down during off-hours

**Implement Cost Alerts:**
```yaml
# Add to prometheus-rules/alerts.yaml
- alert: HighDailyCost
  expr: sum(increase(agent_requests_total[1d])) * 0.012 > 1000
  for: 1h
  annotations:
    summary: "Daily API cost exceeding $1000"
```

---

## Module 8: Certification Test

### Knowledge Check

**Section A: Platform Architecture (10 questions)**
1. How many AI agents are in the platform?
2. Name 5 core components of the platform
3. What database is used for persistent storage?
4. What is used for secrets management?
5. What monitoring tools are included?

**Section B: Operations (10 questions)**
1. What command scales an agent to 5 replicas?
2. How do you view logs for a specific agent?
3. What's the command to restart an agent?
4. How do you check pod health?
5. What's the morning checklist?

**Section C: Troubleshooting (5 questions)**
1. Agent in CrashLoopBackOff - what do you check first?
2. High error rate alert - what are 3 possible causes?
3. How do you rollback a deployment?
4. Where do you check Anthropic API status?
5. What's the emergency shutdown command?

**Section D: Practical Exercise**
Complete a hands-on exercise:
1. Deploy a new agent version
2. Scale it to 10 replicas
3. Monitor its performance
4. Rollback if issues occur
5. Document the process

### Passing Score
- **Required**: 80% (20/25 questions correct)
- **Practical**: Must complete successfully

---

## Additional Resources

### Documentation
- Full Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Operations Runbook: `RUNBOOK.md`
- API Documentation: `docs/api/`

### Support Channels
- Slack: #ai-agents-support
- Email: support@your-company.com
- Emergency: PagerDuty

### Continuing Education
- Advanced Kubernetes course
- Anthropic API deep dive
- Security best practices
- Cost optimization workshop

---

## Appendix: Quick Reference

### Essential Commands
```bash
# Health check
./infrastructure/scripts/health_check.py

# Scale agent
kubectl scale deployment <agent>-deployment -n ai-agents --replicas=N

# View logs
kubectl logs -n ai-agents -l app=<agent-id> --tail=100

# Restart agent
kubectl rollout restart deployment/<agent>-deployment -n ai-agents

# Check resources
kubectl top pods -n ai-agents
kubectl top nodes

# Rollback
kubectl rollout undo deployment/<agent>-deployment -n ai-agents
```

### Key Metrics
- Error rate: < 1%
- Response time P95: < 3s
- Uptime: > 99.9%
- CPU usage: < 70%
- Memory usage: < 70%

### Emergency Contacts
- On-call: PagerDuty
- Platform Lead: @platform-lead
- Security: security@company.com

---

**Training Manual Version**: 1.0
**Last Updated**: 2025-01-15
**Next Review**: 2025-04-15
