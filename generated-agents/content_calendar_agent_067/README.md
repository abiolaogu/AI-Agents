# Content Calendar Agent

Plans monthly content topics and dates

**Agent ID**: `content_calendar_agent_067`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- calendar_management

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8267
```

## API Usage

```bash
curl -X POST http://localhost:8267/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
