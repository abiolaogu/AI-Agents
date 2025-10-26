# Technical Onboarding Guide

## 1. Introduction

Welcome to the development team for the multi-agent AI platform! This guide will walk you through setting up your development environment, understanding the monorepo structure, and creating your first agent.

## 2. Development Environment Setup

Our development environment is fully containerized using Docker to ensure consistency and eliminate "works on my machine" issues.

### Prerequisites
- Docker and Docker Compose
- Git
- An IDE of your choice (VS Code with the Dev Containers extension is recommended)

### Initial Setup
1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```
2.  **Start the development environment:**
    The project is configured to be used with VS Code Dev Containers. Simply open the cloned repository in VS Code and, when prompted, click "Reopen in Container". This will build the Docker containers and install all necessary dependencies.
3.  **Install shared packages:**
    To ensure that the microservices can access the shared code in the `packages/` directory, install them in editable mode. From the root of the repository, run:
    ```bash
    pip install -e packages/agent_framework
    ```

## 3. Monorepo Structure Overview

The repository is organized as a monorepo to facilitate code sharing and centralized dependency management.

-   `docs/`: Contains all project documentation, including the files you are reading now.
-   `packages/`: Shared Python packages that are used by multiple services.
    -   `agent_framework/`: The core framework, including the `BaseAgent` class.
-   `services/`: Houses the individual microservices.
    -   `orchestration_engine/`: Manages agent lifecycles and workflows.
    -   `seo_agent/`: A sample agent implementation.
-   `web/`: Source code for the frontend web application.
-   `scripts/`: Utility and automation scripts.
-   `terraform/`: Infrastructure as Code (IaC) for managing our GCP resources.

## 4. How to Create a New Agent

Creating a new agent involves scaffolding a new microservice and implementing the agent's specific logic.

1.  **Create the Service Directory:**
    Create a new directory for your agent under `services/`. For example: `services/my_new_agent/my_new_agent`.
2.  **Implement the Agent Class:**
    Inside the new directory, create an `agent.py` file. Your new agent class should inherit from `BaseAgent`.
    ```python
    # services/my_new_agent/my_new_agent/agent.py
    import logging
    from agent_framework.base_agent import BaseAgent

    class MyNewAgent(BaseAgent):
        def __init__(self, agent_id: str, logger: logging.Logger):
            super().__init__(agent_id, logger)

        def execute(self, task: dict) -> dict:
            self.logger.info(f"Executing task: {task}")
            # Your agent's logic goes here
            return {"status": "success", "result": "Task completed!"}
    ```
3.  **Create a Dockerfile:**
    Add a `Dockerfile` to the `services/my_new_agent/` directory. You can use the `Dockerfile` from `services/seo_agent/` as a template.
4.  **Register the Agent (Future Step):**
    In the future, you will register your agent with the `AgentManager` in the orchestration engine. For now, you can test it standalone by adding an `if __name__ == '__main__':` block, similar to the `seo_agent`.
5.  **Add Documentation:**
    Create a `README.md` within your agent's directory explaining its purpose, the tasks it can handle, and any required configuration.
