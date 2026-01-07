import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from . import database
from .agent_manager import AgentManager
from .workflow_manager import WorkflowManager
from .analytics_manager import AnalyticsManager
from .auth import register_user, authenticate_user, get_current_user
from .schemas import UserCreate, UserLogin, WorkflowCreate
from .database import get_db, get_db_session, User
from .rate_limiter import default_rate_limiter, auth_rate_limiter, read_rate_limiter

# API Version
API_VERSION = "1.0.0"
API_V1_PREFIX = "/api/v1"

# --- Setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
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

app = FastAPI(
    title="AI Agents Orchestration Engine",
    description="Multi-agent orchestration platform for AI workflows",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - use environment variable for allowed origins
# In production, set ALLOWED_ORIGINS to comma-separated list of allowed domains
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )

# --- API Routers ---

# V1 API Router
v1_router = APIRouter(prefix=API_V1_PREFIX, tags=["v1"])

# Auth Router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def handle_register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(auth_rate_limiter)
):
    """Registers a new user."""
    if await register_user(user.username, user.password, db):
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")


@auth_router.post("/login")
async def handle_login(
    user: UserLogin,
    db: AsyncSession = Depends(get_db),
    _rate_limit: bool = Depends(auth_rate_limiter)
):
    """Logs in a user and returns a JWT."""
    token = await authenticate_user(user.username, user.password, db)
    if token:
        return {"token": token}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


# Agents Router
agents_router = APIRouter(prefix="/agents", tags=["agents"])


@agents_router.get("/")
async def get_agent_library(_rate_limit: bool = Depends(read_rate_limiter)):
    """Returns a list of all available agents for the Agent Marketplace."""
    return {
        "agents": agent_manager.list_agents_details(),
        "total": agent_manager.get_agent_count()
    }


@agents_router.get("/search")
async def search_agents(query: str, _rate_limit: bool = Depends(read_rate_limiter)):
    """Search agents by name or description."""
    results = agent_manager.search_agents(query)
    return {"results": results, "count": len(results)}


@agents_router.get("/category/{category}")
async def get_agents_by_category(category: str, _rate_limit: bool = Depends(read_rate_limiter)):
    """Get agents by category."""
    agents = agent_manager.list_agents_by_category(category)
    return {"agents": agents, "count": len(agents), "category": category}


@agents_router.get("/{agent_id}")
async def get_agent_details(agent_id: str, _rate_limit: bool = Depends(read_rate_limiter)):
    """Get detailed information about a specific agent."""
    agent = agent_manager.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return {**agent, "id": agent_id}


# Workflows Router
workflows_router = APIRouter(prefix="/workflows", tags=["workflows"])


@workflows_router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(default_rate_limiter)
):
    """Creates a new workflow for the logged-in user."""
    workflow_id = await workflow_manager.create_and_dispatch_workflow(
        workflow.name,
        [task.model_dump() for task in workflow.tasks],
        current_user.id
    )

    return {
        "message": "Workflow created and dispatched for execution.",
        "workflow_id": workflow_id,
        "status_url": f"{API_V1_PREFIX}/workflows/{workflow_id}"
    }


@workflows_router.get("/")
async def get_user_workflows(
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(read_rate_limiter)
):
    """Gets all workflows for the logged-in user."""
    workflows = await workflow_manager.get_workflows_for_user(current_user.id)
    return {"workflows": workflows, "count": len(workflows)}


@workflows_router.get("/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(read_rate_limiter)
):
    """Gets the status of a specific workflow."""
    status_info = await workflow_manager.get_workflow_status(workflow_id, current_user.id)
    if status_info is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found or access denied")

    return status_info


# Analytics Router
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@analytics_router.get("/events")
async def get_analytics_events(
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(read_rate_limiter)
):
    """Gets all analytics events for the logged-in user."""
    events = await analytics_manager.get_events_for_user(current_user.id)
    return {"events": events, "count": len(events)}


# Include routers in v1 router
v1_router.include_router(auth_router)
v1_router.include_router(agents_router)
v1_router.include_router(workflows_router)
v1_router.include_router(analytics_router)

# Include v1 router in app
app.include_router(v1_router)

# Legacy routes (backward compatibility - deprecated)
# These routes maintain backward compatibility but will be removed in v2
@app.post("/auth/register", status_code=status.HTTP_201_CREATED, deprecated=True, tags=["legacy"])
async def legacy_register(user: UserCreate, db: AsyncSession = Depends(get_db), _rate_limit: bool = Depends(auth_rate_limiter)):
    """[DEPRECATED] Use /api/v1/auth/register instead."""
    return await handle_register(user, db, _rate_limit)


@app.post("/auth/login", deprecated=True, tags=["legacy"])
async def legacy_login(user: UserLogin, db: AsyncSession = Depends(get_db), _rate_limit: bool = Depends(auth_rate_limiter)):
    """[DEPRECATED] Use /api/v1/auth/login instead."""
    return await handle_login(user, db, _rate_limit)


@app.get("/agents/library", deprecated=True, tags=["legacy"])
async def legacy_agents(_rate_limit: bool = Depends(read_rate_limiter)):
    """[DEPRECATED] Use /api/v1/agents/ instead."""
    return agent_manager.list_agents_details()


@app.post("/workflows", status_code=status.HTTP_202_ACCEPTED, deprecated=True, tags=["legacy"])
async def legacy_create_workflow(workflow: WorkflowCreate, current_user: User = Depends(get_current_user), _rate_limit: bool = Depends(default_rate_limiter)):
    """[DEPRECATED] Use /api/v1/workflows/ instead."""
    return await create_workflow(workflow, current_user, _rate_limit)


@app.get("/workflows", deprecated=True, tags=["legacy"])
async def legacy_get_workflows(current_user: User = Depends(get_current_user), _rate_limit: bool = Depends(read_rate_limiter)):
    """[DEPRECATED] Use /api/v1/workflows/ instead."""
    return await workflow_manager.get_workflows_for_user(current_user.id)


@app.get("/workflows/{workflow_id}", deprecated=True, tags=["legacy"])
async def legacy_get_workflow(workflow_id: str, current_user: User = Depends(get_current_user), _rate_limit: bool = Depends(read_rate_limiter)):
    """[DEPRECATED] Use /api/v1/workflows/{workflow_id} instead."""
    return await get_workflow_status(workflow_id, current_user, _rate_limit)


# --- Health & Status Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "orchestration-engine",
        "version": "1.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - verifies all dependencies are available."""
    checks = {
        "database": False,
        "redpanda": False
    }

    # Check database connection
    try:
        session = await get_db_session()
        try:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            checks["database"] = True
        finally:
            await session.close()
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")

    # Check Redpanda connection
    checks["redpanda"] = redpanda_manager.is_connected if hasattr(redpanda_manager, 'is_connected') else True

    all_healthy = all(checks.values())
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AI Agents Orchestration Engine",
        "version": API_VERSION,
        "api_versions": {
            "v1": {
                "prefix": API_V1_PREFIX,
                "status": "stable",
                "deprecated": False
            }
        },
        "docs_url": "/docs",
        "health_url": "/health",
        "agents_count": agent_manager.get_agent_count()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
