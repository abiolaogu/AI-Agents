# services/crm_data_entry_agent/agent.py
from agent_framework.agent import BaseAgent
from integration_framework.credential_manager import CredentialManager
from .hubspot_connector import HubSpotConnector
import os

class CrmDataEntryAgent(BaseAgent):
    def __init__(self, agent_id, logger):
        super().__init__(agent_id, logger)

        # Initialize the Credential Manager
        self.cred_manager = CredentialManager()
        if not self.cred_manager.get_credential("hubspot"):
            self.logger.info("HubSpot credential not found. Adding a placeholder.")
            self.cred_manager.add_credential("hubspot", {"api_key": os.environ.get("HUBSPOT_API_KEY", "YOUR_HUBSPOT_API_KEY")})

        # Initialize the connector, but do not connect yet.
        self.hubspot_connector = HubSpotConnector("hubspot_001", self.logger)

    def _ensure_connected(self):
        """Connects to HubSpot if not already connected."""
        if not self.hubspot_connector.connected:
            self.logger.info("Connector not connected, attempting to connect...")
            hubspot_creds = self.cred_manager.get_credential("hubspot")
            if hubspot_creds:
                self.hubspot_connector.connect(hubspot_creds)

    def execute(self, data):
        self.logger.info(f"Executing CRM data entry task with data: {data}")

        # Ensure the connection is established before proceeding.
        self._ensure_connected()

        if not self.hubspot_connector.connected:
            error_message = "Failed to execute task: Could not connect to HubSpot."
            self.logger.error(error_message)
            return {"status": "error", "message": error_message}

        # Extract contact details from the input data
        email = data.get("email")
        firstname = data.get("firstname")
        lastname = data.get("lastname")

        if not all([email, firstname, lastname]):
            return {"status": "error", "message": "Missing required fields: email, firstname, lastname."}

        # Create the contact in HubSpot
        contact_id = self.hubspot_connector.create_contact(
            email=email, firstname=firstname, lastname=lastname
        )

        if contact_id:
            message = f"Successfully created contact in HubSpot with ID: {contact_id}"
            self.logger.info(message)
            return {"status": "success", "message": message, "contact_id": contact_id}
        else:
            message = "Failed to create contact in HubSpot."
            self.logger.error(message)
            return {"status": "error", "message": message}
