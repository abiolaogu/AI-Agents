# Administrator Guide

## 1. Introduction

This guide is intended for platform administrators responsible for the configuration, management, and maintenance of the multi-agent AI platform. It provides an overview of key administrative tasks and the tools available to perform them.

## 2. Platform Configuration

The platform's core configuration is managed via Infrastructure as Code (IaC) using Terraform, located in the `terraform/` directory of the repository. Modifying the core infrastructure should be done with care and follow the established CI/CD process.

### Key Configuration Areas:
- **Environment Variables:** Service-specific configurations (e.g., API keys, database connection strings) are managed as environment variables, securely stored in Google Secret Manager.
- **Resource Allocation:** GKE cluster size, node pools, and database instance types are defined in the Terraform configuration files.
- **Scaling Policies:** Autoscaling rules for GKE services are also configured within the Terraform scripts.

## 3. User Management

User access and permissions are managed through a role-based access control (RBAC) system.

### Roles:
- **Administrator:** Full access to all platform features, including user management and system-level configuration.
- **Manager:** Can create and manage workflows, and view analytics for their team or department.
- **User:** Can interact with assigned agents and view their own task history.

### User Provisioning (Future State):
User provisioning and de-provisioning will be integrated with third-party identity providers (e.g., Google Workspace, Azure AD) via SAML or SCIM. In the MVP, user management will be handled via a dedicated admin dashboard.

## 4. Agent Deployment and Management

Agents are deployed as individual microservices on the GKE cluster.

### Deployment Process:
1.  **Containerization:** Each agent is packaged as a Docker container.
2.  **CI/CD Pipeline:** When a new agent is merged into the main branch, a CI/CD pipeline in Google Cloud Build is triggered.
3.  **Artifact Storage:** The pipeline builds the Docker image and pushes it to Google Artifact Registry.
4.  **Deployment to GKE:** The pipeline then deploys the new container to the GKE cluster, typically using a Canary release strategy.

### Monitoring Agent Status:
The health and status of all deployed agents can be monitored through the central admin dashboard. This dashboard provides real-time insights into:
- **Agent Status:** (e.g., running, idle, error)
- **Resource Consumption:** CPU and memory usage.
- **Task Throughput:** The number of tasks being processed.

Administrators can restart or scale agent services directly from the dashboard if issues are detected.
