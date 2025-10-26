# services/orchestration_engine/orchestration_engine/agent_manager.py

import logging

class AgentManager:
    """Manages the lifecycle and state of agents."""

    def __init__(self, logger: logging.Logger):
        """Initializes the AgentManager."""
        self.agents = {}
        self.logger = logger

    def register_agent(self, agent_instance):
        """
        Registers a new agent instance with the manager.

        Args:
            agent_instance: An instance of a class that inherits from BaseAgent.
        """
        agent_id = agent_instance.agent_id
        if agent_id in self.agents:
            self.logger.warning(f"Agent {agent_id} is already registered. Overwriting.")
        self.agents[agent_id] = agent_instance
        self.logger.info(f"Agent {agent_id} registered successfully.")

    def get_agent(self, agent_id: str):
        """
        Retrieves a registered agent instance.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            The agent instance, or None if not found.
        """
        return self.agents.get(agent_id)

    def set_agent_status(self, agent_id: str, status: str):
        """
        Sets the status of a specific agent.

        Args:
            agent_id: The ID of the agent.
            status: The new status (e.g., "running", "idle").
        """
        agent = self.get_agent(agent_id)
        if agent:
            agent.set_status(status)
        else:
            self.logger.error(f"Attempted to set status for unregistered agent: {agent_id}")

    def list_agents(self):
        """Returns a list of all registered agent IDs."""
        return list(self.agents.keys())
