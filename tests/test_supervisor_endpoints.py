import pytest
from fastapi.testclient import TestClient

from smith.api.supervisor import get_supervisor_read_service
from smith.config import get_settings
from smith.connectors.postgres import PostgresConnector, UnsafeReadOnlyQueryError
from smith.core.supervisor import SupervisorListResponse
from smith.main import create_app


class MockSupervisorReadService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, int]]] = []

    async def list_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        self.calls.append(("list_jobs", {"limit": limit}))
        return SupervisorListResponse(items=[{"id": "job-1", "status": "done"}], count=1)

    async def list_active_jobs(self, *, limit: int = 50) -> SupervisorListResponse:
        self.calls.append(("list_active_jobs", {"limit": limit}))
        return SupervisorListResponse(items=[{"id": "job-2", "status": "running"}], count=1)

    async def list_stuck_jobs(
        self,
        *,
        limit: int = 50,
        stale_minutes: int = 30,
    ) -> SupervisorListResponse:
        self.calls.append(
            ("list_stuck_jobs", {"limit": limit, "stale_minutes": stale_minutes})
        )
        return SupervisorListResponse(items=[{"id": "job-3", "status": "running"}], count=1)

    async def list_recent_errors(self, *, limit: int = 50) -> SupervisorListResponse:
        self.calls.append(("list_recent_errors", {"limit": limit}))
        return SupervisorListResponse(items=[{"id": "error-1", "job_id": "job-3"}], count=1)

    async def list_pending_approvals(self, *, limit: int = 50) -> SupervisorListResponse:
        self.calls.append(("list_pending_approvals", {"limit": limit}))
        return SupervisorListResponse(items=[{"id": "approval-1", "status": "pending"}], count=1)


@pytest.fixture
def supervisor_client() -> tuple[TestClient, MockSupervisorReadService]:
    get_settings.cache_clear()
    app = create_app()
    service = MockSupervisorReadService()
    app.dependency_overrides[get_supervisor_read_service] = lambda: service
    return TestClient(app), service


def test_jobs_endpoint_uses_mocked_db_service(supervisor_client) -> None:
    client, service = supervisor_client

    response = client.get("/jobs?limit=5")

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"id": "job-1", "status": "done"}],
        "count": 1,
        "source": "postgres",
    }
    assert service.calls == [("list_jobs", {"limit": 5})]


def test_active_jobs_endpoint_uses_mocked_db_service(supervisor_client) -> None:
    client, service = supervisor_client

    response = client.get("/jobs/active?limit=7")

    assert response.status_code == 200
    assert response.json()["items"] == [{"id": "job-2", "status": "running"}]
    assert service.calls == [("list_active_jobs", {"limit": 7})]


def test_stuck_jobs_endpoint_uses_mocked_db_service(supervisor_client) -> None:
    client, service = supervisor_client

    response = client.get("/jobs/stuck?limit=3&stale_minutes=45")

    assert response.status_code == 200
    assert response.json()["items"] == [{"id": "job-3", "status": "running"}]
    assert service.calls == [("list_stuck_jobs", {"limit": 3, "stale_minutes": 45})]


def test_recent_errors_endpoint_uses_mocked_db_service(supervisor_client) -> None:
    client, service = supervisor_client

    response = client.get("/errors/recent")

    assert response.status_code == 200
    assert response.json()["items"] == [{"id": "error-1", "job_id": "job-3"}]
    assert service.calls == [("list_recent_errors", {"limit": 50})]


def test_pending_approvals_endpoint_uses_mocked_db_service(supervisor_client) -> None:
    client, service = supervisor_client

    response = client.get("/approvals/pending")

    assert response.status_code == 200
    assert response.json()["items"] == [{"id": "approval-1", "status": "pending"}]
    assert service.calls == [("list_pending_approvals", {"limit": 50})]


@pytest.mark.parametrize(
    "path",
    [
        "/jobs",
        "/jobs/active",
        "/jobs/stuck",
        "/errors/recent",
        "/approvals/pending",
    ],
)
def test_supervisor_endpoints_return_503_without_postgres(monkeypatch, path: str) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get(path)

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "error": "postgres_unavailable",
            "message": "Postgres is not configured for Agent Smith.",
        }
    }


def test_postgres_connector_blocks_mutating_queries() -> None:
    connector = PostgresConnector(database_url="postgres://example")

    with pytest.raises(UnsafeReadOnlyQueryError):
        connector._validate_read_only_query("DELETE FROM jobs WHERE id = 1")


def test_supervisor_endpoint_returns_503_for_malformed_postgres_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "not-a-valid-dsn")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/jobs")

    assert response.status_code == 503
    payload = response.json()
    assert payload["detail"]["error"] == "postgres_unavailable"
    assert payload["detail"]["message"] == "Postgres is unavailable or misconfigured."
    assert "not-a-valid-dsn" not in payload["detail"]["message"]
