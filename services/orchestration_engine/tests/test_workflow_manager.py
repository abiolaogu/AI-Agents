# services/orchestration_engine/tests/test_workflow_manager.py

import pytest
import sqlite3
import json
from unittest.mock import MagicMock, patch

from services.orchestration_engine.orchestration_engine.workflow_manager import WorkflowManager

@pytest.fixture
def mock_logger():
    """Fixture for a mock logger."""
    return MagicMock()

@pytest.fixture
def mock_agent_manager():
    """Fixture for a mock AgentManager."""
    manager = MagicMock()
    manager.get_agent_url.return_value = "http://fake-agent:5001"
    return manager

@pytest.fixture
def test_db(tmpdir):
    """Fixture to set up an in-memory SQLite database for testing."""
    db_file = tmpdir.join("test_workflows.db")
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE workflows (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, tasks TEXT NOT NULL,
            status TEXT NOT NULL, results TEXT
        );
    """)
    conn.close()
    return db_file

def test_create_workflow_persists_to_db(mock_agent_manager, mock_logger, test_db):
    """
    Tests that creating a workflow correctly persists it to the database.
    """
    # Patch the get_db_connection to use our temporary test database
    with patch('services.orchestration_engine.orchestration_engine.database.DB_FILE', str(test_db)):
        # We also need to patch the tasks import to avoid Celery setup issues in a unit test
        with patch('services.orchestration_engine.orchestration_engine.workflow_manager.execute_workflow_task'):
            manager = WorkflowManager(agent_manager=mock_agent_manager, logger=mock_logger)

            workflow_name = "My Test Workflow"
            tasks = [{"agent_id": "test_agent", "task_details": {"action": "do_something"}}]

            # The method to test has been renamed, let's call the right one
            workflow_id = manager.create_and_dispatch_workflow(workflow_name, tasks)

            # Verify that the workflow was saved correctly
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            workflow_from_db = cursor.fetchone()
            conn.close()

            assert workflow_from_db is not None
            assert workflow_from_db[0] == workflow_id
            assert workflow_from_db[1] == workflow_name
            assert json.loads(workflow_from_db[2]) == tasks
            assert workflow_from_db[3] == "pending" # It should be pending before the worker picks it up
