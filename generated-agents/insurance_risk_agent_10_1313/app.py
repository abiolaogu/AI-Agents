"""
Insurance & Risk Agent #10
Specialized agent for insurance & risk management (agent 10)

Auto-generated from catalog definition: insurance_risk_agent_10_1313
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    APP_NAME = "insurance-risk-agent-10-1313"
    VERSION = "1.0.0"
    PORT = 8713
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    MAX_TOKENS = 4096
    TEMPERATURE = 0.7

config = Config()

# Metrics
requests_counter = Counter('agent_requests_total', 'Total requests', ['agent_id'])
processing_duration = Histogram('agent_processing_seconds', 'Processing duration')

# Data Models
class AgentRequest(BaseModel):
    task_description: str
    context: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]
    processing_time_ms: float

# Service
class InsuranceAndRiskAgent10Service:
    """Main agent service"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.prompt_template = """{prompt_template}"""
        self.system_prompt = """{system_prompt}"""

    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        """Execute agent task"""
        start_time = datetime.utcnow()
        requests_counter.labels(agent_id=config.APP_NAME).inc()

        try:
            # Format prompt
            prompt = self.prompt_template.format(task_description=request.task_description)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            result_text = response.content[0].text if response.content else "No response"
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResponse(
                result=result_text,
                metadata={
                    "agent_id": config.APP_NAME,
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Application
app = FastAPI(
    title="Insurance & Risk Agent #10",
    description="Specialized agent for insurance & risk management (agent 10)",
    version=config.VERSION
)

service = InsuranceAndRiskAgent10Service(config.CLAUDE_API_KEY, config.CLAUDE_MODEL)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_id": config.APP_NAME,
        "version": config.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/execute", response_model=AgentResponse)
async def execute_task(request: AgentRequest):
    try:
        return await service.execute_task(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    return {
        "agent_id": config.APP_NAME,
        "name": "Insurance & Risk Agent #10",
        "version": config.VERSION,
        "status": "operational",
        "category": "insurance_risk"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
