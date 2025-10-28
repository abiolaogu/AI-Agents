# services/proposal_generation_agent/agent.py
from agent_framework.agent import BaseAgent

class ProposalGenerationAgent(BaseAgent):
    def execute(self, data):
        self.logger.info(f"Executing proposal generation task with data: {data}")

        # Extract proposal details from the input data
        client_name = data.get("client_name")
        project_scope = data.get("project_scope")
        budget = data.get("budget")

        if not all([client_name, project_scope, budget]):
            return {"status": "error", "message": "Missing required fields: client_name, project_scope, budget."}

        try:
            # Format the budget as a currency string
            formatted_budget = f"${budget:,.2f}"
        except (ValueError, TypeError):
            return {"status": "error", "message": "Invalid budget format. Please provide a number."}

        # In the future, this could generate a PDF or a more complex document.
        # For now, we'll create a simple string-based proposal.
        proposal_text = (
            f"--- Proposal for {client_name} ---\n\n"
            f"**Project Scope:**\n{project_scope}\n\n"
            f"**Proposed Budget:** {formatted_budget}\n\n"
            f"--- End of Proposal ---"
        )

        self.logger.info("Proposal generation task finished.")
        return {"status": "success", "proposal_text": proposal_text}
