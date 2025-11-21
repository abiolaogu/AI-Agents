# 🤖 AI Agents Platform - 1,500 Production-Ready AI Agents

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Production Ready](https://img.shields.io/badge/status-95%25%20production%20ready-brightgreen.svg)]()
[![Agents](https://img.shields.io/badge/agents-1500-blueviolet.svg)]()
[![Documentation](https://img.shields.io/badge/docs-complete-success.svg)](docs/)

This repository contains a comprehensive, enterprise-grade multi-agent AI platform with **1,500 specialized agents** powered by Anthropic Claude 3.5 Sonnet. Designed as a complete business automation solution with production-ready deployment, comprehensive monitoring, and enterprise security.

## 🚀 Project Overview

A cloud-native, microservices-based system providing 1,500 specialized AI agents across 29 business categories. Each agent is a production-ready FastAPI microservice with Docker containerization, Kubernetes orchestration, and complete observability.

**Key Highlights:**
- **Agents:** 1,500 pre-built specialized agents across 29 business categories
- **Architecture:** Kubernetes, Docker, FastAPI microservices
- **AI Model:** Anthropic Claude 3.5 Sonnet integration
- **Infrastructure:** Complete K8s manifests, monitoring stack, security policies
- **Testing:** Unit, integration, load, and E2E tests
- **Documentation:** Training manuals, video scripts, API docs, runbooks
- **Installation:** One-command Docker Compose setup
- **Security:** Vault, JWT auth, network policies, vulnerability scanning
- **Monitoring:** Prometheus, Grafana, Loki log aggregation

## 📚 Documentation

**New to the platform?** Start here:
1. **[Installation Guide](installation/README.md)** - One-command installation (5 minutes)
2. **[User Guide](docs/training/03_ENDUSER_TRAINING_MANUAL.md)** - For end users
3. **[Developer Guide](docs/training/02_DEVELOPER_TRAINING_MANUAL.md)** - API integration
4. **[Admin Guide](docs/training/01_ADMIN_TRAINING_MANUAL.md)** - Platform management
5. **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
6. **[Operations Runbook](RUNBOOK.md)** - Daily operations & incident response
7. **[Technical Documentation](docs/technical/TECHNICAL_DOCUMENTATION.md)** - Complete technical reference
8. **[Production Readiness](PRODUCTION_READINESS.md)** - Readiness assessment
9. **[Video Scripts](docs/videos/VIDEO_SCRIPTS.md)** - Tutorial scripts
10. **[Preview Dashboard](preview/index.html)** - Interactive HTML preview

## 🚀 Quick Start

### Option 1: One-Command Installation (Recommended)

```bash
git clone https://github.com/your-org/AI-Agents.git
cd AI-Agents/installation

# Configure environment
cp .env.template .env
nano .env  # Add your ANTHROPIC_API_KEY

# Install everything
chmod +x install.sh
./install.sh
```

**What you get:**
- Complete platform running in Docker
- Business Plan Agent ready at http://localhost:8209
- Grafana dashboard at http://localhost:3000
- Prometheus at http://localhost:9090
- All infrastructure services (Vault, Consul, Redis, PostgreSQL)

### Option 2: Kubernetes Production Deployment

```bash
cd infrastructure/scripts
./deploy.sh production full
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions.

### Running Tests

-   **Unit Tests:**
    ```bash
    ./scripts/run_tests.sh
    ```
-   **End-to-End Test:**
    Ensure the services are running in Docker (`docker compose up`), then:
    ```bash
    ./scripts/run_e2e_test.py
    ```

## Deployment

This project is configured for deployment on Kubernetes.

1.  **Build and Push Images:** Build the Docker images and push them to your container registry.
2.  **Apply Manifests:** Update the image placeholders in the `k8s/` files and apply them to your cluster:
    ```bash
    kubectl apply -f k8s/
    ```

## Project Structure

-   `docs/`: All project documentation
    -   `guides/`: User, admin, and developer guides
    -   `project_docs/`: Technical specifications and architecture
-   `packages/`: Shared Python packages
-   `services/`: 700+ individual microservices for agents and orchestration
-   `web/`: React TypeScript frontend application
-   `k8s/`: Kubernetes manifest files
-   `scripts/`: Automation and testing scripts
-   `tests/`: Comprehensive test suites
-   `policies/`: Security and compliance policies

## Key Features

- ✅ **700+ Pre-Built Agents** across marketing, sales, operations, analytics, AIOps, support
- ✅ **Multi-Framework Support** (LangGraph, CrewAI, AutoGen)
- ✅ **Team Collaboration** with RBAC and shared workspaces
- ✅ **Enterprise Security** (OAuth 2.0, SAML, audit logging, vulnerability scanning)
- ✅ **Modern Frontends** (React web + Flutter mobile)
- ✅ **Real-Time Analytics** with comprehensive monitoring
- ✅ **API-First Design** with extensive REST API
- ✅ **Cloud-Native** deployment (Docker, Kubernetes, RunPod)

## Quick Links

- **Training**: [docs/guides/training/](./docs/guides/training/)
- **Administration**: [docs/guides/administration/](./docs/guides/administration/)
- **Development**: [docs/guides/development/](./docs/guides/development/)
- **API Documentation**: [docs/project_docs/api_documentation/](./docs/project_docs/api_documentation/)
- **Architecture**: [docs/project_docs/architecture/](./docs/project_docs/architecture/)
