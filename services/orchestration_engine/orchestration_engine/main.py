# services/orchestration_engine/orchestration_engine/main.py

import logging
from flask import Flask, request, jsonify, g
from flask_cors import CORS

from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from .analytics_manager import AnalyticsManager
from . import database
from .auth import register_user, authenticate_user, token_required

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Initialization ---
database.init_db()

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Initialize Managers ---
agent_manager = AgentManager(logger=logger)
analytics_manager = AnalyticsManager(logger=logger)
workflow_manager = WorkflowManager(agent_manager=agent_manager, analytics_manager=analytics_manager, logger=logger)

# --- Agent Registration ---
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
agent_manager.register_agent("crm_data_entry_agent_001", {
    "url": "http://crm-data-entry-agent:5004",
    "name": "CRM Data Entry Agent",
    "description": "Enters new contacts into the CRM.",
    "category": "Sales"
})
agent_manager.register_agent("meeting_scheduling_agent_001", {
    "url": "http://meeting-scheduling-agent:5005",
    "name": "Meeting Scheduling Agent",
    "description": "Schedules meetings with clients and team members.",
    "category": "Sales"
})
agent_manager.register_agent("proposal_generation_agent_001", {
    "url": "http://proposal-generation-agent:5006",
    "name": "Proposal Generation Agent",
    "description": "Generates proposals for clients.",
    "category": "Sales"
})

# --- API Endpoints ---

@app.route("/auth/register", methods=["POST"])
def handle_register():
    """Registers a new user."""
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing 'username' or 'password'"}), 400

    if register_user(data["username"], data["password"]):
        return jsonify({"message": "User registered successfully"}), 201
    else:
        return jsonify({"error": "Username already exists"}), 409

@app.route("/auth/login", methods=["POST"])
def handle_login():
    """Logs in a user and returns a JWT."""
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Missing 'username' or 'password'"}), 400

    token = authenticate_user(data["username"], data["password"])
    if token:
        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/agents/library", methods=["GET"])
def get_agent_library():
    """Returns a list of all available agents for the Agent Marketplace."""
    agents = agent_manager.list_agents_details()
    return jsonify(agents)

@app.route("/workflows", methods=["POST"])
@token_required
def create_workflow():
    """Creates a new workflow for the logged-in user."""
    data = request.get_json()
    if not data or "name" not in data or "tasks" not in data:
        return jsonify({"error": "Missing 'name' or 'tasks' in request body"}), 400

    user_id = g.current_user['id']
    workflow_id = workflow_manager.create_and_dispatch_workflow(data["name"], data["tasks"], user_id)

    return jsonify({
        "message": "Workflow created and dispatched for execution.",
        "workflow_id": workflow_id,
        "status_url": f"/workflows/{workflow_id}"
    }), 202

@app.route("/workflows", methods=["GET"])
@token_required
def get_user_workflows():
    """Gets all workflows for the logged-in user."""
    user_id = g.current_user['id']
    workflows = workflow_manager.get_workflows_for_user(user_id)
    return jsonify(workflows)

@app.route("/workflows/<workflow_id>", methods=["GET"])
@token_required
def get_workflow_status(workflow_id):
    """Gets the status of a specific workflow."""
    user_id = g.current_user['id']
    status_info = workflow_manager.get_workflow_status(workflow_id, user_id)
    if status_info is None:
        return jsonify({"error": "Workflow not found or access denied"}), 404

    return jsonify(status_info)

@app.route("/analytics/events", methods=["GET"])
@token_required
def get_analytics_events():
    """Gets all analytics events for the logged-in user."""
    user_id = g.current_user['id']
    events = analytics_manager.get_events_for_user(user_id)
    return jsonify(events)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
