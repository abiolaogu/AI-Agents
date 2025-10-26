# API Documentation

## 1. Introduction

This document provides a high-level overview of the APIs for the multi-agent AI platform. Our platform uses an API-first design, with a combination of REST, WebSocket, and GraphQL APIs to support different use cases.

**Note:** This document is a high-level guide. For detailed endpoint specifications, please refer to the [Software Architecture Document](../architecture/Software_Architecture.md). In the future, this documentation will be automatically generated from our OpenAPI and GraphQL schemas.

## 2. API Design Principles

All of our APIs adhere to the following principles:
- **Consistency:** Predictable structure and naming conventions.
- **Simplicity:** Easy to understand and use.
- **Resource-Oriented:** Designed around resources (e.g., agents, workflows).
- **Statelessness:** Each request contains all necessary information.
- **Versioning:** APIs are versioned to ensure backward compatibility.

## 3. REST API

The REST API is the primary way to interact with the platform for most client-server communication.

-   **Authentication:** All requests must be authenticated using an OAuth 2.0 bearer token.
-   **Base URL:** `https://api.ourplatform.com/v1/`
-   **Key Resources:**
    -   `/agents`: For creating, listing, and managing agents.
    -   `/workflows`: For creating, executing, and monitoring workflows.
    -   `/users`: For managing user accounts (admin-only).

### Example Request

```bash
curl -X GET "https://api.ourplatform.com/v1/agents/agent-123" \
     -H "Authorization: Bearer <your_access_token>"
```

## 4. WebSocket API

The WebSocket API is used for real-time, bidirectional communication between the client and the platform. This is ideal for receiving live updates on agent status or workflow progress.

-   **Connection URL:** `wss://ws.ourplatform.com/v1/`
-   **Authentication:** The initial connection request must include the OAuth 2.0 token for authentication.
-   **Key Events:**
    -   `agent:status_update`: Receive real-time updates on agent status.
    -   `workflow:log_message`: Stream logs from a running workflow.

## 5. GraphQL API

The GraphQL API is provided for complex data queries and fetching multiple resources in a single request, which is particularly useful for building rich frontend dashboards.

-   **Endpoint:** `https://api.ourplatform.com/graphql/`
-   **Authentication:** Same as the REST API (OAuth 2.0 bearer token).
-   **Key Queries:**
    -   Fetch an agent and its recent tasks.
    -   Get a workflow and the status of all its constituent tasks.

### Example Query

```graphql
query GetWorkflowDetails {
  workflow(id: "wf-456") {
    id
    name
    status
    tasks {
      id
      status
      agent {
        id
        name
      }
    }
  }
}
```
