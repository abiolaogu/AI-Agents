# services/competitor_analysis_agent/tests/test_agent.py
import unittest
import logging
from ..agent import CompetitorAnalysisAgent

class TestCompetitorAnalysisAgent(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.agent = CompetitorAnalysisAgent(agent_id="test_competitor_agent", logger=self.logger)
        self.valid_data = {"competitor_url": "http://example.com"}
        self.invalid_data = {}

    def test_successful_analysis(self):
        """Test successful analysis of a competitor."""
        result = self.agent.execute(self.valid_data)
        self.assertEqual(result['status'], 'success')
        self.assertIn("analysis", result)
        self.assertEqual(result['analysis']['seo_score'], 85)

    def test_missing_data(self):
        """Test failure when competitor_url is missing."""
        result = self.agent.execute(self.invalid_data)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Missing required field: competitor_url.')

if __name__ == '__main__':
    unittest.main()
