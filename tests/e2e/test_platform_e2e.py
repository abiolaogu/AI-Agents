"""
End-to-End Tests for AI Agents Platform
Tests complete user workflows from authentication to agent execution
"""

import pytest
import requests
import time
import json
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAuthenticationFlow:
    """Test complete authentication workflow"""

    def test_user_login(self, base_url: str):
        """Test user can log in and receive JWT token"""
        response = requests.post(
            f"{base_url}/auth/login",
            json={
                "username": "test_user",
                "password": "test_password"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        return data["access_token"]

    def test_token_validation(self, base_url: str, token: str):
        """Test token can be used for authenticated requests"""
        response = requests.get(
            f"{base_url}/api/v1/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data

    def test_token_expiration(self, base_url: str, expired_token: str):
        """Test expired tokens are rejected"""
        response = requests.get(
            f"{base_url}/api/v1/user/profile",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


class TestAgentDiscovery:
    """Test agent discovery and listing"""

    def test_list_all_agents(self, base_url: str, token: str):
        """Test listing all available agents"""
        response = requests.get(
            f"{base_url}/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 1500
        assert "agents" in data
        assert len(data["agents"]) > 0

    def test_search_agents_by_category(self, base_url: str, token: str):
        """Test searching agents by category"""
        response = requests.get(
            f"{base_url}/api/v1/agents?category=business_ops",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(agent["category"] == "business_ops" for agent in data["agents"])

    def test_search_agents_by_keyword(self, base_url: str, token: str):
        """Test searching agents by keyword"""
        response = requests.get(
            f"{base_url}/api/v1/agents?search=business+plan",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) > 0
        # Verify results contain keyword
        assert any("business" in agent["name"].lower() for agent in data["agents"])


class TestAgentExecution:
    """Test complete agent execution workflow"""

    def test_execute_single_agent(self, base_url: str, token: str):
        """Test executing a single agent"""
        agent_id = "business_plan_agent_009"

        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "task_description": "Create a business plan for a coffee shop",
                "context": {
                    "industry": "food_service",
                    "budget": 50000
                }
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "result" in data
        assert "metadata" in data
        assert "processing_time_ms" in data

        # Verify metadata
        assert data["metadata"]["agent_id"] == agent_id
        assert "tokens_used" in data["metadata"]
        assert "model" in data["metadata"]

        # Verify result is not empty
        assert len(data["result"]) > 100

        logger.info(f"Agent executed in {data['processing_time_ms']}ms")

    def test_execute_with_invalid_agent(self, base_url: str, token: str):
        """Test execution fails gracefully with invalid agent ID"""
        response = requests.post(
            f"{base_url}/api/v1/agents/invalid_agent_999/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"task_description": "Test task"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_execute_without_task_description(self, base_url: str, token: str):
        """Test execution fails without task description"""
        agent_id = "business_plan_agent_009"

        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"context": {}}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


class TestMultiAgentWorkflow:
    """Test workflows involving multiple agents"""

    def test_sequential_agent_execution(self, base_url: str, token: str):
        """Test executing agents in sequence"""

        # Step 1: Research agent
        research_response = requests.post(
            f"{base_url}/api/v1/agents/market_research_agent/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "task_description": "Research the coffee shop market in Seattle"
            }
        )

        assert research_response.status_code == 200
        research_data = research_response.json()

        # Step 2: Use research results in strategy agent
        strategy_response = requests.post(
            f"{base_url}/api/v1/agents/strategy_agent/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "task_description": "Create business strategy",
                "context": {
                    "research": research_data["result"][:500]  # First 500 chars
                }
            }
        )

        assert strategy_response.status_code == 200

        logger.info("Sequential workflow completed successfully")

    def test_parallel_agent_execution(self, base_url: str, token: str):
        """Test executing multiple agents in parallel"""
        import concurrent.futures

        agent_ids = [
            "content_writer_agent",
            "seo_agent",
            "social_media_agent"
        ]

        def execute_agent(agent_id):
            return requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "task_description": "Create content about AI in business"
                }
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(execute_agent, aid) for aid in agent_ids]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in results)

        logger.info(f"Parallel execution: {len(results)} agents completed")


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_enforcement(self, base_url: str, token: str):
        """Test rate limits are enforced"""
        agent_id = "business_plan_agent_009"

        # Make requests until rate limited
        responses = []
        for i in range(110):  # Assuming limit is 100/min
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/execute",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"task_description": "Quick test"}
            )
            responses.append(response)

            if response.status_code == 429:
                break

        # Should hit rate limit
        assert any(r.status_code == 429 for r in responses)

        # Check rate limit headers
        rate_limited_response = next(r for r in responses if r.status_code == 429)
        assert "X-RateLimit-Limit" in rate_limited_response.headers
        assert "X-RateLimit-Remaining" in rate_limited_response.headers
        assert "Retry-After" in rate_limited_response.headers

    def test_rate_limit_reset(self, base_url: str, token: str):
        """Test rate limit resets after specified time"""
        agent_id = "business_plan_agent_009"

        # Hit rate limit
        for _ in range(110):
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/execute",
                headers={"Authorization": f"Bearer {token}"},
                json={"task_description": "test"}
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                break

        # Wait for rate limit to reset
        logger.info(f"Waiting {retry_after}s for rate limit reset...")
        time.sleep(retry_after + 1)

        # Should work again
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={"task_description": "test"}
        )

        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and recovery"""

    def test_invalid_json(self, base_url: str, token: str):
        """Test handling of invalid JSON"""
        response = requests.post(
            f"{base_url}/api/v1/agents/business_plan_agent_009/execute",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            data="invalid json"
        )

        assert response.status_code == 400

    def test_missing_auth_header(self, base_url: str):
        """Test request fails without authentication"""
        response = requests.post(
            f"{base_url}/api/v1/agents/business_plan_agent_009/execute",
            json={"task_description": "test"}
        )

        assert response.status_code == 401

    def test_network_timeout_handling(self, base_url: str, token: str):
        """Test handling of network timeouts"""
        try:
            response = requests.post(
                f"{base_url}/api/v1/agents/business_plan_agent_009/execute",
                headers={"Authorization": f"Bearer {token}"},
                json={"task_description": "test"},
                timeout=0.001  # Very short timeout to force failure
            )
        except requests.exceptions.Timeout:
            # Expected behavior
            pass


class TestMonitoringEndpoints:
    """Test monitoring and health check endpoints"""

    def test_agent_health_check(self, base_url: str):
        """Test agent health check endpoint"""
        response = requests.get(f"{base_url}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agent_id" in data
        assert "version" in data

    def test_metrics_endpoint(self, base_url: str):
        """Test Prometheus metrics endpoint"""
        response = requests.get(f"{base_url}/metrics")

        assert response.status_code == 200
        assert "agent_requests_total" in response.text
        assert "agent_processing_seconds" in response.text


class TestDataValidation:
    """Test input validation"""

    def test_long_task_description(self, base_url: str, token: str):
        """Test handling of very long task descriptions"""
        long_task = "x" * 10000  # 10K characters

        response = requests.post(
            f"{base_url}/api/v1/agents/business_plan_agent_009/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={"task_description": long_task}
        )

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 413]

    def test_special_characters_in_task(self, base_url: str, token: str):
        """Test handling of special characters"""
        special_task = "Create plan with 'quotes', \"double quotes\", <html>, and émojis 🚀"

        response = requests.post(
            f"{base_url}/api/v1/agents/business_plan_agent_009/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={"task_description": special_task}
        )

        assert response.status_code == 200


# Pytest fixtures
@pytest.fixture(scope="session")
def base_url():
    """Base URL for the platform"""
    return "http://localhost:8209"  # Adjust as needed


@pytest.fixture(scope="session")
def token(base_url):
    """Get authentication token for tests"""
    # In real tests, this would authenticate properly
    # For now, returning mock token
    return "test-token-12345"


@pytest.fixture(scope="session")
def expired_token():
    """Get expired token for testing"""
    return "expired-token-12345"


# Test runners
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
