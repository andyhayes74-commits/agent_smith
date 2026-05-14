# Agent Smith Architecture

Agent Smith is a standalone supervisor-agent service.

Smith should not run inside n8n. It should run beside n8n as its own Docker container, with its own logs, configuration, permissions, and deployment lifecycle.

---

## High-Level Shape

```text
Telegram / operator
        ↓
Smith Telegram Adapter
        ↓
Smith API / command router
        ↓
Context resolver
        ↓
Supervisor core
        ↓
Postgres + tool registry + n8n API
        ↓
Optional LLM reasoning
        ↓
Recommendation / response / audit log
```

---

## Core Services

| Area | Purpose |
|---|---|
| API | FastAPI endpoints for health, status, workflow events, and future actions. |
| Config | Environment-driven runtime settings. |
| Connectors | Interfaces for Postgres, n8n, Telegram, and future services. |
| Core | Deterministic supervisor logic. |
| Memory | Session, context packet, human thread, and future MemoryCore structures. |
| Policies | Permission levels and action guardrails. |
| Telegram | Future direct Telegram command adapter. |

---

## Smith v1 Rule

Smith v1 must stay read-only until the operator explicitly raises its permission level and action auditing exists.

Smith v1 should prove:

- service deployment
- health checks
- environment loading
- safe configuration
- Postgres/n8n/Telegram connector boundaries
- bounded session model
- human-thread model
- clean docs

---

## Smith v2 Rule

Smith v2 may add ALLM-class MemoryCore concepts.

The memory system should remain human-readable, structured, auditable, and independent of Nuvion.
