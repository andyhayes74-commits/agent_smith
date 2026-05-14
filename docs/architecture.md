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
| Adapters | Schema mappings from generic Smith concepts to supervised-system tables and columns. |
| Connectors | Interfaces for Postgres, n8n, Telegram, and future services. |
| Core | Deterministic supervisor logic. |
| Memory | Session, context packet, human thread, and future MemoryCore structures. |
| Policies | Permission levels and action guardrails. |
| Telegram | Direct command handling for allowlisted operator commands. |

---

## Schema Adapter Boundary

Smith v1 reads existing supervised databases through a schema adapter. The adapter
maps Smith's generic supervisor concepts to the table and column names used by the
system being observed:

| Smith concept | Generic default table |
|---|---|
| Jobs | `jobs` |
| Errors | `errors` |
| Approvals | `approvals` |

Identifier validation is intentionally strict because table and column names cannot
be safely passed as database parameters. Smith only allows simple unqualified SQL
identifiers and rejects spaces, punctuation, schema-qualified names, comments, SQL
expressions, function calls, and dangerous SQL keywords.

Smith does not own the supervised schema. It must not create migrations, create
tables, alter tables, or write records as part of v1 supervisor reads.

---

## Telegram Model-control Boundary

Smith v1 supports Telegram model-control commands for observing and changing the
active LLM model at runtime:

- `/model` reports provider, active model, source, and whether LLM access is configured.
- `/models` lists `SMITH_ALLOWED_MODELS` and marks the active model.
- `/model set <model_name>` creates a pending runtime-only change for an allowed model.
- `/model confirm <code>` applies the pending change for the same Telegram user before expiry.
- `/model reset` clears the runtime override and returns to `SMITH_LLM_MODEL`.

These commands do not expose secrets, rewrite `.env`, call model providers, trigger
n8n, or mutate supervised databases. Read-only model status commands are available
at permission level 0. Runtime model changes require permission level 1 or higher
and write only an in-memory Smith audit event.

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
