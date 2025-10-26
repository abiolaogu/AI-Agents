# Technical Onboarding Guide

## 1. Introduction

Welcome to the development team for the multi-agent AI platform! This guide will walk you through setting up your development environment, understanding the monorepo structure, and creating your first agent.

## 2. Development Environment Setup

Our development environment is fully containerized using Docker and Docker Compose.

### Prerequisites
- Docker and Docker Compose
- Git
- An IDE of your choice (VS Code is recommended)

### Initial Setup
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
2.  **Build and Run the Environment:**
    ```bash
    sudo docker compose up --build -d
    ```
    This command will build all the service images and start the containers in the background.

## 3. Running Tests

We have a suite of tests to ensure code quality and system stability.

### Unit Tests
Our unit tests are written using `pytest`. You can run all unit tests with the provided script:
```bash
./scripts/run_tests.sh
```
This script will install dependencies and run the test suites for all services.

### End-to-End (E2E) Test
The E2E test validates the entire workflow, from API call to agent execution.
1.  Make sure the services are running (`sudo docker compose up -d`).
2.  Run the E2E test script:
    ```bash
    ./scripts/run_e2e_test.py
    ```

## 4. Monorepo Structure Overview

-   `docs/`: All project documentation.
-   `packages/`: Shared Python packages.
-   `services/`: Individual microservices.
-   `k8s/`: Kubernetes deployment files.
-   `scripts/`: Automation and testing scripts.

## 5. How to Create a New Agent

1.  **Scaffold the Service:** Create a new directory under `services/` (e.g., `services/my_agent`). Add a `Dockerfile`, `requirements.txt`, and `setup.py`.
2.  **Implement the Agent:** Create an `agent.py` with a class that inherits from `BaseAgent`.
3.  **Create the Service Entrypoint:** Create a `main.py` with a Flask app to expose an `/execute` endpoint.
4.  **Add Unit Tests:** Add a `tests/` directory with `pytest` tests for your new agent.
5.  **Integrate with Docker Compose:** Add your new service to the `docker-compose.yml` file.
6.  **Register with Orchestrator:** Add the new agent's service URL to the `orchestration_engine/main.py` registration block.
7.  **Update Test Scripts:** Add your new tests to the `scripts/run_tests.sh` script.
