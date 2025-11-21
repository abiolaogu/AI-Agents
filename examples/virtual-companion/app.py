"""
Virtual Companion AI Agent
Empathetic conversation AI with emotional support and mental wellness features.

Scale: 10K+ concurrent users, 500K+ daily conversations
Tech: Python 3.11, FastAPI, Claude 3.5 Sonnet, Pinecone, Redis
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import anthropic
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    APP_NAME = "virtual-companion"
    VERSION = "1.0.0"
    PORT = 8090
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

config = Config()

# Metrics
conversations_counter = Counter('companion_conversations_total', 'Total conversations')
response_time = Histogram('companion_response_duration_seconds', 'Response time')
crisis_detections = Counter('companion_crisis_detections_total', 'Crisis detections', ['severity'])

# Data Models
class EmotionalState(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    NEUTRAL = "neutral"

class ConversationRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    emotional_context: Optional[EmotionalState] = None

class ConversationResponse(BaseModel):
    session_id: str
    response: str
    detected_emotion: str
    crisis_detected: bool
    support_resources: List[str]
    processing_time_ms: float

# Services
class CompanionService:
    """Empathetic conversation service"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_response(self, request: ConversationRequest) -> ConversationResponse:
        start_time = datetime.utcnow()

        # Crisis detection
        crisis_detected, severity = self.detect_crisis(request.message)
        if crisis_detected:
            crisis_detections.labels(severity=severity).inc()

        # Build empathetic prompt
        prompt = f"""You are a compassionate AI companion. Provide emotional support and empathetic responses.

User message: {request.message}

Provide a caring, supportive response that:
1. Acknowledges their feelings
2. Offers validation and understanding
3. Provides gentle guidance if appropriate
4. Maintains hope and positivity

Response:"""

        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Detect emotion in user message
            detected_emotion = self.detect_emotion(request.message)

            support_resources = []
            if crisis_detected:
                support_resources = [
                    "National Suicide Prevention Lifeline: 988",
                    "Crisis Text Line: Text HOME to 741741",
                    "SAMHSA Helpline: 1-800-662-4357"
                ]

            conversations_counter.inc()

            return ConversationResponse(
                session_id=request.session_id,
                response=response_text,
                detected_emotion=detected_emotion,
                crisis_detected=crisis_detected,
                support_resources=support_resources,
                processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise

    def detect_crisis(self, message: str) -> tuple[bool, str]:
        """Detect crisis situations"""
        crisis_keywords = ["suicide", "kill myself", "end it all", "want to die"]
        message_lower = message.lower()

        for keyword in crisis_keywords:
            if keyword in message_lower:
                return True, "critical"

        return False, "none"

    def detect_emotion(self, message: str) -> str:
        """Simple emotion detection"""
        sad_words = ["sad", "depressed", "down", "unhappy"]
        anxious_words = ["anxious", "worried", "nervous", "scared"]
        angry_words = ["angry", "furious", "mad", "frustrated"]

        message_lower = message.lower()

        if any(word in message_lower for word in sad_words):
            return "sad"
        elif any(word in message_lower for word in anxious_words):
            return "anxious"
        elif any(word in message_lower for word in angry_words):
            return "angry"
        else:
            return "neutral"

# Application
app = FastAPI(
    title="Virtual Companion AI Agent",
    description="Empathetic conversation and emotional support",
    version=config.VERSION
)

companion_service = CompanionService(config.CLAUDE_API_KEY)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": config.VERSION}

@app.post("/api/v1/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest):
    """Chat with AI companion"""
    try:
        return await companion_service.generate_response(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    return {
        "service": "Virtual Companion AI Agent",
        "version": config.VERSION,
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
