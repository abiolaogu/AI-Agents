# Dockerfile for the Email Campaign Agent

FROM python:3.9-slim

WORKDIR /app

# Set the PYTHONPATH to include the root directory
ENV PYTHONPATH="/app"

# Install dependencies
COPY services/email_campaign_agent/requirements.txt /app/services/email_campaign_agent/requirements.txt
RUN pip install --no-cache-dir -r /app/services/email_campaign_agent/requirements.txt

# Install the shared agent_framework package
COPY packages/agent_framework /tmp/packages/agent_framework
RUN pip install --no-cache-dir /tmp/packages/agent_framework

# Copy all service and package code
COPY services /app/services
COPY packages /app/packages

# Expose the port the app runs on
EXPOSE 5004

# Run the application
CMD ["python", "-m", "services.email_campaign_agent.email_campaign_agent.main"]
