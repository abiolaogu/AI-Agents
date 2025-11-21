# Ideal Customer Profile Agent

Refines ICP based on closed-won data

**Agent ID**: `ideal_customer_profile_agent_065`
**Category**: sales_marketing
**Version**: 1.0.0

## Features

- document_processing

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8265
```

## API Usage

```bash
curl -X POST http://localhost:8265/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
