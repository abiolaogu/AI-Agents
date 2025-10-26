# services/seo_agent/seo_agent/main.py

import logging
from flask import Flask, request, jsonify

from .agent import SeoAgent

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Initialize Agent ---
# In a real system, the agent_id might come from configuration.
agent = SeoAgent(agent_id="seo_agent_001", logger=logger)

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
    # The port should be different from the orchestration engine
    app.run(host="0.0.0.0", port=5001)
