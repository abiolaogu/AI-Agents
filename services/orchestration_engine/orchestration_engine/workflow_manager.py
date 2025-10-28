# services/orchestration_engine/orchestration_engine/workflow_manager.py

import logging
import requests
import json
import time
from uuid import uuid4
from .database import get_db_connection
from .tasks import execute_workflow_task
from .analytics_manager import AnalyticsManager

class WorkflowManager:
    """Manages the creation, execution, and state of agent workflows using a database."""

    def __init__(self, agent_manager, analytics_manager, logger: logging.Logger):
        """
        Initializes the WorkflowManager.

        Args:
            agent_manager: An instance of AgentManager.
            analytics_manager: An instance of AnalyticsManager.
            logger: A logger instance.
        """
        self.agent_manager = agent_manager
        self.analytics_manager = analytics_manager
        self.logger = logger

    def create_and_dispatch_workflow(self, name: str, tasks: list, user_id: int) -> str:
        """
        Creates a new workflow, persists it, and dispatches it to the task queue.
        """
        workflow_id = str(uuid4())
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO workflows (id, name, tasks, status, results, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (workflow_id, name, json.dumps(tasks), "pending", json.dumps([]), user_id),
        )
        conn.commit()
        conn.close()
        self.logger.info(f"Workflow '{name}' ({workflow_id}) for user {user_id} created.")
        self.analytics_manager.log_event("workflow_created", workflow_id=workflow_id, user_id=user_id)

        execute_workflow_task.delay(workflow_id)
        self.logger.info(f"Dispatched workflow {workflow_id} to Celery.")

        return workflow_id

    def execute_workflow(self, workflow_id: str):
        """
        Executes a given workflow. This is now called by the Celery worker.
        """
        workflow = self._get_workflow_from_db(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found.")
            return

        user_id = workflow["user_id"]
        self.logger.info(f"Executing workflow '{workflow['name']}' ({workflow_id})...")
        self._update_workflow_status(workflow_id, "running")
        start_time = time.time()
        self.analytics_manager.log_event("workflow_started", workflow_id=workflow_id, user_id=user_id)

        tasks = json.loads(workflow['tasks'])
        results = []
        final_status = "completed"

        for i, task in enumerate(tasks):
            agent_id = task.get("agent_id")
            task_details = task.get("task_details")

            agent_url = self.agent_manager.get_agent_url(agent_id)
            if not agent_url:
                self.logger.error(f"Task {i+1}: Agent {agent_id} not found. Aborting.")
                final_status = "failed"
                break

            try:
                task_start_time = time.time()
                response = requests.post(f"{agent_url}/execute", json=task_details, timeout=60)
                response.raise_for_status()

                result = response.json()
                results.append(result)
                task_duration = time.time() - task_start_time
                self.analytics_manager.log_event(
                    "agent_task_completed", workflow_id=workflow_id, agent_id=agent_id,
                    duration=task_duration, status="success", user_id=user_id
                )
                self.logger.info(f"Task {i+1} completed by agent {agent_id}.")
            except requests.RequestException as e:
                self.logger.error(f"Task {i+1} failed: Request to {agent_id} failed: {e}. Aborting.")
                final_status = "failed"
                task_duration = time.time() - task_start_time
                self.analytics_manager.log_event(
                    "agent_task_failed", workflow_id=workflow_id, agent_id=agent_id,
                    duration=task_duration, status="failed", user_id=user_id
                )
                break

        self._update_workflow_results(workflow_id, results)
        self._update_workflow_status(workflow_id, final_status)
        workflow_duration = time.time() - start_time
        self.analytics_manager.log_event(
            "workflow_finished", workflow_id=workflow_id, duration=workflow_duration,
            status=final_status, user_id=user_id
        )
        self.logger.info(f"Workflow '{workflow['name']}' ({workflow_id}) finished with status '{final_status}'.")

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
