"""Travel Agent AI Agent - Itinerary optimization and booking assistance"""
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import anthropic
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

class Config:
    APP_NAME, VERSION, PORT = "travel-agent", "1.0.0", 8100
    CLAUDE_API_KEY, CLAUDE_MODEL = "your-api-key-here", "claude-3-5-sonnet-20241022"

config = Config()
app = FastAPI(title="Travel Agent AI Agent", version=config.VERSION)
itineraries_counter = Counter('travel_itineraries_total', 'Total itineraries')

class TravelRequest(BaseModel):
    destination: str
    duration_days: int
    budget: float
    interests: List[str]

class ItineraryResponse(BaseModel):
    destination: str
    daily_plans: List[Dict]
    estimated_cost: float
    recommendations: List[str]

class TravelService:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def create_itinerary(self, request: TravelRequest) -> ItineraryResponse:
        itineraries_counter.inc()

        daily_plans = [
            {"day": i+1, "activities": ["Morning: City tour", "Afternoon: Museum", "Evening: Local restaurant"]}
            for i in range(request.duration_days)
        ]

        return ItineraryResponse(
            destination=request.destination,
            daily_plans=daily_plans,
            estimated_cost=request.budget * 0.95,
            recommendations=["Book flights 2 months early", "Get travel insurance"]
        )

service = TravelService(config.CLAUDE_API_KEY)

@app.get("/health")
async def health(): return {"status": "healthy", "version": config.VERSION}

@app.post("/api/v1/itinerary", response_model=ItineraryResponse)
async def create_itinerary(request: TravelRequest):
    return await service.create_itinerary(request)

@app.get("/metrics")
async def metrics(): return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
