# services/orchestration_engine/orchestration_engine/agent_manager.py

import logging

class AgentManager:
    """Manages the registration and location of agent services."""

    def __init__(self, logger: logging.Logger):
        """Initializes the AgentManager."""
        self.agents = {}  # Stores agent_id -> agent_url mapping
        self.logger = logger

    def register_agent(self, agent_id: str, agent_url: str):
        """
        Registers a new agent service.

        Args:
            agent_id: A unique identifier for the agent.
            agent_url: The base URL of the agent's microservice.
        """
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} is already registered. Updating URL.")
        self.agents[agent_id] = agent_url
        self.logger.info(f"Agent {agent_id} registered at {agent_url}.")

    def get_agent_url(self, agent_id: str) -> str:
        """
        Retrieves the URL for a registered agent.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            The agent's URL, or None if not found.
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> list:
        """Returns a list of all registered agent IDs."""
        return list(self.agents.keys())
