# Voice-of-Customer Agent

Summarizes themes from tickets and reviews

**Agent ID**: `voice_of_customer_agent_121`
**Category**: customer_support
**Version**: 1.0.0

## Features

- text_summarization

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8321
```

## API Usage

```bash
curl -X POST http://localhost:8321/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
