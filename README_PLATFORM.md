# AI Agents Platform - 700+ Specialized AI Agents

🤖 **The Real Magic:** Multiple agents collaborating as teams, not working alone!

[![Security Scan](https://github.com/abiolaogu/AI-Agents/workflows/Security%20Scanning/badge.svg)](https://github.com/abiolaogu/AI-Agents/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

A comprehensive multi-agent platform featuring **701 specialized AI agents** across **14 business domains** with built-in team collaboration, governance, and serverless deployment.

### Key Features

- ✨ **701 Specialized Agents** across 14 categories
- 🤝 **Team Collaboration** - agents work together on complex tasks
- 🎯 **5 Execution Strategies** - Sequential, Parallel, Consensus, Leader-Follower, Pipeline
- 🔐 **Policy-as-Code** governance with OPA
- 🚀 **RunPod Serverless** deployment
- 🧪 **Comprehensive Testing** - Unit, Integration, E2E
- 🛡️ **Security-First** - Vulnerability scanning, SAST, secret detection
- 📊 **Observable** - Metrics, logging, tracing
- 🌍 **Scalable** - Handle 10,000+ concurrent executions

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- OPA (Open Policy Agent)

### Installation

```bash
# Clone repository
git clone https://github.com/abiolaogu/AI-Agents.git
cd AI-Agents

# Install Python dependencies
pip install -r requirements-serverless.txt

# Install agent framework
pip install -e packages/agent_framework
pip install -e packages/integration_framework

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Generate agent definitions (if not already done)
python scripts/generate_agent_definitions.py agents/definitions

# Run tests
pytest tests/ -v
```

### Local Development

```bash
# Start all services
docker-compose up -d

# Check agent definitions loaded
python -c "
from pathlib import Path
from agent_framework.agent_loader import AgentDefinitionLoader

loader = AgentDefinitionLoader(Path('agents/definitions'))
loader.load_all_definitions()
print(f'✅ Loaded {len(loader.definitions)} agent definitions')
print(f'📊 Categories: {loader.count_by_category()}')
"

# Test single agent execution
python services/orchestration_engine/orchestration_engine/serverless_handler.py test_agent

# Test team collaboration
python services/orchestration_engine/orchestration_engine/serverless_handler.py test_team
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│   API Gateway (RunPod Serverless)          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│   Orchestration Engine                      │
│   ┌──────────┬───────────┬──────────────┐  │
│   │ Team Mgr │ Registry  │ OPA Enforcer │  │
│   └──────────┴───────────┴──────────────┘  │
└────────────────┬────────────────────────────┘
                 │
     ┌───────────┼───────────┬────────────┐
     │           │           │            │
┌────▼───┐  ┌───▼───┐  ┌───▼───┐   ┌───▼───┐
│Agent   │  │Agent  │  │Agent  │...│Agent  │
│Runtime │  │Runtime│  │Runtime│   │Pool   │
│Pod 1   │  │Pod 2  │  │Pod 3  │   │(701)  │
└────────┘  └───────┘  └───────┘   └───────┘
```

See [docs/ARCHITECTURE_700_AGENTS.md](docs/ARCHITECTURE_700_AGENTS.md) for detailed architecture.

---

## 14 Agent Categories (701 Agents)

| Category | Agents | Description |
|----------|--------|-------------|
| **Business Operations** | 50 | Executive summaries, meeting notes, OKR planning, risk management |
| **Sales & Marketing** | 50 | Lead qualification, content creation, SEO, campaigns |
| **Customer Support** | 50 | Tier-1 support, troubleshooting, onboarding, CSAT surveys |
| **Finance & Legal** | 50 | Invoicing, budgeting, contract drafting, compliance |
| **HR & People** | 50 | Job descriptions, recruiting, onboarding, performance reviews |
| **Product & Tech** | 50 | PRDs, user stories, release notes, bug triage |
| **Retail & eCommerce** | 50 | Product descriptions, inventory, merchandising, reviews |
| **Healthcare & Wellness** | 50 | Appointment scheduling, patient education, billing |
| **Education & Training** | 50 | Curriculum design, lesson plans, quizzes, feedback |
| **Real Estate** | 50 | Property listings, market analysis, staging, contracts |
| **Logistics & Manufacturing** | 50 | Order routing, inventory, production scheduling, quality control |
| **Creators & Media** | 50 | Content ideas, scriptwriting, social posts, newsletters |
| **Personal Productivity** | 50 | Daily planning, habit tracking, email drafts, meal planning |
| **Personal Growth** | 51 | Life vision, goal setting, journaling, creativity prompts |

**Total: 701 specialized agents** 🎯

---

## Team Collaboration Examples

### Example 1: Quarterly Report Generation

```python
from agent_framework.team import Team, TeamConfiguration, TeamMember, TeamStrategy

# Create reporting team
config = TeamConfiguration(
    team_id="q4_report_team",
    name="Q4 Report Team",
    description="Collaborative quarterly reporting",
    members=[
        TeamMember(agent_id="executive_summary_agent_001", role="summarizer", priority=1),
        TeamMember(agent_id="kpi_dashboard_narrator_agent_011", role="analyst", priority=2),
        TeamMember(agent_id="financial_narrative_agent_156", role="finance", priority=3)
    ],
    strategy=TeamStrategy.SEQUENTIAL,
    shared_context={"quarter": "Q4 2024", "company": "Acme Corp"}
)

team = Team(config, agent_registry)

# Execute collaborative task
result = team.execute(
    task={"data_sources": ["financials.csv", "kpis.json"]},
    user_id="ceo@acme.com"
)

print(f"✅ Report generated by {result.agents_executed} agents in {result.execution_time_ms}ms")
```

### Example 2: Customer Onboarding Pipeline

```python
# Pipeline strategy: Each agent's output feeds into next
config = TeamConfiguration(
    team_id="onboarding_pipeline",
    name="Customer Onboarding Pipeline",
    members=[
        TeamMember(agent_id="onboarding_wizard_agent_103", priority=3),
        TeamMember(agent_id="product_tour_agent_104", priority=2),
        TeamMember(agent_id="feature_education_agent_116", priority=1)
    ],
    strategy=TeamStrategy.PIPELINE
)

team = Team(config, agent_registry)
result = team.execute(task={"customer_id": "cust_123"})
```

### Example 3: Parallel Market Research

```python
# Parallel strategy: All agents work simultaneously
config = TeamConfiguration(
    team_id="market_research",
    name="Market Research Team",
    members=[
        TeamMember(agent_id="competitor_monitoring_agent_018", priority=1),
        TeamMember(agent_id="macro_trends_agent_038", priority=1),
        TeamMember(agent_id="social_listening_agent_090", priority=1)
    ],
    strategy=TeamStrategy.PARALLEL
)

team = Team(config, agent_registry)
result = team.execute(task={"market": "AI/ML SaaS"})
```

---

## Deployment

### RunPod Serverless

```bash
# Build container
docker build -f Dockerfile.runpod -t ai-agents-platform:latest .

# Test locally
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/agents:/app/agents \
  ai-agents-platform:latest

# Deploy to RunPod
runpod deploy --config runpod-config.yaml
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -l app=ai-agents

# Port forward for testing
kubectl port-forward svc/orchestration-engine 8000:8000
```

### Docker Compose (Development)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f orchestration-engine

# Scale agent workers
docker-compose up -d --scale worker=5

# Stop
docker-compose down
```

---

## API Usage

### Execute Single Agent

```bash
curl -X POST http://localhost:8000/v1/agents/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "agent_id": "executive_summary_agent_001",
    "task": {
      "task_description": "Summarize our Q4 earnings report"
    },
    "user_id": "user_123"
  }'
```

### Execute Team

```bash
curl -X POST http://localhost:8000/v1/teams/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "team": {
      "name": "Report Team",
      "strategy": "sequential",
      "members": [
        {"agent_id": "executive_summary_agent_001", "role": "leader", "priority": 1},
        {"agent_id": "kpi_dashboard_narrator_agent_011", "role": "analyst", "priority": 2}
      ]
    },
    "task": {
      "task_description": "Create quarterly report"
    }
  }'
```

### List Agents

```bash
# List all agents
curl http://localhost:8000/v1/agents

# Filter by category
curl http://localhost:8000/v1/agents?category=business_ops

# Filter by capability
curl http://localhost:8000/v1/agents?capability=text_summarization
```

---

## Governance & Security

### OPA Policies

All agent executions are governed by policies:

```bash
# Test policy locally
opa test policies/ -v

# Check policy for specific execution
curl -X POST http://localhost:8181/v1/data/agents/access/allow \
  -d '{
    "input": {
      "user": {"id": "user_123", "roles": ["user"]},
      "agent": {"agent_id": "executive_summary_agent_001", "category": "business_ops"}
    }
  }'
```

### Security Scanning

```bash
# Run all security scans
./scripts/security-scan.sh

# Individual scans
trivy fs .
bandit -r packages/ services/
semgrep --config=auto
```

---

## Testing

### Run All Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (requires services running)
pytest tests/test_team_collaboration.py -v --tb=short

# Coverage report
pytest --cov=packages --cov=services --cov-report=html
```

### Test Specific Features

```bash
# Test team collaboration
pytest tests/test_team_collaboration.py::TestSequentialExecution -v

# Test agent loading
pytest tests/test_agent_loader.py -v

# Test policies
opa test policies/ -v
```

---

## Monitoring

### Metrics

```python
from agent_framework import AgentRegistry

registry = AgentRegistry()
agent = registry.get_agent("executive_summary_agent_001")

# Get metrics
metrics = agent.get_metrics()
print(f"""
Total Executions: {metrics['total_executions']}
Total Tokens: {metrics['total_tokens_used']}
Avg Time: {metrics['average_execution_time_ms']}ms
Status: {metrics['current_status']}
""")
```

### Logs

All agents emit structured JSON logs:

```json
{
  "timestamp": "2024-11-14T10:30:45Z",
  "level": "INFO",
  "agent_id": "executive_summary_agent_001",
  "team_id": "team_xyz_789",
  "action": "execute",
  "duration_ms": 1250,
  "status": "success",
  "tokens_used": 1500
}
```

---

## Configuration

### Environment Variables

```bash
# LLM API Keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# Database
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://localhost:6379"

# OPA
export OPA_URL="http://localhost:8181"

# Performance
export PREWARM_AGENTS="executive_summary_agent_001,meeting_notes_agent_002"
export MAX_WORKERS=4
```

### Agent Configuration

Agents are defined in YAML:

```yaml
agent_id: "executive_summary_agent_001"
name: "Executive Summary Agent"
description: "Condenses long reports into 1-page briefs"
category: "business_ops"
capabilities: ["text_summarization"]

inputs:
  - name: "task_description"
    type: "text"
    required: true

outputs:
  - name: "result"
    type: "text"

llm:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 4096
  temperature: 0.7

prompt_template: "Summarize: {{task_description}}"
system_prompt: "You are an executive summary specialist..."
```

---

## Performance

### Benchmarks

- **Single Agent**: ~500ms average execution
- **Sequential Team (3 agents)**: ~1.8s
- **Parallel Team (3 agents)**: ~600ms
- **Pipeline Team (5 agents)**: ~3.2s
- **Cold Start**: <2s (RunPod serverless)
- **Concurrent Teams**: 100+ simultaneous

### Optimization Tips

1. **Prewarm Common Agents**: Set `PREWARM_AGENTS`
2. **Use Parallel Strategy**: When agents are independent
3. **Cache Agent Definitions**: Enabled by default
4. **Batch Requests**: Use workflow API for multiple tasks
5. **Monitor Metrics**: Track and optimize slow agents

---

## Troubleshooting

### Agent Not Found

```python
# List all loaded agents
from agent_framework.agent_loader import AgentDefinitionLoader
loader = AgentDefinitionLoader(Path("agents/definitions"))
loader.load_all_definitions()
print(loader.definitions.keys())
```

### Policy Denials

```bash
# Check user permissions
opa eval -d policies/ -i policy_input.json "data.agents.access.allow"

# View denial reasons
opa eval -d policies/ -i policy_input.json "data.agents.access.deny"
```

### Slow Execution

```python
# Check agent metrics
agent = registry.get_agent("slow_agent")
metrics = agent.get_metrics()
print(f"Average time: {metrics['average_execution_time_ms']}ms")

# Profile execution
import cProfile
cProfile.run('agent.execute(task)')
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding New Agents

1. Create agent definition YAML in `agents/definitions/`
2. Add to appropriate category directory
3. Test agent execution
4. Update documentation
5. Submit PR

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-agent-category

# Make changes
# ...

# Run tests
pytest tests/ -v

# Run security scans
./scripts/security-scan.sh

# Commit and push
git add .
git commit -m "feat: Add new agent category"
git push origin feature/new-agent-category
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE_700_AGENTS.md) - Detailed system architecture
- [API Documentation](docs/project_docs/api_documentation/API_Documentation.md) - Complete API reference
- [Training Manual](TRAINING_MANUAL.md) - User training guide
- [Admin Manual](ADMIN_MANUAL.md) - Administrator reference
- [Developer Manual](DEVELOPER_MANUAL.md) - Integration guide
- [Policy Guide](policies/README.md) - Governance policies

---

## License

MIT License - see [LICENSE](LICENSE) file

---

## Support

- 📧 Email: support@ai-agents.example.com
- 💬 Discord: [Join our community](https://discord.gg/ai-agents)
- 📚 Docs: [docs.ai-agents.example.com](https://docs.ai-agents.example.com)
- 🐛 Issues: [GitHub Issues](https://github.com/abiolaogu/AI-Agents/issues)

---

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com) - AI foundation
- [Open Policy Agent](https://www.openpolicyagent.org) - Policy engine
- [RunPod](https://www.runpod.io) - Serverless infrastructure
- [Flask](https://flask.palletsprojects.com) - Web framework
- [React](https://react.dev) - Frontend UI

---

**"The real magic happens when several of these agents collaborate as a team rather than living alone."** ✨

---

Made with ❤️ by the AI Agents Platform Team
