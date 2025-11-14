"""
End-to-End Tests for Team Collaboration

Tests the core feature: "The real magic happens when several of these
agents collaborate as a team rather than living alone."
"""

import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "agent_framework"))

from agent_framework.enhanced_agent import (
    AgentCategory,
    AgentCapability,
    create_agent_metadata,
    TaskContext
)
from agent_framework.agent_loader import AgentDefinitionLoader, GenericLLMAgent
from agent_framework.team import (
    Team,
    TeamConfiguration,
    TeamMember,
    TeamStrategy,
    AgentRegistry
)


@pytest.fixture
def agent_registry():
    """Create agent registry with test agents"""
    registry = AgentRegistry()
    return registry


@pytest.fixture
def agent_loader(tmp_path):
    """Create agent loader with test definitions"""
    # Create test agent definitions
    definitions_dir = tmp_path / "definitions"
    definitions_dir.mkdir()

    # Create test business ops agents
    business_ops_dir = definitions_dir / "business_ops"
    business_ops_dir.mkdir()

    test_agents = {
        "agents": [
            {
                "agent_id": "test_summary_agent",
                "name": "Test Summary Agent",
                "description": "Test agent for summarization",
                "category": "business_ops",
                "version": "1.0.0",
                "capabilities": ["text_summarization"],
                "inputs": [{"name": "text", "type": "text", "required": True}],
                "outputs": [{"name": "summary", "type": "text"}],
                "prompt_template": "Summarize: {{text}}",
                "system_prompt": "You are a summary agent",
                "llm": {"model": "claude-3-5-sonnet-20241022"}
            },
            {
                "agent_id": "test_action_agent",
                "name": "Test Action Agent",
                "description": "Test agent for action extraction",
                "category": "business_ops",
                "version": "1.0.0",
                "capabilities": ["text_generation"],
                "inputs": [{"name": "text", "type": "text", "required": True}],
                "outputs": [{"name": "actions", "type": "array"}],
                "prompt_template": "Extract actions from: {{text}}",
                "system_prompt": "You are an action extraction agent",
                "llm": {"model": "claude-3-5-sonnet-20241022"}
            }
        ]
    }

    import yaml
    with open(business_ops_dir / "test_agents.yaml", "w") as f:
        yaml.dump(test_agents, f)

    loader = AgentDefinitionLoader(definitions_dir)
    loader.load_all_definitions()
    return loader


class TestSingleAgentExecution:
    """Test individual agent execution"""

    def test_agent_creation_from_definition(self, agent_loader):
        """Test creating agent from YAML definition"""
        agent = agent_loader.create_agent("test_summary_agent")

        assert agent.agent_id == "test_summary_agent"
        assert agent.metadata.name == "Test Summary Agent"
        assert agent.metadata.category == AgentCategory.BUSINESS_OPS

    def test_agent_execution(self, agent_loader):
        """Test basic agent execution"""
        agent = agent_loader.create_agent("test_summary_agent")

        task = {"text": "This is a long document that needs summarizing."}
        result = agent.execute(task)

        assert result.status == "success"
        assert "summary" in result.outputs
        assert result.execution_time_ms > 0
        assert result.agent_id == "test_summary_agent"

    def test_agent_execution_with_context(self, agent_loader):
        """Test agent execution with shared context"""
        agent = agent_loader.create_agent("test_summary_agent")

        context = TaskContext(
            task_id="test_task_001",
            user_id="test_user",
            shared_data={"project": "Q4 Report"}
        )

        task = {"text": "Financial summary for Q4"}
        result = agent.execute(task, context)

        assert result.status == "success"
        assert result.execution_time_ms > 0


class TestTeamFormation:
    """Test team creation and management"""

    def test_team_creation(self, agent_registry, agent_loader):
        """Test creating a team"""
        # Register agents
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        # Create team configuration
        config = TeamConfiguration(
            team_id="test_team_001",
            name="Test Team",
            description="Team for testing",
            members=[
                TeamMember(agent_id="test_summary_agent", role="leader", priority=1),
                TeamMember(agent_id="test_action_agent", role="contributor", priority=2)
            ],
            strategy=TeamStrategy.SEQUENTIAL
        )

        team = Team(config, agent_registry)

        assert team.config.team_id == "test_team_001"
        assert len(team.members) == 2

    def test_agents_join_team(self, agent_registry, agent_loader):
        """Test agents joining a team"""
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        # Before joining team
        assert agent1.current_team is None
        assert len(agent1.team_members) == 0

        # Join team
        team_id = "test_team_001"
        members = {agent1.agent_id, agent2.agent_id}
        agent1.join_team(team_id, members)

        assert agent1.current_team == team_id
        assert agent1.team_members == members

        # Leave team
        agent1.leave_team()
        assert agent1.current_team is None


class TestSequentialExecution:
    """Test sequential team execution strategy"""

    def test_sequential_team_execution(self, agent_registry, agent_loader):
        """Test team executing agents sequentially"""
        # Setup
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        config = TeamConfiguration(
            team_id="sequential_team",
            name="Sequential Test Team",
            description="Test sequential execution",
            members=[
                TeamMember(agent_id="test_summary_agent", role="leader", priority=1),
                TeamMember(agent_id="test_action_agent", role="contributor", priority=2)
            ],
            strategy=TeamStrategy.SEQUENTIAL
        )

        team = Team(config, agent_registry)

        # Execute
        task = {"text": "Meeting notes: Discussed Q4 goals. Action: Create report."}
        result = team.execute(task, user_id="test_user")

        # Verify
        assert result.status == "success"
        assert result.agents_executed == 2
        assert "test_summary_agent" in result.outputs
        assert "test_action_agent" in result.outputs
        assert result.execution_time_ms > 0


class TestParallelExecution:
    """Test parallel team execution strategy"""

    def test_parallel_team_execution(self, agent_registry, agent_loader):
        """Test team executing agents in parallel"""
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        config = TeamConfiguration(
            team_id="parallel_team",
            name="Parallel Test Team",
            description="Test parallel execution",
            members=[
                TeamMember(agent_id="test_summary_agent", role="contributor", priority=1),
                TeamMember(agent_id="test_action_agent", role="contributor", priority=1)
            ],
            strategy=TeamStrategy.PARALLEL
        )

        team = Team(config, agent_registry)

        task = {"text": "Complex document with multiple aspects"}
        result = team.execute(task)

        assert result.status == "success"
        assert result.agents_executed == 2


class TestPipelineExecution:
    """Test pipeline team execution strategy"""

    def test_pipeline_team_execution(self, agent_registry, agent_loader):
        """Test pipeline where output of one agent feeds into next"""
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        config = TeamConfiguration(
            team_id="pipeline_team",
            name="Pipeline Test Team",
            description="Test pipeline execution",
            members=[
                TeamMember(agent_id="test_summary_agent", role="stage1", priority=2),
                TeamMember(agent_id="test_action_agent", role="stage2", priority=1)
            ],
            strategy=TeamStrategy.PIPELINE
        )

        team = Team(config, agent_registry)

        task = {"text": "Initial input document"}
        result = team.execute(task)

        assert result.status == "success"
        # In pipeline, final output is from last agent
        assert result.outputs is not None


class TestInterAgentCommunication:
    """Test communication between agents in a team"""

    def test_send_message_between_agents(self, agent_loader):
        """Test agents sending messages to each other"""
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")

        # Setup team
        team_id = "comm_test_team"
        members = {agent1.agent_id, agent2.agent_id}
        agent1.join_team(team_id, members)
        agent2.join_team(team_id, members)

        # Agent 1 sends message to Agent 2
        message = agent1.send_message(
            to_agent=agent2.agent_id,
            message_type="request",
            payload={"data": "test data"}
        )

        assert message.from_agent == agent1.agent_id
        assert message.to_agent == agent2.agent_id
        assert message.message_type == "request"
        assert message.payload["data"] == "test data"

        # Agent 2 receives message
        agent2.receive_message(message)
        assert len(agent2.message_queue) == 1

    def test_broadcast_to_team(self, agent_loader):
        """Test agent broadcasting to all team members"""
        agents = [
            agent_loader.create_agent("test_summary_agent"),
            agent_loader.create_agent("test_action_agent")
        ]

        team_id = "broadcast_team"
        members = {a.agent_id for a in agents}

        for agent in agents:
            agent.join_team(team_id, members)

        # Broadcast from first agent
        messages = agents[0].broadcast_to_team(
            message_type="notification",
            payload={"event": "task_completed"}
        )

        # Should send to all other members (N-1)
        assert len(messages) == len(agents) - 1


class TestSharedContext:
    """Test shared context and memory between agents"""

    def test_shared_data_access(self, agent_loader):
        """Test agents sharing data via context"""
        agent = agent_loader.create_agent("test_summary_agent")

        context = TaskContext(
            task_id="context_test",
            shared_data={"project_name": "Test Project"}
        )

        agent.shared_context = context

        # Get shared data
        project = agent.get_shared_data("project_name")
        assert project == "Test Project"

        # Set shared data
        agent.set_shared_data("status", "in_progress")
        assert context.shared_data["status"] == "in_progress"


class TestErrorHandling:
    """Test error handling and fault tolerance"""

    def test_failed_agent_in_team(self, agent_registry, agent_loader):
        """Test team handling when an agent fails"""
        agent1 = agent_loader.create_agent("test_summary_agent")
        agent2 = agent_loader.create_agent("test_action_agent")
        agent_registry.register_agent(agent1)
        agent_registry.register_agent(agent2)

        config = TeamConfiguration(
            team_id="error_test_team",
            name="Error Handling Team",
            description="Test error handling",
            members=[
                TeamMember(agent_id="test_summary_agent", role="leader", priority=1, required=True),
                TeamMember(agent_id="test_action_agent", role="contributor", priority=2, required=False)
            ],
            strategy=TeamStrategy.SEQUENTIAL
        )

        team = Team(config, agent_registry)

        # Execute with missing required input (should fail gracefully)
        task = {}  # Missing required "text" field
        result = team.execute(task)

        # Team should handle error
        assert result.status == "error"
        assert result.error is not None


class TestPerformanceMetrics:
    """Test agent and team performance tracking"""

    def test_agent_metrics_tracking(self, agent_loader):
        """Test that agent tracks performance metrics"""
        agent = agent_loader.create_agent("test_summary_agent")

        assert agent.total_executions == 0
        assert agent.total_tokens_used == 0

        # Execute multiple times
        task = {"text": "Test document"}
        for _ in range(3):
            agent.execute(task)

        metrics = agent.get_metrics()
        assert metrics["total_executions"] == 3
        assert metrics["total_tokens_used"] > 0
        assert metrics["average_execution_time_ms"] > 0


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world collaboration scenarios"""

    def test_quarterly_report_generation(self, agent_registry, agent_loader):
        """
        Test complex scenario: Multiple agents collaborating to create
        a quarterly business report.

        This is "the real magic" - agents working as a team!
        """
        # Create specialized agents for the task
        agents_needed = ["test_summary_agent", "test_action_agent"]

        for agent_id in agents_needed:
            agent = agent_loader.create_agent(agent_id)
            agent_registry.register_agent(agent)

        # Configure team with specific strategy
        config = TeamConfiguration(
            team_id="quarterly_report_team",
            name="Quarterly Report Team",
            description="Generates comprehensive quarterly reports",
            members=[
                TeamMember(agent_id="test_summary_agent", role="summarizer", priority=1),
                TeamMember(agent_id="test_action_agent", role="action_tracker", priority=2)
            ],
            strategy=TeamStrategy.SEQUENTIAL,
            shared_context={
                "quarter": "Q4 2024",
                "company": "Test Corp"
            }
        )

        team = Team(config, agent_registry)

        # Execute complex task
        task = {
            "text": """
            Q4 2024 Performance Summary:
            - Revenue: $10M (up 25% YoY)
            - New customers: 150
            - Action items: Launch new product, expand to EU market
            """
        }

        result = team.execute(task, user_id="ceo@testcorp.com")

        # Verify successful collaboration
        assert result.status == "success"
        assert result.agents_executed == 2
        assert result.execution_time_ms < 10000  # Complete in under 10 seconds
        assert "test_summary_agent" in result.agent_results
        assert "test_action_agent" in result.agent_results

        # Verify shared context was used
        assert result.metadata.get("shared_context") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
