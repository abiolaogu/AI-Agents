"""
RunPod Serverless Handler

Handles serverless function execution for 700+ AI agents.
Optimized for cold-start performance and horizontal scaling.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("serverless_handler")

# Lazy imports to reduce cold start time
agent_loader = None
agent_registry = None
team_manager = None


def initialize_system():
    """
    Initialize the agent system.
    Called once per container instance (warm pool).
    """
    global agent_loader, agent_registry, team_manager

    if agent_registry is not None:
        logger.info("System already initialized")
        return

    logger.info("Initializing agent system...")
    start_time = time.time()

    # Import heavy dependencies
    from agent_framework.agent_loader import AgentDefinitionLoader
    from agent_framework.team import AgentRegistry

    # Initialize components
    definitions_path = Path("/app/agents/definitions")
    agent_loader = AgentDefinitionLoader(definitions_path, logger)
    agent_loader.load_all_definitions()

    agent_registry = AgentRegistry(logger)

    # Pre-warm frequently used agents (optional)
    # This reduces latency for common requests
    prewarm_agents = os.getenv("PREWARM_AGENTS", "").split(",")
    if prewarm_agents and prewarm_agents[0]:
        for agent_id in prewarm_agents:
            try:
                agent = agent_loader.create_agent(agent_id.strip())
                agent_registry.register_agent(agent)
                logger.info(f"Pre-warmed agent: {agent_id}")
            except Exception as e:
                logger.warning(f"Failed to prewarm {agent_id}: {e}")

    elapsed = (time.time() - start_time) * 1000
    logger.info(f"System initialized in {elapsed:.2f}ms")


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main serverless handler for RunPod.

    Args:
        event: Request event with input data

    Returns:
        Response with output or error
    """
    request_start = time.time()

    try:
        # Initialize system if needed
        initialize_system()

        # Parse request
        input_data = event.get("input", {})
        action = input_data.get("action", "execute_agent")

        logger.info(f"Handling request: action={action}")

        # Route to appropriate handler
        if action == "execute_agent":
            result = handle_execute_agent(input_data)
        elif action == "execute_team":
            result = handle_execute_team(input_data)
        elif action == "execute_workflow":
            result = handle_execute_workflow(input_data)
        elif action == "list_agents":
            result = handle_list_agents(input_data)
        elif action == "health":
            result = handle_health(input_data)
        else:
            result = {
                "error": f"Unknown action: {action}",
                "status": "error"
            }

        # Add timing metadata
        result["metadata"] = result.get("metadata", {})
        result["metadata"]["total_time_ms"] = (time.time() - request_start) * 1000

        return result

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "metadata": {
                "total_time_ms": (time.time() - request_start) * 1000
            }
        }


def handle_execute_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single agent.

    Input:
        {
            "action": "execute_agent",
            "agent_id": "executive_summary_agent_001",
            "task": {"task_description": "..."},
            "user_id": "user_123",
            "context": {...}
        }

    Returns:
        Agent execution result
    """
    agent_id = input_data.get("agent_id")
    task = input_data.get("task", {})
    user_id = input_data.get("user_id")

    if not agent_id:
        return {"error": "agent_id is required", "status": "error"}

    # Get or create agent
    try:
        agent = agent_registry.get_agent(agent_id)
    except ValueError:
        # Agent not in registry, create it
        agent = agent_loader.create_agent(agent_id)
        agent_registry.register_agent(agent)

    # Create context if provided
    context = None
    if "context" in input_data:
        from agent_framework.enhanced_agent import TaskContext
        context = TaskContext(
            task_id=input_data.get("task_id", f"task_{int(time.time())}"),
            user_id=user_id,
            shared_data=input_data.get("context", {})
        )

    # Execute agent
    result = agent.execute(task, context)

    return {
        "status": result.status,
        "outputs": result.outputs,
        "metadata": {
            "agent_id": agent_id,
            "execution_time_ms": result.execution_time_ms,
            "tokens_used": result.tokens_used,
            "agent_name": agent.metadata.name,
            "category": agent.metadata.category.value
        },
        "error": result.error
    }


def handle_execute_team(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a team of agents.

    Input:
        {
            "action": "execute_team",
            "team": {
                "name": "Report Team",
                "strategy": "sequential",
                "members": [
                    {"agent_id": "agent_1", "role": "leader", "priority": 1},
                    {"agent_id": "agent_2", "role": "contributor", "priority": 2}
                ]
            },
            "task": {...},
            "user_id": "user_123"
        }

    Returns:
        Team execution result
    """
    from agent_framework.team import (
        Team,
        TeamConfiguration,
        TeamMember,
        TeamStrategy
    )
    import uuid

    team_config_data = input_data.get("team", {})
    task = input_data.get("task", {})
    user_id = input_data.get("user_id")

    # Parse team configuration
    members = []
    for member_data in team_config_data.get("members", []):
        members.append(TeamMember(
            agent_id=member_data["agent_id"],
            role=member_data.get("role", "contributor"),
            priority=member_data.get("priority", 1),
            required=member_data.get("required", True)
        ))

    strategy_str = team_config_data.get("strategy", "sequential")
    strategy = TeamStrategy(strategy_str)

    team_config = TeamConfiguration(
        team_id=str(uuid.uuid4()),
        name=team_config_data.get("name", "Dynamic Team"),
        description=team_config_data.get("description", ""),
        members=members,
        strategy=strategy,
        shared_context=team_config_data.get("shared_context", {}),
        timeout_seconds=team_config_data.get("timeout_seconds", 300)
    )

    # Ensure all agents are loaded
    for member in members:
        try:
            agent_registry.get_agent(member.agent_id)
        except ValueError:
            agent = agent_loader.create_agent(member.agent_id)
            agent_registry.register_agent(agent)

    # Create and execute team
    team = Team(team_config, agent_registry, logger)
    result = team.execute(task, user_id=user_id)

    return {
        "status": result.status,
        "outputs": result.outputs,
        "metadata": {
            "team_id": result.team_id,
            "execution_time_ms": result.execution_time_ms,
            "agents_executed": result.agents_executed,
            "strategy": strategy.value
        },
        "error": result.error,
        "agent_results": {
            agent_id: {
                "status": res.status,
                "execution_time_ms": res.execution_time_ms,
                "tokens_used": res.tokens_used
            }
            for agent_id, res in result.agent_results.items()
        }
    }


def handle_execute_workflow(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a predefined workflow.

    Input:
        {
            "action": "execute_workflow",
            "workflow_id": "quarterly_report_workflow",
            "inputs": {...},
            "user_id": "user_123"
        }

    Returns:
        Workflow execution result
    """
    # TODO: Implement workflow execution
    # Load workflow definition and execute steps

    return {
        "error": "Workflow execution not yet implemented",
        "status": "error"
    }


def handle_list_agents(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    List available agents.

    Input:
        {
            "action": "list_agents",
            "category": "business_ops",  # optional
            "capability": "text_summarization"  # optional
        }

    Returns:
        List of agents
    """
    category = input_data.get("category")
    capability = input_data.get("capability")

    # Get all agents from loader
    definitions = agent_loader.definitions

    # Filter by category
    if category:
        definitions = {
            aid: defn for aid, defn in definitions.items()
            if defn.get("category") == category
        }

    # Filter by capability
    if capability:
        definitions = {
            aid: defn for aid, defn in definitions.items()
            if capability in defn.get("capabilities", [])
        }

    # Format response
    agents = []
    for agent_id, defn in definitions.items():
        agents.append({
            "agent_id": agent_id,
            "name": defn.get("name"),
            "description": defn.get("description"),
            "category": defn.get("category"),
            "capabilities": defn.get("capabilities", []),
            "version": defn.get("version")
        })

    # Group by category
    by_category = {}
    for agent in agents:
        cat = agent["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(agent)

    return {
        "status": "success",
        "total_agents": len(agents),
        "agents": agents,
        "by_category": by_category,
        "metadata": {
            "total_definitions_loaded": len(agent_loader.definitions)
        }
    }


def handle_health(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "system": "ai-agents-platform",
        "version": "1.0.0",
        "agents_loaded": len(agent_loader.definitions) if agent_loader else 0,
        "agents_registered": len(agent_registry.agents) if agent_registry else 0
    }


# For local testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python serverless_handler.py <action> [params]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "test_agent":
        # Test single agent execution
        event = {
            "input": {
                "action": "execute_agent",
                "agent_id": "executive_summary_agent_001",
                "task": {
                    "task_description": "Summarize this report: Q4 earnings were strong..."
                }
            }
        }
        result = handler(event)
        print(json.dumps(result, indent=2))

    elif action == "test_team":
        # Test team execution
        event = {
            "input": {
                "action": "execute_team",
                "team": {
                    "name": "Test Team",
                    "strategy": "sequential",
                    "members": [
                        {"agent_id": "executive_summary_agent_001", "role": "leader", "priority": 1},
                        {"agent_id": "meeting_notes_agent_002", "role": "contributor", "priority": 2}
                    ]
                },
                "task": {
                    "task_description": "Create executive summary and meeting notes"
                }
            }
        }
        result = handler(event)
        print(json.dumps(result, indent=2))

    elif action == "list":
        # List agents
        event = {
            "input": {
                "action": "list_agents",
                "category": sys.argv[2] if len(sys.argv) > 2 else None
            }
        }
        result = handler(event)
        print(json.dumps(result, indent=2))

    elif action == "health":
        # Health check
        event = {"input": {"action": "health"}}
        result = handler(event)
        print(json.dumps(result, indent=2))
