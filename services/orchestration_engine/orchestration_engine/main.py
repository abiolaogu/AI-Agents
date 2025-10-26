# services/orchestration_engine/orchestration_engine/main.py

import logging
from flask import Flask, request, jsonify

from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from . import database

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Database Initialization ---
database.init_db()

app = Flask(__name__)

# --- Initialize Managers ---
agent_manager = AgentManager(logger=logger)
workflow_manager = WorkflowManager(agent_manager=agent_manager, logger=logger)

# --- Agent Registration ---
SEO_AGENT_URL = "http://seo-agent:5001"
LEAD_SCORING_AGENT_URL = "http://lead-scoring-agent:5002"

agent_manager.register_agent(agent_id="seo_agent_001", agent_url=SEO_AGENT_URL)
agent_manager.register_agent(agent_id="lead_scoring_agent_001", agent_url=LEAD_SCORING_AGENT_URL)

# --- API Endpoints ---

@app.route("/workflows", methods=["POST"])
def create_workflow():
    """
    Creates a new workflow and dispatches it to the task queue.
    """
    data = request.get_json()
    if not data or "name" not in data or "tasks" not in data:
        return jsonify({"error": "Missing 'name' or 'tasks' in request body"}), 400

    # This now creates the workflow in the DB and dispatches the task
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

@app.route("/agents", methods=["GET"])
def list_agents():
    """
    Lists all registered agents.
    """
    agents = agent_manager.list_agents()
    return jsonify({"agents": agents})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
