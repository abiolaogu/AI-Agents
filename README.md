# AI Agents Platform - 700+ AI Agents

This repository contains a comprehensive, enterprise-grade multi-agent AI platform with 700+ specialized agents. Designed as a complete business operations solution with team collaboration, multi-framework support, and production-ready deployment.

## Project Overview

A cloud-native, microservices-based system orchestrating 700+ specialized AI agents across multiple frameworks (LangGraph, CrewAI, AutoGen) for various business domains including marketing, sales, operations, analytics, and more.

- **Architecture:** Microservices, Event-Driven (Celery), Docker, Kubernetes, RunPod Serverless
- **Technology:** Python, FastAPI, React, TypeScript, Flutter, Redis, PostgreSQL, MongoDB
- **Agents:** 700+ pre-built specialized agents across 7 major categories
- **Security:** OAuth 2.0, SAML, RBAC, comprehensive vulnerability scanning
- **Frontend:** React TypeScript web app + Flutter mobile app (iOS/Android)

## 📚 Documentation

**New to the platform?** Start here:
1. **[00_START_HERE.md](./00_START_HERE.md)** - Quick orientation guide
2. **[PLATFORM_GUIDE.md](./PLATFORM_GUIDE.md)** - Comprehensive unified documentation
3. **[docs/guides/](./docs/guides/)** - Detailed guides by topic

## Getting Started

### Local Development

1.  **Prerequisites:** Docker, Docker Compose.
2.  **Build and Run:**
    ```bash
    sudo docker compose up --build -d
    ```
3.  **Access the API:** The orchestration engine API will be available at `http://localhost:5000`.

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
