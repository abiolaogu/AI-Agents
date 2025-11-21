# Executive Summary Agent

Condenses long reports into 1-page briefs

**Agent ID**: `executive_summary_agent_001`
**Category**: business_ops
**Version**: 1.0.0

## Features

- text_summarization\n- report_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8201
```

## API Usage

```bash
curl -X POST http://localhost:8201/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
