from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
import os

# Use postgresql+asyncpg for async support
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/ai_agents")

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
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
