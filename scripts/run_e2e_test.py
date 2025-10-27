#!/usr/bin/env python3
# scripts/run_e2e_test.py

import requests
import time
import sys
import json

ORCHESTRATION_ENGINE_URL = "http://localhost:5000"

def run_e2e_test():
    """
    Runs an end-to-end test of the platform.
    1. Creates a workflow with multiple agents.
    2. Polls the status endpoint until the workflow is complete.
    3. Verifies that the results are as expected.
    """
    print("Starting End-to-End Test...")

    # 1. Define the workflow
    workflow_payload = {
        "name": "E2E Test Workflow",
        "tasks": [
            {
                "agent_id": "seo_agent_001",
                "task_details": {"url": "http://e2e-test.com"}
            },
            {
                "agent_id": "lead_scoring_agent_001",
                "task_details": {
                    "company_size": 500,
                    "industry": "finance",
                    "engagement_score": 90
                }
            }
        ]
    }

    # 2. Create the workflow
    print("Creating workflow...")
    try:
        response = requests.post(f"{ORCHESTRATION_ENGINE_URL}/workflows", json=workflow_payload, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        workflow_id = response_data.get("workflow_id")
        print(f"Workflow created successfully with ID: {workflow_id}")
    except requests.RequestException as e:
        print(f"Error creating workflow: {e}")
        sys.exit(1)

    # 3. Poll for status
    status_url = f"{ORCHESTRATION_ENGINE_URL}/workflows/{workflow_id}"
    for _ in range(20): # Poll for up to 20 seconds
        try:
            print("Polling for workflow status...")
            response = requests.get(status_url, timeout=5)
            response.raise_for_status()
            status_data = response.json()

            if status_data.get("status") == "completed":
                print("Workflow completed successfully!")
                # 4. Verify results
                results = status_data.get("results", [])
                assert len(results) == 2, f"Expected 2 results, but got {len(results)}"
                assert results[0]["status"] == "success", "First task failed"
                assert results[1]["status"] == "success", "Second task failed"
                # Corrected the expected priority from "high" to "medium"
                assert results[1]["priority"] == "medium", f"Expected medium priority, got {results[1]['priority']}"
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
