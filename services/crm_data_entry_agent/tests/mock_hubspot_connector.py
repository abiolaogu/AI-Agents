# services/crm_data_entry_agent/tests/mock_hubspot_connector.py
from integration_framework.base_connector import BaseConnector
import logging

class MockHubSpotConnector(BaseConnector):
    def __init__(self, connector_id: str, logger: logging.Logger, should_succeed: bool = True):
        super().__init__(connector_id, logger)
        self.should_succeed = should_succeed

    def connect(self, credentials: dict):
        if self.should_succeed:
            self.connected = True
            self.logger.info("Mock HubSpot connection successful.")
        else:
            self.connected = False
            self.logger.error("Mock HubSpot connection failed.")

    def disconnect(self):
        self.connected = False
        self.logger.info("Mock HubSpot disconnected.")

    def create_contact(self, email: str, firstname: str, lastname: str):
        if not self.connected or not self.should_succeed:
            return None

        self.logger.info(f"Mock HubSpot: Creating contact {firstname} {lastname} ({email}).")
        return "mock_contact_id_123"
