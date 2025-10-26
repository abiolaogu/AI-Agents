# services/lead_scoring_agent/lead_scoring_agent/main.py

import logging
from flask import Flask, request, jsonify

from .agent import LeadScoringAgent

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Initialize Agent ---
agent = LeadScoringAgent(agent_id="lead_scoring_agent_001", logger=logger)

# --- API Endpoints ---

@app.route("/execute", methods=["POST"])
def execute_task():
    """
    Executes a task on the agent.
    Expects a JSON payload with the task details.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing task details in request body"}), 400

    try:
        result = agent.execute(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == "__main__":
    # The port should be unique for this agent
    app.run(host="0.0.0.0", port=5002)
