# Smith Supervisor Agent - Design Brief

**Status:** Canonical Smith v1 design brief  
**System:** Agent Smith  
**Agent name:** Smith  
**Purpose:** Define the first practical supervisor agent without turning it into a general-purpose agent platform.

---

## 1. Executive Summary

Smith is a dedicated supervisor agent for automation systems.

Smith is not the production workflow engine, not a replacement for n8n, not a general personal assistant, and not an OpenClaw-style autonomous platform. Smith is a controlled operational intelligence layer that watches jobs, understands tool registries, reviews workflow state, answers operator questions, detects problems, recommends safe actions, and eventually performs limited low-risk actions within strict policy.

The first target integration is the AI Content n8n System.

The core architecture is:

```text
Telegram / operator interface
→ Smith supervisor service
→ Postgres operational state
→ tool registry
→ n8n API/webhooks
→ optional LLM reasoning calls
```

Smith should be built as a standalone Dockerised service, probably using Python FastAPI, with Postgres as its operational state source.

Smith must not rely on long-running OpenAI chat history for workflow decisions. Automated workflow reasoning must use fresh, isolated sessions with curated context packets. Human interactions must use persistent but bounded conversation threads so Smith can answer natural follow-up questions such as “why did it fail?”, “how long left?”, or “give me a progress update”.

---

## 2. Smith v1 Scope

Smith v1 should remain focused, practical, and buildable.

Smith v1 is responsible for:

- running as a separate supervisor service
- reading Postgres operational state
- reading the tool registry
- watching jobs and workflow state
- supporting direct Telegram communication
- using isolated workflow sessions
- using bounded human conversation threads
- providing read-only status, errors, approvals, jobs, tools, and stuck-job summaries
- avoiding long-running OpenAI chat history
- remaining auditable and permission-bounded

Smith v1 proves the supervisor.

Smith v2 may add an ALLM-class MemoryCore, but Smith v1 must not be blocked by the v2 memory design.

---

## 3. Why Smith Exists

As automation systems grow, they accumulate jobs, tools, assets, client profiles, approvals, errors, retries, QA checks, and delivery stages.

Without a supervisor layer, the operator has to inspect n8n, Postgres, logs, GitHub, and messaging channels manually. Smith exists to reduce that operational burden.

Smith should answer questions like:

- What jobs are running?
- What jobs are stuck?
- What needs approval?
- Why did this workflow fail?
- Which tool failed?
- Is this safe to retry?
- How long is this process likely to take?
- Which capabilities are missing from the system?
- Did the planner select valid tools?
- Which tool should be built next?
- Are there repeated failures that indicate a system problem?

Smith turns a set of workflows into something that feels watched, managed, and understandable.

---

## 4. What Smith Is

Smith is:

1. **A supervisor agent.** Smith observes, explains, recommends, and later performs limited safe actions.
2. **A domain-specific operational agent.** Smith is built for supervising real systems, not vague chat.
3. **A Postgres-aware service.** Smith reads job state, events, errors, outputs, approvals, tool plans, and tool runs.
4. **A tool-registry-aware service.** Smith understands what tools exist, what inputs they need, and whether they are active, disabled, experimental, or deprecated.
5. **An n8n-aware service.** Smith can inspect workflow state and eventually call safe n8n actions through approved APIs or webhooks.
6. **A Telegram-capable service.** Smith can communicate directly through Telegram without needing OpenClaw.
7. **An audit-first service.** Smith records sessions, recommendations, actions, explanations, and operator interactions.
8. **A safety-bounded agent.** Smith has explicit permission levels and must not bypass approval policy.

---

## 5. What Smith Is Not

Smith is not:

1. **A replacement for n8n.** n8n remains the workflow runtime.
2. **A replacement for the planner.** The planner creates execution plans. Smith reviews, explains, and monitors them.
3. **A broad general agent platform.** Smith should start narrow.
4. **A workflow itself.** Smith should not be implemented only as another n8n workflow.
5. **A long-running OpenAI chat thread.** Smith must not send old workflow/session history into every model call.
6. **An approval bypass.** Smith must not impersonate a human reviewer where human approval is required.
7. **A secret holder in GitHub.** Tokens, API keys, and credentials must stay outside the repository.

---

## 6. Recommended Platform

Recommended stack:

```text
Service: agent-smith
Language: Python FastAPI
Database: Postgres
Workflow control: n8n API/webhooks
Messaging: direct Telegram bot adapter
LLM: OpenAI/OpenRouter/LiteLLM as optional reasoning layer
Deployment: Docker Compose alongside n8n/Postgres
```

Smith should communicate directly with Telegram using a bot token created through BotFather.

Initial mode:

```text
Long polling
```

Production mode:

```text
HTTPS webhook
```

---

## 7. High-Level Architecture

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

## 8. Permission Levels

Smith must be permission-tiered. Do not start with broad action permissions.

```text
0 = Read-only observer
1 = Operator assistant
2 = Safe automation agent
3 = Production supervisor
4 = Development assistant
```

Smith v1 should default to level 0.

---

## 9. Session Model

Smith needs two separate session types:

```text
1. Workflow Event Sessions
2. Human Conversation Threads
```

Workflow event sessions are fresh, isolated, and scoped to one operational event.

Human conversation threads are persistent but bounded. They allow Smith to answer natural follow-up questions without carrying the entire conversation into every LLM call.

---

## 10. LLM Usage Rules

Every LLM call should include:

- fresh system instruction
- bounded context packet
- clear task
- allowed actions
- output schema

It should not include:

- full previous sessions
- full Telegram chat history
- unrelated jobs
- raw secrets
- unnecessary logs

---

## 11. Smith v1 Definition of Done

Smith v1 is complete when:

- Smith runs as its own service.
- Smith connects to Postgres.
- Smith reads active jobs.
- Smith reads pending approvals.
- Smith reads recent errors.
- Smith reads the tool registry.
- Smith exposes a health endpoint.
- Smith has a direct Telegram bot adapter.
- Telegram access is limited to allowed users.
- `/status` works.
- `/jobs` works.
- `/stuck` works.
- `/approvals` works.
- `/errors` works.
- `/tools` works.
- Smith stores human thread context.
- Smith does not perform write actions.
- Smith does not use long-running OpenAI chat history.

---

## 12. Final Direction

Smith should become the calm operational supervisor for automation systems.

Smith should not be magical, vague, or overpowered. It should be controlled, auditable, useful, and narrow.

The long-term relationship should be:

```text
n8n does the work.
Postgres stores the truth.
The tool registry defines capabilities.
The planner chooses tools.
Smith watches, explains, recommends, and safely supervises.
Andy stays in control.
```
