from fastapi.testclient import TestClient

from smith.config import get_settings
from smith.main import create_app

_ENV_VARS = (
    "DATABASE_URL",
    "N8N_BASE_URL",
    "N8N_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ALLOWED_USER_IDS",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "SMITH_SCHEMA_PROFILE",
    "SMITH_JOBS_TABLE",
    "SMITH_ERRORS_TABLE",
    "SMITH_APPROVALS_TABLE",
    "SMITH_JOBS_ID_COLUMN",
    "SMITH_JOBS_STATUS_COLUMN",
    "SMITH_JOBS_CREATED_AT_COLUMN",
    "SMITH_JOBS_UPDATED_AT_COLUMN",
    "SMITH_JOBS_TITLE_COLUMN",
    "SMITH_JOBS_CLIENT_ID_COLUMN",
    "SMITH_JOBS_WORKFLOW_RUN_ID_COLUMN",
    "SMITH_ERRORS_ID_COLUMN",
    "SMITH_ERRORS_JOB_ID_COLUMN",
    "SMITH_ERRORS_TOOL_ID_COLUMN",
    "SMITH_ERRORS_CREATED_AT_COLUMN",
    "SMITH_ERRORS_MESSAGE_COLUMN",
    "SMITH_ERRORS_SEVERITY_COLUMN",
    "SMITH_ERRORS_RAW_PAYLOAD_COLUMN",
    "SMITH_APPROVALS_ID_COLUMN",
    "SMITH_APPROVALS_JOB_ID_COLUMN",
    "SMITH_APPROVALS_STATUS_COLUMN",
    "SMITH_APPROVALS_APPROVAL_TYPE_COLUMN",
    "SMITH_APPROVALS_CREATED_AT_COLUMN",
    "SMITH_APPROVALS_REQUESTED_BY_COLUMN",
)


def _clear_env(monkeypatch) -> None:
    for env_var in _ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)


def test_status_endpoint_returns_ok(monkeypatch) -> None:
    _clear_env(monkeypatch)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/status")

    assert response.status_code == 200


def test_status_includes_expected_default_fields(monkeypatch) -> None:
    _clear_env(monkeypatch)
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
        "schema_profile": "generic",
        "schema_adapter_valid": True,
        "schema_adapter_warnings": [],
        "supervisor_tables": {
            "jobs": "jobs",
            "errors": "errors",
            "approvals": "approvals",
        },
        "configured_integrations": [],
        "missing_integrations": ["postgres", "n8n", "telegram"],
        "warnings": [
            "Smith is running in read-only mode.",
            "Postgres is not configured.",
            "n8n is not configured.",
            "Telegram is not configured.",
        ],
    }


def test_status_reports_invalid_schema_adapter_state(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("SMITH_JOBS_TABLE", "jobs; DROP TABLE jobs")
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = client.get("/status").json()

    assert payload["schema_profile"] == "generic"
    assert payload["schema_adapter_valid"] is False
    assert payload["schema_adapter_warnings"]
    assert "jobs table" in payload["schema_adapter_warnings"][0]
    assert any(warning.startswith("Schema adapter warning:") for warning in payload["warnings"])
