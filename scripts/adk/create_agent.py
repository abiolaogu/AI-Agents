#!/usr/bin/env python3
import os
import sys
import argparse
from jinja2 import Environment, FileSystemLoader

# A dictionary to hold the templates for the new agent
TEMPLATES = {
    "app.py": """import os
import logging
from flask import Flask, request, jsonify
from .agent import {{ agent_class_name }}

app = Flask(__name__)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instantiate the agent
agent_id = "{{ agent_name }}_001"
agent = {{ agent_class_name }}(agent_id=agent_id, logger=logger)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    result = agent.execute(data)
    return jsonify(result)
""",
    "run.py": """import os
from services.{{ agent_name }}.app import app

if __name__ == "__main__":
    port = int(os.environ.get("AGENT_PORT", 5001))
    app.run(host='0.0.0.0', port=port)
""",
    "agent.py": """from agent_framework.agent import BaseAgent

class {{ agent_class_name }}(BaseAgent):
    def execute(self, data):
        self.logger.info(f"Executing task with data: {data}")
        # Your agent's logic goes here
        result = {"status": "success", "message": "Agent {{ agent_name }} reporting in!"}
        self.logger.info(f"Task execution finished. Result: {result}")
        return result
""",
    "Dockerfile": """FROM python:3.9-slim

WORKDIR /app

# Add the app directory to the python path
ENV PYTHONPATH="/app"

# Set the agent port
ENV AGENT_PORT=5001
EXPOSE $AGENT_PORT

# Copy all source code
COPY . /app

# Install dependencies for the specific agent
RUN pip install --no-cache-dir -r services/{{ agent_name }}/requirements.txt

# Install the shared agent_framework package in editable mode
# This makes it available as a package to all other code
RUN pip install -e packages/agent_framework

# Run the application using the explicit entrypoint
CMD ["python", "services/{{ agent_name }}/run.py"]
""",
    "requirements.txt": """Flask>=2.3.0
""",
    "__init__.py": "",
    "tests/__init__.py": "",
    "tests/test_agent.py": """import unittest
import logging
from ..agent import {{ agent_class_name }}

class Test{{ agent_class_name }}(unittest.TestCase):
    def test_execute(self):
        logger = logging.getLogger(__name__)
        agent = {{ agent_class_name }}(agent_id="test_agent", logger=logger)
        result = agent.execute({})
        self.assertEqual(result['status'], "success")

if __name__ == '__main__':
    unittest.main()
""",
    "setup.py": """from setuptools import setup, find_packages

setup(
    name='{{ agent_name }}',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'agent-framework @ file://localhost/./packages/agent_framework#egg=agent_framework',
    ],
)
"""
}

def main():
    parser = argparse.ArgumentParser(description="Create a new agent microservice.")
    parser.add_argument("agent_name", help="The name of the agent to create (e.g., 'social_media_agent').")
    args = parser.parse_args()

    agent_name = args.agent_name.lower()
    # Convert snake_case to CamelCase for the class name
    agent_class_name = "".join(word.capitalize() for word in agent_name.split('_'))

    print(f"Creating new agent: {agent_name}")

    base_path = os.path.join("services", agent_name)
    if os.path.exists(base_path):
        print(f"Error: Directory '{base_path}' already exists.")
        sys.exit(1)

    os.makedirs(base_path)
    os.makedirs(os.path.join(base_path, "tests"))

    # Use a Jinja2 environment to render the templates
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

    for filename, content in TEMPLATES.items():
        filepath = os.path.join(base_path, filename)
        # We are using string-based templates here for simplicity
        template = Environment(loader=FileSystemLoader('.')).from_string(content)
        rendered_content = template.render(agent_name=agent_name, agent_class_name=agent_class_name)
        with open(filepath, "w") as f:
            f.write(rendered_content)

    print(f"Agent '{agent_name}' created successfully in '{base_path}'.")
    print("Remember to add the new service to your docker-compose.yml file and assign a unique port.")

if __name__ == "__main__":
    main()
