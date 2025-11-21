#!/usr/bin/env python3
"""
Generate Kubernetes manifests for all 1,500 agents
"""

import os
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any


class ManifestGenerator:
    """Generate K8s manifests for agents"""

    def __init__(self, template_path: str, output_dir: str, environment: str):
        self.template_path = template_path
        self.output_dir = Path(output_dir)
        self.environment = environment
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self) -> str:
        """Load deployment template"""
        with open(self.template_path, 'r') as f:
            return f.read()

    def load_agent_catalog(self) -> list[Dict[str, Any]]:
        """Load all agent definitions from catalog"""
        agents = []
        catalog_dir = Path("../../agents/definitions")

        for yaml_file in catalog_dir.rglob("*.yaml"):
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
                if 'agents' in data:
                    agents.extend(data['agents'])

        return agents

    def generate_manifest(self, agent: Dict[str, Any], template: str) -> str:
        """Generate manifest for a single agent"""
        agent_id = agent['agent_id']
        category = agent.get('category', 'general')

        # Extract agent number for port calculation
        try:
            agent_num = int(agent_id.split('_')[-1])
        except (IndexError, ValueError):
            agent_num = hash(agent_id) % 1000

        port = 8200 + (agent_num % 800)

        # Replace placeholders
        manifest = template.replace('AGENT_ID', agent_id)
        manifest = manifest.replace('AGENT_CATEGORY', category)
        manifest = manifest.replace('AGENT_PORT', str(port))

        # Adjust resources based on environment
        if self.environment == 'production':
            manifest = manifest.replace('replicas: 2', 'replicas: 3')
            manifest = manifest.replace('memory: "256Mi"', 'memory: "512Mi"')
            manifest = manifest.replace('memory: "512Mi"', 'memory: "1Gi"')

        return manifest

    def generate_all_manifests(self) -> int:
        """Generate manifests for all agents"""
        print("Loading agent catalog...")
        agents = self.load_agent_catalog()
        print(f"Found {len(agents)} agents")

        print("Loading template...")
        template = self.load_template()

        print("Generating manifests...")
        count = 0

        for agent in agents:
            agent_id = agent['agent_id']
            manifest = self.generate_manifest(agent, template)

            # Save manifest
            output_file = self.output_dir / f"{agent_id}-deployment.yaml"
            with open(output_file, 'w') as f:
                f.write(manifest)

            count += 1
            if count % 100 == 0:
                print(f"Generated {count}/{len(agents)} manifests...")

        print(f"✓ Generated {count} manifests in {self.output_dir}")
        return count

    def generate_kustomization(self, agent_count: int):
        """Generate kustomization.yaml for all manifests"""
        kustomization = {
            'apiVersion': 'kustomize.config.k8s.io/v1beta1',
            'kind': 'Kustomization',
            'namespace': 'ai-agents',
            'resources': [
                f"{agent_id}-deployment.yaml"
                for agent_id in [
                    f.stem.replace('-deployment', '')
                    for f in self.output_dir.glob('*-deployment.yaml')
                ]
            ]
        }

        kustomization_file = self.output_dir / 'kustomization.yaml'
        with open(kustomization_file, 'w') as f:
            yaml.dump(kustomization, f)

        print(f"✓ Generated kustomization.yaml with {agent_count} resources")


def main():
    parser = argparse.ArgumentParser(description='Generate K8s manifests for all agents')
    parser.add_argument(
        '--environment',
        default='development',
        choices=['development', 'staging', 'production'],
        help='Deployment environment'
    )
    parser.add_argument(
        '--output-dir',
        default='./generated-manifests',
        help='Output directory for manifests'
    )
    parser.add_argument(
        '--template',
        default='../kubernetes/agent-deployment-template.yaml',
        help='Path to deployment template'
    )

    args = parser.parse_args()

    generator = ManifestGenerator(
        template_path=args.template,
        output_dir=args.output_dir,
        environment=args.environment
    )

    count = generator.generate_all_manifests()
    generator.generate_kustomization(count)

    print("\nNext steps:")
    print(f"1. Review manifests in {args.output_dir}")
    print(f"2. Apply with: kubectl apply -k {args.output_dir}")


if __name__ == "__main__":
    main()
