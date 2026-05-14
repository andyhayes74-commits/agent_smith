# Smith v2 - ALLM-Class MemoryCore Direction

**Status:** Future design direction  
**System:** Agent Smith  
**Agent:** Smith  
**Version target:** Smith v2  
**Depends on:** Smith v1 supervisor design brief  

---

## 1. Version Boundary

Smith v1 is the first supervisor-agent design captured in:

```text
docs/smith_v1_supervisor_design_brief.md
```

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

Smith v2 is where the deeper memory architecture begins.

Smith v2 may add an ALLM-class MemoryCore adapted for operational agents.

Smith v1 must not be blocked by the v2 memory design.

---

## 2. Why Memory Moves to v2

A serious agent memory system is larger than basic job/session storage.

Smith v1 needs simple memory so it can operate safely:

```text
jobs
sessions
context packets
human threads
recommendations
action logs
```

Smith v2 can then add a true memory layer that grows from experience.

The rule is:

```text
Smith v1 proves the supervisor.
Smith v2 evolves the memory.
```

---

## 3. ALLM-Class MemoryCore Concept

The ALLM MemoryCore concept should be adapted into a practical agent memory system.

The goal is not just to store records. The goal is to create a memory subsystem that can:

- ingest new operational events
- classify memory types
- link related memories
- track how knowledge was used
- detect repeated patterns
- mutate raw events into useful rules
- maintain confidence and freshness
- support planned retrieval
- build context packets
- influence Smith’s behaviour before LLM calls
- provide an audit trail for memory use

This should become a reusable foundation for future custom agents.

---

## 4. No Nuvion in Smith v2 MemoryCore

Smith v2 MemoryCore should not depend on Nuvion.

Nuvion requires:

- a minting engine
- a symbol registry
- validation rules
- symbolic lifecycle management
- debugging tools
- translation layers

That is unnecessary for Smith v2.

The canonical Smith memory store should remain:

```text
Postgres
JSONB
plain-English summaries
structured tags
relationships
confidence scores
audit logs
retrieval plans
context packets
```

Nuvion may be reconsidered in a later custom-AI phase only after the required minting and validation infrastructure exists.

---

## 5. MemoryCore Design Principle

Smith v2 should treat memory as an active subsystem, not passive storage.

Memory should become its own service-like entity inside the architecture.

```text
Smith
→ asks MemoryCore for context, patterns, risk, and prior experience

MemoryCore
→ ingests, classifies, links, retrieves, distills, audits, and evolves memory
```

The memory system should not simply answer, “What stored text is similar to this question?”

It should answer:

```text
What is this event or question about?
What context is required?
Which records are exact matches?
Which relationships matter?
Which previous incidents are similar?
Which known patterns apply?
Which rules or preferences should influence behaviour?
What is missing?
What should be included in the context packet?
```

---

## 6. Memory Layers

Smith v2 MemoryCore should support multiple memory layers.

### 6.1 Operational Memory

Factual system state:

- jobs
- workflow runs
- tool runs
- events
- errors
- approvals
- outputs
- delivery packs

This is the source-of-truth layer.

### 6.2 Human Interaction Memory

Bounded operator context:

- current job
- current topic
- last referenced job
- last referenced error
- last suggested action
- compact thread summaries

This lets Smith answer follow-up questions naturally without sending long chat history to the LLM.

### 6.3 Tool Memory

Tool experience and capability memory:

- tool status
- tool inputs and outputs
- known failure modes
- average runtime
- recent failures
- successful fixes
- retry limits
- tool health scores

### 6.4 Client Memory

Client-specific operating context:

- brand voice
- approval rules
- forbidden claims
- preferred outputs
- product families
- delivery preferences
- previous job patterns

### 6.5 Incident Memory

Structured failure and recovery history:

- what failed
- why it failed
- which tool was involved
- what fixed it
- whether it repeated
- whether it became a known issue

### 6.6 Learning Memory

Distilled memory created from repeated events:

- known issue patterns
- common fixes
- missing capability patterns
- operator preferences
- risk patterns
- retrieval checklists
- action policy hints

### 6.7 Context Packet Memory

Records of what Smith sent to the LLM or used for deterministic answers:

- context packet
- retrieved records
- missing records
- recommendation
- result
- later outcome

This is essential for debugging memory/retrieval failures.

---

## 7. Memory Lifecycle

Smith v2 MemoryCore should allow memory to evolve.

```text
raw event
→ structured memory
→ linked memory
→ pattern candidate
→ confirmed pattern
→ embedded operating rule
→ reinforced, revised, archived, or deprecated
```

Example:

```text
Raw event:
tool_qa_delivery failed with invalid_json.

Linked memory:
The failure is associated with tool_qa_delivery and Parse QA JSON.

Pattern candidate:
QA workflows sometimes fail when model output contains markdown-wrapped JSON.

Confirmed pattern:
This has happened several times and JSON repair usually works.

Embedded operating rule:
If invalid_json occurs in QA and repair_count < 2, recommend JSON repair before retrying the full workflow.
```

---

## 8. Planned Retrieval

Smith v2 should use planned retrieval, not passive retrieval.

For each workflow event or human question, Smith should:

```text
classify intent
resolve scope
choose required context checklist
fetch exact records first
fetch related records second
fetch patterns third
fetch semantic/similar records only as support
record what was retrieved
record what was missing
build bounded context packet
```

### Example: “Why did it fail?”

Required context:

- current job
- latest failed tool run
- latest error
- failed node
- last successful stage
- tool registry entry
- retry count
- similar incidents
- known fixes
- allowed recovery actions

### Example: “How long left?”

Required context:

- current job
- selected tools
- completed tools
- remaining tools
- average runtime per tool
- historical runtime if available
- queue/concurrency state
- retry/failure status

### Example: “Progress update?”

Required context:

- job status
- completed stages
- current stage
- pending approvals
- recent events
- blocked state
- estimated next stage

---

## 9. Embedded Memory

Smith v2 should not treat memory as a passive archive.

Important memories should be compiled into active structures such as:

- tool priors
- client rules
- operator preferences
- known issue patterns
- common fixes
- retrieval checklists
- risk flags
- action policy hints
- context assembly rules

This means memory influences Smith before any LLM reasoning call.

---

## 10. Suggested MemoryCore Components

Smith v2 MemoryCore may include:

| Component | Purpose |
|---|---|
| Memory Ingestor | Captures new events, sessions, errors, actions, and human messages. |
| Memory Classifier | Assigns memory type, scope, importance, and tags. |
| Memory Linker | Connects memories to jobs, tools, clients, workflow runs, errors, and approvals. |
| Memory Retriever | Builds retrieval plans and fetches required context. |
| Memory Distiller | Converts repeated raw events into patterns and summaries. |
| Memory Pattern Engine | Detects recurring failures, fixes, and missing capabilities. |
| Memory Policy Tagger | Adds safety, approval, visibility, and sensitivity tags. |
| Context Packet Builder | Builds bounded context packets for LLM or deterministic responses. |
| Memory Auditor | Records which memories were used, ignored, missing, or contradicted. |
| Memory Decay Engine | Reduces confidence in stale or contradicted memories. |
| Memory Promoter | Promotes confirmed patterns into operating rules. |

---

## 11. Memory Metadata

Each important memory should include metadata such as:

```text
memory_id
memory_type
scope
source
linked_entities
summary
structured_payload
confidence
importance
freshness
usage_count
success_count
failure_count
contradiction_count
last_confirmed_at
created_at
updated_at
archived_at
```

This allows Smith to know whether a memory is fresh, reliable, global, client-specific, or only weakly supported.

---

## 12. Example Memory Record

```json
{
  "memory_type": "tool_failure_pattern",
  "scope": "tool",
  "linked_entities": {
    "tool_id": "tool_qa_delivery",
    "error_type": "invalid_json"
  },
  "summary": "QA delivery often fails when the model returns markdown-wrapped JSON instead of strict JSON.",
  "pattern": "invalid_json_from_llm",
  "safe_first_action": "run_json_repair",
  "confidence": 0.78,
  "importance": "high",
  "usage_count": 5,
  "success_count": 4,
  "failure_count": 1,
  "last_confirmed_at": "2026-05-14T09:30:00Z"
}
```

---

## 13. Smith v2 Definition of Done

Smith v2 MemoryCore is complete when:

- Smith v1 supervisor remains stable.
- MemoryCore tables or storage structures exist.
- Operational events can be ingested as structured memory.
- Memories are linked to jobs, tools, clients, errors, and workflow runs.
- Human thread memory is stored and summarised.
- Context retrieval uses intent-based required-context checklists.
- Context packets record retrieved and missing context.
- Incident memory can detect repeated failures.
- Tool priors can be generated from incident history.
- Memory confidence and freshness are tracked.
- Smith can explain which memories influenced a recommendation.
- Nuvion is not required.
- Memory remains human-readable and auditable.

---

## 14. Long-Term Direction

Smith v2 should turn memory from static storage into an evolving operational intelligence layer.

The long-term path is:

```text
Smith v1
→ practical supervisor agent

Smith v2
→ ALLM-class MemoryCore for agent memory

Future Custom Agent Runtime
→ reusable memory architecture for multiple agents

Future Custom AI
→ memory-driven behaviour, learning, and adaptation
```

Smith v2 should be the first practical implementation of the deeper memory system: readable, structured, auditable, adaptive, and useful in real operational work.
