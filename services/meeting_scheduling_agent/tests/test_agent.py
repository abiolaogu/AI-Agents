# services/meeting_scheduling_agent/tests/test_agent.py
import unittest
import logging
from ..agent import MeetingSchedulingAgent

class TestMeetingSchedulingAgent(unittest.TestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.agent = MeetingSchedulingAgent(agent_id="test_scheduler", logger=self.logger)
        self.valid_data = {
            "participants": ["test1@example.com", "test2@example.com"],
            "time": "2025-12-01T14:30:00",
            "topic": "Project Kick-off"
        }
        self.invalid_data_missing = {
            "participants": ["test1@example.com"],
            "topic": "Project Kick-off"
        }
        self.invalid_data_time_format = {
            "participants": ["test1@example.com"],
            "time": "December 1st, 2025",
            "topic": "Project Kick-off"
        }

    def test_successful_scheduling(self):
        """Test successful creation of a meeting confirmation."""
        result = self.agent.execute(self.valid_data)
        self.assertEqual(result['status'], 'success')
        self.assertIn("Meeting scheduled successfully!", result['message'])
        self.assertIn("Monday, December 01, 2025 at 02:30 PM", result['message'])

    def test_scheduling_with_missing_data(self):
        """Test failure when required fields are missing."""
        result = self.agent.execute(self.invalid_data_missing)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Missing required fields: participants, time, topic.')

    def test_scheduling_with_invalid_time_format(self):
        """Test failure when the time format is incorrect."""
        result = self.agent.execute(self.invalid_data_time_format)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'Invalid time format. Please use ISO 8601 format.')

if __name__ == '__main__':
    unittest.main()
