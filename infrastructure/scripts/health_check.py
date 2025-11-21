#!/usr/bin/env python3
"""
Health check script for deployed agents
"""

import requests
import concurrent.futures
from typing import Dict, List, Tuple
import sys


def check_agent_health(agent_id: str, port: int) -> Tuple[str, bool, str]:
    """Check health of a single agent"""
    try:
        url = f"http://localhost:{port}/health"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                return agent_id, True, "OK"
            else:
                return agent_id, False, f"Unhealthy: {data.get('status')}"
        else:
            return agent_id, False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return agent_id, False, "Timeout"
    except requests.exceptions.ConnectionError:
        return agent_id, False, "Connection refused"
    except Exception as e:
        return agent_id, False, str(e)


def main():
    """Run health checks on all deployed agents"""
    print("Running health checks on deployed agents...\n")

    # Sample agents to check (expand to all 1,500)
    agents_to_check = [
        ("business_plan_agent_009", 8209),
        ("marketing_agent_001", 8201),
        ("sales_agent_002", 8202),
        # Add all 1,500 agents here
    ]

    healthy = 0
    unhealthy = 0
    results = []

    # Check agents in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [
            executor.submit(check_agent_health, agent_id, port)
            for agent_id, port in agents_to_check
        ]

        for future in concurrent.futures.as_completed(futures):
            agent_id, is_healthy, message = future.result()
            results.append((agent_id, is_healthy, message))

            if is_healthy:
                healthy += 1
                print(f"✓ {agent_id}: {message}")
            else:
                unhealthy += 1
                print(f"✗ {agent_id}: {message}")

    # Summary
    total = healthy + unhealthy
    health_percentage = (healthy / total * 100) if total > 0 else 0

    print(f"\n{'=' * 50}")
    print(f"Health Check Summary")
    print(f"{'=' * 50}")
    print(f"Total agents checked: {total}")
    print(f"Healthy: {healthy}")
    print(f"Unhealthy: {unhealthy}")
    print(f"Health percentage: {health_percentage:.2f}%")
    print(f"{'=' * 50}\n")

    # Exit with error if health is below threshold
    if health_percentage < 95:
        print("⚠ Warning: Health below 95% threshold")
        sys.exit(1)

    print("✓ All systems operational")
    sys.exit(0)


if __name__ == "__main__":
    main()
