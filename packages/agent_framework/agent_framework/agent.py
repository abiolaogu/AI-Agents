from abc import ABC, abstractmethod
import logging

class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, agent_id: str, logger: logging.Logger):
        """
        Initializes the BaseAgent.

        Args:
            agent_id: A unique identifier for the agent.
            logger: A logger instance for logging agent activity.
        """
        self.agent_id = agent_id
        self.logger = logger
        self.status = "idle"

    @abstractmethod
    async def execute(self, task: dict) -> dict:
        """
        Execute a task. This method must be implemented by subclasses.

        Args:
            task: A dictionary representing the task to be executed.

        Returns:
            A dictionary representing the result of the task.
        """
        pass

    def set_status(self, status: str):
        """
        Set the status of the agent.

        Args:
            status: The new status of the agent (e.g., "idle", "running", "error").
        """
        self.status = status
        self.logger.info(f"Agent {self.agent_id} status changed to {status}")

    def log_error(self, error: str):
        """
        Log an error.

        Args:
            error: The error message to log.
        """
        self.logger.error(f"Agent {self.agent_id} encountered an error: {error}")
