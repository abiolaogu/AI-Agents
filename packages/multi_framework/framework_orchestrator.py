"""
Multi-Framework Orchestrator
Unified interface for LangGraph, CrewAI, AutoGen, and custom framework
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import asyncio
from dataclasses import dataclass

class FrameworkType(Enum):
    """Supported AI agent frameworks"""
    LANGGRAPH = "langgraph"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    CUSTOM = "custom"
    LANGCHAIN = "langchain"
    SEMANTIC_KERNEL = "semantic_kernel"

@dataclass
class FrameworkConfig:
    """Configuration for framework execution"""
    framework_type: FrameworkType
    model_provider: str = "anthropic"
    model_name: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4000
    streaming: bool = False
    callbacks: List[Any] = None
    custom_settings: Dict[str, Any] = None

class BaseFrameworkAdapter(ABC):
    """Base adapter for all AI frameworks"""

    def __init__(self, config: FrameworkConfig):
        self.config = config

    @abstractmethod
    async def execute_agent(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent"""
        pass

    @abstractmethod
    async def execute_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a team of agents"""
        pass

    @abstractmethod
    async def execute_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complex workflow"""
        pass

    @abstractmethod
    def supports_feature(self, feature: str) -> bool:
        """Check if framework supports a specific feature"""
        pass

class LangGraphAdapter(BaseFrameworkAdapter):
    """Adapter for LangGraph framework - best for complex workflows and state machines"""

    def __init__(self, config: FrameworkConfig):
        super().__init__(config)
        try:
            from langgraph.graph import StateGraph, END
            from langgraph.prebuilt import ToolExecutor
            self.StateGraph = StateGraph
            self.END = END
            self.ToolExecutor = ToolExecutor
        except ImportError:
            raise ImportError("LangGraph not installed. Install with: pip install langgraph")

    async def execute_agent(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent using LangGraph"""
        from langchain_anthropic import ChatAnthropic
        from langchain.agents import AgentExecutor, create_openai_functions_agent
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

        # Initialize LLM
        llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", agent_def.get("system_prompt", "")),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Execute
        result = await llm.ainvoke(task.get("task_description", ""))

        return {
            "result": result.content,
            "metadata": {
                "framework": "langgraph",
                "model": self.config.model_name,
                "tokens_used": result.response_metadata.get("usage", {})
            }
        }

    async def execute_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute team workflow using LangGraph state machine"""
        from langchain_anthropic import ChatAnthropic

        # Define state
        class TeamState(dict):
            messages: List[str]
            current_agent: str
            results: Dict[str, Any]
            final_output: str

        # Create state graph
        workflow = self.StateGraph(TeamState)

        # Add nodes for each agent
        for agent in team_def.get("agents", []):
            async def agent_node(state, agent_id=agent["agent_id"]):
                llm = ChatAnthropic(model=self.config.model_name)
                result = await llm.ainvoke(state.get("messages", [])[-1])
                state["results"][agent_id] = result.content
                return state

            workflow.add_node(agent["agent_id"], agent_node)

        # Add edges based on execution strategy
        strategy = team_def.get("execution_strategy", "sequential")

        if strategy == "sequential":
            agents = team_def.get("agents", [])
            for i in range(len(agents) - 1):
                workflow.add_edge(agents[i]["agent_id"], agents[i + 1]["agent_id"])
            workflow.add_edge(agents[-1]["agent_id"], self.END)

        # Set entry point
        workflow.set_entry_point(team_def["agents"][0]["agent_id"])

        # Compile and run
        app = workflow.compile()
        final_state = await app.ainvoke({
            "messages": [task.get("task_description", "")],
            "current_agent": "",
            "results": {},
            "final_output": ""
        })

        return {
            "result": final_state.get("final_output", ""),
            "metadata": {
                "framework": "langgraph",
                "team_id": team_def.get("team_id"),
                "agents_executed": list(final_state.get("results", {}).keys())
            }
        }

    async def execute_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complex workflow with branching logic"""
        # LangGraph excels at this - full state machine support
        return await self.execute_team(workflow_def, task)

    def supports_feature(self, feature: str) -> bool:
        """LangGraph feature support"""
        return feature in [
            "state_machine",
            "complex_workflows",
            "branching",
            "loops",
            "error_recovery",
            "streaming",
            "human_in_loop"
        ]

class CrewAIAdapter(BaseFrameworkAdapter):
    """Adapter for CrewAI framework - best for role-based agent teams"""

    def __init__(self, config: FrameworkConfig):
        super().__init__(config)
        try:
            from crewai import Agent, Task, Crew, Process
            self.Agent = Agent
            self.Task = Task
            self.Crew = Crew
            self.Process = Process
        except ImportError:
            raise ImportError("CrewAI not installed. Install with: pip install crewai")

    async def execute_agent(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent using CrewAI"""
        from crewai import Agent, Task
        from langchain_anthropic import ChatAnthropic

        # Create LLM
        llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature
        )

        # Create agent
        agent = Agent(
            role=agent_def.get("name", "Agent"),
            goal=agent_def.get("description", "Complete the task"),
            backstory=agent_def.get("system_prompt", "I am an AI assistant"),
            llm=llm,
            verbose=True
        )

        # Create task
        crew_task = Task(
            description=task.get("task_description", ""),
            agent=agent,
            expected_output="Detailed response"
        )

        # Execute (CrewAI is sync, wrap in async)
        result = await asyncio.to_thread(crew_task.execute)

        return {
            "result": result,
            "metadata": {
                "framework": "crewai",
                "agent_role": agent.role
            }
        }

    async def execute_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute team using CrewAI's crew concept"""
        from crewai import Agent, Task, Crew, Process
        from langchain_anthropic import ChatAnthropic

        llm = ChatAnthropic(model=self.config.model_name)

        # Create agents
        agents = []
        for agent_def in team_def.get("agents", []):
            agent = Agent(
                role=agent_def.get("name", "Agent"),
                goal=agent_def.get("description", "Complete assigned tasks"),
                backstory=agent_def.get("system_prompt", "I am an expert"),
                llm=llm,
                verbose=True
            )
            agents.append(agent)

        # Create tasks
        tasks = []
        task_desc = task.get("task_description", "")
        for agent in agents:
            crew_task = Task(
                description=task_desc,
                agent=agent,
                expected_output="Detailed analysis"
            )
            tasks.append(crew_task)

        # Create crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential if team_def.get("execution_strategy") == "sequential" else Process.hierarchical,
            verbose=True
        )

        # Execute
        result = await asyncio.to_thread(crew.kickoff)

        return {
            "result": result,
            "metadata": {
                "framework": "crewai",
                "team_id": team_def.get("team_id"),
                "agents_count": len(agents)
            }
        }

    async def execute_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow - uses team execution"""
        return await self.execute_team(workflow_def, task)

    def supports_feature(self, feature: str) -> bool:
        """CrewAI feature support"""
        return feature in [
            "role_based_agents",
            "hierarchical_teams",
            "sequential_execution",
            "delegation",
            "collaboration"
        ]

class AutoGenAdapter(BaseFrameworkAdapter):
    """Adapter for AutoGen framework - best for conversational multi-agent systems"""

    def __init__(self, config: FrameworkConfig):
        super().__init__(config)
        try:
            import autogen
            self.autogen = autogen
        except ImportError:
            raise ImportError("AutoGen not installed. Install with: pip install pyautogen")

    async def execute_agent(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single agent using AutoGen"""
        config_list = [{
            "model": self.config.model_name,
            "api_key": "your_api_key",  # Should come from environment
            "api_type": "anthropic"
        }]

        assistant = self.autogen.AssistantAgent(
            name=agent_def.get("name", "assistant"),
            llm_config={"config_list": config_list},
            system_message=agent_def.get("system_prompt", "")
        )

        user_proxy = self.autogen.UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )

        # Execute conversation
        await asyncio.to_thread(
            user_proxy.initiate_chat,
            assistant,
            message=task.get("task_description", "")
        )

        return {
            "result": assistant.last_message()["content"],
            "metadata": {
                "framework": "autogen",
                "conversation_length": len(assistant.chat_messages)
            }
        }

    async def execute_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi-agent conversation using AutoGen"""
        config_list = [{
            "model": self.config.model_name,
            "api_key": "your_api_key"
        }]

        # Create agents
        agents = []
        for agent_def in team_def.get("agents", []):
            agent = self.autogen.AssistantAgent(
                name=agent_def.get("name", "agent"),
                llm_config={"config_list": config_list},
                system_message=agent_def.get("system_prompt", "")
            )
            agents.append(agent)

        # Create group chat
        groupchat = self.autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=10
        )

        manager = self.autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": config_list}
        )

        # Initiate chat
        await asyncio.to_thread(
            agents[0].initiate_chat,
            manager,
            message=task.get("task_description", "")
        )

        return {
            "result": groupchat.messages[-1]["content"],
            "metadata": {
                "framework": "autogen",
                "messages_exchanged": len(groupchat.messages),
                "agents_participated": len(agents)
            }
        }

    async def execute_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using nested conversations"""
        return await self.execute_team(workflow_def, task)

    def supports_feature(self, feature: str) -> bool:
        """AutoGen feature support"""
        return feature in [
            "conversational_agents",
            "code_execution",
            "group_chat",
            "human_in_loop",
            "nested_conversations",
            "function_calling"
        ]

class CustomFrameworkAdapter(BaseFrameworkAdapter):
    """Adapter for our custom framework - optimized for our use cases"""

    async def execute_agent(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using custom framework"""
        from packages.agent_framework.enhanced_agent import EnhancedAgent

        agent = EnhancedAgent(agent_def)
        result = await agent.execute(task)

        return result

    async def execute_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute team using custom team framework"""
        from packages.agent_framework.team import AgentTeam

        team = AgentTeam(team_def)
        result = await team.execute(task)

        return result

    async def execute_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using custom orchestration"""
        from packages.agent_framework.workflow import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(workflow_def)
        result = await orchestrator.execute(task)

        return result

    def supports_feature(self, feature: str) -> bool:
        """Custom framework feature support"""
        return True  # We support everything!

class FrameworkOrchestrator:
    """Main orchestrator that routes to appropriate framework"""

    def __init__(self):
        self.adapters = {
            FrameworkType.LANGGRAPH: LangGraphAdapter,
            FrameworkType.CREWAI: CrewAIAdapter,
            FrameworkType.AUTOGEN: AutoGenAdapter,
            FrameworkType.CUSTOM: CustomFrameworkAdapter
        }

    def get_adapter(self, config: FrameworkConfig) -> BaseFrameworkAdapter:
        """Get appropriate adapter for framework"""
        adapter_class = self.adapters.get(config.framework_type)
        if not adapter_class:
            raise ValueError(f"Unsupported framework: {config.framework_type}")

        return adapter_class(config)

    async def execute_agent(
        self,
        agent_def: Dict[str, Any],
        task: Dict[str, Any],
        framework: Optional[FrameworkType] = None
    ) -> Dict[str, Any]:
        """Execute agent using best framework for the task"""

        # Auto-select framework if not specified
        if not framework:
            framework = self._select_best_framework(agent_def, task)

        config = FrameworkConfig(framework_type=framework)
        adapter = self.get_adapter(config)

        return await adapter.execute_agent(agent_def, task)

    async def execute_team(
        self,
        team_def: Dict[str, Any],
        task: Dict[str, Any],
        framework: Optional[FrameworkType] = None
    ) -> Dict[str, Any]:
        """Execute team using best framework"""

        if not framework:
            framework = self._select_best_framework_for_team(team_def, task)

        config = FrameworkConfig(framework_type=framework)
        adapter = self.get_adapter(config)

        return await adapter.execute_team(team_def, task)

    async def execute_workflow(
        self,
        workflow_def: Dict[str, Any],
        task: Dict[str, Any],
        framework: Optional[FrameworkType] = None
    ) -> Dict[str, Any]:
        """Execute complex workflow"""

        if not framework:
            framework = self._select_best_framework_for_workflow(workflow_def, task)

        config = FrameworkConfig(framework_type=framework)
        adapter = self.get_adapter(config)

        return await adapter.execute_workflow(workflow_def, task)

    def _select_best_framework(self, agent_def: Dict[str, Any], task: Dict[str, Any]) -> FrameworkType:
        """Intelligently select best framework for agent execution"""

        # If agent specifies preferred framework, use it
        if "preferred_framework" in agent_def:
            return FrameworkType(agent_def["preferred_framework"])

        # Default to custom framework for single agents
        return FrameworkType.CUSTOM

    def _select_best_framework_for_team(self, team_def: Dict[str, Any], task: Dict[str, Any]) -> FrameworkType:
        """Select best framework for team execution"""

        strategy = team_def.get("execution_strategy", "sequential")

        # CrewAI for role-based teams
        if "roles" in team_def or strategy == "hierarchical":
            return FrameworkType.CREWAI

        # AutoGen for conversational teams
        if strategy == "conversational":
            return FrameworkType.AUTOGEN

        # LangGraph for complex workflows
        if strategy in ["pipeline", "conditional"]:
            return FrameworkType.LANGGRAPH

        # Default to custom
        return FrameworkType.CUSTOM

    def _select_best_framework_for_workflow(self, workflow_def: Dict[str, Any], task: Dict[str, Any]) -> FrameworkType:
        """Select best framework for workflow execution"""

        # LangGraph for complex state machines
        if "branches" in workflow_def or "loops" in workflow_def:
            return FrameworkType.LANGGRAPH

        # CrewAI for process-driven workflows
        if "process" in workflow_def:
            return FrameworkType.CREWAI

        # Default to LangGraph for workflows
        return FrameworkType.LANGGRAPH

# Global orchestrator instance
orchestrator = FrameworkOrchestrator()
