# Dockerfile for the Social Media Agent

FROM python:3.9-slim

WORKDIR /app

# Set the PYTHONPATH to include the root directory
ENV PYTHONPATH="/app"

# Install dependencies
COPY services/social_media_agent/requirements.txt /app/services/social_media_agent/requirements.txt
RUN pip install --no-cache-dir -r /app/services/social_media_agent/requirements.txt

# Install the shared agent_framework package
COPY packages/agent_framework /tmp/packages/agent_framework
RUN pip install --no-cache-dir /tmp/packages/agent_framework

# Copy all service and package code
COPY services /app/services
COPY packages /app/packages

# Expose the port the app runs on
EXPOSE 5003

# Run the application
CMD ["python", "-m", "services.social_media_agent.social_media_agent.main"]
