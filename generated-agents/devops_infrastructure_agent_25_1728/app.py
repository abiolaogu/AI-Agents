"""
DevOps & Infrastructure Agent #25
Specialized agent for DevOps & infrastructure automation (agent 25)

Auto-generated from catalog definition: devops_infrastructure_agent_25_1728
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Use environment variables for sensitive values
class Config:
    APP_NAME = "devops-infrastructure-agent-25-1728"
    VERSION = "1.0.0"
    PORT = int(os.getenv("AGENT_PORT", 8328))
    CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", os.getenv("CLAUDE_API_KEY", ""))
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

config = Config()

# Validate API key at startup
if not config.CLAUDE_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not set. API calls will fail until configured.")

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
class DevopsAndInfrastructureAgent25Service:
    """Main agent service"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.prompt_template = """{prompt_template}"""
        self.system_prompt = """{system_prompt}"""

    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        """Execute agent task"""
        start_time = datetime.now(timezone.utc)
        requests_counter.labels(agent_id=config.APP_NAME).inc()

        try:
            if not config.CLAUDE_API_KEY:
                raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

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
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return AgentResponse(
                result=result_text,
                metadata={
                    "agent_id": config.APP_NAME,
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                },
                processing_time_ms=processing_time
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Application
app = FastAPI(
    title="DevOps & Infrastructure Agent #25",
    description="Specialized agent for DevOps & infrastructure automation (agent 25)",
    version=config.VERSION
)

service = DevopsAndInfrastructureAgent25Service(config.CLAUDE_API_KEY, config.CLAUDE_MODEL)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_id": config.APP_NAME,
        "version": config.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
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
        "name": "DevOps & Infrastructure Agent #25",
        "version": config.VERSION,
        "status": "operational",
        "category": "devops_infrastructure"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
