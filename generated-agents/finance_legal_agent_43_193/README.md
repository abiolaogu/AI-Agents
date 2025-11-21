# Finance, Accounting & Legal Agent #43

Specialized agent for finance, accounting & legal tasks (agent 43)

**Agent ID**: `finance_legal_agent_43_193`
**Category**: finance_legal
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8393
```

## API Usage

```bash
curl -X POST http://localhost:8393/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
