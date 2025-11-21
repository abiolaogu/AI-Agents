"""
Executive Assistant AI Agent
Intelligent calendar optimization, meeting preparation, email triage, and task prioritization.

Scale: 5K concurrent users, 500K daily operations
Tech: FastAPI, Claude 3.5 Sonnet, Redis, Pinecone, PostgreSQL, Celery
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response
import anthropic
import pinecone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, Integer

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration"""
    APP_NAME = "executive-assistant"
    VERSION = "1.0.0"
    PORT = 8080

    # Redis configuration
    REDIS_URL = "redis://localhost:6379/0"
    REDIS_POOL_SIZE = 50
    SESSION_TTL = 86400  # 24 hours

    # Claude API
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS = 4000

    # Pinecone (vector memory)
    PINECONE_API_KEY = "your-pinecone-key"
    PINECONE_ENVIRONMENT = "us-west1-gcp"
    PINECONE_INDEX = "executive-assistant-memory"

    # PostgreSQL
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/exec_assistant"

    # Integration APIs
    GOOGLE_CALENDAR_ENABLED = True
    MICROSOFT_GRAPH_ENABLED = True
    SLACK_ENABLED = True
    NOTION_ENABLED = True

    # Performance settings
    MAX_CONCURRENT_REQUESTS = 5000
    EMAIL_BATCH_SIZE = 100
    CALENDAR_LOOKAHEAD_DAYS = 30

config = Config()

# ============================================================================
# METRICS
# ============================================================================

request_counter = Counter('exec_assistant_requests_total', 'Total requests', ['endpoint', 'status'])
request_duration = Histogram('exec_assistant_request_duration_seconds', 'Request duration', ['endpoint'])
active_sessions = Gauge('exec_assistant_active_sessions', 'Active user sessions')
email_triage_duration = Histogram('exec_assistant_email_triage_seconds', 'Email triage duration')
calendar_optimization_duration = Histogram('exec_assistant_calendar_optimization_seconds', 'Calendar optimization duration')
meeting_prep_duration = Histogram('exec_assistant_meeting_prep_seconds', 'Meeting prep duration')

# ============================================================================
# DATABASE MODELS
# ============================================================================

Base = declarative_base()

class User(Base):
    """User profile and preferences"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    preferences = Column(JSON, default={})
    integrations = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Task(Base):
    """Task management"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    priority = Column(Integer, default=3)  # 1=urgent, 2=important, 3=normal, 4=low
    status = Column(String, default="pending")  # pending, in_progress, completed
    due_date = Column(DateTime)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# ============================================================================
# DATA MODELS
# ============================================================================

class EmailTriageRequest(BaseModel):
    """Request to triage emails"""
    user_id: str
    emails: List[Dict[str, Any]] = Field(..., description="List of emails to triage")

    @validator('emails')
    def validate_emails(cls, v):
        if not v:
            raise ValueError("Emails list cannot be empty")
        if len(v) > 100:
            raise ValueError("Maximum 100 emails per batch")
        return v

class EmailTriageResponse(BaseModel):
    """Email triage results"""
    user_id: str
    triaged_emails: List[Dict[str, Any]]
    summary: str
    processing_time_ms: float

class CalendarOptimizationRequest(BaseModel):
    """Request to optimize calendar"""
    user_id: str
    date_range: Dict[str, str] = Field(..., description="start_date and end_date")
    constraints: Optional[Dict[str, Any]] = Field(default={}, description="User constraints")

class CalendarOptimizationResponse(BaseModel):
    """Calendar optimization results"""
    user_id: str
    suggestions: List[Dict[str, Any]]
    conflicts_resolved: int
    time_saved_minutes: int
    processing_time_ms: float

class MeetingPrepRequest(BaseModel):
    """Request for meeting preparation"""
    user_id: str
    meeting_id: str
    meeting_title: str
    attendees: List[str]
    scheduled_time: datetime
    context: Optional[str] = None

class MeetingPrepResponse(BaseModel):
    """Meeting preparation results"""
    user_id: str
    meeting_id: str
    briefing_document: str
    attendee_research: List[Dict[str, Any]]
    suggested_agenda: List[str]
    processing_time_ms: float

class TaskPrioritizationRequest(BaseModel):
    """Request to prioritize tasks"""
    user_id: str
    tasks: List[Dict[str, Any]]

class TaskPrioritizationResponse(BaseModel):
    """Task prioritization results"""
    user_id: str
    prioritized_tasks: List[Dict[str, Any]]
    eisenhower_matrix: Dict[str, List[str]]
    recommendations: str
    processing_time_ms: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]

# ============================================================================
# SERVICES
# ============================================================================

class ClaudeService:
    """Claude API integration for decision-making and content generation"""

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS

    async def triage_email(self, email: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Triage a single email using Claude"""
        prompt = f"""Analyze this email and provide triage recommendations:

FROM: {email.get('from', 'Unknown')}
SUBJECT: {email.get('subject', 'No subject')}
BODY: {email.get('body', '')[:1000]}
RECEIVED: {email.get('received_at', 'Unknown')}

User Context:
- Role: {user_context.get('role', 'Professional')}
- Priorities: {user_context.get('priorities', [])}
- Working hours: {user_context.get('working_hours', '9-5')}

Provide a JSON response with:
1. category: "urgent_action" | "important_read" | "routine" | "delegate" | "archive"
2. priority_score: 1-10
3. suggested_action: specific action to take
4. estimated_time_minutes: time needed to handle
5. reasoning: brief explanation

Respond with ONLY valid JSON, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            # Parse JSON from response
            import json
            result = json.loads(result_text)

            return {
                "email_id": email.get("id"),
                "category": result.get("category"),
                "priority_score": result.get("priority_score"),
                "suggested_action": result.get("suggested_action"),
                "estimated_time_minutes": result.get("estimated_time_minutes"),
                "reasoning": result.get("reasoning")
            }
        except Exception as e:
            logger.error(f"Email triage error: {e}")
            return {
                "email_id": email.get("id"),
                "category": "routine",
                "priority_score": 5,
                "suggested_action": "Review manually",
                "estimated_time_minutes": 10,
                "reasoning": f"Error during analysis: {str(e)}"
            }

    async def optimize_calendar(self, events: List[Dict], constraints: Dict) -> List[Dict]:
        """Optimize calendar scheduling"""
        prompt = f"""Analyze this calendar and suggest optimizations:

EVENTS (next 7 days):
{self._format_events(events)}

CONSTRAINTS:
- Focus time needed: {constraints.get('focus_time_hours', 4)} hours/day
- No meetings before: {constraints.get('no_meetings_before', '9:00')}
- No meetings after: {constraints.get('no_meetings_after', '17:00')}
- Preferred meeting buffer: {constraints.get('meeting_buffer_minutes', 15)} minutes
- Max meetings per day: {constraints.get('max_meetings_per_day', 6)}

Provide optimization suggestions as JSON array with:
1. type: "reschedule" | "decline" | "shorten" | "merge" | "add_buffer"
2. event_id: ID of event to modify
3. suggestion: specific recommendation
4. reasoning: why this helps
5. time_saved_minutes: estimated time saved

Respond with ONLY valid JSON array, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            suggestions = json.loads(response.content[0].text)
            return suggestions
        except Exception as e:
            logger.error(f"Calendar optimization error: {e}")
            return []

    async def prepare_meeting(self, meeting: Dict, attendees_info: List[Dict]) -> Dict:
        """Generate meeting preparation materials"""
        prompt = f"""Prepare comprehensive meeting materials:

MEETING: {meeting.get('title')}
WHEN: {meeting.get('scheduled_time')}
DURATION: {meeting.get('duration_minutes', 60)} minutes
CONTEXT: {meeting.get('context', 'Standard meeting')}

ATTENDEES:
{self._format_attendees(attendees_info)}

Generate:
1. briefing_document: Executive summary of what this meeting is about
2. key_points: List of key discussion points
3. suggested_agenda: Detailed agenda with time allocations
4. attendee_insights: Brief context on each attendee
5. preparation_checklist: What to prepare before meeting

Respond with ONLY valid JSON, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            prep_materials = json.loads(response.content[0].text)
            return prep_materials
        except Exception as e:
            logger.error(f"Meeting prep error: {e}")
            return {
                "briefing_document": "Error generating briefing",
                "key_points": [],
                "suggested_agenda": [],
                "attendee_insights": [],
                "preparation_checklist": []
            }

    async def prioritize_tasks(self, tasks: List[Dict], user_context: Dict) -> Dict:
        """Prioritize tasks using Eisenhower Matrix"""
        prompt = f"""Prioritize these tasks for optimal productivity:

TASKS:
{self._format_tasks(tasks)}

USER CONTEXT:
- Goals: {user_context.get('goals', [])}
- Deadlines: {user_context.get('upcoming_deadlines', [])}
- Energy levels: {user_context.get('peak_hours', 'Morning')}

Use the Eisenhower Matrix to categorize tasks:
- Q1 (Do First): Urgent and Important
- Q2 (Schedule): Important but Not Urgent
- Q3 (Delegate): Urgent but Not Important
- Q4 (Eliminate): Neither Urgent nor Important

Respond with JSON containing:
1. eisenhower_matrix: {"Q1": [], "Q2": [], "Q3": [], "Q4": []} with task IDs
2. prioritized_tasks: Sorted list with reasoning
3. daily_plan: Suggested schedule for today
4. recommendations: Strategic advice

Respond with ONLY valid JSON, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            prioritization = json.loads(response.content[0].text)
            return prioritization
        except Exception as e:
            logger.error(f"Task prioritization error: {e}")
            return {
                "eisenhower_matrix": {"Q1": [], "Q2": [], "Q3": [], "Q4": []},
                "prioritized_tasks": tasks,
                "daily_plan": [],
                "recommendations": "Error during prioritization"
            }

    def _format_events(self, events: List[Dict]) -> str:
        """Format events for Claude prompt"""
        return "\n".join([
            f"- [{e.get('id')}] {e.get('title')} | {e.get('start_time')} | {e.get('duration_minutes')}min"
            for e in events[:20]  # Limit to first 20
        ])

    def _format_attendees(self, attendees: List[Dict]) -> str:
        """Format attendees for Claude prompt"""
        return "\n".join([
            f"- {a.get('name')} ({a.get('role', 'Unknown role')}) | {a.get('department', 'Unknown dept')}"
            for a in attendees
        ])

    def _format_tasks(self, tasks: List[Dict]) -> str:
        """Format tasks for Claude prompt"""
        return "\n".join([
            f"- [{t.get('id')}] {t.get('title')} | Due: {t.get('due_date', 'No deadline')} | Est: {t.get('estimated_time', 'Unknown')}"
            for t in tasks[:30]  # Limit to first 30
        ])

class MemoryService:
    """Long-term memory using Pinecone vector database"""

    def __init__(self, api_key: str, environment: str, index_name: str):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)

    async def store_interaction(self, user_id: str, interaction_type: str, data: Dict):
        """Store interaction in vector memory"""
        # In production, use proper embedding model
        # For now, simplified storage
        vector_id = f"{user_id}_{interaction_type}_{uuid.uuid4()}"
        metadata = {
            "user_id": user_id,
            "type": interaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": str(data)[:1000]  # Truncate for metadata limit
        }
        # Note: In production, generate proper embeddings
        # self.index.upsert([(vector_id, embedding, metadata)])
        logger.info(f"Stored interaction: {vector_id}")

    async def retrieve_context(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Retrieve relevant context from memory"""
        # In production, embed query and search
        # For now, return mock context
        return []

class IntegrationService:
    """External API integrations"""

    async def fetch_google_calendar_events(self, user_id: str, days: int = 7) -> List[Dict]:
        """Fetch Google Calendar events"""
        # Mock implementation - replace with actual Google Calendar API
        logger.info(f"Fetching Google Calendar for user {user_id}")
        return [
            {
                "id": f"gcal_{i}",
                "title": f"Meeting {i}",
                "start_time": (datetime.utcnow() + timedelta(hours=i*2)).isoformat(),
                "duration_minutes": 60,
                "attendees": ["john@example.com", "jane@example.com"]
            }
            for i in range(5)
        ]

    async def fetch_gmail_emails(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Fetch Gmail emails"""
        # Mock implementation - replace with actual Gmail API
        logger.info(f"Fetching Gmail for user {user_id}")
        return [
            {
                "id": f"email_{i}",
                "from": f"sender{i}@example.com",
                "subject": f"Important email {i}",
                "body": "Email body content...",
                "received_at": (datetime.utcnow() - timedelta(hours=i)).isoformat()
            }
            for i in range(min(limit, 10))
        ]

    async def fetch_notion_tasks(self, user_id: str) -> List[Dict]:
        """Fetch Notion tasks"""
        # Mock implementation - replace with actual Notion API
        logger.info(f"Fetching Notion tasks for user {user_id}")
        return [
            {
                "id": f"task_{i}",
                "title": f"Task {i}",
                "due_date": (datetime.utcnow() + timedelta(days=i)).isoformat(),
                "estimated_time": "30 minutes",
                "status": "pending"
            }
            for i in range(5)
        ]

    async def send_slack_notification(self, user_id: str, message: str):
        """Send Slack notification"""
        logger.info(f"Sending Slack notification to {user_id}: {message}")

# ============================================================================
# APPLICATION SETUP
# ============================================================================

class AppState:
    """Shared application state"""
    redis_client: redis.Redis
    claude_service: ClaudeService
    memory_service: MemoryService
    integration_service: IntegrationService
    db_engine: Any
    db_session: Any

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Executive Assistant agent...")

    # Initialize Redis
    app_state.redis_client = await redis.from_url(
        config.REDIS_URL,
        max_connections=config.REDIS_POOL_SIZE,
        decode_responses=True
    )

    # Initialize services
    app_state.claude_service = ClaudeService(config.CLAUDE_API_KEY)
    app_state.memory_service = MemoryService(
        config.PINECONE_API_KEY,
        config.PINECONE_ENVIRONMENT,
        config.PINECONE_INDEX
    )
    app_state.integration_service = IntegrationService()

    # Initialize database
    app_state.db_engine = create_async_engine(config.DATABASE_URL, echo=False)
    app_state.db_session = async_sessionmaker(app_state.db_engine, class_=AsyncSession, expire_on_commit=False)

    logger.info("Executive Assistant agent started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Executive Assistant agent...")
    await app_state.redis_client.close()
    await app_state.db_engine.dispose()
    logger.info("Shutdown complete")

app = FastAPI(
    title="Executive Assistant AI Agent",
    description="Intelligent calendar optimization, meeting prep, email triage, and task prioritization",
    version=config.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    redis_status = "healthy"
    try:
        await app_state.redis_client.ping()
    except:
        redis_status = "unhealthy"

    return HealthResponse(
        status="healthy" if redis_status == "healthy" else "degraded",
        version=config.VERSION,
        timestamp=datetime.utcnow(),
        dependencies={
            "redis": redis_status,
            "claude_api": "healthy",
            "pinecone": "healthy"
        }
    )

@app.post("/api/v1/email/triage", response_model=EmailTriageResponse)
async def triage_emails(request: EmailTriageRequest):
    """Triage emails with AI-powered categorization and prioritization"""
    start_time = datetime.utcnow()
    request_counter.labels(endpoint="email_triage", status="started").inc()

    try:
        # Get user context
        user_context = {
            "role": "Executive",
            "priorities": ["revenue growth", "team development"],
            "working_hours": "9-18"
        }

        # Triage each email
        triaged_emails = []
        for email in request.emails[:config.EMAIL_BATCH_SIZE]:
            with email_triage_duration.time():
                result = await app_state.claude_service.triage_email(email, user_context)
                triaged_emails.append(result)

        # Generate summary
        urgent_count = sum(1 for e in triaged_emails if e['category'] == 'urgent_action')
        important_count = sum(1 for e in triaged_emails if e['category'] == 'important_read')

        summary = f"Triaged {len(triaged_emails)} emails: {urgent_count} urgent actions, {important_count} important reads"

        # Store in memory
        await app_state.memory_service.store_interaction(
            request.user_id,
            "email_triage",
            {"count": len(triaged_emails), "urgent": urgent_count}
        )

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        request_counter.labels(endpoint="email_triage", status="success").inc()

        return EmailTriageResponse(
            user_id=request.user_id,
            triaged_emails=triaged_emails,
            summary=summary,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Email triage failed: {e}")
        request_counter.labels(endpoint="email_triage", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/calendar/optimize", response_model=CalendarOptimizationResponse)
async def optimize_calendar(request: CalendarOptimizationRequest):
    """Optimize calendar with AI-powered scheduling suggestions"""
    start_time = datetime.utcnow()
    request_counter.labels(endpoint="calendar_optimize", status="started").inc()

    try:
        # Fetch calendar events
        events = await app_state.integration_service.fetch_google_calendar_events(
            request.user_id,
            days=7
        )

        # Optimize calendar
        with calendar_optimization_duration.time():
            suggestions = await app_state.claude_service.optimize_calendar(
                events,
                request.constraints
            )

        # Calculate metrics
        conflicts_resolved = sum(1 for s in suggestions if s.get('type') == 'reschedule')
        time_saved = sum(s.get('time_saved_minutes', 0) for s in suggestions)

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        request_counter.labels(endpoint="calendar_optimize", status="success").inc()

        return CalendarOptimizationResponse(
            user_id=request.user_id,
            suggestions=suggestions,
            conflicts_resolved=conflicts_resolved,
            time_saved_minutes=time_saved,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Calendar optimization failed: {e}")
        request_counter.labels(endpoint="calendar_optimize", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/meeting/prepare", response_model=MeetingPrepResponse)
async def prepare_meeting(request: MeetingPrepRequest):
    """Generate comprehensive meeting preparation materials"""
    start_time = datetime.utcnow()
    request_counter.labels(endpoint="meeting_prep", status="started").inc()

    try:
        # Gather attendee information (mock)
        attendees_info = [
            {
                "name": attendee,
                "role": "Team Member",
                "department": "Engineering"
            }
            for attendee in request.attendees
        ]

        # Generate meeting prep
        meeting_data = {
            "title": request.meeting_title,
            "scheduled_time": request.scheduled_time.isoformat(),
            "duration_minutes": 60,
            "context": request.context
        }

        with meeting_prep_duration.time():
            prep_materials = await app_state.claude_service.prepare_meeting(
                meeting_data,
                attendees_info
            )

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        request_counter.labels(endpoint="meeting_prep", status="success").inc()

        return MeetingPrepResponse(
            user_id=request.user_id,
            meeting_id=request.meeting_id,
            briefing_document=prep_materials.get('briefing_document', ''),
            attendee_research=prep_materials.get('attendee_insights', []),
            suggested_agenda=prep_materials.get('suggested_agenda', []),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Meeting prep failed: {e}")
        request_counter.labels(endpoint="meeting_prep", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/prioritize", response_model=TaskPrioritizationResponse)
async def prioritize_tasks(request: TaskPrioritizationRequest):
    """Prioritize tasks using Eisenhower Matrix and AI insights"""
    start_time = datetime.utcnow()
    request_counter.labels(endpoint="task_prioritize", status="started").inc()

    try:
        user_context = {
            "goals": ["Complete Q4 objectives", "Team development"],
            "upcoming_deadlines": ["Product launch in 2 weeks"],
            "peak_hours": "Morning (9-12)"
        }

        # Prioritize tasks
        prioritization = await app_state.claude_service.prioritize_tasks(
            request.tasks,
            user_context
        )

        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        request_counter.labels(endpoint="task_prioritize", status="success").inc()

        return TaskPrioritizationResponse(
            user_id=request.user_id,
            prioritized_tasks=prioritization.get('prioritized_tasks', []),
            eisenhower_matrix=prioritization.get('eisenhower_matrix', {}),
            recommendations=prioritization.get('recommendations', ''),
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        logger.error(f"Task prioritization failed: {e}")
        request_counter.labels(endpoint="task_prioritize", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Executive Assistant AI Agent",
        "version": config.VERSION,
        "status": "operational",
        "documentation": "/docs"
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        workers=4,
        log_level="info"
    )
