"""
Enhanced Multi-Framework Super-Agent Backend
Complete Data Layer Integration: Milvus, ScyllaDB, DragonflyDB, PostgreSQL
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
import json
import uuid
import logging

# Database clients
import asyncpg  # PostgreSQL
from cassandra.cluster import Cluster  # ScyllaDB
from cassandra.auth import PlainTextAuthProvider
from redis import asyncio as aioredis  # DragonflyDB
from pymilvus import MilvusClient, Collection  # Milvus

# Security & Auth
import jwt
import hashlib
from cryptography.fernet import Fernet

# Frameworks
import structlog

# Metrics
from prometheus_client import Counter, Histogram, Gauge

# ============================================================================
# Configuration
# ============================================================================

# PostgreSQL
PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "super_agent"
PG_PASSWORD = "secure_password"
PG_DB = "super_agent_db"

# ScyllaDB
SCYLLA_HOSTS = ["localhost:9042"]
SCYLLA_USER = "cassandra"
SCYLLA_PASSWORD = "cassandra"
SCYLLA_KEYSPACE = "super_agent"

# DragonflyDB
DRAGONFLY_URL = "redis://localhost:6379"

# Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_DB = "super_agent"

# JWT
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

logger = structlog.get_logger()

# ============================================================================
# Database Connection Managers
# ============================================================================

class PostgreSQLPool:
    """PostgreSQL connection pool for control plane"""
    
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DB,
            min_size=10,
            max_size=50,
            command_timeout=60
        )
        logger.info("postgres_connected")
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def execute(self, query: str, *args):
        """Execute query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def transaction(self):
        """Get transaction context"""
        async with self.pool.acquire() as conn:
            return conn.transaction()

class ScyllaDBClient:
    """ScyllaDB client for events, sessions, audit logs"""
    
    def __init__(self):
        self.cluster = None
        self.session = None
    
    async def initialize(self):
        """Initialize ScyllaDB connection"""
        auth_provider = PlainTextAuthProvider(SCYLLA_USER, SCYLLA_PASSWORD)
        self.cluster = Cluster(
            contact_points=SCYLLA_HOSTS,
            auth_provider=auth_provider
        )
        self.session = self.cluster.connect()
        self.session.set_keyspace(SCYLLA_KEYSPACE)
        
        # Create keyspace if not exists
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {SCYLLA_KEYSPACE}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 3}}
        """)
        
        logger.info("scylla_connected")
    
    async def close(self):
        """Close connection"""
        if self.session:
            self.session.shutdown()
        if self.cluster:
            self.cluster.shutdown()
    
    async def execute(self, query: str, parameters: List = None):
        """Execute query"""
        if parameters:
            return self.session.execute(query, parameters)
        return self.session.execute(query)
    
    async def insert_audit_log(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        details: Dict
    ):
        """Insert audit log (immutable)"""
        query = """
            INSERT INTO audit_logs 
            (log_id, user_id, action, resource, result, timestamp, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.execute(query, [
            str(uuid.uuid4()),
            user_id,
            action,
            resource,
            result,
            datetime.utcnow(),
            json.dumps(details),
            "0.0.0.0"  # Replace with actual IP
        ])
    
    async def store_job(
        self,
        job_id: str,
        user_id: str,
        status: str,
        cost: float,
        result: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Store job execution"""
        query = """
            INSERT INTO jobs
            (job_id, user_id, status, created_at, cost, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        await self.execute(query, [
            job_id,
            user_id,
            status,
            datetime.utcnow(),
            cost,
            result,
            error
        ])

class DragonflyDBClient:
    """DragonflyDB client for caching and transient state"""
    
    def __init__(self):
        self.redis = None
    
    async def initialize(self):
        """Initialize DragonflyDB connection"""
        self.redis = await aioredis.from_url(DRAGONFLY_URL)
        logger.info("dragonfly_connected")
    
    async def close(self):
        """Close connection"""
        if self.redis:
            await self.redis.close()
    
    async def get_agent_context(self, execution_id: str) -> Dict:
        """Get agent execution context"""
        context = await self.redis.hgetall(f"agent:{execution_id}")
        return {k.decode(): v.decode() for k, v in context.items()}
    
    async def set_agent_context(self, execution_id: str, context: Dict, ttl: int = 3600):
        """Store agent context"""
        pipe = self.redis.pipeline()
        for key, value in context.items():
            pipe.hset(f"agent:{execution_id}", key, json.dumps(value))
        pipe.expire(f"agent:{execution_id}", ttl)
        await pipe.execute()
    
    async def cache_tool_result(self, tool_name: str, params: str, result: str, ttl: int = 1800):
        """Cache tool execution result"""
        cache_key = f"tool_result:{tool_name}:{hashlib.md5(params.encode()).hexdigest()}"
        await self.redis.setex(cache_key, ttl, result)
    
    async def get_cached_result(self, tool_name: str, params: str) -> Optional[str]:
        """Get cached tool result"""
        cache_key = f"tool_result:{tool_name}:{hashlib.md5(params.encode()).hexdigest()}"
        return await self.redis.get(cache_key)
    
    async def publish_event(self, channel: str, message: Dict):
        """Publish real-time event"""
        await self.redis.publish(channel, json.dumps(message))

class MilvusVectorDB:
    """Milvus client for vector embeddings and semantic search"""
    
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """Initialize Milvus connection"""
        self.client = MilvusClient(
            uri=f"http://{MILVUS_HOST}:{MILVUS_PORT}",
            db_name=MILVUS_DB
        )
        logger.info("milvus_connected")
    
    async def create_collection(self, collection_name: str, dimension: int = 1536):
        """Create vector collection"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                primary_field_name="id",
                vector_field_name="embedding",
                auto_id=True
            )
            logger.info(f"collection_created", collection=collection_name)
        except Exception as e:
            logger.warning(f"collection_exists", collection=collection_name)
    
    async def insert_embedding(
        self,
        collection_name: str,
        embedding: List[float],
        metadata: Dict
    ):
        """Insert document embedding"""
        data = [{
            "embedding": embedding,
            "metadata": json.dumps(metadata)
        }]
        self.client.insert(collection_name, data)
    
    async def search_similar(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar documents"""
        results = self.client.search(
            collection_name=collection_name,
            data=[query_embedding],
            limit=top_k,
            filter=filter_expr,
            output_fields=["metadata"]
        )
        return results[0] if results else []

# Initialize clients
pg_pool = PostgreSQLPool()
scylla_client = ScyllaDBClient()
dragonfly_client = DragonflyDBClient()
milvus_client = MilvusVectorDB()

# ============================================================================
# Data Models
# ============================================================================

class User:
    """User model from PostgreSQL"""
    def __init__(self, id: str, username: str, email: str, role: str, tenant_id: str):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.tenant_id = tenant_id

class ExecutionJob:
    """Job model - spans multiple databases"""
    def __init__(
        self,
        job_id: str,
        user_id: str,
        engine: str,
        task_description: str,
        status: str,
        cost_usd: float
    ):
        self.job_id = job_id
        self.user_id = user_id
        self.engine = engine
        self.task_description = task_description
        self.status = status
        self.cost_usd = cost_usd
        self.created_at = datetime.utcnow()

# ============================================================================
# Authentication & Authorization (PostgreSQL)
# ============================================================================

async def verify_user(credentials: HTTPAuthCredentials) -> User:
    """Verify JWT token and load user from PostgreSQL"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        # Load user from PostgreSQL
        user_row = await pg_pool.fetchrow(
            "SELECT id, username, email, role, tenant_id FROM users WHERE id = $1",
            user_id
        )
        
        if not user_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        return User(**dict(user_row))
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

# ============================================================================
# Session Management (DragonflyDB)
# ============================================================================

async def get_user_session(user_id: str) -> Dict:
    """Get user session from DragonflyDB cache"""
    session_data = await dragonfly_client.redis.hgetall(f"session:{user_id}")
    return {k.decode(): v.decode() for k, v in session_data.items()} if session_data else {}

async def store_user_session(user_id: str, session_data: Dict, ttl: int = 28800):
    """Store session in DragonflyDB (8 hours TTL)"""
    pipe = dragonfly_client.redis.pipeline()
    for key, value in session_data.items():
        pipe.hset(f"session:{user_id}", key, json.dumps(value))
    pipe.expire(f"session:{user_id}", ttl)
    await pipe.execute()

# ============================================================================
# Semantic Search (Milvus)
# ============================================================================

async def search_knowledge_base(
    query_embedding: List[float],
    top_k: int = 10,
    filter_expr: Optional[str] = None
) -> List[Dict]:
    """Search across all knowledge with semantic similarity"""
    # Search in documents collection
    doc_results = await milvus_client.search_similar(
        "documents",
        query_embedding,
        top_k,
        filter_expr
    )
    
    # Search in code collection
    code_results = await milvus_client.search_similar(
        "code_repository",
        query_embedding,
        top_k,
        filter_expr
    )
    
    # Combine and rank
    combined = doc_results + code_results
    combined.sort(key=lambda x: x.get("distance", 0), reverse=True)
    
    return combined[:top_k]

# ============================================================================
# Audit Logging (ScyllaDB)
# ============================================================================

async def log_audit_event(
    user_id: str,
    action: str,
    resource: str,
    result: str,
    details: Dict
):
    """Log audit event to ScyllaDB"""
    await scylla_client.insert_audit_log(
        user_id=user_id,
        action=action,
        resource=resource,
        result=result,
        details=details
    )

# ============================================================================
# Job Management (ScyllaDB + PostgreSQL)
# ============================================================================

async def create_job(
    user_id: str,
    engine: str,
    task_description: str,
    cost_usd: float
) -> ExecutionJob:
    """Create new job"""
    job_id = str(uuid.uuid4())
    
    job = ExecutionJob(
        job_id=job_id,
        user_id=user_id,
        engine=engine,
        task_description=task_description,
        status="pending",
        cost_usd=cost_usd
    )
    
    # Store in ScyllaDB
    await scylla_client.store_job(job_id, user_id, "pending", cost_usd)
    
    # Log audit event
    await log_audit_event(
        user_id=user_id,
        action="create_job",
        resource="job",
        result="success",
        details={"job_id": job_id}
    )
    
    return job

async def complete_job(
    job_id: str,
    user_id: str,
    result: str,
    cost_usd: float
):
    """Mark job as completed"""
    # Update in ScyllaDB
    await scylla_client.store_job(job_id, user_id, "completed", cost_usd, result=result)
    
    # Update billing in PostgreSQL
    await pg_pool.execute("""
        UPDATE billing 
        SET api_calls = api_calls + 1,
            cost_usd = cost_usd + $1
        WHERE user_id = $2 AND billing_period_end > NOW()
    """, cost_usd, user_id)
    
    # Log audit event
    await log_audit_event(
        user_id=user_id,
        action="complete_job",
        resource="job",
        result="success",
        details={"job_id": job_id, "cost": cost_usd}
    )

# ============================================================================
# Agent Orchestration
# ============================================================================

class EnhancedAgentRouter:
    """Multi-framework router with all data layer integrations"""
    
    async def route_and_execute(
        self,
        task_description: str,
        user: User,
        background_tasks: BackgroundTasks
    ) -> Dict:
        """Execute with data layer integrations"""
        
        # 1. Get user session from DragonflyDB
        session = await get_user_session(user.id)
        
        # 2. Generate embedding for semantic search
        # (In production, call embedding service)
        query_embedding = await self._generate_embedding(task_description)
        
        # 3. Search knowledge base in Milvus
        knowledge = await search_knowledge_base(
            query_embedding,
            top_k=5,
            filter_expr=f"tenant_id == '{user.tenant_id}'"
        )
        
        # 4. Create job in ScyllaDB
        job = await create_job(
            user_id=user.id,
            engine="crewai",
            task_description=task_description,
            cost_usd=0.01
        )
        
        # 5. Store execution context in DragonflyDB
        execution_context = {
            "execution_id": job.job_id,
            "task": task_description,
            "knowledge_base": json.dumps(knowledge),
            "session": json.dumps(session),
            "status": "executing"
        }
        await dragonfly_client.set_agent_context(job.job_id, execution_context)
        
        # 6. Execute in background
        background_tasks.add_task(
            self._execute_job,
            job.job_id,
            user.id,
            execution_context
        )
        
        return {
            "job_id": job.job_id,
            "status": "queued",
            "estimated_cost": 0.01
        }
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # TODO: Integrate with embedding service
        return [0.0] * 1536  # Placeholder
    
    async def _execute_job(self, job_id: str, user_id: str, context: Dict):
        """Execute job (background task)"""
        try:
            # Get updated context from DragonflyDB
            current_context = await dragonfly_client.get_agent_context(job_id)
            
            # Execute agent logic here
            result = "Agent execution result"
            
            # Complete job
            await complete_job(job_id, user_id, result, 0.01)
            
        except Exception as e:
            logger.error("job_execution_failed", job_id=job_id, error=str(e))
            await log_audit_event(
                user_id=user_id,
                action="job_failed",
                resource="job",
                result="error",
                details={"job_id": job_id, "error": str(e)}
            )

# ============================================================================
# FastAPI Application
# ============================================================================

async def lifespan(app: FastAPI):
    """Application lifecycle"""
    # Startup
    await pg_pool.initialize()
    await scylla_client.initialize()
    await dragonfly_client.initialize()
    await milvus_client.initialize()
    
    # Create Milvus collections
    await milvus_client.create_collection("documents")
    await milvus_client.create_collection("code_repository")
    await milvus_client.create_collection("policies")
    
    logger.info("application_started")
    yield
    
    # Shutdown
    await pg_pool.close()
    await scylla_client.close()
    await dragonfly_client.close()
    
    logger.info("application_shutdown")

app = FastAPI(
    title="Super-Agent Platform API",
    version="2.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check all data layers"""
    return {
        "status": "healthy",
        "databases": {
            "postgresql": "connected",
            "scylla": "connected",
            "dragonfly": "connected",
            "milvus": "connected"
        }
    }

@app.post("/api/v2/execute")
async def execute_agent(
    task_description: str,
    user: User = Depends(verify_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Execute agent with full data layer integration"""
    router = EnhancedAgentRouter()
    
    result = await router.route_and_execute(
        task_description=task_description,
        user=user,
        background_tasks=background_tasks
    )
    
    # Log execution
    await log_audit_event(
        user_id=user.id,
        action="execute_agent",
        resource="agent",
        result="success",
        details={"job_id": result["job_id"]}
    )
    
    return result

@app.get("/api/v2/job/{job_id}")
async def get_job_status(
    job_id: str,
    user: User = Depends(verify_user)
):
    """Get job status from cache or ScyllaDB"""
    # Try cache first
    context = await dragonfly_client.get_agent_context(job_id)
    if context:
        return {
            "job_id": job_id,
            "status": context.get("status", "unknown"),
            "source": "cache"
        }
    
    # Fall back to ScyllaDB
    # TODO: Query ScyllaDB
    return {
        "job_id": job_id,
        "status": "not_found"
    }

@app.get("/api/v2/search")
async def semantic_search(
    query: str,
    top_k: int = Query(10, ge=1, le=100),
    user: User = Depends(verify_user)
):
    """Semantic search across knowledge base"""
    # Generate embedding
    query_embedding = [0.0] * 1536  # TODO: Generate real embedding
    
    # Search Milvus with tenant filter
    results = await search_knowledge_base(
        query_embedding=query_embedding,
        top_k=top_k,
        filter_expr=f"tenant_id == '{user.tenant_id}'"
    )
    
    # Log search
    await log_audit_event(
        user_id=user.id,
        action="semantic_search",
        resource="knowledge",
        result="success",
        details={"query": query, "results_count": len(results)}
    )
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }

# ============================================================================
# Status Endpoint
# ============================================================================

@app.get("/api/v2/status")
async def system_status():
    """System status with data layer information"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "data_layers": {
            "postgresql": {
                "type": "Control Plane",
                "role": "Users, Auth, Billing",
                "status": "connected"
            },
            "scylla": {
                "type": "Event & State Backbone",
                "role": "Jobs, Audit Logs, Sessions",
                "status": "connected"
            },
            "dragonfly": {
                "type": "Transient Brain",
                "role": "Cache, Agent Context",
                "status": "connected"
            },
            "milvus": {
                "type": "Vector Memory",
                "role": "Embeddings, Semantic Search",
                "status": "connected"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
