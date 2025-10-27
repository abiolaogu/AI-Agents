# services/orchestration_engine/orchestration_engine/tasks.py

import logging
from .celery_worker import celery

# Import WorkflowManager and AgentManager inside the task to avoid circular imports
# This is a standard pattern for Celery tasks.
@celery.task(name='execute_workflow_task')
def execute_workflow_task(workflow_id: str):
    """
    Celery task to execute a workflow.
    This runs in a separate worker process.
    """
    from .workflow_manager import WorkflowManager
    from .agent_manager import AgentManager

    logger = logging.getLogger(__name__)
    agent_manager = AgentManager(logger=logger)

    # Re-register agents for the worker context
    # This is necessary because the worker is a separate process.
    SEO_AGENT_URL = "http://seo-agent:5001"
    LEAD_SCORING_AGENT_URL = "http://lead-scoring-agent:5002"

    seo_agent_metadata = {
        "name": "SEO Content Optimization Agent",
        "url": SEO_AGENT_URL,
        "description": "Optimizes content for search engines.",
        "category": "Marketing",
        "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}},
        "output_schema": {"type": "object", "properties": {"optimized_text": {"type": "string"}}}
    }
    lead_scoring_agent_metadata = {
        "name": "Lead Scoring Agent",
        "url": LEAD_SCORING_AGENT_URL,
        "description": "Scores leads based on provided data.",
        "category": "Lead Generation",
        "input_schema": {"type": "object", "properties": {"lead_data": {"type": "object"}}},
        "output_schema": {"type": "object", "properties": {"score": {"type": "integer"}}}
    }

    agent_manager.register_agent(agent_id="seo_agent_001", agent_metadata=seo_agent_metadata)
    agent_manager.register_agent(agent_id="lead_scoring_agent_001", agent_metadata=lead_scoring_agent_metadata)

    workflow_manager = WorkflowManager(agent_manager=agent_manager, logger=logger)

    logger.info(f"Celery task started for workflow {workflow_id}")
    workflow_manager.execute_workflow(workflow_id)
    logger.info(f"Celery task finished for workflow {workflow_id}")
