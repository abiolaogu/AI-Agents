import unittest
from unittest.mock import MagicMock
from services.orchestration_engine.orchestration_engine.agent_manager import AgentManager

class TestAgentManager(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.agent_manager = AgentManager(logger=self.logger, definitions_dir="/tmp/nonexistent")

    def test_register_agent(self):
        agent_id = "test_agent"
        metadata = {"name": "Test Agent", "url": "http://test"}
        self.agent_manager.register_agent(agent_id, metadata)
        
        self.assertIn(agent_id, self.agent_manager.agents)
        self.assertEqual(self.agent_manager.agents[agent_id], metadata)

    def test_get_agent_url(self):
        agent_id = "test_agent"
        metadata = {"name": "Test Agent", "url": "http://test"}
        self.agent_manager.register_agent(agent_id, metadata)
        
        url = self.agent_manager.get_agent_url(agent_id)
        self.assertEqual(url, "http://test")

    def test_get_agent_url_default(self):
        agent_id = "test_agent_no_url"
        metadata = {"name": "Test Agent"}
        self.agent_manager.register_agent(agent_id, metadata)
        
        url = self.agent_manager.get_agent_url(agent_id)
        self.assertEqual(url, "http://generic-agent:5000")

    def test_list_agents(self):
        self.agent_manager.register_agent("a1", {})
        self.agent_manager.register_agent("a2", {})
        
        agents = self.agent_manager.list_agents()
        self.assertEqual(len(agents), 2)
        self.assertIn("a1", agents)
        self.assertIn("a2", agents)

if __name__ == '__main__':
    unittest.main()
