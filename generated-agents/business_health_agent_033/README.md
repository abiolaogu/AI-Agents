# Business Health Agent

Monthly health check report on core metrics

**Agent ID**: `business_health_agent_033`
**Category**: business_ops
**Version**: 1.0.0

## Features

- data_analysis\n- report_generation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8233
```

## API Usage

```bash
curl -X POST http://localhost:8233/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
