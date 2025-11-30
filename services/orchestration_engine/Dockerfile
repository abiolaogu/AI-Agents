# Dockerfile for the Agent Orchestration Engine

# Stage 1: Builder
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY services/orchestration_engine/requirements.txt /app/services/orchestration_engine/requirements.txt
RUN pip install --no-cache-dir -r /app/services/orchestration_engine/requirements.txt

# Install packages
COPY packages/agent_framework /tmp/packages/agent_framework
RUN pip install --no-cache-dir /tmp/packages/agent_framework

COPY services/seo_agent /tmp/services/seo_agent
RUN pip install --no-cache-dir /tmp/services/seo_agent

# Stage 2: Final
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONPATH="/app"
ENV PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY services /app/services
COPY packages /app/packages
COPY agents /app/agents

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "services.orchestration_engine.orchestration_engine.main"]
