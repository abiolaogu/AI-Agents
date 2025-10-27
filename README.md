# Multi-Agent AI Platform

This repository contains the source code for a comprehensive, enterprise-grade multi-agent AI platform. It is designed to serve as a complete business operations solution.

## Project Overview

This platform is a cloud-native, microservices-based system for orchestrating a large number of specialized AI agents across various business domains.

- **Architecture:** Microservices, Event-Driven (with Celery), running on Docker and Kubernetes.
- **Technology:** Python, Flask, Celery, Redis, Docker, Kubernetes.

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

-   `docs/`: All project documentation.
-   `packages/`: Shared Python packages.
-   `services/`: Individual microservices for agents and the orchestration engine.
-   `k8s/`: Kubernetes manifest files.
-   `scripts/`: Automation and testing scripts.
