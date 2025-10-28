# services/meeting_scheduling_agent/agent.py
from agent_framework.agent import BaseAgent
from datetime import datetime

class MeetingSchedulingAgent(BaseAgent):
    def execute(self, data):
        self.logger.info(f"Executing meeting scheduling task with data: {data}")

        # Extract meeting details from the input data
        participants = data.get("participants") # Expected to be a list of emails
        time_str = data.get("time") # Expected to be in ISO 8601 format
        topic = data.get("topic")

        if not all([participants, time_str, topic]):
            return {"status": "error", "message": "Missing required fields: participants, time, topic."}

        try:
            # Parse the time and format it for the confirmation
            meeting_time = datetime.fromisoformat(time_str)
            formatted_time = meeting_time.strftime("%A, %B %d, %Y at %I:%M %p")
        except ValueError:
            return {"status": "error", "message": "Invalid time format. Please use ISO 8601 format."}

        # In the future, this is where an integration with a calendar API (e.g., Google Calendar) would go.
        # For now, we just format a confirmation message.

        confirmation_message = (
            f"Meeting scheduled successfully!\n"
            f"Topic: {topic}\n"
            f"Time: {formatted_time}\n"
            f"Participants: {', '.join(participants)}"
        )

        self.logger.info(f"Task execution finished. Result: {confirmation_message}")
        return {"status": "success", "message": confirmation_message}
