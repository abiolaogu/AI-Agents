# services/seo_agent/tests/test_agent.py

import pytest
from unittest.mock import MagicMock

from services.seo_agent.seo_agent.agent import SeoAgent

@pytest.fixture
def mock_logger():
    """Fixture for a mock logger."""
    return MagicMock()

def test_seo_agent_execute(mock_logger):
    """
    Tests the placeholder logic of the SeoAgent's execute method.
    """
    agent = SeoAgent(agent_id="test_seo_agent", logger=mock_logger)

    task = {"url": "http://test.com"}
    result = agent.execute(task)

    assert result["status"] == "success"
    assert "Placeholder SEO analysis complete" in result["message"]
    assert len(result["suggestions"]) > 0
    mock_logger.info.assert_called_with(f"Executing SEO task for URL: {task.get('url')}")
