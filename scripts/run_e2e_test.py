#!/usr/bin/env python3
# scripts/run_e2e_test.py

import requests
import time
import sys
import json
from uuid import uuid4

ORCHESTRATION_ENGINE_URL = "http://localhost:5000"

def get_auth_token():
    """Registers and logs in a test user to get an auth token."""
    # Use a unique username for each test run to avoid conflicts
    username = f"testuser_{uuid4()}"
    password = "password123"

    # Register
    try:
        requests.post(f"{ORCHESTRATION_ENGINE_URL}/auth/register", json={"username": username, "password": password}, timeout=5).raise_for_status()
        print("Test user registered.")
    except requests.RequestException as e:
        print(f"Could not register test user: {e}")
        sys.exit(1)

    # Login
    try:
        response = requests.post(f"{ORCHESTRATION_ENGINE_URL}/auth/login", json={"username": username, "password": password}, timeout=5)
        response.raise_for_status()
        token = response.json().get("token")
        print("Test user logged in and token obtained.")
        return token
    except requests.RequestException as e:
        print(f"Could not log in test user: {e}")
        sys.exit(1)

def run_e2e_test():
    """
    Runs an end-to-end test of the platform.
    """
    print("Starting End-to-End Test...")

    # 1. Get auth token
    auth_token = get_auth_token()
    headers = {"x-access-token": auth_token}

    # 2. Define the workflow
    workflow_payload = {
        "name": "E2E Test Workflow",
        "tasks": [
            {"agent_id": "seo_agent_001", "task_details": {"url": "http://e2e-test.com"}},
            {"agent_id": "lead_scoring_agent_001", "task_details": {"company_size": 500, "industry": "tech", "engagement_score": 90}}
        ]
    }

    # 3. Create the workflow
    print("Creating workflow...")
    try:
        response = requests.post(f"{ORCHESTRATION_ENGINE_URL}/workflows", headers=headers, json=workflow_payload, timeout=10)
        response.raise_for_status()
        workflow_id = response.json().get("workflow_id")
        print(f"Workflow created successfully with ID: {workflow_id}")
    except requests.RequestException as e:
        print(f"Error creating workflow: {e}")
        sys.exit(1)

    # 4. Poll for status
    status_url = f"{ORCHESTRATION_ENGINE_URL}/workflows/{workflow_id}"
    for _ in range(20): # Poll for up to 20 seconds
        try:
            print("Polling for workflow status...")
            response = requests.get(status_url, headers=headers, timeout=5)
            response.raise_for_status()
            status_data = response.json()

            if status_data.get("status") == "completed":
                print("Workflow completed successfully!")
                # 5. Verify results
                results = status_data.get("results", [])
                assert len(results) == 2, f"Expected 2 results, but got {len(results)}"
                assert results[0]["status"] == "success", "First task failed"
                assert results[1]["status"] == "success", "Second task failed"
                assert results[1]["priority"] == "high", f"Expected high priority, got {results[1]['priority']}"
                print("Test verification PASSED.")
                sys.exit(0)
            elif status_data.get("status") == "failed":
                print(f"Workflow failed. Final status: {status_data}")
                sys.exit(1)

            time.sleep(1)
        except requests.RequestException as e:
            print(f"Error polling for status: {e}")
            sys.exit(1)

    print("Test FAILED: Workflow did not complete in time.")
    sys.exit(1)

if __name__ == "__main__":
    run_e2e_test()
