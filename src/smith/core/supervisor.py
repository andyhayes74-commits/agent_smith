from typing import Any

from pydantic import BaseModel, Field

from smith.connectors.postgres import PostgresConnector


class SupervisorListResponse(BaseModel):
    """Read-only supervisor list response backed by Postgres rows."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int
    source: str = "postgres"


class SupervisorReadService:
    """Read-only service for supervisor status views from operational Postgres state."""

    def __init__(self, postgres: PostgresConnector) -> None:
        self.postgres = postgres

    async def list_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        rows = await self.postgres.fetch(
            """
            SELECT *
            FROM jobs
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    async def list_active_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        rows = await self.postgres.fetch(
            """
            SELECT *
            FROM jobs
            WHERE status IN ('queued', 'running', 'in_progress', 'active')
            ORDER BY updated_at DESC, created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    async def list_stuck_jobs(
        self,
        *,
        limit: int = 50,
        stale_minutes: int = 30,
    ) -> SupervisorListResponse:
        rows = await self.postgres.fetch(
            """
            SELECT *
            FROM jobs
            WHERE status IN ('queued', 'running', 'in_progress', 'active')
              AND COALESCE(updated_at, created_at) < NOW() - ($2::text || ' minutes')::interval
            ORDER BY COALESCE(updated_at, created_at) ASC
            LIMIT $1
            """,
            limit,
            stale_minutes,
        )
        return self._response(rows)

    async def list_recent_errors(self, *, limit: int = 50) -> SupervisorListResponse:
        rows = await self.postgres.fetch(
            """
            SELECT *
            FROM errors
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    async def list_pending_approvals(self, *, limit: int = 50) -> SupervisorListResponse:
        rows = await self.postgres.fetch(
            """
            SELECT *
            FROM approvals
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT $1
            """,
            limit,
        )
        return self._response(rows)

    def _response(self, rows: list[dict[str, Any]]) -> SupervisorListResponse:
        return SupervisorListResponse(items=rows, count=len(rows))
