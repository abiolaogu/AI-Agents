import pytest
import httpx
import asyncio
import uuid

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_workflow_lifecycle():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Register User
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        password = "testpassword123"
        response = await client.post("/auth/register", json={"username": username, "password": password})
        assert response.status_code == 201

        # 2. Login
        response = await client.post("/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Workflow
        workflow_data = {
            "name": "E2E Test Workflow",
            "tasks": [
                {
                    "agent_id": "hr_recruitment_agent_001",
                    "task_details": {"role": "Software Engineer"}
                }
            ]
        }
        response = await client.post("/workflows", json=workflow_data, headers=headers)
        assert response.status_code == 202
        workflow_id = response.json()["workflow_id"]

        # 4. Poll for Completion
        for _ in range(10):
            await asyncio.sleep(1)
            response = await client.get(f"/workflows/{workflow_id}", headers=headers)
            assert response.status_code == 200
            status = response.json()["status"]
            if status in ["completed", "failed"]:
                break
        
        assert status == "completed"

        # 5. Verify Analytics
        response = await client.get("/analytics/events", headers=headers)
        assert response.status_code == 200
        events = response.json()
        assert len(events) > 0
        assert any(e["workflow_id"] == workflow_id for e in events)
