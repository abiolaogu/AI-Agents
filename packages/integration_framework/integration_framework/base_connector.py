from abc import ABC, abstractmethod
import logging

class BaseConnector(ABC):
    """Abstract base class for all integration connectors."""

    def __init__(self, connector_id: str, logger: logging.Logger):
        """
        Initializes the BaseConnector.

        Args:
            connector_id: A unique identifier for the connector.
            logger: A logger instance for logging connector activity.
        """
        self.connector_id = connector_id
        self.logger = logger
        self.connected = False

    @abstractmethod
    def connect(self, credentials: dict):
        """
        Connect to the third-party service.

        Args:
            credentials: A dictionary containing the credentials required to connect.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the third-party service."""
        pass

    def log_error(self, error: str):
        """
        Log an error.

        Args:
            error: The error message to log.
        """
        self.logger.error(f"Connector {self.connector_id} encountered an error: {error}")
