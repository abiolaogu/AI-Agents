"""
Agent Definition Loader and Runtime

Loads agent definitions from YAML and creates executable agent instances.
Supports 700+ agents without 700 separate microservices.
"""

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import importlib

from .enhanced_agent import (
    EnhancedBaseAgent,
    AgentWithLLM,
    AgentMetadata,
    AgentCategory,
    AgentCapability,
    TaskContext,
    AgentResult,
    create_agent_metadata
)


class GenericLLMAgent(AgentWithLLM):
    """
    Generic agent that executes based on YAML definition.

    This single class can handle 700+ different agent types by
    loading their behavior from configuration.
    """

    def __init__(
        self,
        definition: Dict[str, Any],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize agent from definition.

        Args:
            definition: Agent definition from YAML
            logger: Logger instance
        """
        # Parse metadata
        metadata = self._parse_metadata(definition)

        # Parse LLM config
        llm_config = definition.get('llm', {})
        model = llm_config.get('model', 'claude-3-5-sonnet-20241022')
        max_tokens = llm_config.get('max_tokens', 4096)
        temperature = llm_config.get('temperature', 0.7)

        super().__init__(
            agent_id=definition['agent_id'],
            metadata=metadata,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            logger=logger
        )

        # Store full definition
        self.definition = definition
        self.prompt_template = definition.get('prompt_template', '')
        self.system_prompt = definition.get('system_prompt', '')
        self.input_schema = definition.get('inputs', [])
        self.output_schema = definition.get('outputs', [])
        self.collaboration_config = definition.get('collaboration', {})

    def _parse_metadata(self, definition: Dict[str, Any]) -> AgentMetadata:
        """Parse agent metadata from definition"""

        # Parse category
        category_str = definition.get('category', 'business_ops')
        category = AgentCategory(category_str)

        # Parse capabilities
        capability_strs = definition.get('capabilities', [])
        capabilities = []
        for cap_str in capability_strs:
            try:
                capabilities.append(AgentCapability(cap_str))
            except ValueError:
                # Unknown capability, skip
                pass

        return create_agent_metadata(
            agent_id=definition['agent_id'],
            name=definition.get('name', 'Unknown Agent'),
            description=definition.get('description', ''),
            category=category,
            capabilities=capabilities,
            version=definition.get('version', '1.0.0'),
            tags=definition.get('tags', [])
        )

    def execute(
        self,
        task: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> AgentResult:
        """
        Execute agent based on definition.

        Args:
            task: Task inputs
            context: Shared context

        Returns:
            AgentResult
        """
        import time
        start_time = time.time()

        self.set_status("running")

        try:
            # Validate inputs
            self._validate_inputs(task)

            # Build prompt from template
            prompt = self._build_prompt(task, context)

            # Call LLM
            llm_response = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt
            )

            # Parse outputs
            outputs = self._parse_outputs(llm_response['text'], task)

            # Create result
            result = AgentResult(
                status="success",
                outputs=outputs,
                metadata={
                    "model": self.model,
                    "agent_type": self.definition.get('name'),
                    "category": self.metadata.category.value
                },
                execution_time_ms=(time.time() - start_time) * 1000,
                tokens_used=llm_response.get('tokens_used', 0),
                agent_id=self.agent_id
            )

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            result = AgentResult(
                status="error",
                outputs={},
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                agent_id=self.agent_id
            )

        finally:
            self.set_status("idle")

        self.log_execution(result)
        return result

    def _validate_inputs(self, task: Dict[str, Any]):
        """Validate task inputs against schema"""
        for input_def in self.input_schema:
            name = input_def['name']
            required = input_def.get('required', False)

            if required and name not in task:
                raise ValueError(f"Required input missing: {name}")

    def _build_prompt(
        self,
        task: Dict[str, Any],
        context: Optional[TaskContext]
    ) -> str:
        """Build prompt from template and task inputs"""

        # Start with base template
        prompt = self.prompt_template

        # Substitute task inputs
        for key, value in task.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        # Add context if available
        if context and context.shared_data:
            context_str = "\n\nShared Context:\n"
            for key, value in context.shared_data.items():
                context_str += f"- {key}: {value}\n"
            prompt += context_str

        return prompt

    def _parse_outputs(
        self,
        llm_text: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM output based on output schema"""

        # Simple parsing - return raw text for each output
        # In practice, use structured output or parsing logic
        outputs = {}

        for output_def in self.output_schema:
            name = output_def['name']
            output_type = output_def.get('type', 'text')

            if output_type == 'text':
                outputs[name] = llm_text
            elif output_type == 'array':
                # Simple split by lines
                outputs[name] = [
                    line.strip()
                    for line in llm_text.split('\n')
                    if line.strip()
                ]
            elif output_type == 'json':
                # Try to parse JSON
                import json
                try:
                    outputs[name] = json.loads(llm_text)
                except:
                    outputs[name] = llm_text
            else:
                outputs[name] = llm_text

        return outputs

    def can_work_with(self, other_agent_id: str) -> bool:
        """Check if can collaborate with another agent"""
        can_work_with_list = self.collaboration_config.get('can_work_with', [])

        # If empty, can work with anyone
        if not can_work_with_list:
            return True

        # Check if other agent is in the list
        return other_agent_id in can_work_with_list


class AgentDefinitionLoader:
    """
    Loads agent definitions from YAML files and creates agent instances.
    """

    def __init__(
        self,
        definitions_path: Path,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize loader.

        Args:
            definitions_path: Path to agent definitions directory
            logger: Logger instance
        """
        self.definitions_path = Path(definitions_path)
        self.logger = logger or logging.getLogger("agent_loader")
        self.definitions: Dict[str, Dict[str, Any]] = {}

    def load_all_definitions(self):
        """Load all agent definitions from YAML files"""
        self.logger.info(f"Loading agent definitions from {self.definitions_path}")

        if not self.definitions_path.exists():
            self.logger.warning(f"Definitions path does not exist: {self.definitions_path}")
            return

        # Load all YAML files
        yaml_files = list(self.definitions_path.rglob("*.yaml")) + \
                     list(self.definitions_path.rglob("*.yml"))

        for yaml_file in yaml_files:
            try:
                self._load_definition_file(yaml_file)
            except Exception as e:
                self.logger.error(f"Failed to load {yaml_file}: {e}")

        self.logger.info(f"Loaded {len(self.definitions)} agent definitions")

    def _load_definition_file(self, yaml_file: Path):
        """Load definitions from a single YAML file"""
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)

        # File can contain single agent or list of agents
        if isinstance(data, dict) and 'agent_id' in data:
            # Single agent
            agent_id = data['agent_id']
            self.definitions[agent_id] = data
            self.logger.debug(f"Loaded agent: {agent_id}")

        elif isinstance(data, dict) and 'agents' in data:
            # List of agents
            for agent_def in data['agents']:
                agent_id = agent_def['agent_id']
                self.definitions[agent_id] = agent_def
                self.logger.debug(f"Loaded agent: {agent_id}")

        elif isinstance(data, list):
            # List format
            for agent_def in data:
                if 'agent_id' in agent_def:
                    agent_id = agent_def['agent_id']
                    self.definitions[agent_id] = agent_def
                    self.logger.debug(f"Loaded agent: {agent_id}")

    def get_definition(self, agent_id: str) -> Dict[str, Any]:
        """Get agent definition by ID"""
        if agent_id not in self.definitions:
            raise ValueError(f"Agent definition not found: {agent_id}")
        return self.definitions[agent_id]

    def create_agent(
        self,
        agent_id: str,
        logger: Optional[logging.Logger] = None
    ) -> GenericLLMAgent:
        """
        Create agent instance from definition.

        Args:
            agent_id: Agent ID
            logger: Logger instance

        Returns:
            Agent instance
        """
        definition = self.get_definition(agent_id)
        return GenericLLMAgent(definition, logger)

    def create_all_agents(
        self,
        category: Optional[str] = None
    ) -> Dict[str, GenericLLMAgent]:
        """
        Create all agents (or filter by category).

        Args:
            category: Optional category filter

        Returns:
            Dict of agent ID -> agent instance
        """
        agents = {}

        for agent_id, definition in self.definitions.items():
            # Filter by category if specified
            if category and definition.get('category') != category:
                continue

            try:
                agent = self.create_agent(agent_id)
                agents[agent_id] = agent
            except Exception as e:
                self.logger.error(f"Failed to create agent {agent_id}: {e}")

        self.logger.info(
            f"Created {len(agents)} agents" +
            (f" in category {category}" if category else "")
        )

        return agents

    def list_categories(self) -> List[str]:
        """List all agent categories"""
        categories = set()
        for definition in self.definitions.values():
            if 'category' in definition:
                categories.add(definition['category'])
        return sorted(categories)

    def count_by_category(self) -> Dict[str, int]:
        """Count agents by category"""
        counts = {}
        for definition in self.definitions.values():
            category = definition.get('category', 'unknown')
            counts[category] = counts.get(category, 0) + 1
        return counts
