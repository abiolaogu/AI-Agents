# AI Agents Platform - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Infrastructure Requirements
- **Kubernetes Cluster**: v1.24+ with at least 3 nodes
- **Node Specifications** (per node):
  - CPU: 8 cores minimum, 16 cores recommended
  - RAM: 32 GB minimum, 64 GB recommended
  - Storage: 500 GB SSD
- **Load Balancer**: Cloud provider LB or MetalLB
- **DNS**: Domain configured for API access

### Software Requirements
- `kubectl` v1.24+
- `helm` v3.10+
- `docker` v20.10+
- `python` 3.11+
- `terraform` v1.5+ (for cloud provisioning)

### Access Requirements
- Kubernetes cluster admin access
- Docker registry credentials (e.g., GitHub Container Registry)
- Anthropic API key(s)
- Cloud provider credentials (AWS/GCP/Azure)

## Quick Start

### Local Development Setup

1. **Clone Repository**
```bash
git clone https://github.com/your-org/AI-Agents.git
cd AI-Agents
```

2. **Start Local Environment**
```bash
cd infrastructure/docker-compose
cp .env.template .env
# Edit .env with your API keys
docker-compose up -d
```

3. **Verify Services**
```bash
docker-compose ps
curl http://localhost:8209/health  # Test an agent
```

4. **Access Monitoring**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Consul: http://localhost:8500

## Production Deployment

### Phase 1: Infrastructure Setup

#### Step 1: Configure Cloud Provider (AWS Example)
```bash
cd infrastructure/terraform/aws

# Configure variables
cat > terraform.tfvars <<EOF
cluster_name = "ai-agents-prod"
region = "us-east-1"
node_count = 5
node_instance_type = "m5.2xlarge"
EOF

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

#### Step 2: Configure kubectl
```bash
aws eks update-kubeconfig --name ai-agents-prod --region us-east-1
kubectl get nodes
```

#### Step 3: Install Prerequisites
```bash
# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install nginx ingress controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install external secrets operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system --create-namespace
```

### Phase 2: Secrets Management

#### Step 1: Deploy Vault
```bash
cd infrastructure/kubernetes
kubectl apply -f vault-deployment.yaml

# Wait for Vault to be ready
kubectl wait --for=condition=ready pod -l app=vault -n ai-agents --timeout=300s
```

#### Step 2: Initialize Vault
```bash
cd ../../security/vault-config

# Port-forward to Vault
kubectl port-forward -n ai-agents svc/vault 8200:8200 &

# Initialize Vault
./vault-init.sh

# Save root token and unseal keys securely!
```

#### Step 3: Store Secrets
```bash
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='your-root-token'

# Add Anthropic API key
vault kv put secret/agents/anthropic \
  api_key="${ANTHROPIC_API_KEY}"

# Add database credentials
vault kv put secret/agents/database \
  password="${DB_PASSWORD}"
```

### Phase 3: Deploy Core Services

#### Step 1: Create Namespaces
```bash
cd infrastructure/kubernetes
kubectl apply -f namespace.yaml
```

#### Step 2: Configure Secrets
```bash
# Update secrets.yaml with actual values or use external-secrets
kubectl apply -f secrets.yaml
```

#### Step 3: Deploy Configuration
```bash
kubectl apply -f configmap.yaml
kubectl apply -f rbac.yaml
```

#### Step 4: Deploy Monitoring Stack
```bash
kubectl apply -f monitoring.yaml

# Wait for monitoring to be ready
kubectl wait --for=condition=ready pod -l app=prometheus \
  -n ai-agents-monitoring --timeout=300s
```

#### Step 5: Deploy Supporting Services
```bash
# Redis
kubectl apply -f redis-deployment.yaml

# PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=redis -n ai-agents --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgres -n ai-agents --timeout=300s
```

### Phase 4: Deploy Agents

#### Step 1: Build Agent Images
```bash
cd infrastructure/scripts

# Build all 1,500 agent images (this will take time!)
./build_all_agents.sh

# Or build in batches
./build_agents_batch.sh 1 100  # Build first 100 agents
```

#### Step 2: Push Images to Registry
```bash
# Login to registry
docker login ghcr.io

# Push images
./push_images.sh
```

#### Step 3: Generate Kubernetes Manifests
```bash
python3 generate_k8s_manifests.py --environment=production

# Review generated manifests
ls generated-manifests/
```

#### Step 4: Deploy Agents
```bash
# Deploy all agents using kustomize
kubectl apply -k generated-manifests/

# Or deploy in batches to avoid overwhelming the cluster
for i in {1..15}; do
  echo "Deploying batch $i..."
  kubectl apply -f generated-manifests/batch-$i/
  sleep 60
done
```

#### Step 5: Configure Ingress
```bash
# Update ingress.yaml with your domain
sed -i 's/yourdomain.com/actual-domain.com/g' ingress.yaml

kubectl apply -f ingress.yaml
```

### Phase 5: Verification

#### Step 1: Health Checks
```bash
cd infrastructure/scripts
python3 health_check.py
```

#### Step 2: Run Tests
```bash
cd ../../testing
pytest -v --environment=production
```

#### Step 3: Load Testing
```bash
# Test with locust
locust -f load/locustfile.py \
  --host=https://api.agents.your-domain.com \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m
```

## Configuration

### Environment Variables

Create `.env` file:
```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Infrastructure
CONSUL_HOST=consul-service
VAULT_ADDR=http://vault-service:8200
REDIS_HOST=redis-service
DB_HOST=postgres-service

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100

# Monitoring
GRAFANA_URL=https://grafana.your-domain.com
PROMETHEUS_URL=https://prometheus.your-domain.com
```

### Scaling Configuration

#### Horizontal Pod Autoscaling
```bash
# HPA is configured per agent in deployment templates
# Default: 2-10 replicas based on CPU/memory

# View HPA status
kubectl get hpa -n ai-agents

# Adjust HPA for specific agent
kubectl patch hpa business-plan-agent-009-hpa -n ai-agents \
  -p '{"spec":{"maxReplicas":20}}'
```

#### Cluster Autoscaling
```bash
# Configure cluster autoscaler (AWS example)
kubectl apply -f infrastructure/kubernetes/cluster-autoscaler.yaml
```

## Verification

### Check Deployment Status
```bash
# All namespaces
kubectl get pods --all-namespaces

# Agents namespace
kubectl get pods -n ai-agents

# Check if agents are ready
kubectl get deployments -n ai-agents
```

### Access Services
```bash
# Port-forward Grafana
kubectl port-forward -n ai-agents-monitoring svc/grafana 3000:3000

# Port-forward Prometheus
kubectl port-forward -n ai-agents-monitoring svc/prometheus 9090:9090

# Test agent endpoint
curl https://api.agents.your-domain.com/api/v1/agents/business-plan-agent-009/health
```

### View Logs
```bash
# View agent logs
kubectl logs -n ai-agents deployment/business-plan-agent-009-deployment -f

# View all agent logs
kubectl logs -n ai-agents -l role=agent --tail=100

# Query logs with Loki (if deployed)
kubectl port-forward -n ai-agents-monitoring svc/loki 3100:3100
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n ai-agents

# Common causes:
# - Image pull errors: Check registry credentials
# - Resource limits: Increase CPU/memory requests
# - Secret not found: Verify secrets are created
```

#### 2. High Error Rates
```bash
# Check Prometheus alerts
kubectl port-forward -n ai-agents-monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/alerts

# Check agent logs
kubectl logs -n ai-agents -l app=<agent-id> --tail=100

# Common causes:
# - Invalid API keys
# - Rate limiting from Anthropic
# - Database connection issues
```

#### 3. Performance Issues
```bash
# Check resource usage
kubectl top pods -n ai-agents
kubectl top nodes

# Check HPA status
kubectl get hpa -n ai-agents

# Scale specific agent manually if needed
kubectl scale deployment business-plan-agent-009-deployment \
  -n ai-agents --replicas=5
```

#### 4. Networking Issues
```bash
# Check network policies
kubectl get networkpolicies -n ai-agents

# Test connectivity between pods
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- /bin/bash
# Then test: curl http://redis-service:6379
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Rollback specific agent
kubectl rollout undo deployment/business-plan-agent-009-deployment -n ai-agents

# Check rollout history
kubectl rollout history deployment/business-plan-agent-009-deployment -n ai-agents
```

#### Emergency Scale Down
```bash
# Scale down all agents to zero
kubectl scale deployment --all -n ai-agents --replicas=0

# Scale back up
kubectl scale deployment --all -n ai-agents --replicas=2
```

#### Drain Node for Maintenance
```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# Perform maintenance
kubectl uncordon <node-name>
```

## Maintenance

### Regular Updates
```bash
# Update agent image
kubectl set image deployment/business-plan-agent-009-deployment \
  business-plan-agent-009=ghcr.io/your-org/business-plan-agent-009:v2.0.0 \
  -n ai-agents

# Watch rollout
kubectl rollout status deployment/business-plan-agent-009-deployment -n ai-agents
```

### Backup Procedures
```bash
# Backup Kubernetes resources
kubectl get all -n ai-agents -o yaml > backup-agents.yaml
kubectl get configmaps -n ai-agents -o yaml > backup-configs.yaml

# Backup Vault
vault operator raft snapshot save backup.snap

# Backup PostgreSQL
kubectl exec -n ai-agents postgres-0 -- pg_dump agents_db > backup-db.sql
```

### Cost Optimization
```bash
# View resource requests
kubectl describe pods -n ai-agents | grep -A 5 "Requests:"

# Identify underutilized agents
kubectl top pods -n ai-agents --sort-by=cpu

# Consider scaling down or removing unused agents
```

## Support

### Getting Help
- Documentation: https://docs.your-company.com/ai-agents
- Slack: #ai-agents-support
- Email: support@your-company.com
- On-call: PagerDuty escalation

### Escalation Path
1. Level 1: DevOps team (#devops-on-call)
2. Level 2: Platform engineering (#platform-eng)
3. Level 3: CTO office

## Next Steps

After successful deployment:
1. Set up continuous monitoring
2. Configure alerting rules
3. Schedule regular health checks
4. Plan capacity for growth
5. Document custom configurations
6. Train team on operations

## Appendix

### Useful Commands
```bash
# Get all resources in namespace
kubectl get all -n ai-agents

# Watch pod status
watch kubectl get pods -n ai-agents

# Get events
kubectl get events -n ai-agents --sort-by='.lastTimestamp'

# Exec into pod
kubectl exec -it <pod-name> -n ai-agents -- /bin/bash

# Copy files from pod
kubectl cp ai-agents/<pod-name>:/path/to/file ./local-file
```

### Performance Tuning
```yaml
# Example resource adjustments
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Monitoring Queries
```promql
# Total request rate
sum(rate(agent_requests_total[5m]))

# Error rate by agent
sum by (agent_id) (rate(agent_errors_total[5m]))

# P95 response time
histogram_quantile(0.95, sum(rate(agent_processing_seconds_bucket[5m])) by (le))
```
