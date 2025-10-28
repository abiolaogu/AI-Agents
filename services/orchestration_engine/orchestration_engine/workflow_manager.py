# services/orchestration_engine/orchestration_engine/workflow_manager.py

import logging
import requests
import json
from uuid import uuid4
from .database import get_db_connection
from .tasks import execute_workflow_task

class WorkflowManager:
    """Manages the creation, execution, and state of agent workflows using a database."""

    def __init__(self, agent_manager, logger: logging.Logger):
        """
        Initializes the WorkflowManager.

        Args:
            agent_manager: An instance of AgentManager.
            logger: A logger instance.
        """
        self.agent_manager = agent_manager
        self.logger = logger

    def create_and_dispatch_workflow(self, name: str, tasks: list, user_id: int) -> str:
        """
        Creates a new workflow, persists it, and dispatches it to the task queue.

        Args:
            name: The name of the workflow.
            tasks: A list of task dictionaries.
            user_id: The ID of the user creating the workflow.

        Returns:
            The ID of the newly created workflow.
        """
        workflow_id = str(uuid4())
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO workflows (id, name, tasks, status, results, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (workflow_id, name, json.dumps(tasks), "pending", json.dumps([]), user_id),
        )
        conn.commit()
        conn.close()
        self.logger.info(f"Workflow '{name}' ({workflow_id}) for user {user_id} created and saved to DB.")

        # Dispatch the task to the Celery queue
        execute_workflow_task.delay(workflow_id)
        self.logger.info(f"Dispatched workflow {workflow_id} to Celery.")

        return workflow_id

    def execute_workflow(self, workflow_id: str):
        """
        Executes a given workflow. This is now called by the Celery worker.
        """
        workflow = self._get_workflow_from_db(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found in DB.")
            return

        self.logger.info(f"Executing workflow '{workflow['name']}' ({workflow_id})...")
        self._update_workflow_status(workflow_id, "running")

        tasks = json.loads(workflow['tasks'])
        results = []
        for i, task in enumerate(tasks):
            agent_id = task.get("agent_id")
            task_details = task.get("task_details")

            agent_url = self.agent_manager.get_agent_url(agent_id)
            if not agent_url:
                self.logger.error(f"Task {i+1}: Agent {agent_id} not found. Aborting workflow.")
                self._update_workflow_status(workflow_id, "failed")
                return

            try:
                response = requests.post(f"{agent_url}/execute", json=task_details, timeout=60)
                response.raise_for_status()

                result = response.json()
                results.append(result)
                self._update_workflow_results(workflow_id, results)
                self.logger.info(f"Task {i+1} completed by agent {agent_id}.")
            except requests.RequestException as e:
                self.logger.error(f"Task {i+1} failed: HTTP request to agent {agent_id} failed: {e}. Aborting workflow.")
                self._update_workflow_status(workflow_id, "failed")
                return

        self._update_workflow_status(workflow_id, "completed")
        self.logger.info(f"Workflow '{workflow['name']}' ({workflow_id}) completed successfully.")

    def get_workflow_status(self, workflow_id: str, user_id: int) -> dict:
        """
        Gets the status and results of a workflow, ensuring it belongs to the user.
        """
        workflow = self._get_workflow_from_db(workflow_id, user_id)
        if not workflow:
            return None
        return {
            "id": workflow["id"],
            "name": workflow["name"],
            "status": workflow["status"],
            "results": json.loads(workflow["results"]) if workflow["results"] else []
        }

    def get_workflows_for_user(self, user_id: int) -> list:
        """Retrieves all workflows for a given user."""
        conn = get_db_connection()
        workflows_cursor = conn.execute("SELECT id, name, status FROM workflows WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [dict(row) for row in workflows_cursor]

    def _get_workflow_from_db(self, workflow_id: str, user_id: int = None):
        conn = get_db_connection()
        if user_id:
            workflow = conn.execute("SELECT * FROM workflows WHERE id = ? AND user_id = ?", (workflow_id, user_id)).fetchone()
        else:
            workflow = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        conn.close()
        return workflow

    def _update_workflow_status(self, workflow_id: str, status: str):
        conn = get_db_connection()
        conn.execute("UPDATE workflows SET status = ? WHERE id = ?", (status, workflow_id))
        conn.commit()
        conn.close()

    def _update_workflow_results(self, workflow_id: str, results: list):
        conn = get_db_connection()
        conn.execute("UPDATE workflows SET results = ? WHERE id = ?", (json.dumps(results), workflow_id))
        conn.commit()
        conn.close()
