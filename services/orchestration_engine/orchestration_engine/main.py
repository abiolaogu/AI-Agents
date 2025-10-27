# services/orchestration_engine/orchestration_engine/main.py

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS # Import CORS

from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from . import database

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Initialization ---
database.init_db()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Initialize Managers ---
agent_manager = AgentManager(logger=logger)
workflow_manager = WorkflowManager(agent_manager=agent_manager, logger=logger)

# --- Agent Registration ---
# In a real system, this would be dynamic (e.g., from a config file or service discovery).
agent_manager.register_agent("seo_agent_001", {
    "url": "http://seo-agent:5001",
    "name": "SEO Content Optimizer",
    "description": "Analyzes and optimizes website content for better search engine rankings.",
    "category": "Marketing"
})
agent_manager.register_agent("lead_scoring_agent_001", {
    "url": "http://lead-scoring-agent:5002",
    "name": "Lead Scoring Agent",
    "description": "Scores and prioritizes leads based on various data points.",
    "category": "Sales"
})
agent_manager.register_agent("social_media_agent_001", {
    "url": "http://social-media-agent:5003",
    "name": "Social Media Poster",
    "description": "Automates posting content to various social media platforms.",
    "category": "Marketing"
})
agent_manager.register_agent("email_campaign_agent_001", {
    "url": "http://email-campaign-agent:5004",
    "name": "Email Campaign Manager",
    "description": "Manages and sends out targeted email marketing campaigns.",
    "category": "Marketing"
})

# --- API Endpoints ---

@app.route("/agents/library", methods=["GET"])
def get_agent_library():
    """
    Returns a list of all available agents for the Agent Marketplace.
    """
    agents = agent_manager.list_agents_details()
    return jsonify(agents)

@app.route("/workflows", methods=["POST"])
def create_workflow():
    """
    Creates a new workflow and dispatches it to the task queue.
    """
    data = request.get_json()
    if not data or "name" not in data or "tasks" not in data:
        return jsonify({"error": "Missing 'name' or 'tasks' in request body"}), 400

    workflow_id = workflow_manager.create_and_dispatch_workflow(data["name"], data["tasks"])

    return jsonify({
        "message": "Workflow created and dispatched for execution.",
        "workflow_id": workflow_id,
        "status_url": f"/workflows/{workflow_id}"
    }), 202

@app.route("/workflows/<workflow_id>", methods=["GET"])
def get_workflow_status(workflow_id):
    """
    Gets the status of a specific workflow.
    """
    status_info = workflow_manager.get_workflow_status(workflow_id)
    if status_info is None:
        return jsonify({"error": "Workflow not found"}), 404

    return jsonify(status_info)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
