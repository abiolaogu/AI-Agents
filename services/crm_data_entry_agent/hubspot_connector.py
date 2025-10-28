# services/crm_data_entry_agent/hubspot_connector.py
from hubspot import HubSpot
from integration_framework.base_connector import BaseConnector
import logging

class HubSpotConnector(BaseConnector):
    def __init__(self, connector_id: str, logger: logging.Logger):
        super().__init__(connector_id, logger)
        self.client = None

    def connect(self, credentials: dict):
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                raise ValueError("HubSpot API key is missing.")

            self.client = HubSpot(api_key=api_key)
            self.client.crm.contacts.basic_api.get_page() # Test connection
            self.connected = True
            self.logger.info("Successfully connected to HubSpot.")
        except Exception as e:
            self.log_error(f"Failed to connect to HubSpot: {e}")
            self.connected = False

    def disconnect(self):
        self.client = None
        self.connected = False
        self.logger.info("Disconnected from HubSpot.")

    def create_contact(self, email: str, firstname: str, lastname: str):
        if not self.connected:
            self.log_error("Cannot create contact, not connected to HubSpot.")
            return None

        try:
            properties = {
                "email": email,
                "firstname": firstname,
                "lastname": lastname
            }
            api_response = self.client.crm.contacts.basic_api.create(
                simple_public_object_input={"properties": properties}
            )
            return api_response.id
        except Exception as e:
            self.log_error(f"Failed to create HubSpot contact: {e}")
            return None
