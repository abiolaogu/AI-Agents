# Meeting Notes Agent

Records, cleans up, and summarizes meetings

**Agent ID**: `meeting_notes_agent_002`
**Category**: business_ops
**Version**: 1.0.0

## Features

- text_summarization\n- calendar_management

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8202
```

## API Usage

```bash
curl -X POST http://localhost:8202/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
