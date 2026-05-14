from typing import Any

from pydantic import BaseModel, Field

from smith.adapters.schema import SchemaAdapterConfigurationError, SupervisorSchemaAdapter
from smith.connectors.postgres import PostgresConnector

ACTIVE_JOB_STATUSES = ("queued", "running", "in_progress", "active")


class SupervisorListResponse(BaseModel):
    """Read-only supervisor list response backed by Postgres rows."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int
    source: str = "postgres"


class SupervisorReadService:
    """Read-only service for supervisor status views from operational Postgres state."""

    def __init__(self, postgres: PostgresConnector, schema: SupervisorSchemaAdapter) -> None:
        self.postgres = postgres
        self.schema = schema

    async def list_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        self.schema.validate_or_raise()
        rows = await self.postgres.fetch(
            f"""
            SELECT {self._jobs_select_clause()}
            FROM {self.schema.tables.jobs}
            ORDER BY {self.schema.jobs.created_at} DESC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    async def list_active_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        self.schema.validate_or_raise()
        activity_expression = self._job_activity_expression()
        rows = await self.postgres.fetch(
            f"""
            SELECT {self._jobs_select_clause()}
            FROM {self.schema.tables.jobs}
            WHERE {self.schema.jobs.status} = ANY($2::text[])
            ORDER BY {activity_expression} DESC
            LIMIT $1
            """,
            limit,
            list(ACTIVE_JOB_STATUSES),
        )
        return self._response(rows)

    async def list_stuck_jobs(
        self,
        *,
        limit: int = 50,
        stale_minutes: int = 30,
    ) -> SupervisorListResponse:
        self.schema.validate_or_raise()
        activity_expression = self._job_activity_expression()
        rows = await self.postgres.fetch(
            f"""
            SELECT {self._jobs_select_clause()}
            FROM {self.schema.tables.jobs}
            WHERE {self.schema.jobs.status} = ANY($2::text[])
              AND {activity_expression} < NOW() - make_interval(mins => $3)
            ORDER BY {activity_expression} ASC
            LIMIT $1
            """,
            limit,
            list(ACTIVE_JOB_STATUSES),
            stale_minutes,
        )
        return self._response(rows)

    async def list_recent_errors(self, *, limit: int = 50) -> SupervisorListResponse:
        self.schema.validate_or_raise()
        rows = await self.postgres.fetch(
            f"""
            SELECT {self._errors_select_clause()}
            FROM {self.schema.tables.errors}
            ORDER BY {self.schema.errors.created_at} DESC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    async def list_pending_approvals(self, *, limit: int = 50) -> SupervisorListResponse:
        self.schema.validate_or_raise()
        rows = await self.postgres.fetch(
            f"""
            SELECT {self._approvals_select_clause()}
            FROM {self.schema.tables.approvals}
            WHERE {self.schema.approvals.status} = $2
            ORDER BY {self.schema.approvals.created_at} ASC
            LIMIT $1
            """,
            limit,
            "pending",
        )
        return self._response(rows)

    def _jobs_select_clause(self) -> str:
        columns = [
            (self.schema.jobs.id, "id"),
            (self.schema.jobs.status, "status"),
            (self.schema.jobs.created_at, "created_at"),
            (self.schema.jobs.updated_at, "updated_at"),
            (self.schema.jobs.title, "title"),
            (self.schema.jobs.client_id, "client_id"),
            (self.schema.jobs.workflow_run_id, "workflow_run_id"),
        ]
        return self._select_clause(columns)

    def _errors_select_clause(self) -> str:
        columns = [
            (self.schema.errors.id, "id"),
            (self.schema.errors.job_id, "job_id"),
            (self.schema.errors.tool_id, "tool_id"),
            (self.schema.errors.message, "message"),
            (self.schema.errors.created_at, "created_at"),
            (self.schema.errors.severity, "severity"),
            (self.schema.errors.raw_payload, "raw_payload"),
        ]
        return self._select_clause(columns)

    def _approvals_select_clause(self) -> str:
        columns = [
            (self.schema.approvals.id, "id"),
            (self.schema.approvals.job_id, "job_id"),
            (self.schema.approvals.status, "status"),
            (self.schema.approvals.approval_type, "approval_type"),
            (self.schema.approvals.created_at, "created_at"),
            (self.schema.approvals.requested_by, "requested_by"),
        ]
        return self._select_clause(columns)

    def _job_activity_expression(self) -> str:
        if not self.schema.jobs.created_at:
            raise SchemaAdapterConfigurationError("Jobs created_at column is required.")
        if self.schema.jobs.updated_at:
            return f"COALESCE({self.schema.jobs.updated_at}, {self.schema.jobs.created_at})"
        return self.schema.jobs.created_at

    def _select_clause(self, columns: list[tuple[str | None, str]]) -> str:
        selected = [f"{column} AS {alias}" for column, alias in columns if column]
        if not selected:
            raise SchemaAdapterConfigurationError("No supervisor columns are configured.")
        return ", ".join(selected)

    def _response(self, rows: list[dict[str, Any]]) -> SupervisorListResponse:
        return SupervisorListResponse(items=rows, count=len(rows))
