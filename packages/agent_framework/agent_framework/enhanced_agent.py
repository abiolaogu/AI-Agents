"""
Enhanced Agent Framework with Team Collaboration Support

This module provides the foundation for 700+ AI agents with built-in
team collaboration, shared context, and workflow orchestration.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import uuid
from datetime import datetime


class AgentCategory(Enum):
    """Agent categories for organization and access control"""
    BUSINESS_OPS = "business_ops"
    SALES_MARKETING = "sales_marketing"
    CUSTOMER_SUPPORT = "customer_support"
    FINANCE_LEGAL = "finance_legal"
    HR_PEOPLE = "hr_people"
    PRODUCT_TECH = "product_tech"
    RETAIL_ECOMMERCE = "retail_ecommerce"
    HEALTHCARE_WELLNESS = "healthcare_wellness"
    EDUCATION_TRAINING = "education_training"
    REAL_ESTATE = "real_estate"
    LOGISTICS_MANUFACTURING = "logistics_manufacturing"
    CREATORS_MEDIA = "creators_media"
    PERSONAL_PRODUCTIVITY = "personal_productivity"
    PERSONAL_GROWTH = "personal_growth"


class AgentCapability(Enum):
    """Standard agent capabilities"""
    TEXT_GENERATION = "text_generation"
    TEXT_SUMMARIZATION = "text_summarization"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    EMAIL_PROCESSING = "email_processing"
    CALENDAR_MANAGEMENT = "calendar_management"
    DOCUMENT_PROCESSING = "document_processing"
    API_INTEGRATION = "api_integration"
    DATABASE_QUERY = "database_query"
    FILE_PROCESSING = "file_processing"
    WEB_SCRAPING = "web_scraping"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CLASSIFICATION = "classification"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"


@dataclass
class AgentMetadata:
    """Metadata for agent definition"""
    agent_id: str
    name: str
    description: str
    category: AgentCategory
    version: str
    capabilities: List[AgentCapability]
    author: str = "AI Agents Platform"
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


@dataclass
class TaskContext:
    """Shared context for agent execution"""
    task_id: str
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    workflow_id: Optional[str] = None
    shared_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResult:
    """Result from agent execution"""
    status: str  # success, error, partial
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0
    tokens_used: int = 0
    agent_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CollaborationMessage:
    """Message for inter-agent communication"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str  # request, response, broadcast, notification
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[TaskContext] = None


class EnhancedBaseAgent(ABC):
    """
    Enhanced base class for all agents with collaboration support.

    Features:
    - Team collaboration
    - Shared context management
    - Inter-agent messaging
    - Metadata and capabilities
    - Audit logging
    """

    def __init__(
        self,
        agent_id: str,
        metadata: AgentMetadata,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize enhanced agent.

        Args:
            agent_id: Unique identifier for this agent instance
            metadata: Agent metadata and capabilities
            logger: Logger instance
        """
        self.agent_id = agent_id
        self.metadata = metadata
        self.logger = logger or logging.getLogger(f"agent.{agent_id}")
        self.status = "idle"

        # Collaboration state
        self.current_team: Optional[str] = None
        self.team_members: Set[str] = set()
        self.shared_context: Optional[TaskContext] = None
        self.message_queue: List[CollaborationMessage] = []

        # Performance tracking
        self.total_executions = 0
        self.total_tokens_used = 0
        self.total_execution_time_ms = 0.0

        self.logger.info(f"Agent {agent_id} ({metadata.name}) initialized")

    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Optional[TaskContext] = None) -> AgentResult:
        """
        Execute a task with optional shared context.

        Args:
            task: Task specification with inputs
            context: Shared context for team collaboration

        Returns:
            AgentResult with outputs and metadata
        """
        pass

    def join_team(self, team_id: str, team_members: Set[str]):
        """
        Join a team for collaborative work.

        Args:
            team_id: Unique team identifier
            team_members: Set of agent IDs in the team
        """
        self.current_team = team_id
        self.team_members = team_members
        self.logger.info(
            f"Agent {self.agent_id} joined team {team_id} "
            f"with {len(team_members)} members"
        )

    def leave_team(self):
        """Leave current team"""
        if self.current_team:
            self.logger.info(f"Agent {self.agent_id} left team {self.current_team}")
        self.current_team = None
        self.team_members.clear()
        self.shared_context = None

    def send_message(
        self,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> CollaborationMessage:
        """
        Send message to another agent.

        Args:
            to_agent: Target agent ID
            message_type: Type of message (request, response, etc.)
            payload: Message payload

        Returns:
            Sent message
        """
        message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            context=self.shared_context
        )

        self.logger.debug(
            f"Agent {self.agent_id} sent {message_type} to {to_agent}"
        )

        return message

    def broadcast_to_team(
        self,
        message_type: str,
        payload: Dict[str, Any]
    ) -> List[CollaborationMessage]:
        """
        Broadcast message to all team members.

        Args:
            message_type: Type of message
            payload: Message payload

        Returns:
            List of sent messages
        """
        if not self.current_team:
            raise RuntimeError("Agent not in a team")

        messages = []
        for member in self.team_members:
            if member != self.agent_id:
                msg = self.send_message(member, message_type, payload)
                messages.append(msg)

        self.logger.info(
            f"Agent {self.agent_id} broadcasted {message_type} "
            f"to {len(messages)} team members"
        )

        return messages

    def receive_message(self, message: CollaborationMessage):
        """
        Receive message from another agent.

        Args:
            message: Incoming message
        """
        self.message_queue.append(message)
        self.logger.debug(
            f"Agent {self.agent_id} received {message.message_type} "
            f"from {message.from_agent}"
        )

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """
        Get data from shared team context.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Shared data value
        """
        if not self.shared_context:
            return default
        return self.shared_context.shared_data.get(key, default)

    def set_shared_data(self, key: str, value: Any):
        """
        Set data in shared team context.

        Args:
            key: Data key
            value: Data value
        """
        if not self.shared_context:
            raise RuntimeError("No shared context available")
        self.shared_context.shared_data[key] = value
        self.logger.debug(f"Agent {self.agent_id} set shared data: {key}")

    def can_work_with(self, other_agent_id: str) -> bool:
        """
        Check if this agent can collaborate with another agent.

        Args:
            other_agent_id: ID of other agent

        Returns:
            True if collaboration is possible
        """
        # Default: all agents can collaborate
        # Override in subclass for specific restrictions
        return True

    def set_status(self, status: str):
        """
        Set agent status.

        Args:
            status: New status (idle, running, error)
        """
        old_status = self.status
        self.status = status
        self.logger.info(
            f"Agent {self.agent_id} status: {old_status} -> {status}"
        )

    def log_execution(self, result: AgentResult):
        """
        Log execution metrics.

        Args:
            result: Execution result
        """
        self.total_executions += 1
        self.total_tokens_used += result.tokens_used
        self.total_execution_time_ms += result.execution_time_ms

        self.logger.info(
            f"Agent {self.agent_id} execution #{self.total_executions}: "
            f"status={result.status}, "
            f"time={result.execution_time_ms:.2f}ms, "
            f"tokens={result.tokens_used}"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Returns:
            Metrics dictionary
        """
        avg_time = (
            self.total_execution_time_ms / self.total_executions
            if self.total_executions > 0
            else 0
        )

        return {
            "agent_id": self.agent_id,
            "total_executions": self.total_executions,
            "total_tokens_used": self.total_tokens_used,
            "total_execution_time_ms": self.total_execution_time_ms,
            "average_execution_time_ms": avg_time,
            "current_status": self.status,
            "current_team": self.current_team
        }


class AgentWithLLM(EnhancedBaseAgent):
    """
    Base class for agents that use LLMs (Claude, GPT, etc.)

    Provides common LLM functionality and token management.
    """

    def __init__(
        self,
        agent_id: str,
        metadata: AgentMetadata,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM-based agent.

        Args:
            agent_id: Agent identifier
            metadata: Agent metadata
            model: LLM model to use
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            logger: Logger instance
        """
        super().__init__(agent_id, metadata, logger)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional LLM parameters

        Returns:
            LLM response with text and usage info
        """
        # This is a placeholder - implement with actual LLM client
        # (Anthropic, OpenAI, etc.)

        start_time = time.time()

        # Placeholder response
        response_text = f"[LLM Response for agent {self.agent_id}]"
        tokens_used = len(prompt.split()) * 2  # Rough estimate

        execution_time = (time.time() - start_time) * 1000

        return {
            "text": response_text,
            "tokens_used": tokens_used,
            "execution_time_ms": execution_time,
            "model": self.model
        }


# Convenience function for creating agent metadata
def create_agent_metadata(
    agent_id: str,
    name: str,
    description: str,
    category: AgentCategory,
    capabilities: List[AgentCapability],
    version: str = "1.0.0",
    **kwargs
) -> AgentMetadata:
    """
    Create agent metadata.

    Args:
        agent_id: Agent identifier
        name: Agent name
        description: Agent description
        category: Agent category
        capabilities: List of capabilities
        version: Version string
        **kwargs: Additional metadata fields

    Returns:
        AgentMetadata instance
    """
    return AgentMetadata(
        agent_id=agent_id,
        name=name,
        description=description,
        category=category,
        capabilities=capabilities,
        version=version,
        **kwargs
    )
