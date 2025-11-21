#!/usr/bin/env python3
"""
Agent Implementation Generator
Converts YAML agent definitions to production-ready code
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List

class AgentGenerator:
    """Generate production agents from YAML catalog"""

    def __init__(self, catalog_dir: str, output_dir: str):
        self.catalog_dir = Path(catalog_dir)
        self.output_dir = Path(output_dir)

    def generate_python_agent(self, agent: Dict, category: str) -> Dict[str, str]:
        """Generate Python FastAPI agent"""

        agent_id = agent['agent_id']
        agent_name = agent['name']
        agent_desc = agent['description']

        # Determine port (8200 + agent number)
        agent_num = int(agent_id.split('_')[-1])
        port = 8200 + (agent_num % 800)  # Keep ports in reasonable range

        # Generate app.py
        app_code = f'''"""
{agent_name}
{agent_desc}

Auto-generated from catalog definition: {agent_id}
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    APP_NAME = "{agent_id.replace('_', '-')}"
    VERSION = "{agent.get('version', '1.0.0')}"
    PORT = {port}
    CLAUDE_API_KEY = "your-api-key-here"
    CLAUDE_MODEL = "{agent.get('llm', {}).get('model', 'claude-3-5-sonnet-20241022')}"
    MAX_TOKENS = {agent.get('llm', {}).get('max_tokens', 4096)}
    TEMPERATURE = {agent.get('llm', {}).get('temperature', 0.7)}

config = Config()

# Metrics
requests_counter = Counter('agent_requests_total', 'Total requests', ['agent_id'])
processing_duration = Histogram('agent_processing_seconds', 'Processing duration')

# Data Models
class AgentRequest(BaseModel):
    task_description: str
    context: Dict[str, Any] = {{}}

class AgentResponse(BaseModel):
    result: str
    metadata: Dict[str, Any]
    processing_time_ms: float

# Service
class {self._to_class_name(agent_name)}Service:
    """Main agent service"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def execute_task(self, request: AgentRequest) -> AgentResponse:
        """Execute agent task"""
        start_time = datetime.utcnow()
        requests_counter.labels(agent_id=config.APP_NAME).inc()

        # Build prompt from template
        prompt_template = agent.get('prompt_template', 'Complete the following task:\\n\\n{{task_description}}')
        prompt = prompt_template

        system_prompt = agent.get('system_prompt', 'You are a helpful AI assistant.')

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                system=system_prompt,
                messages=[{{
                    "role": "user",
                    "content": prompt.format(task_description=request.task_description)
                }}]
            )

            result_text = response.content[0].text if response.content else "No response"

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return AgentResponse(
                result=result_text,
                metadata={{
                    "agent_id": config.APP_NAME,
                    "model": self.model,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }},
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Task execution failed: {{e}}")
            raise HTTPException(status_code=500, detail=str(e))

# Application
app = FastAPI(
    title="{agent_name}",
    description="{agent_desc}",
    version=config.VERSION
)

service = {self._to_class_name(agent_name)}Service(config.CLAUDE_API_KEY, config.CLAUDE_MODEL)

@app.get("/health")
async def health_check():
    return {{
        "status": "healthy",
        "agent_id": config.APP_NAME,
        "version": config.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }}

@app.post("/api/v1/execute", response_model=AgentResponse)
async def execute_task(request: AgentRequest):
    """Execute agent task"""
    try:
        return await service.execute_task(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/")
async def root():
    return {{
        "agent_id": config.APP_NAME,
        "name": "{agent_name}",
        "version": config.VERSION,
        "status": "operational",
        "category": "{category}"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, workers=4)
'''

        # Generate requirements.txt
        requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
anthropic==0.7.7
prometheus-client==0.19.0
"""

        # Generate Dockerfile
        dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE {port}
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "{port}", "--workers", "4"]
"""

        # Generate README
        capabilities_list = "\n".join('- ' + cap for cap in agent.get('capabilities', ['text_generation']))

        readme = f"""# {agent_name}

{agent_desc}

**Agent ID**: `{agent_id}`
**Category**: {category}
**Version**: {agent.get('version', '1.0.0')}

## Features

{capabilities_list}

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port {port}
```

## API Usage

```bash
curl -X POST http://localhost:{port}/api/v1/execute \\
  -H "Content-Type: application/json" \\
  -d '{{"task_description": "Your task here"}}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: {agent.get('version', '1.0.0')}
"""

        return {
            'app.py': app_code,
            'requirements.txt': requirements,
            'Dockerfile': dockerfile,
            'README.md': readme
        }

    def _to_class_name(self, name: str) -> str:
        """Convert agent name to Python class name"""
        # Remove special characters, split words
        words = name.replace('#', '').replace('&', 'And').split()
        return ''.join(word.capitalize() for word in words if word.isalnum())

    def generate_all_agents(self, limit: int = None):
        """Generate all agents from catalog"""

        stats = {'total': 0, 'generated': 0, 'errors': 0}

        # Iterate through all YAML files
        for yaml_file in self.catalog_dir.rglob('*.yaml'):
            category = yaml_file.parent.name

            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if not data or 'agents' not in data:
                    continue

                agents = data['agents']
                stats['total'] += len(agents)

                for agent in agents:
                    if limit and stats['generated'] >= limit:
                        return stats

                    agent_id = agent['agent_id']

                    # Create agent directory
                    agent_dir = self.output_dir / agent_id
                    agent_dir.mkdir(parents=True, exist_ok=True)

                    # Generate files
                    files = self.generate_python_agent(agent, category)

                    for filename, content in files.items():
                        filepath = agent_dir / filename
                        with open(filepath, 'w') as f:
                            f.write(content)

                    stats['generated'] += 1

                    if stats['generated'] % 50 == 0:
                        print(f"Generated {stats['generated']} agents...")

            except Exception as e:
                print(f"Error processing {yaml_file}: {e}")
                stats['errors'] += 1

        return stats

def main():
    """Main entry point"""
    import sys

    catalog_dir = "/home/user/AI-Agents/agents/definitions"
    output_dir = "/home/user/AI-Agents/generated-agents"

    generator = AgentGenerator(catalog_dir, output_dir)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    print(f"Generating agents from {catalog_dir}...")
    print(f"Output directory: {output_dir}")
    if limit:
        print(f"Limit: {limit} agents")
    print()

    stats = generator.generate_all_agents(limit=limit)

    print()
    print("=" * 60)
    print(f"Generation Complete!")
    print(f"  Total agents in catalog: {stats['total']}")
    print(f"  Successfully generated: {stats['generated']}")
    print(f"  Errors: {stats['errors']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
