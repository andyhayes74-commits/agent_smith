from functools import partial
from typing import Any

import anyio
import pytest

from smith.adapters.schema import SupervisorSchemaAdapter
from smith.config import Settings
from smith.connectors.postgres import PostgresConnector
from smith.core.supervisor import SupervisorReadService


class CapturePostgres:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, query: str, *args: object) -> list[dict[str, Any]]:
        self.calls.append((query, args))
        PostgresConnector(database_url="postgres://example")._validate_read_only_query(query)
        return []


def _service(settings: Settings) -> tuple[SupervisorReadService, CapturePostgres]:
    postgres = CapturePostgres()
    service = SupervisorReadService(
        postgres,  # type: ignore[arg-type]
        SupervisorSchemaAdapter.from_settings(settings),
    )
    return service, postgres


def test_generated_jobs_query_uses_mapped_names_and_generic_aliases() -> None:
    service, postgres = _service(
        Settings(
            smith_jobs_table="workflow_jobs",
            smith_jobs_id_column="job_uuid",
            smith_jobs_status_column="state",
            smith_jobs_created_at_column="created_on",
            smith_jobs_updated_at_column="",
            smith_jobs_title_column="summary",
            smith_jobs_client_id_column="account_id",
            smith_jobs_workflow_run_id_column="run_uuid",
            _env_file=None,
        )
    )

    anyio.run(partial(service.list_jobs, limit=10))

    query, args = postgres.calls[0]
    normalized_query = " ".join(query.split())
    assert "SELECT *" not in normalized_query.upper()
    assert "FROM workflow_jobs" in normalized_query
    assert "job_uuid AS id" in normalized_query
    assert "state AS status" in normalized_query
    assert "created_on AS created_at" in normalized_query
    assert "summary AS title" in normalized_query
    assert "account_id AS client_id" in normalized_query
    assert "run_uuid AS workflow_run_id" in normalized_query
    assert args == (10,)


def test_active_and_stuck_queries_use_mapped_status_and_activity_columns() -> None:
    service, postgres = _service(
        Settings(
            smith_jobs_table="workflow_jobs",
            smith_jobs_status_column="state",
            smith_jobs_created_at_column="created_on",
            smith_jobs_updated_at_column="last_seen_at",
            _env_file=None,
        )
    )

    anyio.run(partial(service.list_active_jobs, limit=5))
    anyio.run(partial(service.list_stuck_jobs, limit=6, stale_minutes=45))

    active_query = " ".join(postgres.calls[0][0].split())
    stuck_query = " ".join(postgres.calls[1][0].split())
    assert "WHERE state = ANY($2::text[])" in active_query
    assert "ORDER BY COALESCE(last_seen_at, created_on) DESC" in active_query
    assert "COALESCE(last_seen_at, created_on) < NOW()" in stuck_query
    assert postgres.calls[0][1] == (5, ["queued", "running", "in_progress", "active"])
    assert postgres.calls[1][1] == (6, ["queued", "running", "in_progress", "active"], 45)


def test_stuck_query_falls_back_to_created_at_when_updated_at_is_blank() -> None:
    service, postgres = _service(
        Settings(
            smith_jobs_created_at_column="created_on",
            smith_jobs_updated_at_column="",
            _env_file=None,
        )
    )

    anyio.run(service.list_stuck_jobs)

    query = " ".join(postgres.calls[0][0].split())
    assert "COALESCE" not in query
    assert "created_on < NOW()" in query


def test_error_and_approval_queries_use_mapped_names_and_aliases() -> None:
    service, postgres = _service(
        Settings(
            smith_errors_table="runtime_errors",
            smith_errors_id_column="error_uuid",
            smith_errors_created_at_column="happened_at",
            smith_errors_message_column="error_text",
            smith_errors_severity_column="level",
            smith_approvals_table="review_requests",
            smith_approvals_id_column="review_uuid",
            smith_approvals_status_column="review_state",
            smith_approvals_created_at_column="requested_at",
            smith_approvals_requested_by_column="requester",
            _env_file=None,
        )
    )

    anyio.run(partial(service.list_recent_errors, limit=3))
    anyio.run(partial(service.list_pending_approvals, limit=4))

    errors_query = " ".join(postgres.calls[0][0].split())
    approvals_query = " ".join(postgres.calls[1][0].split())
    assert "FROM runtime_errors" in errors_query
    assert "error_uuid AS id" in errors_query
    assert "error_text AS message" in errors_query
    assert "level AS severity" in errors_query
    assert "FROM review_requests" in approvals_query
    assert "review_uuid AS id" in approvals_query
    assert "review_state AS status" in approvals_query
    assert "requester AS requested_by" in approvals_query
    assert "WHERE review_state = $2" in approvals_query


def test_invalid_adapter_configuration_prevents_query_execution() -> None:
    service, postgres = _service(
        Settings(smith_jobs_table="jobs; DROP TABLE jobs", _env_file=None)
    )

    with pytest.raises(RuntimeError):
        anyio.run(service.list_jobs)

    assert postgres.calls == []
