# services/proposal_generation_agent/tests/test_agent.py
import unittest
import logging
from ..agent import ProposalGenerationAgent

class TestProposalGenerationAgent(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.agent = ProposalGenerationAgent(agent_id="test_proposal_agent", logger=self.logger)
        self.valid_data = {
            "client_name": "ABC Corp",
            "project_scope": "A new website.",
            "budget": 5000
        }
        self.invalid_data_missing = {
            "client_name": "ABC Corp",
            "project_scope": "A new website."
        }
        self.invalid_data_budget = {
            "client_name": "ABC Corp",
            "project_scope": "A new website.",
            "budget": "five thousand"
        }

    def test_successful_proposal_generation(self):
        """Test successful creation of a proposal."""
        result = self.agent.execute(self.valid_data)
        self.assertEqual(result['status'], 'success')
        self.assertIn("Proposal for ABC Corp", result['proposal_text'])
        self.assertIn("$5,000.00", result['proposal_text'])

    def test_proposal_generation_with_missing_data(self):
        """Test failure when required fields are missing."""
        result = self.agent.execute(self.invalid_data_missing)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Missing required fields: client_name, project_scope, budget.')

    def test_proposal_generation_with_invalid_budget(self):
        """Test failure when the budget is not a number."""
        result = self.agent.execute(self.invalid_data_budget)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Invalid budget format. Please provide a number.')

if __name__ == '__main__':
    unittest.main()
