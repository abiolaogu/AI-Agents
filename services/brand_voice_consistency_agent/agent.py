# services/brand_voice_consistency_agent/agent.py
from agent_framework.agent import BaseAgent

class BrandVoiceConsistencyAgent(BaseAgent):
    def execute(self, data):
        self.logger.info(f"Executing brand voice consistency task with data: {data}")

        text = data.get("text")
        brand_voice = data.get("brand_voice") # e.g., "formal", "casual", "humorous"

        if not all([text, brand_voice]):
            return {"status": "error", "message": "Missing required fields: text, brand_voice."}

        # Placeholder logic: a real implementation would use NLP to analyze the text.
        # For now, we'll just check for keywords.
        is_consistent = False
        if brand_voice == "formal" and "please" in text.lower():
            is_consistent = True
        elif brand_voice == "casual" and "hey" in text.lower():
            is_consistent = True
        elif brand_voice == "humorous" and "lol" in text.lower():
            is_consistent = True

        if is_consistent:
            return {"status": "success", "message": "Text is consistent with brand voice.", "consistent": True}
        else:
            return {"status": "success", "message": "Text is not consistent with brand voice.", "consistent": False}
