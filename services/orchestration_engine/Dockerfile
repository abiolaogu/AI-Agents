# Dockerfile for the Agent Orchestration Engine

FROM python:3.9-slim

WORKDIR /app

# Install the shared agent_framework package
COPY packages/agent_framework /app/packages/agent_framework
RUN pip install /app/packages/agent_framework

# Copy the service code
COPY services/orchestration_engine /app/services/orchestration_engine

# This is a placeholder for the actual service entrypoint
CMD ["python", "-c", "print('Orchestration Engine MVP')"]
