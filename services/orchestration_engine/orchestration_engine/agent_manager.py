# services/orchestration_engine/orchestration_engine/agent_manager.py

import logging
import os
import json
from typing import Dict, List, Optional, Any

# Import YAML library (optional, graceful fallback)
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class AgentManager:
    """Manages the registration and metadata of agent services."""

    def __init__(self, logger: logging.Logger, definitions_dir: str = "/app/agents/definitions"):
        """Initializes the AgentManager."""
        self.agents: Dict[str, Dict[str, Any]] = {}  # Stores agent_id -> agent_metadata mapping
        self.logger = logger
        self.definitions_dir = definitions_dir
        self.load_agents_from_directory()

    def load_agents_from_directory(self):
        """Loads agent definitions from JSON and YAML files in the specified directory."""
        if not os.path.exists(self.definitions_dir):
            self.logger.warning(f"Definitions directory {self.definitions_dir} does not exist.")
            return

        # Recursively walk through all subdirectories
        for root, dirs, files in os.walk(self.definitions_dir):
            for filename in files:
                filepath = os.path.join(root, filename)

                if filename.endswith(".json"):
                    self._load_json_file(filepath)
                elif filename.endswith((".yaml", ".yml")) and YAML_AVAILABLE:
                    self._load_yaml_file(filepath)

        self.logger.info(f"Loaded {len(self.agents)} agent definitions from {self.definitions_dir}")

    def _load_json_file(self, filepath: str):
        """Load agent definitions from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._process_definition_data(data, filepath)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load agent definition from {filepath}: {e}")

    def _load_yaml_file(self, filepath: str):
        """Load agent definitions from a YAML file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._process_definition_data(data, filepath)
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load agent definition from {filepath}: {e}")

    def _process_definition_data(self, data: Any, filepath: str):
        """Process loaded definition data (handles both single and multi-agent files)."""
        if not data:
            return

        # Handle file with list of agents under 'agents' key
        if isinstance(data, dict) and "agents" in data:
            for agent_def in data["agents"]:
                self._register_from_definition(agent_def, filepath)
        # Handle file with single agent definition
        elif isinstance(data, dict) and "id" in data:
            self._register_from_definition(data, filepath)
        # Handle file that is a list of agents directly
        elif isinstance(data, list):
            for agent_def in data:
                self._register_from_definition(agent_def, filepath)

    def _register_from_definition(self, agent_def: Dict[str, Any], filepath: str):
        """Register an agent from a definition dictionary."""
        agent_id = agent_def.get("id") or agent_def.get("agent_id")
        if agent_id:
            self.register_agent(agent_id, agent_def)
        else:
            self.logger.warning(f"Agent definition in {filepath} missing 'id' field")

    def register_agent(self, agent_id: str, agent_metadata: Dict[str, Any]):
        """
        Registers a new agent service with its metadata.

        Args:
            agent_id: A unique identifier for the agent.
            agent_metadata: A dictionary containing details like url, name, description, category.
        """
        if agent_id in self.agents:
            self.logger.debug(f"Agent {agent_id} already registered. Updating metadata.")
        self.agents[agent_id] = agent_metadata
        self.logger.debug(f"Agent '{agent_metadata.get('name', agent_id)}' ({agent_id}) registered.")

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the metadata for a registered agent."""
        return self.agents.get(agent_id)

    def get_agent_url(self, agent_id: str) -> Optional[str]:
        """Retrieves the URL for a registered agent."""
        agent_info = self.agents.get(agent_id)
        if not agent_info:
            return None
        # Default to a generic agent runner if no specific URL is provided
        # In a real K8s/Docker setup, this might route to a specific service
        return agent_info.get("url") or os.getenv("GENERIC_AGENT_URL", "http://generic-agent:5000")

    def list_agents_details(self) -> List[Dict[str, Any]]:
        """Returns a list of all registered agents with their full metadata."""
        # Add the id to each agent's metadata for the frontend
        detailed_list = []
        for agent_id, metadata in self.agents.items():
            agent_details = metadata.copy()
            agent_details['id'] = agent_id
            detailed_list.append(agent_details)
        return detailed_list

    def list_agents(self) -> List[str]:
        """Returns a list of all registered agent IDs."""
        return list(self.agents.keys())

    def list_agents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Returns agents filtered by category."""
        return [
            {**metadata, 'id': agent_id}
            for agent_id, metadata in self.agents.items()
            if metadata.get('category') == category
        ]

    def search_agents(self, query: str) -> List[Dict[str, Any]]:
        """Search agents by name or description."""
        query_lower = query.lower()
        results = []
        for agent_id, metadata in self.agents.items():
            name = metadata.get('name', '').lower()
            description = metadata.get('description', '').lower()
            if query_lower in name or query_lower in description:
                results.append({**metadata, 'id': agent_id})
        return results

    def get_agent_count(self) -> int:
        """Returns the total number of registered agents."""
        return len(self.agents)
