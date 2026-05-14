# Agent Smith

Agent Smith is a custom AI supervisor agent for automation systems, with structured memory, tool awareness, Telegram control, and safe operational reasoning.

Smith starts as a practical supervisor for the AI Content n8n System, then grows into a reusable custom-agent runtime. The first goal is not broad autonomy. The first goal is a controlled service that can watch jobs, understand system state, answer operator questions, detect problems, and recommend safe actions.

---

## Current Direction

Smith is being designed in two major stages.

### Smith v1 - Supervisor Agent

Smith v1 is the first practical build.

It should:

- run as its own Docker service
- connect to Postgres
- read automation job state
- read recent errors and events
- read pending approvals
- read the tool registry
- expose a health endpoint
- communicate through Telegram
- use allowlisted Telegram users only
- use isolated workflow sessions
- use bounded human conversation threads
- avoid long-running OpenAI chat history
- remain read-only at first

Smith v1 proves the supervisor.

### Smith v2 - ALLM-Class MemoryCore

Smith v2 adds deeper memory.

It may introduce an ALLM-class MemoryCore adapted for operational agents. The goal is to move beyond passive stored records toward structured, evolving memory that supports planned retrieval, incident learning, context packets, confidence, freshness, tool priors, and embedded behaviour.

Smith v2 evolves the memory.

---

## What Smith Is

Smith is:

- a custom supervisor agent
- a domain-specific operational assistant
- a Postgres-aware service
- a tool-registry-aware service
- an n8n-aware service
- a Telegram-capable service
- an audit-first service
- a stepping stone toward reusable custom agents

Smith is not:

- a replacement for n8n
- a general personal assistant
- an OpenClaw-style agent platform
- a long-running chat thread
- an approval bypass
- a place to store secrets

---

## First Target Architecture

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
Postgres + Tool Registry + n8n API
        ↓
Optional LLM reasoning
        ↓
Recommendation / response / action log
```

---

## Repository Status

This repository currently contains a starter scaffold.

The scaffold deliberately includes minimal implementation code. It establishes structure, naming, boundaries, configuration, and documentation before feature work begins.

No production secrets should be committed to this repository.

---

## Planned Stack

Recommended v1 stack:

```text
Python
FastAPI
Postgres
Docker
Telegram bot API
Optional OpenAI/OpenRouter/LiteLLM reasoning layer
```

Smith should run as a separate container alongside n8n and Postgres, not inside the n8n container.

---

## Suggested Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn smith.main:app --reload
```

Health and deterministic configuration status checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
```

Read-only supervisor endpoints backed by Postgres when `DATABASE_URL` is configured.
Smith maps generic supervisor concepts (`jobs`, `errors`, and `approvals`) to the
supervised system schema through a read-only schema adapter:

```bash
curl http://localhost:8000/jobs
curl http://localhost:8000/jobs/active
curl http://localhost:8000/jobs/stuck
curl http://localhost:8000/errors/recent
curl http://localhost:8000/approvals/pending
```

If Postgres is not configured or unavailable, supervisor endpoints return `503` with a
clear `postgres_unavailable` error instead of preventing Smith from booting. Invalid
schema adapter settings are also reported safely and are never interpolated into SQL.

The generic defaults are `jobs`, `errors`, and `approvals`. Smith only observes these
tables; it does not migrate, create, alter, insert, update, or delete records in the
supervised database. Optional column settings can be left blank and will be omitted
from supervisor responses. Example custom mapping, not a confirmed production schema:

```text
SMITH_SCHEMA_PROFILE=example_n8n_monitor
SMITH_JOBS_TABLE=workflow_jobs
SMITH_JOBS_ID_COLUMN=job_uuid
SMITH_JOBS_STATUS_COLUMN=state
SMITH_JOBS_CREATED_AT_COLUMN=created_on
SMITH_JOBS_UPDATED_AT_COLUMN=last_seen_at
SMITH_ERRORS_TABLE=runtime_errors
SMITH_ERRORS_MESSAGE_COLUMN=error_text
SMITH_APPROVALS_TABLE=review_requests
SMITH_APPROVALS_STATUS_COLUMN=review_state
```

Run tests:

```bash
pytest
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in local values.

Important: `.env` must not be committed.

```text
SMITH_ENV=development
DATABASE_URL=postgres://...
SMITH_SCHEMA_PROFILE=generic
SMITH_JOBS_TABLE=jobs
SMITH_ERRORS_TABLE=errors
SMITH_APPROVALS_TABLE=approvals
N8N_BASE_URL=http://n8n:5678
N8N_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=...
LLM_PROVIDER=none
LLM_API_KEY=...
SMITH_PERMISSION_LEVEL=0
```

---

## Safety Position

Smith v1 should start read-only.

Smith must not:

- delete files
- publish content
- send final deliverables
- alter credentials
- alter database schema without migration approval
- bypass human approval
- execute disabled or deprecated tools
- expose secrets in logs or Telegram messages

Later action support must be policy-controlled and auditable.

---

## Docs

Key documents:

- `docs/smith_v1_supervisor_design_brief.md`
- `docs/smith_v2_allm_memorycore_direction.md`
- `docs/agent_supervisor_api.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/security.md`

---

## Version Rule

```text
Smith v1 = practical supervisor agent
Smith v2 = ALLM-class MemoryCore direction
Future Smith = reusable custom-agent runtime
```

Build the useful machine first. Grow the thinking machine second.
