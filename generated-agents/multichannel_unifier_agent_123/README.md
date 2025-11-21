# Multichannel Unifier Agent

Unifies email, chat, social DMs into one view

**Agent ID**: `multichannel_unifier_agent_123`
**Category**: customer_support
**Version**: 1.0.0

## Features

- email_processing

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8323
```

## API Usage

```bash
curl -X POST http://localhost:8323/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
