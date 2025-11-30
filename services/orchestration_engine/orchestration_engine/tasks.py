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

    import asyncio
    from .analytics_manager import AnalyticsManager

    logger = logging.getLogger(__name__)
    agent_manager = AgentManager(logger=logger)
    analytics_manager = AnalyticsManager(logger=logger)

    # Re-register agents for the worker context
    agent_manager.register_agent("seo_agent_001", {
        "url": "http://seo-agent:5001", "name": "SEO Content Optimizer",
        "description": "Analyzes and optimizes website content for better search engine rankings.", "category": "Marketing"
    })
    agent_manager.register_agent("lead_scoring_agent_001", {
        "url": "http://lead-scoring-agent:5002", "name": "Lead Scoring Agent",
        "description": "Scores and prioritizes leads based on various data points.", "category": "Sales"
    })
    agent_manager.register_agent("social_media_agent_001", {
        "url": "http://social-media-agent:5003", "name": "Social Media Poster",
        "description": "Automates posting content to various social media platforms.", "category": "Marketing"
    })
    agent_manager.register_agent("email_campaign_agent_001", {
        "url": "http://email-campaign-agent:5004", "name": "Email Campaign Manager",
        "description": "Manages and sends out targeted email marketing campaigns.", "category": "Marketing"
    })
    agent_manager.register_agent("crm_data_entry_agent_001", {
        "url": "http://crm-data-entry-agent:5004", "name": "CRM Data Entry Agent",
        "description": "Enters new contacts into the CRM.", "category": "Sales"
    })
    agent_manager.register_agent("meeting_scheduling_agent_001", {
        "url": "http://meeting-scheduling-agent:5005", "name": "Meeting Scheduling Agent",
        "description": "Schedules meetings with clients and team members.", "category": "Sales"
    })
    agent_manager.register_agent("proposal_generation_agent_001", {
        "url": "http://proposal-generation-agent:5006", "name": "Proposal Generation Agent",
        "description": "Generates proposals for clients.", "category": "Sales"
    })

    workflow_manager = WorkflowManager(agent_manager=agent_manager, analytics_manager=analytics_manager, logger=logger)

    logger.info(f"Celery task started for workflow {workflow_id}")
    asyncio.run(workflow_manager.execute_workflow(workflow_id))
    logger.info(f"Celery task finished for workflow {workflow_id}")
