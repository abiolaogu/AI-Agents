# AI-Agents Platform -- Documentation Index

This directory contains the complete documentation suite for the AI-Agents platform.
Use this file as the entry point to navigate all project documentation.

---

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [Gap Analysis](gap-analysis.md) | Codebase audit and remediation roadmap | Engineering leads |
| [Architecture](architecture.md) | System design, component diagrams, data flow | All engineers |
| [API Reference](api-reference.md) | REST endpoint catalogue with request/response schemas | Backend + Frontend |
| [Data Model](data-model.md) | Database schema, relationships, migration strategy | Backend |
| [Agent Catalog](agent-catalog.md) | All 1,500 agents by category with capabilities | Product + Sales |
| [Agent Lifecycle](agent-lifecycle.md) | How agents are defined, generated, deployed, monitored | DevOps + Backend |
| [Orchestration Guide](orchestration-guide.md) | Workflow engine, Celery dispatch, Redpanda streaming | Backend |
| [Multi-Agent Systems](multi-agent-systems.md) | Framework adapters (LangGraph, CrewAI, AutoGen) | AI Engineers |
| [LLM Integration](llm-integration.md) | Claude 3.5 Sonnet integration, prompt engineering, safety | AI Engineers |
| [Agent Marketplace](agent-marketplace.md) | Frontend marketplace, search, discovery, activation | Frontend + Product |
| [Safety Guardrails](safety-guardrails.md) | OPA policies, input validation, output filtering | Security + AI |
| [Security](security.md) | Auth, secrets, network policies, vulnerability scanning | Security |
| [Monitoring and Observability](monitoring-and-observability.md) | Prometheus, Grafana, Loki, alerts | SRE |
| [Deployment Guide](deployment-guide.md) | Docker Compose, Kubernetes, Helm, RunPod | DevOps |
| [Configuration Management](configuration-management.md) | Consul, env vars, feature flags | DevOps + Backend |
| [Testing Strategy](testing-strategy.md) | Unit, integration, e2e, load testing approach | QA + Backend |
| [CI/CD Pipeline](ci-cd-pipeline.md) | GitHub Actions workflows, build, test, deploy | DevOps |
| [Performance](performance.md) | Benchmarks, caching, scaling, cost optimisation | SRE + Backend |
| [Disaster Recovery](disaster-recovery.md) | Backup, restore, failover procedures | SRE |
| [Runbook](runbook.md) | Operational procedures and incident response | SRE + On-call |
| [Contributing](contributing.md) | Development workflow, code standards, PR process | All engineers |
| [Changelog](changelog.md) | Version history and release notes | All |
| [Glossary](glossary.md) | Domain terminology and acronyms | All |
| [FAQ](faq.md) | Frequently asked questions | All |
| [Hardware Requirements](Hardware_Requirements.md) | Compute, storage, network specifications | Infrastructure |
| [Tech Stack Migration](tech-stack-migration.md) | Migration paths for Docker, Helm, Coolify, Fleet | DevOps |
| [Figma/Make Prompts](design/Figma_Make_Prompts.md) | UI/UX design prompts for Figma and Make | Design + Product |

---

## Existing Documentation (Pre-Pipeline)

These documents were present before the documentation pipeline ran and remain valid references:

| Document | Location |
|----------|----------|
| Agent Implementations Summary | [AGENT_IMPLEMENTATIONS_SUMMARY.md](AGENT_IMPLEMENTATIONS_SUMMARY.md) |
| Agent Implementation Template | [AI_AGENT_IMPLEMENTATION_TEMPLATE.md](AI_AGENT_IMPLEMENTATION_TEMPLATE.md) |
| 700-Agent Architecture | [ARCHITECTURE_700_AGENTS.md](ARCHITECTURE_700_AGENTS.md) |
| Complete Platform Roadmap | [COMPLETE_PLATFORM_ROADMAP.md](COMPLETE_PLATFORM_ROADMAP.md) |
| Full Agent Implementation Guide | [FULL_AGENT_IMPLEMENTATION_GUIDE.md](FULL_AGENT_IMPLEMENTATION_GUIDE.md) |
| Phase 2 Agents Summary | [PHASE_2_AGENTS_SUMMARY.md](PHASE_2_AGENTS_SUMMARY.md) |
| Platform Expansion Strategy | [PLATFORM_EXPANSION_STRATEGY.md](PLATFORM_EXPANSION_STRATEGY.md) |
| Technical Specifications | [Technical_Specifications.md](Technical_Specifications.md) |
| Security Report | [Security_Report.md](Security_Report.md) |
| Training Manual | [Training_Manual.md](Training_Manual.md) |
| User Manual | [User_Manual.md](User_Manual.md) |
| Video Training Scripts | [Video_Training_Scripts.md](Video_Training_Scripts.md) |

### Subdirectories

- `guides/` -- User, admin, and developer guides
- `project_docs/` -- Technical specifications and architecture diagrams
- `training/` -- Admin, developer, and end-user training manuals
- `technical/` -- Complete technical reference
- `videos/` -- Video tutorial scripts
- `design/` -- Figma/Make design prompts

---

## Documentation Standards

All new documentation follows these conventions:

1. **Markdown format** with ATX-style headings (`#`, `##`, `###`).
2. **200-500 lines** per document for completeness without bloat.
3. **Code blocks** use triple backticks with language identifiers.
4. **Tables** use pipe syntax with header separators.
5. **Cross-references** use relative markdown links.
6. **No emojis** in technical documentation.
7. **Date stamps** on documents that may become stale.

---

*Last updated: 2026-02-17*
