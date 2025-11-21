# Lead Source Attribution Agent

Explains where leads really came from

**Agent ID**: `lead_source_attribution_agent_095`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8295
```

## API Usage

```bash
curl -X POST http://localhost:8295/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
