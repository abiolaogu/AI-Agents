from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
import os
import hashlib
import secrets

# Use postgresql+asyncpg for async support
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_agents")


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Uses a random salt for each password, stored with the hash.
    Format: salt$iterations$hash
    """
    salt = secrets.token_hex(16)
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    hash_hex = hash_bytes.hex()
    return f"{salt}${iterations}${hash_hex}"


def check_password(stored_hash: str, password: str) -> bool:
    """
    Verify a password against a stored hash.

    Returns True if the password matches, False otherwise.
    """
    try:
        parts = stored_hash.split('$')
        if len(parts) != 3:
            return False
        salt, iterations, stored_hash_hex = parts
        iterations = int(iterations)
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return secrets.compare_digest(hash_bytes.hex(), stored_hash_hex)
    except (ValueError, AttributeError):
        return False

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(String, primary_key=True)
    name = Column(String)
    tasks = Column(Text) # JSON string
    status = Column(String)
    results = Column(Text) # JSON string
    user_id = Column(Integer, ForeignKey("users.id"))

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    workflow_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Async generator for database sessions (use as FastAPI dependency)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Get a database session directly (not as a generator).

    Use this when you need to manage the session lifecycle yourself,
    e.g., in background tasks or non-FastAPI contexts.

    Example:
        session = await get_db_session()
        try:
            # Do database operations
            await session.commit()
        finally:
            await session.close()
    """
    return AsyncSessionLocal()
