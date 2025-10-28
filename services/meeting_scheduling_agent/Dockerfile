FROM python:3.9-slim

WORKDIR /app

# Add the app directory to the python path
ENV PYTHONPATH="/app"

# Set the agent port
ENV AGENT_PORT=5001
EXPOSE $AGENT_PORT

# Copy all source code
COPY . /app

# Install dependencies for the specific agent
RUN pip install --no-cache-dir -r services/meeting_scheduling_agent/requirements.txt

# Install the shared agent_framework package in editable mode
# This makes it available as a package to all other code
RUN pip install -e packages/agent_framework

# Run the application using the explicit entrypoint
CMD ["python", "services/meeting_scheduling_agent/run.py"]