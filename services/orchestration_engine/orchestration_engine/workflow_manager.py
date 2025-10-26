# services/orchestration_engine/orchestration_engine/workflow_manager.py

import logging
from uuid import uuid4

class WorkflowManager:
    """Manages the creation and execution of agent workflows."""

    def __init__(self, agent_manager, logger: logging.Logger):
        """
        Initializes the WorkflowManager.

        Args:
            agent_manager: An instance of AgentManager.
            logger: A logger instance.
        """
        self.agent_manager = agent_manager
        self.workflows = {}
        self.logger = logger

    def create_workflow(self, name: str, tasks: list):
        """
        Creates a new workflow.

        Args:
            name: The name of the workflow.
            tasks: A list of task dictionaries. Each task should have 'agent_id' and 'task_details'.

        Returns:
            The ID of the newly created workflow.
        """
        workflow_id = str(uuid4())
        self.workflows[workflow_id] = {
            "name": name,
            "tasks": tasks,
            "status": "pending",
        }
        self.logger.info(f"Workflow '{name}' ({workflow_id}) created.")
        return workflow_id

    def execute_workflow(self, workflow_id: str):
        """
        Executes a given workflow.

        Args:
            workflow_id: The ID of the workflow to execute.
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found.")
            return

        self.logger.info(f"Executing workflow '{workflow['name']}' ({workflow_id})...")
        workflow["status"] = "running"

        results = []
        for i, task in enumerate(workflow["tasks"]):
            agent_id = task.get("agent_id")
            task_details = task.get("task_details")

            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                self.logger.error(f"Task {i+1}: Agent {agent_id} not found. Aborting workflow.")
                workflow["status"] = "failed"
                return

            try:
                self.agent_manager.set_agent_status(agent_id, "running")
                result = agent.execute(task_details)
                results.append(result)
                self.agent_manager.set_agent_status(agent_id, "idle")
                self.logger.info(f"Task {i+1} completed by agent {agent_id}.")
            except Exception as e:
                self.logger.error(f"Task {i+1} failed: {e}. Aborting workflow.")
                self.agent_manager.set_agent_status(agent_id, "error")
                workflow["status"] = "failed"
                return

        workflow["status"] = "completed"
        self.logger.info(f"Workflow '{workflow['name']}' ({workflow_id}) completed successfully.")
        return results
