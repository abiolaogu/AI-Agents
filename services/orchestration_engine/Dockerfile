# Dockerfile for the Agent Orchestration Engine

FROM python:3.9-slim

WORKDIR /app

# Set the PYTHONPATH to include the root directory
ENV PYTHONPATH="/app"

# Install dependencies for the orchestration engine
COPY services/orchestration_engine/requirements.txt /app/services/orchestration_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/orchestration_engine/requirements.txt

# Install the shared agent_framework package
COPY packages/agent_framework /tmp/packages/agent_framework
RUN pip install --no-cache-dir /tmp/packages/agent_framework

# Install the seo_agent package
COPY services/seo_agent /tmp/services/seo_agent
RUN pip install --no-cache-dir /tmp/services/seo_agent

# Copy all service and package code
COPY services /app/services
COPY packages /app/packages

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "-m", "services.orchestration_engine.orchestration_engine.main"]
