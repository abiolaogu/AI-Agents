# Knowledge Quiz Agent

Trains support staff with mini-quizzes

**Agent ID**: `knowledge_quiz_agent_148`
**Category**: customer_support
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8348
```

## API Usage

```bash
curl -X POST http://localhost:8348/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
