# Dockerfile for the SEO Agent

FROM python:3.9-slim

WORKDIR /app

# Install the shared agent_framework package
COPY packages/agent_framework /app/packages/agent_framework
RUN pip install /app/packages/agent_framework

# Copy the service code
COPY services/seo_agent /app/services/seo_agent

# This is a placeholder for the actual service entrypoint
CMD ["python", "services/seo_agent/seo_agent/agent.py"]
