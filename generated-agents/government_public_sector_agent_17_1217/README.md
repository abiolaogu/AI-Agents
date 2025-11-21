# Government & Public Sector Agent #17

Specialized agent for government & public sector services (agent 17)

**Agent ID**: `government_public_sector_agent_17_1217`
**Category**: government_public_sector
**Version**: 1.0.0

## Features

- text_generation\n- analysis\n- automation

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8617
```

## API Usage

```bash
curl -X POST http://localhost:8617/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
