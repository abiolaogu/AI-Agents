# Finance, Accounting & Legal Agent #25

Specialized agent for finance, accounting & legal tasks (agent 25)

**Agent ID**: `finance_legal_agent_25_175`
**Category**: finance_legal
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8375
```

## API Usage

```bash
curl -X POST http://localhost:8375/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
