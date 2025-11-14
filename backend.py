"""
Multi-Framework Super-Agent Backend
FastAPI with Role-Based Access Control & Security Integration
"""

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi.responses import StreamingResponse
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
import asyncio
from enum import Enum

# Core dependencies
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
import uvicorn

# Database & Cache
import asyncpg
from redis import asyncio as aioredis

# Frameworks
import structlog
from pythonjsonlogger import jsonlogger

# Security
from cryptography.fernet import Fernet
import hashlib

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge
import time

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# ============================================================================
# Constants & Configuration
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"
    SERVICE_ACCOUNT = "service_account"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# Database
DB_USER = os.getenv("DB_USER", "yugabyte")
DB_PASSWORD = os.getenv("DB_PASSWORD", "yugabyte")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "agent_db")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Security Headers
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# ============================================================================
# Prometheus Metrics
# ============================================================================

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'user_role']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['execution_engine', 'status', 'user_role']
)

agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['execution_engine']
)

# ============================================================================
# Data Models
# ============================================================================

class TokenData(BaseModel):
    user_id: str
    username: str
    role: UserRole
    exp: datetime
    scopes: List[str] = []

class User(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class ExecutionRequest(BaseModel):
    task_description: str = Field(..., min_length=10, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    context: Optional[Dict[str, Any]] = {}
    max_tokens: Optional[int] = Field(2000, ge=100, le=10000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    
    @validator('task_description')
    def sanitize_description(cls, v):
        # XSS prevention
        dangerous_chars = ['<', '>', '"', "'", '{', '}']
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[str] = None
    execution_time: float
    engine: str
    tokens_used: int
    cost_usd: float
    timestamp: datetime

class AuditLog(BaseModel):
    user_id: str
    action: str
    resource: str
    method: str
    status_code: int
    ip_address: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = {}

# ============================================================================
# Security & Authentication
# ============================================================================

security = HTTPBearer()

class SecurityContext:
    def __init__(self):
        self.cipher_suite = Fernet(os.getenv("ENCRYPTION_KEY", Fernet.generate_key()).encode())
    
    def hash_password(self, password: str) -> str:
        """Secure password hashing"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            os.urandom(32),
            100000
        ).hex()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

security_context = SecurityContext()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> TokenData:
    """Verify JWT token and extract user information"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        scopes: List[str] = payload.get("scopes", [])
        
        if not all([user_id, username, role]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=UserRole(role),
            exp=datetime.fromtimestamp(payload.get("exp")),
            scopes=scopes
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def check_permission(
    token_data: TokenData,
    required_role: UserRole
) -> TokenData:
    """Check if user has required role"""
    role_hierarchy = {
        UserRole.ADMIN: 4,
        UserRole.ANALYST: 3,
        UserRole.USER: 2,
        UserRole.SERVICE_ACCOUNT: 1,
    }
    
    if role_hierarchy[token_data.role] < role_hierarchy[required_role]:
        logger.warning(
            "permission_denied",
            user_id=token_data.user_id,
            required_role=required_role.value,
            user_role=token_data.role.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return token_data

# ============================================================================
# Database & Cache
# ============================================================================

class DatabasePool:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
        logger.info("database_connected", host=DB_HOST, database=DB_NAME)
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("database_disconnected")
    
    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch query results"""
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

class CacheManager:
    def __init__(self):
        self.redis = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(REDIS_URL)
        logger.info("cache_connected", url=REDIS_URL)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str):
        """Get value from cache"""
        value = await self.redis.get(key)
        if value:
            logger.debug("cache_hit", key=key)
        return value
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache"""
        await self.redis.setex(key, ttl, value)
    
    async def delete(self, key: str):
        """Delete from cache"""
        await self.redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.redis.exists(key) > 0

# Initialize
db_pool = DatabasePool()
cache_manager = CacheManager()

# ============================================================================
# Audit Logging
# ============================================================================

async def log_audit(
    user_id: str,
    action: str,
    resource: str,
    method: str,
    status_code: int,
    ip_address: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log all audit events"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        method=method,
        status_code=status_code,
        ip_address=ip_address,
        details=details or {},
        timestamp=datetime.utcnow()
    )
    
    # Store in database
    query = """
        INSERT INTO audit_logs 
        (user_id, action, resource, method, status_code, ip_address, details, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    
    try:
        await db_pool.execute(
            query,
            audit_log.user_id,
            audit_log.action,
            audit_log.resource,
            audit_log.method,
            audit_log.status_code,
            audit_log.ip_address,
            audit_log.details,
            audit_log.timestamp
        )
        logger.info("audit_logged", **audit_log.dict())
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))

# ============================================================================
# Multi-Framework Integration
# ============================================================================

class AgentRouter:
    """Intelligent routing to appropriate execution engine"""
    
    async def route_request(
        self,
        task_description: str,
        priority: TaskPriority,
        user_role: UserRole,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to appropriate execution engine based on:
        - Task complexity
        - Available resources
        - Cost optimization
        - User role/permissions
        """
        
        # Analyze task complexity
        complexity_score = self._calculate_complexity(task_description)
        
        # Check resource availability
        resources = await self._check_resources()
        
        # Determine routing decision
        routing_decision = self._make_routing_decision(
            complexity_score=complexity_score,
            priority=priority,
            resources=resources,
            user_role=user_role,
            context=context
        )
        
        logger.info(
            "routing_decision",
            engine=routing_decision['engine'],
            complexity=complexity_score,
            priority=priority.value
        )
        
        return routing_decision
    
    def _calculate_complexity(self, task_description: str) -> float:
        """Calculate task complexity (0.0 to 1.0)"""
        # Simple heuristics
        complexity_factors = {
            "analyze": 0.3,
            "research": 0.4,
            "write": 0.5,
            "code": 0.7,
            "debug": 0.8,
            "optimize": 0.9,
            "refactor": 0.85,
        }
        
        description_lower = task_description.lower()
        complexity = 0.5  # default
        
        for keyword, score in complexity_factors.items():
            if keyword in description_lower:
                complexity = max(complexity, score)
        
        return complexity
    
    async def _check_resources(self) -> Dict[str, Any]:
        """Check available GPU/CPU resources"""
        # This would integrate with RunPod API
        return {
            "gpu_available": True,
            "cpu_utilization": 0.45,
            "memory_available_gb": 200
        }
    
    def _make_routing_decision(
        self,
        complexity_score: float,
        priority: TaskPriority,
        resources: Dict[str, Any],
        user_role: UserRole,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make intelligent routing decision"""
        
        # Speed path: Direct LLM call
        if complexity_score < 0.3:
            return {
                "engine": "direct_llm",
                "model": "gemini-2.0-flash",  # Fast
                "estimated_cost": 0.001,
                "estimated_time": 2
            }
        
        # Quality path: CrewAI multi-agent
        elif complexity_score >= 0.3 and complexity_score < 0.7:
            return {
                "engine": "crewai",
                "agents": ["researcher", "writer", "reviewer"],
                "model": "claude-3.5-sonnet",  # Quality
                "estimated_cost": 0.05,
                "estimated_time": 15
            }
        
        # Reliability path: AutoGen with code execution
        else:
            return {
                "engine": "autogen",
                "mode": "code_execution",
                "model": "gpt-4o",  # Reliability
                "estimated_cost": 0.10,
                "estimated_time": 30
            }

router = AgentRouter()

# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    # Startup
    logger.info("starting_application")
    await db_pool.initialize()
    await cache_manager.initialize()
    yield
    # Shutdown
    logger.info("shutting_down_application")
    await db_pool.close()
    await cache_manager.close()

# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="Super-Agent Platform API",
    description="Multi-Framework AI Agent Orchestration",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware - Security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS,
    allow_edge_case_middleware=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZIPMiddleware, minimum_size=1000)

# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "dependencies": {}
    }
    
    # Check database
    try:
        result = await db_pool.fetchrow("SELECT 1")
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check cache
    try:
        await cache_manager.redis.ping()
        health_status["dependencies"]["cache"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/login", tags=["Authentication"])
async def login(username: str, password: str):
    """User login and token generation"""
    # Query user from database
    user = await db_pool.fetchrow(
        "SELECT id, username, email, role FROM users WHERE username = $1",
        username
    )
    
    if not user:
        logger.warning("login_failed", username=username, reason="user_not_found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password (in production, use bcrypt)
    # password_hash = security_context.hash_password(password)
    
    # Generate JWT token
    exp_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {
        "user_id": user['id'],
        "username": user['username'],
        "role": user['role'],
        "exp": exp_time.timestamp(),
        "scopes": []
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # Update last login
    await db_pool.execute(
        "UPDATE users SET last_login = NOW() WHERE id = $1",
        user['id']
    )
    
    logger.info("login_successful", user_id=user['id'], username=username)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role']
        }
    }

@app.post("/auth/refresh", tags=["Authentication"])
async def refresh_token(token_data: TokenData = Depends(verify_token)):
    """Refresh JWT token"""
    exp_time = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {
        "user_id": token_data.user_id,
        "username": token_data.username,
        "role": token_data.role.value,
        "exp": exp_time.timestamp(),
        "scopes": token_data.scopes
    }
    
    new_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    logger.info("token_refreshed", user_id=token_data.user_id)
    
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60
    }

# ============================================================================
# Agent Execution Endpoints
# ============================================================================

@app.post("/api/v1/execute", response_model=ExecutionResponse, tags=["Execution"])
async def execute_agent(
    request: ExecutionRequest,
    token_data: TokenData = Depends(verify_token),
    request_ip: str = Query(...)
):
    """
    Execute agent with intelligent routing
    Requires authentication
    """
    execution_start = time.time()
    execution_id = f"{token_data.user_id}_{int(time.time() * 1000)}"
    
    try:
        # Make routing decision
        routing = await router.route_request(
            task_description=request.task_description,
            priority=request.priority,
            user_role=token_data.role,
            context=request.context or {}
        )
        
        # Execute based on routing decision
        if routing['engine'] == 'direct_llm':
            result, tokens = await _execute_direct_llm(
                request.task_description,
                routing['model'],
                request.max_tokens,
                request.temperature
            )
        elif routing['engine'] == 'crewai':
            result, tokens = await _execute_crewai(
                request.task_description,
                routing['agents'],
                routing['model']
            )
        else:  # autogen
            result, tokens = await _execute_autogen(
                request.task_description,
                routing['model']
            )
        
        execution_time = time.time() - execution_start
        cost_usd = routing.get('estimated_cost', 0.01)
        
        # Record execution
        await _record_execution(
            execution_id=execution_id,
            user_id=token_data.user_id,
            engine=routing['engine'],
            task=request.task_description,
            tokens_used=tokens,
            cost=cost_usd,
            duration=execution_time
        )
        
        # Audit log
        await log_audit(
            user_id=token_data.user_id,
            action="execute_agent",
            resource="agent",
            method="POST",
            status_code=200,
            ip_address=request_ip,
            details={
                "execution_id": execution_id,
                "engine": routing['engine'],
                "tokens": tokens,
                "cost": cost_usd
            }
        )
        
        # Record metrics
        request_count.labels(
            method="POST",
            endpoint="/execute",
            status=200,
            user_role=token_data.role.value
        ).inc()
        
        agent_executions.labels(
            execution_engine=routing['engine'],
            status="success",
            user_role=token_data.role.value
        ).inc()
        
        agent_execution_duration.labels(
            execution_engine=routing['engine']
        ).observe(execution_time)
        
        logger.info(
            "execution_completed",
            execution_id=execution_id,
            engine=routing['engine'],
            user_id=token_data.user_id,
            duration=execution_time
        )
        
        return ExecutionResponse(
            execution_id=execution_id,
            status="completed",
            result=result,
            execution_time=execution_time,
            engine=routing['engine'],
            tokens_used=tokens,
            cost_usd=cost_usd,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(
            "execution_failed",
            execution_id=execution_id,
            user_id=token_data.user_id,
            error=str(e)
        )
        
        await log_audit(
            user_id=token_data.user_id,
            action="execute_agent",
            resource="agent",
            method="POST",
            status_code=500,
            ip_address=request_ip,
            details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution failed"
        )

# ============================================================================
# Placeholder Execution Functions
# ============================================================================

async def _execute_direct_llm(
    task: str,
    model: str,
    max_tokens: int,
    temperature: float
) -> tuple:
    """Execute simple LLM call"""
    # In production, integrate with LLM APIs
    logger.info("executing_direct_llm", model=model)
    result = f"Result from {model}: {task[:50]}..."
    tokens = 100
    return result, tokens

async def _execute_crewai(
    task: str,
    agents: List[str],
    model: str
) -> tuple:
    """Execute CrewAI multi-agent workflow"""
    logger.info("executing_crewai", agents=agents, model=model)
    result = f"CrewAI result with agents {agents}: {task[:50]}..."
    tokens = 500
    return result, tokens

async def _execute_autogen(
    task: str,
    model: str
) -> tuple:
    """Execute AutoGen with code execution"""
    logger.info("executing_autogen", model=model)
    result = f"AutoGen result with {model}: {task[:50]}..."
    tokens = 300
    return result, tokens

async def _record_execution(
    execution_id: str,
    user_id: str,
    engine: str,
    task: str,
    tokens_used: int,
    cost: float,
    duration: float
):
    """Record execution in database"""
    query = """
        INSERT INTO executions 
        (execution_id, user_id, engine, task, tokens_used, cost_usd, duration_seconds, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
    """
    await db_pool.execute(query, execution_id, user_id, engine, task, tokens_used, cost, duration)

# ============================================================================
# WebSocket for Real-time Updates
# ============================================================================

@app.websocket("/ws/status/{execution_id}")
async def websocket_status(websocket: WebSocket, execution_id: str):
    """WebSocket for real-time execution status"""
    await websocket.accept()
    
    try:
        while True:
            # Get current status from cache
            status_data = await cache_manager.get(f"exec_status:{execution_id}")
            if status_data:
                await websocket.send_json({"execution_id": execution_id, "status": status_data})
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        await websocket.close(code=status.WS_1011_SERVER_ERROR)

# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Use structlog
    )
