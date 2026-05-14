from fastapi.testclient import TestClient

from smith.config import get_settings
from smith.main import create_app


def test_status_endpoint_returns_ok(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("N8N_BASE_URL", raising=False)
    monkeypatch.delenv("N8N_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/status")

    assert response.status_code == 200


def test_status_includes_expected_default_fields(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("N8N_BASE_URL", raising=False)
    monkeypatch.delenv("N8N_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = client.get("/status").json()

    assert payload == {
        "service": "agent-smith",
        "environment": "development",
        "permission_level": 0,
        "read_only": True,
        "postgres_configured": False,
        "n8n_configured": False,
        "telegram_configured": False,
        "llm_provider": "none",
        "llm_configured": False,
        "ready_for_supervision": False,
        "configured_integrations": [],
        "missing_integrations": ["postgres", "n8n", "telegram"],
        "warnings": [
            "Smith is running in read-only mode.",
            "Postgres is not configured.",
            "n8n is not configured.",
            "Telegram is not configured.",
        ],
    }
