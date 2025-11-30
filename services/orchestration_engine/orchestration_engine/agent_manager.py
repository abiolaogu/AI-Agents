# services/orchestration_engine/orchestration_engine/agent_manager.py

import logging
import os
import json

class AgentManager:
    """Manages the registration and metadata of agent services."""

    def __init__(self, logger: logging.Logger, definitions_dir: str = "/app/agents/definitions"):
        """Initializes the AgentManager."""
        self.agents = {}  # Stores agent_id -> agent_metadata mapping
        self.logger = logger
        self.definitions_dir = definitions_dir
        self.load_agents_from_directory()

    def load_agents_from_directory(self):
        """Loads agent definitions from JSON files in the specified directory."""
        if not os.path.exists(self.definitions_dir):
            self.logger.warning(f"Definitions directory {self.definitions_dir} does not exist.")
            return

        for filename in os.listdir(self.definitions_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.definitions_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        agent_def = json.load(f)
                        agent_id = agent_def.get("id")
                        if agent_id:
                            self.register_agent(agent_id, agent_def)
                except Exception as e:
                    self.logger.error(f"Failed to load agent definition from {filename}: {e}")

    def register_agent(self, agent_id: str, agent_metadata: dict):
        """
        Registers a new agent service with its metadata.

        Args:
            agent_id: A unique identifier for the agent.
            agent_metadata: A dictionary containing details like url, name, description, category.
        """
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} is already registered. Updating metadata.")
        self.agents[agent_id] = agent_metadata
        self.logger.info(f"Agent '{agent_metadata.get('name')}' ({agent_id}) registered.")

    def get_agent_url(self, agent_id: str) -> str:
        """Retrieves the URL for a registered agent."""
        agent_info = self.agents.get(agent_id)
        # Default to a generic agent runner if no specific URL is provided
        # In a real K8s/Docker setup, this might route to a specific service
        return agent_info.get("url") or os.getenv("GENERIC_AGENT_URL", "http://generic-agent:5000")

    def list_agents_details(self) -> list:
        """Returns a list of all registered agents with their full metadata."""
        # Add the id to each agent's metadata for the frontend
        detailed_list = []
        for agent_id, metadata in self.agents.items():
            agent_details = metadata.copy()
            agent_details['id'] = agent_id
            detailed_list.append(agent_details)
        return detailed_list

    def list_agents(self) -> list:
        """Returns a list of all registered agent IDs."""
        return list(self.agents.keys())
