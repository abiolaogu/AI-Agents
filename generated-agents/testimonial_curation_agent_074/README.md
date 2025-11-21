# Testimonial Curation Agent

Selects and formats customer quotes

**Agent ID**: `testimonial_curation_agent_074`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- text_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8274
```

## API Usage

```bash
curl -X POST http://localhost:8274/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
