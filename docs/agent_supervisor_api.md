# Agent Supervisor API

Webhook prefix: `/v1/`.

Endpoints map to workflow files:

- `api_create_job`
- `api_submit_message`
- `api_attach_drive_folder`
- `api_check_job_status`
- `api_list_active_jobs`
- `api_progress_updates`
- `api_error_reports`
- `api_approve_analysis`
- `api_approve_plan`
- `api_request_revisions`
- `api_retry_step`
- `api_pause_job`
- `api_resume_job`
- `api_cancel_job`

---

## Safety Boundaries

Agent layer must not:

- delete files
- publish content
- send final deliverables
- alter credentials
- alter database schema
- bypass human approval

---


## Smith v1 Read-only Supervisor Endpoints

Smith v1 exposes read-only HTTP status views backed by Postgres when `DATABASE_URL`
is configured:

| Endpoint | Purpose |
|---|---|
| `GET /jobs` | List recent jobs. |
| `GET /jobs/active` | List queued, running, in-progress, or active jobs. |
| `GET /jobs/stuck` | List active jobs whose latest activity is older than the stale threshold. |
| `GET /errors/recent` | List recent error records. |
| `GET /approvals/pending` | List approval records awaiting human review. |

These endpoints do not trigger n8n actions and do not mutate database state. If
Postgres is not configured or unavailable, they return `503` with a
`postgres_unavailable` detail payload.

---

## Smith v1 Interpretation

For Smith v1, this API should be treated as an external system boundary.

Smith may read status, progress, errors, approvals, and job state.

Smith should not call mutating endpoints until action permissions, confirmation flow, and audit logging exist.

---

## Future Action Flow

```text
operator request
→ authenticate operator
→ resolve job/context
→ check permission level
→ check action safety
→ confirm if required
→ call approved API endpoint
→ record audit log
→ report result
```
