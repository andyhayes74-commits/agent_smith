from fastapi.testclient import TestClient

from smith.main import create_app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "agent-smith"
    assert payload["read_only"] is True
