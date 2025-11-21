# Event Follow-up Agent

Sends tailored follow-up messages post-event

**Agent ID**: `event_followup_agent_089`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- email_processing

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8289
```

## API Usage

```bash
curl -X POST http://localhost:8289/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
