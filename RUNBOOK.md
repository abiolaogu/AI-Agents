# AI Agents Platform - Operations Runbook

## Quick Reference

### Emergency Contacts
- **On-Call Engineer**: PagerDuty auto-page
- **Platform Team Lead**: @platform-lead on Slack
- **Security Team**: security@company.com
- **Anthropic Support**: support@anthropic.com

### Critical URLs
- Grafana: https://grafana.your-domain.com
- Prometheus: https://prometheus.your-domain.com
- AlertManager: https://alerts.your-domain.com
- API Gateway: https://api.agents.your-domain.com

---

## Incident Response Procedures

### Severity Definitions

**P0 - Critical (Response: Immediate)**
- Complete platform outage
- Data breach or security incident
- >50% of agents down
- Response time: < 5 minutes

**P1 - High (Response: 15 minutes)**
- Significant degradation (>25% agents affected)
- High error rate (>10%)
- Performance degradation (>5x normal latency)
- Security vulnerability discovered

**P2 - Medium (Response: 1 hour)**
- Individual agent failures
- Moderate performance issues
- Non-critical component failure

**P3 - Low (Response: Next business day)**
- Minor issues
- Feature requests
- Documentation updates

### Incident Response Workflow

1. **Acknowledge**
   - Acknowledge alert in PagerDuty
   - Join incident Slack channel: #incident-YYYY-MM-DD
   - Update status page

2. **Assess**
   - Check Grafana dashboards
   - Review recent deployments
   - Check error logs
   - Determine severity

3. **Communicate**
   - Post initial assessment in incident channel
   - Update status page
   - Notify stakeholders if P0/P1

4. **Mitigate**
   - Follow specific runbook procedures
   - Implement temporary fixes if needed
   - Document all actions taken

5. **Resolve**
   - Implement permanent fix
   - Verify resolution
   - Update status page
   - Close PagerDuty incident

6. **Post-Mortem** (for P0/P1)
   - Schedule post-mortem within 48 hours
   - Document timeline, impact, root cause
   - Create action items
   - Share learnings

---

## Alert Runbooks

### HighErrorRate Alert

**Alert**: Error rate > 5% for 5 minutes

**Investigation Steps**:
1. Check Grafana dashboard for affected agents
   ```bash
   # Query Prometheus
   curl "http://prometheus:9090/api/v1/query?query=sum%20by%20(agent_id)%20(rate(agent_errors_total[5m]))"
   ```

2. Check recent deployments
   ```bash
   kubectl rollout history deployment -n ai-agents | tail -10
   ```

3. Review error logs
   ```bash
   kubectl logs -n ai-agents -l role=agent --tail=100 | grep ERROR
   ```

**Common Causes & Fixes**:

- **Invalid API Keys**
  ```bash
  # Verify API key in Vault
  vault kv get secret/agents/anthropic

  # Rotate if needed
  vault kv put secret/agents/anthropic api_key="new-key"

  # Restart affected agents
  kubectl rollout restart deployment -n ai-agents -l category=affected_category
  ```

- **Anthropic API Rate Limiting**
  ```bash
  # Check rate limit status
  kubectl logs -n ai-agents -l role=agent | grep "rate_limit"

  # Temporary fix: Scale down to reduce load
  kubectl scale deployment --all -n ai-agents --replicas=1

  # Long-term: Request rate limit increase from Anthropic
  ```

- **Database Connection Errors**
  ```bash
  # Check PostgreSQL health
  kubectl get pods -n ai-agents -l app=postgres
  kubectl logs -n ai-agents -l app=postgres --tail=50

  # Restart PostgreSQL if needed
  kubectl rollout restart statefulset/postgres -n ai-agents
  ```

**Resolution Criteria**: Error rate < 1% for 10 minutes

---

### AgentDown Alert

**Alert**: Agent pod not responding to health checks

**Investigation Steps**:
1. Check pod status
   ```bash
   kubectl get pods -n ai-agents -l app=<agent-id>
   kubectl describe pod <pod-name> -n ai-agents
   ```

2. Check recent events
   ```bash
   kubectl get events -n ai-agents --sort-by='.lastTimestamp' | grep <agent-id>
   ```

3. Review pod logs
   ```bash
   kubectl logs <pod-name> -n ai-agents --previous  # Previous container
   kubectl logs <pod-name> -n ai-agents              # Current container
   ```

**Common Causes & Fixes**:

- **Image Pull Errors**
  ```bash
  # Check image pull secret
  kubectl get secrets -n ai-agents | grep regcred

  # Recreate secret if needed
  kubectl create secret docker-registry regcred \
    --docker-server=ghcr.io \
    --docker-username=<username> \
    --docker-password=<token> \
    -n ai-agents
  ```

- **Resource Limits**
  ```bash
  # Check if pod is OOMKilled
  kubectl get pod <pod-name> -n ai-agents -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'

  # Increase memory limit
  kubectl patch deployment <agent-id>-deployment -n ai-agents \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
  ```

- **Crash Loop BackOff**
  ```bash
  # Check logs for error
  kubectl logs <pod-name> -n ai-agents

  # Common issues:
  # - Missing environment variable
  # - Invalid configuration
  # - Dependency not available

  # Fix and restart
  kubectl rollout restart deployment/<agent-id>-deployment -n ai-agents
  ```

**Resolution Criteria**: Agent healthy and passing health checks

---

### HighResponseTime Alert

**Alert**: Average response time > 10 seconds for 5 minutes

**Investigation Steps**:
1. Check response time metrics
   ```bash
   # P95 response time by agent
   kubectl port-forward -n ai-agents-monitoring svc/prometheus 9090:9090
   # Query: histogram_quantile(0.95, sum(rate(agent_processing_seconds_bucket[5m])) by (le, agent_id))
   ```

2. Check resource utilization
   ```bash
   kubectl top pods -n ai-agents --sort-by=memory
   kubectl top nodes
   ```

3. Check for throttling
   ```bash
   kubectl logs -n ai-agents -l role=agent | grep -i "throttl\|timeout\|slow"
   ```

**Common Causes & Fixes**:

- **High CPU Usage**
  ```bash
  # Scale up replicas
  kubectl scale deployment <agent-id>-deployment -n ai-agents --replicas=5

  # Or increase CPU limits
  kubectl patch deployment <agent-id>-deployment -n ai-agents \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","resources":{"limits":{"cpu":"2"}}}]}}}}'
  ```

- **Database Slowness**
  ```bash
  # Check database queries
  kubectl exec -n ai-agents postgres-0 -- psql -U agents_admin agents_db \
    -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

  # Add indexes if needed
  # Increase database resources
  ```

- **Anthropic API Latency**
  ```bash
  # Check Anthropic status: https://status.anthropic.com

  # Implement timeout
  # Enable caching for repeated requests
  # Consider using batch API if available
  ```

**Resolution Criteria**: P95 response time < 5 seconds

---

### HighCPUUsage / HighMemoryUsage Alerts

**Alert**: CPU > 80% or Memory > 85% for 10 minutes

**Investigation Steps**:
1. Identify resource-hungry pods
   ```bash
   kubectl top pods -n ai-agents --sort-by=cpu
   kubectl top pods -n ai-agents --sort-by=memory
   ```

2. Check for memory leaks
   ```bash
   # Monitor memory over time
   kubectl logs <pod-name> -n ai-agents | grep -i "memory\|oom"
   ```

**Immediate Actions**:
```bash
# Scale horizontally
kubectl scale deployment <agent-id>-deployment -n ai-agents --replicas=5

# Or scale vertically
kubectl patch deployment <agent-id>-deployment -n ai-agents \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","resources":{"requests":{"cpu":"1","memory":"1Gi"},"limits":{"cpu":"2","memory":"2Gi"}}}]}}}}'
```

**Long-term Fixes**:
- Optimize code
- Implement caching
- Add resource-based HPA
- Investigate memory leaks

**Resolution Criteria**: Resource usage < 70%

---

### PodRestartingFrequently Alert

**Alert**: Pod restarted > 0.1 times per minute in last 15 minutes

**Investigation Steps**:
1. Check restart count
   ```bash
   kubectl get pods -n ai-agents -o wide
   kubectl describe pod <pod-name> -n ai-agents | grep -A 5 "State:"
   ```

2. Review logs from previous containers
   ```bash
   kubectl logs <pod-name> -n ai-agents --previous
   ```

**Common Causes**:
- Liveness probe failures
- OOMKills
- Application crashes
- Configuration errors

**Fixes**:
```bash
# Adjust liveness probe
kubectl patch deployment <agent-id>-deployment -n ai-agents \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"<agent-id>","livenessProbe":{"initialDelaySeconds":60,"periodSeconds":20}}]}}}}'

# Increase resources if OOMKilled
# Fix application bugs if crashing
```

**Resolution Criteria**: No restarts for 30 minutes

---

## Routine Operations

### Daily Tasks

**Morning Checks** (10 minutes)
```bash
# Check platform health
./infrastructure/scripts/health_check.py

# Review overnight alerts
kubectl logs -n ai-agents-monitoring deployment/alertmanager --since=12h | grep firing

# Check error rates
# Visit Grafana dashboard: https://grafana.your-domain.com/d/agents-overview
```

**End of Day** (5 minutes)
```bash
# Check any pending deployments
kubectl get deployments -n ai-agents -o wide

# Review day's metrics
# Note any concerning trends in Grafana
```

### Weekly Tasks

**Monday Morning** (30 minutes)
- Review previous week's metrics
- Check capacity trends
- Review cost dashboard
- Plan capacity adjustments

**Wednesday** (15 minutes)
- Update dependencies check
  ```bash
  # Check for updates
  kubectl get pods -n ai-agents -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u
  ```

**Friday** (20 minutes)
- Review security alerts
- Check certificate expiration
  ```bash
  kubectl get certificates -n ai-agents
  ```
- Backup verification

### Monthly Tasks

**First Monday** (2 hours)
- Security patches
- Dependency updates
- Capacity planning review
- Cost optimization review

**Third Monday** (1 hour)
- Secret rotation (if not automated)
  ```bash
  # Rotate database password
  # Rotate API keys
  # Update Vault secrets
  ```

**Last Friday** (1 hour)
- Disaster recovery drill
- Backup restoration test
- Documentation review

---

## Maintenance Procedures

### Rolling Update

```bash
# Update single agent
kubectl set image deployment/<agent-id>-deployment \
  <agent-id>=ghcr.io/your-org/<agent-id>:v2.0.0 \
  -n ai-agents

# Watch progress
kubectl rollout status deployment/<agent-id>-deployment -n ai-agents

# Verify
curl https://api.agents.your-domain.com/api/v1/agents/<agent-id>/health
```

### Database Maintenance

```bash
# Backup database
kubectl exec -n ai-agents postgres-0 -- pg_dump -U agents_admin agents_db > backup.sql

# Vacuum database
kubectl exec -n ai-agents postgres-0 -- psql -U agents_admin agents_db -c "VACUUM ANALYZE;"

# Check size
kubectl exec -n ai-agents postgres-0 -- psql -U agents_admin agents_db \
  -c "SELECT pg_size_pretty(pg_database_size('agents_db'));"
```

### Certificate Renewal

```bash
# Check expiration
kubectl get certificates -n ai-agents

# Force renewal if needed
kubectl delete certificate <cert-name> -n ai-agents
# cert-manager will recreate automatically
```

### Node Maintenance

```bash
# Drain node
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Perform maintenance (patch OS, upgrade, etc.)

# Uncordon node
kubectl uncordon <node-name>

# Verify
kubectl get nodes
```

---

## Disaster Recovery

### Backup Procedures

**Daily Automated Backups**:
- Kubernetes manifests: Stored in Git
- Vault snapshots: Automated via CronJob
- PostgreSQL dumps: Automated via CronJob
- Redis snapshots: Configured in redis.conf

**Manual Backup**:
```bash
# Full platform backup
./infrastructure/scripts/backup_platform.sh

# Verify backup
./infrastructure/scripts/verify_backup.sh
```

### Recovery Procedures

**Scenario 1: Complete Cluster Loss**
```bash
# 1. Provision new cluster
terraform apply

# 2. Restore Vault
vault operator raft snapshot restore backup.snap

# 3. Deploy platform
./infrastructure/scripts/deploy.sh production full

# 4. Restore database
kubectl exec -n ai-agents postgres-0 -- psql -U agents_admin agents_db < backup.sql

# 5. Verify
./infrastructure/scripts/health_check.py
```

**Scenario 2: Database Corruption**
```bash
# 1. Stop all agents
kubectl scale deployment --all -n ai-agents --replicas=0

# 2. Restore database
kubectl exec -n ai-agents postgres-0 -- dropdb agents_db
kubectl exec -n ai-agents postgres-0 -- createdb agents_db
kubectl exec -n ai-agents postgres-0 -- psql -U agents_admin agents_db < backup.sql

# 3. Start agents
kubectl scale deployment --all -n ai-agents --replicas=2

# 4. Verify
```

**Scenario 3: Compromised Secrets**
```bash
# 1. Rotate all secrets immediately
./security/vault-config/rotate_all_secrets.sh

# 2. Restart all agents to pick up new secrets
kubectl rollout restart deployment -n ai-agents --all

# 3. Audit access logs
# 4. Investigate breach
# 5. Update security policies
```

---

## Performance Tuning

### Optimize Agent Performance

```yaml
# Best practices for agent configuration
resources:
  requests:
    memory: "512Mi"  # Start conservative
    cpu: "500m"
  limits:
    memory: "2Gi"    # Allow burst
    cpu: "2"

# HPA configuration
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_agent_requests ON requests(agent_id, timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM requests WHERE agent_id = 'business_plan_agent_009';

-- Update statistics
VACUUM ANALYZE;
```

### Cache Configuration

```yaml
# Redis cache settings
redis:
  maxmemory: 2gb
  maxmemory-policy: allkeys-lru
  ttl: 3600  # 1 hour default
```

---

## Monitoring & Alerting

### Key Metrics to Watch

1. **Request Rate**: Should be steady during business hours
2. **Error Rate**: Should be < 1%
3. **Response Time**: P95 should be < 3 seconds
4. **Resource Usage**: Should be < 70% average
5. **Cost**: Should align with usage patterns

### Custom Alerts Setup

```yaml
# Add custom alert
- alert: CustomBusinessMetric
  expr: custom_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert fired"
    description: "Metric exceeded threshold"
```

### Dashboard Links

- **Platform Overview**: https://grafana.your-domain.com/d/agents-overview
- **Individual Agent**: https://grafana.your-domain.com/d/agent-detail?var-agent_id=<agent-id>
- **Cost Dashboard**: https://grafana.your-domain.com/d/cost-analysis
- **Security Dashboard**: https://grafana.your-domain.com/d/security

---

## Contact & Escalation

### Support Tiers

**Tier 1: DevOps Team**
- Slack: #devops-oncall
- Response: 15 minutes
- Scope: Platform operations, deployments

**Tier 2: Platform Engineering**
- Slack: #platform-eng
- Response: 30 minutes
- Scope: Infrastructure issues, architecture

**Tier 3: CTO Office**
- Email: cto@company.com
- Response: 1 hour
- Scope: Critical business impact

### External Vendors

**Anthropic**
- Support: support@anthropic.com
- Status: https://status.anthropic.com
- For: API issues, rate limits

**Cloud Provider (AWS/GCP/Azure)**
- Support Portal: [Provider-specific]
- For: Infrastructure issues

---

## Appendix

### Useful Commands Cheat Sheet

```bash
# Get all resources
kubectl get all -n ai-agents

# Watch pods
watch kubectl get pods -n ai-agents

# Logs with grep
kubectl logs -n ai-agents -l app=<agent-id> | grep ERROR

# Execute command in pod
kubectl exec -it <pod-name> -n ai-agents -- /bin/bash

# Port forward
kubectl port-forward -n ai-agents svc/<service-name> 8080:80

# Resource usage
kubectl top pods -n ai-agents
kubectl top nodes

# Describe for debugging
kubectl describe pod <pod-name> -n ai-agents

# Get events
kubectl get events -n ai-agents --sort-by='.lastTimestamp'
```

### Emergency Shutdown

```bash
#!/bin/bash
# Emergency platform shutdown
kubectl scale deployment --all -n ai-agents --replicas=0
kubectl scale statefulset --all -n ai-agents --replicas=0
echo "Platform shut down. To restart: kubectl scale deployment --all -n ai-agents --replicas=2"
```

### Quick Recovery

```bash
#!/bin/bash
# Quick recovery script
kubectl scale deployment --all -n ai-agents --replicas=2
sleep 30
./infrastructure/scripts/health_check.py
```

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-15 | DevOps | Initial runbook created |
| | | |

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Next Review**: 2025-04-15
