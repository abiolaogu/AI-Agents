# Stakeholder Briefing Agent

Makes tailored briefs for investors, partners, etc

**Agent ID**: `stakeholder_briefing_agent_022`
**Category**: business_ops
**Version**: 1.0.0

## Features

- text_summarization

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8222
```

## API Usage

```bash
curl -X POST http://localhost:8222/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task here"}'
```

## Configuration

Set `CLAUDE_API_KEY` environment variable before running.

---

*Auto-generated from catalog definition*
**Version**: 1.0.0
