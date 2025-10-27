# services/orchestration_engine/orchestration_engine/agent_manager.py

import logging

class AgentManager:
    """Manages the registration and metadata of agent services."""

    def __init__(self, logger: logging.Logger):
        """Initializes the AgentManager."""
        self.agents = {}  # Stores agent_id -> agent_metadata mapping
        self.logger = logger

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
        return agent_info.get("url") if agent_info else None

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
