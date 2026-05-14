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

These endpoints do not trigger n8n actions and do not mutate database state. They
read through Smith's schema adapter, which maps generic supervisor concepts to the
actual table and column names of the supervised system. If Postgres is not configured
or unavailable, they return `503` with a `postgres_unavailable` detail payload. If
the schema adapter configuration is invalid, they return a safe `503` with a
`schema_adapter_invalid` detail payload rather than executing SQL.

Generic defaults:

```text
SMITH_SCHEMA_PROFILE=generic
SMITH_JOBS_TABLE=jobs
SMITH_ERRORS_TABLE=errors
SMITH_APPROVALS_TABLE=approvals
```

Example custom mapping only, not a confirmed live AI Content schema:

```text
SMITH_SCHEMA_PROFILE=example_monitor
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

Smith does not migrate, alter, or otherwise own supervised databases.

---

## Smith v1 Interpretation

For Smith v1, this API should be treated as an external system boundary.

Smith may read status, progress, errors, approvals, and job state.

Smith should not call mutating endpoints until action permissions, confirmation flow, and audit logging exist.

---

## Telegram Model-control Commands

Smith v1 model-control is command based rather than a write API endpoint. It is
available only to allowlisted Telegram users. The commands are:

| Command | Purpose | Permission |
|---|---|---|
| `/model` | Show provider, active model, source, and LLM configured state. | Level 0 |
| `/models` | List `SMITH_ALLOWED_MODELS` and mark the current model. | Level 0 |
| `/model set <model_name>` | Request a pending runtime-only model override. | Level 1+ |
| `/model confirm <code>` | Confirm the pending override for the requesting user before expiry. | Level 1+ |
| `/model reset` | Clear the runtime override and return to environment config. | Level 1+ |

Model changes never rewrite `.env`, never edit secrets, never restart Smith, and
never allow a model outside `SMITH_ALLOWED_MODELS`. Confirmation writes only an
in-memory Smith audit event in v1.

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
