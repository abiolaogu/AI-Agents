import os
import logging
from flask import Flask, request, jsonify
from .agent import MeetingSchedulingAgent

app = Flask(__name__)

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instantiate the agent
agent_id = "meeting_scheduling_agent_001"
agent = MeetingSchedulingAgent(agent_id=agent_id, logger=logger)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    result = agent.execute(data)
    return jsonify(result)