# Agent Smith Roadmap

## v1 - Practical Supervisor Agent

Goal: create a small, useful, read-only supervisor service.

Deliverables:

- FastAPI service scaffold
- Dockerfile and Compose example
- environment configuration
- health endpoint
- Postgres connector boundary
- n8n connector boundary
- Telegram connector boundary
- permission levels
- basic memory/session models
- docs and safety rules

Future v1 milestones:

- `/status` endpoint
- `/jobs` endpoint
- `/errors` endpoint
- `/approvals` endpoint
- `/tools` endpoint
- Telegram long-polling command adapter
- allowed-user enforcement
- human thread persistence
- workflow event session endpoint

## v2 - ALLM-Class MemoryCore

Goal: add a deeper operational memory layer.

Deliverables:

- memory ingestion
- memory classification
- memory linking
- planned retrieval
- context packet builder
- incident memory
- tool priors
- confidence and freshness
- memory audit trail
- retrieval checklists

## Future - Reusable Agent Runtime

Goal: extract Smith patterns into reusable custom-agent architecture.

Possible future agents:

- Builder: development/Codex assistant
- Archivist: document and memory agent
- Operator: server and deployment monitor
- Editor: content QA and review agent
- Scout: research agent
