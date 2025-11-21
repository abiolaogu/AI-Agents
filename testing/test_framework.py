"""
Comprehensive Testing Framework for AI Agents
Supports unit, integration, load, and end-to-end testing
"""

import asyncio
import time
import requests
import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data"""
    agent_id: str
    test_name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


@dataclass
class LoadTestResult:
    """Load test metrics"""
    agent_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float


class AgentTester:
    """Base tester for individual agents"""

    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url
        self.timeout = timeout

    def test_health(self, agent_id: str, port: int) -> TestResult:
        """Test agent health endpoint"""
        start = time.time()
        test_name = f"{agent_id}_health_check"

        try:
            url = f"http://{self.base_url}:{port}/health"
            response = requests.get(url, timeout=5)
            duration_ms = (time.time() - start) * 1000

            passed = response.status_code == 200 and response.json().get("status") == "healthy"

            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                response_data=response.json() if passed else None,
                error_message=None if passed else f"Status: {response.status_code}"
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )

    def test_execute_endpoint(
        self,
        agent_id: str,
        port: int,
        task_description: str = "Test task"
    ) -> TestResult:
        """Test agent execution endpoint"""
        start = time.time()
        test_name = f"{agent_id}_execute_test"

        try:
            url = f"http://{self.base_url}:{port}/api/v1/execute"
            payload = {
                "task_description": task_description,
                "context": {"test": True}
            }

            response = requests.post(url, json=payload, timeout=self.timeout)
            duration_ms = (time.time() - start) * 1000

            passed = response.status_code == 200
            response_data = response.json() if passed else None

            # Additional validation
            if passed and response_data:
                passed = (
                    "result" in response_data and
                    "metadata" in response_data and
                    "processing_time_ms" in response_data
                )

            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                response_data=response_data,
                error_message=None if passed else f"Status: {response.status_code}"
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )

    def test_metrics_endpoint(self, agent_id: str, port: int) -> TestResult:
        """Test metrics endpoint"""
        start = time.time()
        test_name = f"{agent_id}_metrics_test"

        try:
            url = f"http://{self.base_url}:{port}/metrics"
            response = requests.get(url, timeout=5)
            duration_ms = (time.time() - start) * 1000

            passed = response.status_code == 200 and "agent_requests_total" in response.text

            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                error_message=None if passed else "Metrics endpoint failed"
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return TestResult(
                agent_id=agent_id,
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )


class LoadTester:
    """Load testing for agents"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def run_load_test(
        self,
        agent_id: str,
        port: int,
        num_requests: int = 100,
        concurrent_users: int = 10,
        task_description: str = "Load test task"
    ) -> LoadTestResult:
        """Run load test on agent"""
        logger.info(f"Starting load test: {num_requests} requests with {concurrent_users} concurrent users")

        url = f"http://{self.base_url}:{port}/api/v1/execute"
        payload = {
            "task_description": task_description,
            "context": {"load_test": True}
        }

        response_times = []
        errors = 0
        start_time = time.time()

        def make_request():
            req_start = time.time()
            try:
                response = requests.post(url, json=payload, timeout=60)
                duration = (time.time() - req_start) * 1000
                return duration, response.status_code == 200
            except Exception as e:
                duration = (time.time() - req_start) * 1000
                logger.error(f"Request failed: {e}")
                return duration, False

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]

            for future in as_completed(futures):
                duration, success = future.result()
                response_times.append(duration)
                if not success:
                    errors += 1

        total_duration = time.time() - start_time
        successful = num_requests - errors

        # Calculate statistics
        response_times.sort()
        avg_time = statistics.mean(response_times)
        p50 = response_times[int(len(response_times) * 0.5)]
        p95 = response_times[int(len(response_times) * 0.95)]
        p99 = response_times[int(len(response_times) * 0.99)]
        rps = num_requests / total_duration
        error_rate = (errors / num_requests) * 100

        return LoadTestResult(
            agent_id=agent_id,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=errors,
            avg_response_time_ms=avg_time,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            requests_per_second=rps,
            error_rate_percent=error_rate
        )


class IntegrationTester:
    """Integration testing for agent workflows"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tester = AgentTester(base_url)

    def test_agent_workflow(
        self,
        workflow: List[Dict[str, Any]]
    ) -> List[TestResult]:
        """Test a workflow involving multiple agents"""
        results = []

        for step in workflow:
            agent_id = step["agent_id"]
            port = step["port"]
            task = step.get("task_description", "Integration test task")

            result = self.tester.test_execute_endpoint(agent_id, port, task)
            results.append(result)

            # Stop if any step fails
            if not result.passed:
                logger.error(f"Workflow failed at step: {agent_id}")
                break

        return results

    def test_agent_dependencies(
        self,
        primary_agent: Dict[str, Any],
        dependent_agents: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Test agent dependencies"""
        results = {}

        # Test primary agent first
        primary_result = self.tester.test_execute_endpoint(
            primary_agent["agent_id"],
            primary_agent["port"]
        )
        results["primary"] = primary_result.passed

        if not primary_result.passed:
            return results

        # Test dependent agents
        for agent in dependent_agents:
            result = self.tester.test_execute_endpoint(
                agent["agent_id"],
                agent["port"]
            )
            results[agent["agent_id"]] = result.passed

        return results


class TestReporter:
    """Generate test reports"""

    @staticmethod
    def generate_report(results: List[TestResult]) -> Dict[str, Any]:
        """Generate test summary report"""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        avg_duration = statistics.mean([r.duration_ms for r in results]) if results else 0

        failed_tests = [
            {
                "agent_id": r.agent_id,
                "test_name": r.test_name,
                "error": r.error_message,
                "duration_ms": r.duration_ms
            }
            for r in results if not r.passed
        ]

        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate_percent": (passed / total * 100) if total > 0 else 0,
                "avg_duration_ms": avg_duration
            },
            "failed_tests": failed_tests
        }

    @staticmethod
    def generate_load_test_report(result: LoadTestResult) -> str:
        """Generate load test report"""
        report = f"""
Load Test Report: {result.agent_id}
{'=' * 50}

Summary:
  Total Requests:      {result.total_requests}
  Successful:          {result.successful_requests}
  Failed:              {result.failed_requests}
  Error Rate:          {result.error_rate_percent:.2f}%

Performance:
  Requests/Second:     {result.requests_per_second:.2f}
  Avg Response Time:   {result.avg_response_time_ms:.2f}ms
  P50 Response Time:   {result.p50_response_time_ms:.2f}ms
  P95 Response Time:   {result.p95_response_time_ms:.2f}ms
  P99 Response Time:   {result.p99_response_time_ms:.2f}ms
"""
        return report


# Pytest fixtures and tests
@pytest.fixture
def agent_tester():
    return AgentTester(base_url="localhost")


def test_agent_health(agent_tester):
    """Pytest example: Test agent health"""
    result = agent_tester.test_health("business_plan_agent_009", 8209)
    assert result.passed, f"Health check failed: {result.error_message}"


def test_agent_execution(agent_tester):
    """Pytest example: Test agent execution"""
    result = agent_tester.test_execute_endpoint(
        "business_plan_agent_009",
        8209,
        "Create a business plan for a tech startup"
    )
    assert result.passed, f"Execution test failed: {result.error_message}"
    assert result.response_data is not None
    assert "result" in result.response_data


if __name__ == "__main__":
    # Example usage
    tester = AgentTester(base_url="localhost")

    # Test health
    health_result = tester.test_health("business_plan_agent_009", 8209)
    print(f"Health test: {'PASS' if health_result.passed else 'FAIL'}")

    # Test execution
    exec_result = tester.test_execute_endpoint(
        "business_plan_agent_009",
        8209,
        "Create a business plan"
    )
    print(f"Execution test: {'PASS' if exec_result.passed else 'FAIL'}")

    # Load test
    load_tester = LoadTester(base_url="localhost")
    load_result = load_tester.run_load_test(
        "business_plan_agent_009",
        8209,
        num_requests=50,
        concurrent_users=5
    )
    print(TestReporter.generate_load_test_report(load_result))
