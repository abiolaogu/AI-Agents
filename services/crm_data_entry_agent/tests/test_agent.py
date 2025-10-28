# services/crm_data_entry_agent/tests/test_agent.py
import unittest
import logging
from unittest.mock import patch, MagicMock
from ..agent import CrmDataEntryAgent

class TestCrmDataEntryAgent(unittest.TestCase):

    def setUp(self):
        """Set up a logger and mock data for each test."""
        self.logger = logging.getLogger(__name__)
        self.valid_data = {
            "email": "test@example.com",
            "firstname": "John",
            "lastname": "Doe"
        }
        self.invalid_data = {
            "email": "test@example.com"
        }

    @patch('services.crm_data_entry_agent.agent.HubSpotConnector')
    def test_successful_contact_creation(self, MockConnector):
        """Test the agent's execute method for a successful contact creation."""
        # Configure the mock connector to simulate success
        mock_connector = MockConnector.return_value
        mock_connector.connected = False # Starts as not connected

        # The connect method will be called by the agent's _ensure_connected
        def mock_connect(*args, **kwargs):
            mock_connector.connected = True
        mock_connector.connect.side_effect = mock_connect
        mock_connector.create_contact.return_value = "mock_contact_id_123"

        agent = CrmDataEntryAgent(agent_id="test_crm_agent", logger=self.logger)
        result = agent.execute(self.valid_data)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['contact_id'], 'mock_contact_id_123')
        mock_connector.connect.assert_called_once()
        mock_connector.create_contact.assert_called_once_with(
            email="test@example.com", firstname="John", lastname="Doe"
        )

    @patch('services.crm_data_entry_agent.agent.HubSpotConnector')
    def test_failed_contact_creation_due_to_missing_data(self, MockConnector):
        """Test failure when required data is missing, without attempting to connect."""
        agent = CrmDataEntryAgent(agent_id="test_crm_agent", logger=self.logger)
        result = agent.execute(self.invalid_data)

        self.assertEqual(result['status'], 'error')
        self.assertIn('Missing required fields', result['message'])
        # The connector should not be used if the input data is invalid
        MockConnector.return_value.connect.assert_not_called()

    @patch('services.crm_data_entry_agent.agent.HubSpotConnector')
    def test_failed_contact_creation_due_to_connector_failure(self, MockConnector):
        """Test failure when the HubSpot connector fails to connect."""
        # Configure the mock to fail on connect
        mock_connector = MockConnector.return_value
        mock_connector.connected = False
        def mock_connect_fail(*args, **kwargs):
            mock_connector.connected = False
        mock_connector.connect.side_effect = mock_connect_fail

        agent = CrmDataEntryAgent(agent_id="test_crm_agent", logger=self.logger)
        result = agent.execute(self.valid_data)

        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Failed to execute task: Could not connect to HubSpot.')
        mock_connector.connect.assert_called_once()
        mock_connector.create_contact.assert_not_called()

if __name__ == "__main__":
    unittest.main()
