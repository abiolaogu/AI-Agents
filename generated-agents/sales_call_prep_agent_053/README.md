# Sales Call Prep Agent

Briefs reps before each call with research

**Agent ID**: `sales_call_prep_agent_053`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- text_summarization

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8253
```

## API Usage

```bash
curl -X POST http://localhost:8253/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
