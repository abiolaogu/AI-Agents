import logging
import httpx
import json
import time
from uuid import uuid4
from sqlalchemy import select, update
from .database import get_db_session, Workflow
from .tasks import execute_workflow_task
from .analytics_manager import AnalyticsManager

class WorkflowManager:
    """Manages the creation, execution, and state of agent workflows using a database."""

    def __init__(self, agent_manager, analytics_manager, logger: logging.Logger):
        self.agent_manager = agent_manager
        self.analytics_manager = analytics_manager
        self.logger = logger

    async def create_and_dispatch_workflow(self, name: str, tasks: list, user_id: int) -> str:
        """
        Creates a new workflow, persists it, and dispatches it to the task queue.
        """
        workflow_id = str(uuid4())
        session = await get_db_session()
        try:
            workflow = Workflow(
                id=workflow_id,
                name=name,
                tasks=json.dumps(tasks),
                status="pending",
                results=json.dumps([]),
                user_id=user_id
            )
            session.add(workflow)
            await session.commit()
        finally:
            await session.close()

        self.logger.info(f"Workflow '{name}' ({workflow_id}) for user {user_id} created.")
        await self.analytics_manager.log_event("workflow_created", workflow_id=workflow_id, user_id=user_id)

        execute_workflow_task.delay(workflow_id)
        self.logger.info(f"Dispatched workflow {workflow_id} to Celery.")

        return workflow_id

    async def execute_workflow(self, workflow_id: str):
        """
        Executes a given workflow.
        """
        workflow = await self._get_workflow_from_db(workflow_id)
        if not workflow:
            self.logger.error(f"Workflow {workflow_id} not found.")
            return

        user_id = workflow.user_id
        self.logger.info(f"Executing workflow '{workflow.name}' ({workflow_id})...")
        await self._update_workflow_status(workflow_id, "running")
        start_time = time.time()
        await self.analytics_manager.log_event("workflow_started", workflow_id=workflow_id, user_id=user_id)

        tasks = json.loads(workflow.tasks)
        results = []
        final_status = "completed"

        async with httpx.AsyncClient() as client:
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
                    response = await client.post(f"{agent_url}/execute", json=task_details, timeout=60)
                    response.raise_for_status()

                    result = response.json()
                    results.append(result)
                    task_duration = time.time() - task_start_time
                    await self.analytics_manager.log_event(
                        "agent_task_completed", workflow_id=workflow_id, agent_id=agent_id,
                        duration=task_duration, status="success", user_id=user_id
                    )
                    self.logger.info(f"Task {i+1} completed by agent {agent_id}.")
                except httpx.RequestError as e:
                    self.logger.error(f"Task {i+1} failed: Request to {agent_id} failed: {e}. Aborting.")
                    final_status = "failed"
                    task_duration = time.time() - task_start_time
                    await self.analytics_manager.log_event(
                        "agent_task_failed", workflow_id=workflow_id, agent_id=agent_id,
                        duration=task_duration, status="failed", user_id=user_id
                    )
                    break

        await self._update_workflow_results(workflow_id, results)
        await self._update_workflow_status(workflow_id, final_status)
        workflow_duration = time.time() - start_time
        await self.analytics_manager.log_event(
            "workflow_finished", workflow_id=workflow_id, duration=workflow_duration,
            status=final_status, user_id=user_id
        )
        self.logger.info(f"Workflow '{workflow.name}' ({workflow_id}) finished with status '{final_status}'.")

    async def get_workflow_status(self, workflow_id: str, user_id: int) -> dict:
        """
        Gets the status and results of a workflow, ensuring it belongs to the user.
        """
        workflow = await self._get_workflow_from_db(workflow_id, user_id)
        if not workflow:
            return None
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status,
            "results": json.loads(workflow.results) if workflow.results else []
        }

    async def get_workflows_for_user(self, user_id: int) -> list:
        """Retrieves all workflows for a given user."""
        session = await get_db_session()
        try:
            result = await session.execute(select(Workflow).where(Workflow.user_id == user_id))
            workflows = result.scalars().all()
            return [
                {"id": w.id, "name": w.name, "status": w.status}
                for w in workflows
            ]
        finally:
            await session.close()

    async def _get_workflow_from_db(self, workflow_id: str, user_id: int = None):
        session = await get_db_session()
        try:
            query = select(Workflow).where(Workflow.id == workflow_id)
            if user_id:
                query = query.where(Workflow.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().first()
        finally:
            await session.close()

    async def _update_workflow_status(self, workflow_id: str, status: str):
        session = await get_db_session()
        try:
            await session.execute(
                update(Workflow).where(Workflow.id == workflow_id).values(status=status)
            )
            await session.commit()
        finally:
            await session.close()

    async def _update_workflow_results(self, workflow_id: str, results: list):
        session = await get_db_session()
        try:
            await session.execute(
                update(Workflow).where(Workflow.id == workflow_id).values(results=json.dumps(results))
            )
            await session.commit()
        finally:
            await session.close()
