from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Task(BaseModel):
    agent_id: str
    task_details: Dict[str, Any]

class WorkflowCreate(BaseModel):
    name: str
    tasks: List[Task]
