# HR, People & Culture Agent #28

Specialized agent for hr, people & culture tasks (agent 28)

**Agent ID**: `hr_people_agent_28_228`
**Category**: hr_people
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8428
```

## API Usage

```bash
curl -X POST http://localhost:8428/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
