import json
import os
import logging
from typing import Dict, Optional

class CredentialManager:
    """Manages the secure storage and retrieval of credentials."""

    def __init__(self, storage_path: str = ".credentials", logger: Optional[logging.Logger] = None):
        """
        Initializes the CredentialManager.

        Args:
            storage_path: The path to the file where credentials will be stored.
            logger: A logger instance.
        """
        self.storage_path = storage_path
        self.logger = logger or logging.getLogger(__name__)
        self._credentials = self._load_credentials()

    def _load_credentials(self) -> Dict:
        """Loads credentials from the storage file."""
        if not os.path.exists(self.storage_path):
            return {}
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load credentials from {self.storage_path}: {e}")
            return {}

    def _save_credentials(self):
        """Saves the current credentials to the storage file."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self._credentials, f, indent=4)
        except IOError as e:
            self.logger.error(f"Failed to save credentials to {self.storage_path}: {e}")

    def add_credential(self, service: str, credential: Dict):
        """
        Adds or updates a credential for a service.

        Args:
            service: The name of the service (e.g., 'hubspot').
            credential: The credential dictionary to store.
        """
        self._credentials[service] = credential
        self._save_credentials()
        self.logger.info(f"Credential for '{service}' has been added/updated.")

    def get_credential(self, service: str) -> Optional[Dict]:
        """
        Retrieves a credential for a service.

        Args:
            service: The name of the service.

        Returns:
            The credential dictionary, or None if not found.
        """
        return self._credentials.get(service)

    def remove_credential(self, service: str):
        """
        Removes a credential for a service.

        Args:
            service: The name of the service.
        """
        if service in self._credentials:
            del self._credentials[service]
            self._save_credentials()
            self.logger.info(f"Credential for '{service}' has been removed.")
        else:
            self.logger.warning(f"No credential found for '{service}' to remove.")
