import logging
import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from .agent import SeoAgent

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Initialize Agent ---
agent = SeoAgent(agent_id="seo_agent_001", logger=logger)

class TaskRequest(BaseModel):
    url: str
    # Add other task parameters as needed

@app.post("/execute", status_code=status.HTTP_200_OK)
async def execute_task(task: Dict[str, Any]):
    """
    Executes a task on the agent.
    Expects a JSON payload with the task details.
    """
    if not task:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing task details in request body")

    try:
        result = await agent.execute(task)
        return result
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
