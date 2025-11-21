"""
Locust load testing configuration for AI Agents
Run with: locust -f locustfile.py --host=http://localhost:8209
"""

from locust import HttpUser, task, between
import random


class AgentUser(HttpUser):
    """Simulated user interacting with agents"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task(3)
    def execute_task(self):
        """Execute agent task (higher weight)"""
        tasks = [
            "Analyze market trends for Q4 2025",
            "Create a marketing strategy for a new product",
            "Draft a business proposal",
            "Generate customer persona",
            "Optimize pricing strategy"
        ]

        self.client.post(
            "/api/v1/execute",
            json={
                "task_description": random.choice(tasks),
                "context": {"load_test": True}
            },
            name="/api/v1/execute"
        )

    @task(1)
    def check_health(self):
        """Check agent health"""
        self.client.get("/health", name="/health")

    @task(1)
    def get_metrics(self):
        """Get agent metrics"""
        self.client.get("/metrics", name="/metrics")

    def on_start(self):
        """Called when a simulated user starts"""
        self.client.verify = False  # Disable SSL verification for testing
