"""
Team Collaboration System

Enables multiple agents to work together on complex tasks.
"The real magic happens when several of these agents collaborate as a team."
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
import asyncio
from enum import Enum

from .enhanced_agent import (
    EnhancedBaseAgent,
    TaskContext,
    AgentResult,
    CollaborationMessage
)


class TeamStrategy(Enum):
    """Team execution strategies"""
    SEQUENTIAL = "sequential"  # Agents execute in order
    PARALLEL = "parallel"  # Agents execute simultaneously
    CONSENSUS = "consensus"  # Agents vote on output
    LEADER_FOLLOWER = "leader_follower"  # One agent leads, others support
    PIPELINE = "pipeline"  # Output of one feeds into next


@dataclass
class TeamMember:
    """Team member configuration"""
    agent_id: str
    role: str  # leader, contributor, reviewer, etc.
    priority: int = 1  # Higher priority agents execute first
    required: bool = True  # If True, team fails if this agent fails


@dataclass
class TeamConfiguration:
    """Team configuration"""
    team_id: str
    name: str
    description: str
    members: List[TeamMember]
    strategy: TeamStrategy = TeamStrategy.SEQUENTIAL
    shared_context: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    max_retries: int = 3


@dataclass
class TeamResult:
    """Result from team execution"""
    team_id: str
    status: str  # success, error, partial
    outputs: Dict[str, Any]
    agent_results: Dict[str, AgentResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0
    agents_executed: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class Team:
    """
    Team of agents collaborating on a task.

    Features:
    - Multiple execution strategies
    - Shared context and memory
    - Inter-agent communication
    - Fault tolerance
    - Result aggregation
    """

    def __init__(
        self,
        config: TeamConfiguration,
        agent_registry: 'AgentRegistry',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize team.

        Args:
            config: Team configuration
            agent_registry: Registry to get agent instances
            logger: Logger instance
        """
        self.config = config
        self.agent_registry = agent_registry
        self.logger = logger or logging.getLogger(f"team.{config.team_id}")

        # Team state
        self.context: Optional[TaskContext] = None
        self.members: Dict[str, EnhancedBaseAgent] = {}
        self.message_bus: List[CollaborationMessage] = []

        # Load team members
        self._load_members()

    def _load_members(self):
        """Load agent instances for team members"""
        for member in self.config.members:
            try:
                agent = self.agent_registry.get_agent(member.agent_id)
                self.members[member.agent_id] = agent
                self.logger.info(
                    f"Loaded agent {member.agent_id} for team {self.config.team_id}"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to load agent {member.agent_id}: {e}"
                )
                if member.required:
                    raise

    async def execute(
        self,
        task: Dict[str, Any],
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> TeamResult:
        """
        Execute task with team.

        Args:
            task: Task specification
            user_id: User requesting execution
            workflow_id: Associated workflow ID

        Returns:
            TeamResult with aggregated outputs
        """
        import time
        start_time = time.time()

        # Create shared context
        self.context = TaskContext(
            task_id=str(uuid.uuid4()),
            user_id=user_id,
            team_id=self.config.team_id,
            workflow_id=workflow_id,
            shared_data=self.config.shared_context.copy()
        )

        # Notify agents they joined a team
        member_ids = set(self.members.keys())
        for agent in self.members.values():
            agent.join_team(self.config.team_id, member_ids)
            agent.shared_context = self.context

        self.logger.info(
            f"Team {self.config.team_id} executing with strategy: "
            f"{self.config.strategy.value}"
        )

        # Execute based on strategy
        try:
            if self.config.strategy == TeamStrategy.SEQUENTIAL:
                result = await self._execute_sequential(task)
            elif self.config.strategy == TeamStrategy.PARALLEL:
                result = await self._execute_parallel(task)
            elif self.config.strategy == TeamStrategy.CONSENSUS:
                result = await self._execute_consensus(task)
            elif self.config.strategy == TeamStrategy.LEADER_FOLLOWER:
                result = await self._execute_leader_follower(task)
            elif self.config.strategy == TeamStrategy.PIPELINE:
                result = await self._execute_pipeline(task)
            else:
                raise ValueError(f"Unknown strategy: {self.config.strategy}")

        except Exception as e:
            self.logger.error(f"Team execution failed: {e}")
            result = TeamResult(
                team_id=self.config.team_id,
                status="error",
                outputs={},
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

        finally:
            # Cleanup: agents leave team
            for agent in self.members.values():
                agent.leave_team()

        result.execution_time_ms = (time.time() - start_time) * 1000
        result.agents_executed = len(result.agent_results)

        self.logger.info(
            f"Team {self.config.team_id} finished: "
            f"status={result.status}, "
            f"time={result.execution_time_ms:.2f}ms, "
            f"agents={result.agents_executed}"
        )

        return result

    async def _execute_sequential(self, task: Dict[str, Any]) -> TeamResult:
        """Execute agents sequentially in priority order"""
        agent_results = {}
        outputs = {}

        # Sort members by priority (descending)
        sorted_members = sorted(
            self.config.members,
            key=lambda m: m.priority,
            reverse=True
        )

        for member in sorted_members:
            agent = self.members[member.agent_id]

            try:
                self.logger.info(f"Executing agent: {member.agent_id}")

                # Execute agent
                result = await agent.execute(task, self.context)
                agent_results[member.agent_id] = result

                # Add agent outputs to shared context
                if result.status == "success":
                    outputs[member.agent_id] = result.outputs
                    self.context.shared_data[f"{member.agent_id}_output"] = result.outputs
                elif member.required:
                    # Required agent failed
                    return TeamResult(
                        team_id=self.config.team_id,
                        status="error",
                        outputs=outputs,
                        agent_results=agent_results,
                        error=f"Required agent {member.agent_id} failed: {result.error}"
                    )

            except Exception as e:
                self.logger.error(f"Agent {member.agent_id} error: {e}")
                if member.required:
                    return TeamResult(
                        team_id=self.config.team_id,
                        status="error",
                        outputs=outputs,
                        agent_results=agent_results,
                        error=f"Required agent {member.agent_id} error: {e}"
                    )

        return TeamResult(
            team_id=self.config.team_id,
            status="success",
            outputs=outputs,
            agent_results=agent_results,
            metadata={"shared_context": self.context.shared_data}
        )

    async def _execute_parallel(self, task: Dict[str, Any]) -> TeamResult:
        """Execute all agents in parallel"""
        # For now, simulate parallel with sequential (can use asyncio later)
        agent_results = {}
        outputs = {}

        for member in self.config.members:
            agent = self.members[member.agent_id]

            try:
                result = await agent.execute(task, self.context)
                agent_results[member.agent_id] = result

                if result.status == "success":
                    outputs[member.agent_id] = result.outputs

            except Exception as e:
                self.logger.error(f"Agent {member.agent_id} error: {e}")
                if member.required:
                    return TeamResult(
                        team_id=self.config.team_id,
                        status="error",
                        outputs=outputs,
                        agent_results=agent_results,
                        error=str(e)
                    )

        return TeamResult(
            team_id=self.config.team_id,
            status="success",
            outputs=outputs,
            agent_results=agent_results
        )

    async def _execute_consensus(self, task: Dict[str, Any]) -> TeamResult:
        """Execute all agents and aggregate via consensus"""
        # Execute all agents
        parallel_result = await self._execute_parallel(task)

        # Aggregate outputs (simple majority voting)
        # In practice, this would use more sophisticated consensus
        consensus_output = self._aggregate_outputs(
            parallel_result.agent_results
        )

        parallel_result.outputs["consensus"] = consensus_output
        return parallel_result

    async def _execute_leader_follower(self, task: Dict[str, Any]) -> TeamResult:
        """Leader agent executes first, followers support"""
        # Find leader (highest priority)
        leader = max(self.config.members, key=lambda m: m.priority)
        followers = [m for m in self.config.members if m.agent_id != leader.agent_id]

        agent_results = {}

        # Execute leader
        leader_agent = self.members[leader.agent_id]
        leader_result = await leader_agent.execute(task, self.context)
        agent_results[leader.agent_id] = leader_result

        if leader_result.status != "success":
            return TeamResult(
                team_id=self.config.team_id,
                status="error",
                outputs={},
                agent_results=agent_results,
                error=f"Leader {leader.agent_id} failed"
            )

        # Share leader output
        self.context.shared_data["leader_output"] = leader_result.outputs

        # Execute followers
        for follower in followers:
            agent = self.members[follower.agent_id]
            result = await agent.execute(task, self.context)
            agent_results[follower.agent_id] = result

        return TeamResult(
            team_id=self.config.team_id,
            status="success",
            outputs={"leader": leader_result.outputs},
            agent_results=agent_results
        )

    async def _execute_pipeline(self, task: Dict[str, Any]) -> TeamResult:
        """Execute agents in pipeline: output of N feeds into N+1"""
        agent_results = {}
        current_input = task

        sorted_members = sorted(
            self.config.members,
            key=lambda m: m.priority,
            reverse=True
        )

        for member in sorted_members:
            agent = self.members[member.agent_id]

            # Execute with current input
            result = await agent.execute(current_input, self.context)
            agent_results[member.agent_id] = result

            if result.status != "success":
                if member.required:
                    return TeamResult(
                        team_id=self.config.team_id,
                        status="error",
                        outputs={},
                        agent_results=agent_results,
                        error=f"Pipeline broken at {member.agent_id}"
                    )
            else:
                # Next agent receives this agent's output as input
                current_input = result.outputs

        return TeamResult(
            team_id=self.config.team_id,
            status="success",
            outputs=current_input,  # Final output is last agent's output
            agent_results=agent_results
        )

    def _aggregate_outputs(
        self,
        agent_results: Dict[str, AgentResult]
    ) -> Dict[str, Any]:
        """Aggregate outputs from multiple agents"""
        # Simple aggregation: collect all outputs
        # In practice, use voting, averaging, or LLM-based synthesis
        aggregated = {}

        for agent_id, result in agent_results.items():
            if result.status == "success":
                for key, value in result.outputs.items():
                    if key not in aggregated:
                        aggregated[key] = []
                    aggregated[key].append(value)

        return aggregated

    def send_message_to_agent(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ):
        """
        Send message between team members.

        Args:
            from_agent_id: Source agent
            to_agent_id: Target agent
            message_type: Message type
            payload: Message payload
        """
        message = CollaborationMessage(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            message_type=message_type,
            payload=payload,
            context=self.context
        )

        self.message_bus.append(message)

        # Deliver to target agent
        if to_agent_id in self.members:
            self.members[to_agent_id].receive_message(message)


class AgentRegistry:
    """
    Registry for managing agent instances.
    Supports dynamic loading of 700+ agent definitions.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize agent registry"""
        self.logger = logger or logging.getLogger("agent_registry")
        self.agents: Dict[str, EnhancedBaseAgent] = {}
        self.agent_definitions: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent: EnhancedBaseAgent):
        """Register an agent instance"""
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")

    def get_agent(self, agent_id: str) -> EnhancedBaseAgent:
        """Get agent instance by ID"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self.agents[agent_id]

    def list_agents(
        self,
        category: Optional[str] = None,
        capability: Optional[str] = None
    ) -> List[str]:
        """
        List registered agents.

        Args:
            category: Filter by category
            capability: Filter by capability

        Returns:
            List of agent IDs
        """
        agents = list(self.agents.keys())

        # TODO: Implement filtering

        return agents

    def get_agents_by_category(self, category: str) -> List[EnhancedBaseAgent]:
        """Get all agents in a category"""
        return [
            agent for agent in self.agents.values()
            if agent.metadata.category.value == category
        ]

    def get_agents_by_capability(
        self,
        capability: str
    ) -> List[EnhancedBaseAgent]:
        """Get all agents with a specific capability"""
        return [
            agent for agent in self.agents.values()
            if any(cap.value == capability for cap in agent.metadata.capabilities)
        ]
