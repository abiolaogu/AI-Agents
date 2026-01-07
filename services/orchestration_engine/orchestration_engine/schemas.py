from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import re


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be 8-128 characters"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class Task(BaseModel):
    """Schema for a workflow task."""
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID of the agent to execute this task"
    )
    task_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task-specific configuration and inputs"
    )

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Agent ID can only contain letters, numbers, underscores, and hyphens')
        return v


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the workflow"
    )
    tasks: List[Task] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of tasks to execute in the workflow"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""
    id: str
    name: str
    status: str
    results: Optional[List[Dict[str, Any]]] = None


class AgentResponse(BaseModel):
    """Schema for agent information response."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    capabilities: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
