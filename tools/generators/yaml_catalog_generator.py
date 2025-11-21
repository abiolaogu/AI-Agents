#!/usr/bin/env python3
"""
YAML Agent Catalog Generator
Generates agent definition YAML files for expansion categories
"""

import yaml
from pathlib import Path
from typing import List, Dict

class YAMLCatalogGenerator:
    """Generate YAML agent definitions for new categories"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    # 15 new categories to reach 1,500 agents
    EXPANSION_CATEGORIES = [
        {
            'dir': 'agriculture_food',
            'name': 'Agriculture & Food',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for agriculture & food industry tasks'
        },
        {
            'dir': 'construction_engineering',
            'name': 'Construction & Engineering',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for construction & engineering tasks'
        },
        {
            'dir': 'energy_utilities',
            'name': 'Energy & Utilities',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for energy & utilities management'
        },
        {
            'dir': 'environmental_sustainability',
            'name': 'Environmental Sustainability',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for environmental sustainability initiatives'
        },
        {
            'dir': 'government_public_sector',
            'name': 'Government & Public Sector',
            'agents_count': 53,  # Extra agents to reach 799
            'description_prefix': 'Specialized agent for government & public sector services'
        },
        {
            'dir': 'hospitality_tourism',
            'name': 'Hospitality & Tourism',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for hospitality & tourism operations'
        },
        {
            'dir': 'insurance_risk',
            'name': 'Insurance & Risk',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for insurance & risk management'
        },
        {
            'dir': 'nonprofit_social_impact',
            'name': 'Nonprofit & Social Impact',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for nonprofit & social impact initiatives'
        },
        {
            'dir': 'research_development',
            'name': 'Research & Development',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for research & development projects'
        },
        {
            'dir': 'security_compliance',
            'name': 'Security & Compliance',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for security & compliance management'
        },
        {
            'dir': 'sports_entertainment',
            'name': 'Sports & Entertainment',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for sports & entertainment industry'
        },
        {
            'dir': 'telecommunications',
            'name': 'Telecommunications',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for telecommunications services'
        },
        {
            'dir': 'transportation_mobility',
            'name': 'Transportation & Mobility',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for transportation & mobility solutions'
        },
        {
            'dir': 'data_science_analytics',
            'name': 'Data Science & Analytics',
            'agents_count': 50,
            'description_prefix': 'Specialized agent for data science & analytics tasks'
        },
        {
            'dir': 'devops_infrastructure',
            'name': 'DevOps & Infrastructure',
            'agents_count': 96,  # Total expansion = 799 + extra 50 = 849 for 1,550 total
            'description_prefix': 'Specialized agent for DevOps & infrastructure automation'
        }
    ]

    def generate_agent_definition(self, category: Dict, agent_num: int, base_id: int) -> Dict:
        """Generate single agent definition"""

        agent_id = f"{category['dir']}_agent_{agent_num}_{base_id}"

        return {
            'agent_id': agent_id,
            'name': f"{category['name']} Agent #{agent_num}",
            'description': f"{category['description_prefix']} (agent {agent_num})",
            'category': category['dir'],
            'version': '1.0.0',
            'capabilities': ['text_generation', 'analysis', 'automation'],
            'inputs': [
                {
                    'name': 'task_description',
                    'type': 'text',
                    'required': True,
                    'description': 'Description of the task to perform'
                }
            ],
            'outputs': [
                {
                    'name': 'result',
                    'type': 'text',
                    'description': "The result of the agent's work"
                }
            ],
            'collaboration': {
                'can_work_with': [],
                'provides_to_team': ['result']
            },
            'llm': {
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 4096,
                'temperature': 0.7
            },
            'prompt_template': f"You are the {category['name']} Agent #{agent_num}.\\n\\nYour primary function is to: {category['description_prefix']} (agent {agent_num})\\n\\nTask Input:\\n{{task_description}}\\n\\nPlease complete the task according to your function.",
            'system_prompt': f"You are an AI assistant specialized in {category['name']}.\\n\\nYour role is: {category['name']} Agent #{agent_num} - {category['description_prefix']} (agent {agent_num})\\n\\nAlways:\\n- Be professional and helpful\\n- Follow best practices for {category['name']}\\n- Provide accurate and actionable responses\\n- Maintain context across interactions"
        }

    def generate_category(self, category: Dict, starting_id: int):
        """Generate all agents for a category"""

        agents = []
        for i in range(1, category['agents_count'] + 1):
            agent_id = starting_id + i
            agent = self.generate_agent_definition(category, i, agent_id)
            agents.append(agent)

        # Create YAML structure
        yaml_data = {'agents': agents}

        # Create category directory
        category_dir = self.output_dir / category['dir']
        category_dir.mkdir(parents=True, exist_ok=True)

        # Write YAML file
        output_file = category_dir / f"{category['dir']}_agents.yaml"
        with open(output_file, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return len(agents)

    def generate_all_categories(self):
        """Generate all expansion categories"""

        total_agents = 0
        starting_id = 1000  # Start IDs from 1000 to avoid conflicts

        print("Generating expansion agent catalog YAML definitions...")
        print(f"Target: 799 agents across 15 categories")
        print()

        for category in self.EXPANSION_CATEGORIES:
            count = self.generate_category(category, starting_id)
            starting_id += count
            total_agents += count

            print(f"✓ {category['name']:<40} {count:>3} agents")

        print()
        print("=" * 60)
        print(f"Total expansion agents generated: {total_agents}")
        print(f"YAML files location: {self.output_dir}")
        print("=" * 60)

        return total_agents

def main():
    output_dir = "/home/user/AI-Agents/agents/definitions"

    generator = YAMLCatalogGenerator(output_dir)
    total = generator.generate_all_categories()

    print()
    print(f"✅ Success! Generated {total} agent definitions")
    print(f"   Combined with existing 701 agents = {701 + total} total agents")

if __name__ == "__main__":
    main()
