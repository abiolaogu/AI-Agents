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
    async def execute(self, task: Dict[str, Any], context: Optional[TaskContext] = None) -> AgentResult:
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


class LLMClient:
    """
    Universal LLM client supporting multiple providers.

    Supports Anthropic Claude and OpenAI GPT models with automatic fallback.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM client.

        Args:
            model: Model identifier (e.g., "claude-3-5-sonnet-20241022" or "gpt-4-turbo")
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            logger: Logger instance
        """
        import os

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logger or logging.getLogger(__name__)

        # Determine provider based on model name
        self.provider = self._detect_provider(model)

        # Initialize clients
        self._anthropic_client = None
        self._openai_client = None

        # Get API keys from environment
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self._initialize_clients()

    def _detect_provider(self, model: str) -> str:
        """Detect LLM provider from model name."""
        model_lower = model.lower()
        if "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        else:
            # Default to Anthropic
            return "anthropic"

    def _initialize_clients(self):
        """Initialize LLM client libraries."""
        if self.provider == "anthropic" and self.anthropic_api_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                self.logger.info("Anthropic client initialized")
            except ImportError:
                self.logger.warning("anthropic library not installed")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")

        if self.openai_api_key:
            try:
                import openai
                self._openai_client = openai.OpenAI(api_key=self.openai_api_key)
                self.logger.info("OpenAI client initialized")
            except ImportError:
                self.logger.warning("openai library not installed")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")

    def call(
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
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Dict with text, tokens_used, execution_time_ms, model, provider
        """
        start_time = time.time()

        # Override defaults with kwargs
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        model = kwargs.get("model", self.model)

        try:
            if self.provider == "anthropic" and self._anthropic_client:
                result = self._call_anthropic(prompt, system_prompt, model, max_tokens, temperature)
            elif self._openai_client:
                result = self._call_openai(prompt, system_prompt, model, max_tokens, temperature)
            else:
                # Fallback to the other provider if available
                if self._anthropic_client:
                    result = self._call_anthropic(prompt, system_prompt, model, max_tokens, temperature)
                elif self._openai_client:
                    result = self._call_openai(prompt, system_prompt, model, max_tokens, temperature)
                else:
                    raise RuntimeError("No LLM client available. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

            result["execution_time_ms"] = (time.time() - start_time) * 1000
            return result

        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise

    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._anthropic_client.messages.create(**kwargs)

        text = response.content[0].text if response.content else ""
        tokens_used = (
            response.usage.input_tokens + response.usage.output_tokens
            if hasattr(response, 'usage') else 0
        )

        return {
            "text": text,
            "tokens_used": tokens_used,
            "model": model,
            "provider": "anthropic"
        }

    def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Call OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Map Claude model to OpenAI if needed
        if "claude" in model.lower():
            model = "gpt-4-turbo"

        response = self._openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        text = response.choices[0].message.content if response.choices else ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        return {
            "text": text,
            "tokens_used": tokens_used,
            "model": model,
            "provider": "openai"
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

        # Initialize LLM client
        self.llm_client = LLMClient(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            logger=self.logger
        )

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
            LLM response with text, tokens_used, execution_time_ms, model, provider
        """
        return self.llm_client.call(prompt, system_prompt, **kwargs)

    async def call_llm_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async version of call_llm.

        For now, wraps the sync call. Can be extended with async client support.
        """
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.call_llm(prompt, system_prompt, **kwargs)
        )


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
