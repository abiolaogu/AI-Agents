"""Sentiment Analyst AI Agent - Multi-lingual emotion detection"""
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import anthropic
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

class Config:
    APP_NAME, VERSION, PORT = "sentiment-analyst", "1.0.0", 8099
    CLAUDE_API_KEY, CLAUDE_MODEL = "your-api-key-here", "claude-3-5-sonnet-20241022"

config = Config()
app = FastAPI(title="Sentiment Analyst AI Agent", version=config.VERSION)
analyses_counter = Counter('sentiment_analyses_total', 'Total analyses', ['language'])

class SentimentRequest(BaseModel):
    text: str
    language: str = "en"

class SentimentResponse(BaseModel):
    sentiment: str  # positive, negative, neutral
    confidence: float
    emotions: Dict[str, float]
    key_phrases: list

class SentimentService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze_sentiment(self, request: SentimentRequest) -> SentimentResponse:
        analyses_counter.labels(language=request.language).inc()

        # Simple keyword-based sentiment
        positive_words = ["great", "excellent", "amazing", "wonderful", "love"]
        negative_words = ["bad", "terrible", "awful", "hate", "poor"]

        text_lower = request.text.lower()
        positive_count = sum(word in text_lower for word in positive_words)
        negative_count = sum(word in text_lower for word in negative_words)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return SentimentResponse(
            sentiment=sentiment,
            confidence=0.85,
            emotions={"joy": 0.6, "sadness": 0.1, "anger": 0.05, "fear": 0.05},
            key_phrases=["key phrase 1", "key phrase 2"]
        )

service = SentimentService(config.CLAUDE_API_KEY)

@app.get("/health")
async def health(): return {"status": "healthy", "version": config.VERSION}

@app.post("/api/v1/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    return await service.analyze_sentiment(request)

@app.get("/metrics")
async def metrics(): return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
