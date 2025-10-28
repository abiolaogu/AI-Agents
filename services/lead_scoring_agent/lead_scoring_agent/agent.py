# services/lead_scoring_agent/lead_scoring_agent/agent.py

import logging
from agent_framework.agent import BaseAgent

class LeadScoringAgent(BaseAgent):
    """An agent that scores leads based on provided data."""

    def __init__(self, agent_id: str, logger: logging.Logger):
        """Initializes the LeadScoringAgent."""
        super().__init__(agent_id, logger)

    def execute(self, task: dict) -> dict:
        """
        Executes a lead scoring task.

        Args:
            task: A dictionary with lead details, e.g.,
                  {"company_size": 150, "industry": "tech", "engagement_score": 75}.

        Returns:
            A dictionary with the lead score and priority.
        """
        self.logger.info(f"Executing lead scoring task for data: {task}")

        # Placeholder logic for lead scoring
        score = 0
        company_size = task.get("company_size", 0)
        engagement_score = task.get("engagement_score", 0)

        if company_size > 100:
            score += 30
        elif company_size > 50:
            score += 15

        if task.get("industry") == "tech":
            score += 20

        score += (engagement_score / 10) # Add up to 10 points for engagement

        priority = "low"
        if int(score) > 50:
            priority = "high"
        elif int(score) > 30:
            priority = "medium"

        return {
            "status": "success",
            "message": "Lead scoring complete.",
            "lead_score": int(score),
            "priority": priority
        }
