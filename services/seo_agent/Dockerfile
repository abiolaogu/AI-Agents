# Dockerfile for the SEO Agent

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
COPY services/seo_agent/requirements.txt /app/services/seo_agent/requirements.txt
RUN pip install --no-cache-dir -r /app/services/seo_agent/requirements.txt

# Install shared packages
COPY packages/agent_framework /tmp/packages/agent_framework
RUN pip install --no-cache-dir /tmp/packages/agent_framework

# Stage 2: Final
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONPATH="/app"
ENV PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY services/seo_agent /app/services/seo_agent
COPY packages /app/packages

# Create non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5001

CMD ["python", "-m", "services.seo_agent.seo_agent.main"]
