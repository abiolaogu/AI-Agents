# AI Agents Platform - Installation Guide

## Quick Start (5 Minutes)

### Prerequisites
- Docker 20.10+
- Docker Compose v2.0+
- 8GB RAM available
- Anthropic API key

### Installation

```bash
# 1. Clone repository
git clone https://github.com/your-org/AI-Agents.git
cd AI-Agents/installation

# 2. Configure environment
cp .env.template .env
nano .env  # Add your ANTHROPIC_API_KEY

# 3. Run installer
chmod +x install.sh
./install.sh
```

That's it! The platform will be running in 3-5 minutes.

---

## What Gets Installed

### Core Services
- **Consul**: Configuration management (port 8500)
- **Vault**: Secrets management (port 8200)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache (port 6379)
- **Nginx**: API Gateway (port 80)

### Monitoring
- **Prometheus**: Metrics (port 9090)
- **Grafana**: Dashboards (port 3000)
- **Loki**: Log aggregation (port 3100)

### Agents
- **Business Plan Agent**: Sample agent (port 8209)
- More agents can be added by editing docker-compose.full.yml

---

## Testing Your Installation

### 1. Check Service Health

```bash
# All services
docker-compose -f docker-compose.full.yml ps

# Should show all services as "Up" and "healthy"
```

### 2. Test Business Plan Agent

```bash
curl -X POST http://localhost:8209/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a one-page business plan for a mobile app startup"
  }'
```

Expected response:
```json
{
  "result": "# Executive Summary\n\nBusiness Name: ...",
  "metadata": {
    "agent_id": "business-plan-agent-009",
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 1234
  },
  "processing_time_ms": 3456.78
}
```

### 3. Access Monitoring

**Grafana Dashboard:**
- URL: http://localhost:3000
- Username: admin
- Password: admin (or value from .env)

**Prometheus:**
- URL: http://localhost:9090
- Query: `agent_requests_total`

---

## Adding More Agents

### Method 1: Edit docker-compose.full.yml

Uncomment additional agents in the compose file:

```yaml
marketing-agent:
  build:
    context: ../generated-agents/marketing_agent_001
  ports:
    - "8201:8201"
  environment:
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    # ... other config
  networks:
    - ai-agents-network
```

Restart:
```bash
docker-compose -f docker-compose.full.yml up -d marketing-agent
```

### Method 2: Use Kubernetes

For deploying all 1,500 agents, use Kubernetes:
```bash
cd ../infrastructure/scripts
./deploy.sh production full
```

---

## Management Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.full.yml logs -f

# Specific service
docker-compose -f docker-compose.full.yml logs -f business-plan-agent
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.full.yml restart

# Specific service
docker-compose -f docker-compose.full.yml restart business-plan-agent
```

### Stop Platform
```bash
docker-compose -f docker-compose.full.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.full.yml down -v
```

### Update Agents
```bash
# Rebuild agent image
docker-compose -f docker-compose.full.yml build business-plan-agent

# Restart with new image
docker-compose -f docker-compose.full.yml up -d business-plan-agent
```

---

## Troubleshooting

### Issue: Services won't start

**Check Docker resources:**
```bash
docker system df
docker system prune  # Clean up if needed
```

**Check logs:**
```bash
docker-compose -f docker-compose.full.yml logs
```

### Issue: Agent returns errors

**Check API key:**
```bash
# Verify key is set
docker-compose -f docker-compose.full.yml exec business-plan-agent env | grep ANTHROPIC
```

**Check agent logs:**
```bash
docker-compose -f docker-compose.full.yml logs business-plan-agent
```

### Issue: Can't access services

**Check ports are not in use:**
```bash
# On Linux/Mac
lsof -i :8209
lsof -i :3000

# On Windows
netstat -ano | findstr :8209
```

**Check firewall:**
```bash
# Allow ports
sudo ufw allow 80
sudo ufw allow 3000
sudo ufw allow 8209
sudo ufw allow 9090
```

---

## Production Deployment

This Docker Compose setup is for **development and testing only**.

For production, use Kubernetes:
1. See `DEPLOYMENT_GUIDE.md`
2. Use infrastructure/kubernetes manifests
3. Follow security best practices
4. Configure proper secrets management
5. Set up monitoring and alerting

---

## Uninstallation

### Remove containers and images
```bash
docker-compose -f docker-compose.full.yml down --rmi all

# Remove volumes (deletes all data!)
docker volume rm $(docker volume ls -q | grep ai-agents)
```

---

## Getting Help

- **Documentation**: ../docs/
- **Training Manuals**: ../docs/training/
- **Support**: support@your-company.com
- **Issues**: https://github.com/your-org/AI-Agents/issues

---

## What's Next?

1. **Explore Agents**: Try different agents from the 1,500 available
2. **Read Documentation**: Check docs/training/ for detailed guides
3. **Deploy to Production**: Follow DEPLOYMENT_GUIDE.md
4. **Monitor Performance**: Use Grafana dashboards
5. **Scale Up**: Add more agents as needed

---

**Quick Reference:**

| Service | URL | Credentials |
|---------|-----|-------------|
| API Gateway | http://localhost | - |
| Business Plan Agent | http://localhost:8209 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Consul | http://localhost:8500 | - |
| Vault | http://localhost:8200 | dev-root-token |
