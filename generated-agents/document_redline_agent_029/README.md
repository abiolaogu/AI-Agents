# Document Redline Agent

Highlights risks or issues in contracts and memos

**Agent ID**: `document_redline_agent_029`
**Category**: business_ops
**Version**: 1.0.0

## Features

- document_processing

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8229
```

## API Usage

```bash
curl -X POST http://localhost:8229/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
