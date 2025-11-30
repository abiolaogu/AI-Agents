import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from . import database
from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from .analytics_manager import AnalyticsManager
from .auth import register_user, authenticate_user, get_current_user
from .schemas import UserCreate, UserLogin, WorkflowCreate
from .database import get_db, User

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .redpanda_manager import RedpandaManager

# --- Initialize Managers ---
agent_manager = AgentManager(logger=logger)
redpanda_manager = RedpandaManager(logger=logger)
analytics_manager = AnalyticsManager(logger=logger, redpanda_manager=redpanda_manager)
workflow_manager = WorkflowManager(agent_manager=agent_manager, analytics_manager=analytics_manager, logger=logger)

# --- Agent Registration ---
# Agents are now loaded dynamically from the definitions directory by AgentManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.init_db()
    await redpanda_manager.start()
    yield
    # Shutdown
    await redpanda_manager.stop()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def handle_register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new user."""
    if await register_user(user.username, user.password, db):
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

@app.post("/auth/login")
async def handle_login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """Logs in a user and returns a JWT."""
    token = await authenticate_user(user.username, user.password, db)
    if token:
        return {"token": token}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@app.get("/agents/library")
async def get_agent_library():
    """Returns a list of all available agents for the Agent Marketplace."""
    agents = agent_manager.list_agents_details()
    return agents

@app.post("/workflows", status_code=status.HTTP_202_ACCEPTED)
async def create_workflow(workflow: WorkflowCreate, current_user: User = Depends(get_current_user)):
    """Creates a new workflow for the logged-in user."""
    workflow_id = await workflow_manager.create_and_dispatch_workflow(
        workflow.name, 
        [task.dict() for task in workflow.tasks], 
        current_user.id
    )

    return {
        "message": "Workflow created and dispatched for execution.",
        "workflow_id": workflow_id,
        "status_url": f"/workflows/{workflow_id}"
    }

@app.get("/workflows")
async def get_user_workflows(current_user: User = Depends(get_current_user)):
    """Gets all workflows for the logged-in user."""
    workflows = await workflow_manager.get_workflows_for_user(current_user.id)
    return workflows

@app.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str, current_user: User = Depends(get_current_user)):
    """Gets the status of a specific workflow."""
    status_info = await workflow_manager.get_workflow_status(workflow_id, current_user.id)
    if status_info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found or access denied")

    return status_info

@app.get("/analytics/events")
async def get_analytics_events(current_user: User = Depends(get_current_user)):
    """Gets all analytics events for the logged-in user."""
    events = await analytics_manager.get_events_for_user(current_user.id)
    return events

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
