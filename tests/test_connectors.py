import anyio
import asyncpg
import pytest

from smith.connectors.n8n import N8nConnector
from smith.connectors.postgres import PostgresConnector, PostgresUnavailableError
from smith.connectors.telegram import TelegramConnector


def test_connector_configured_states_work() -> None:
    assert PostgresConnector(database_url=None).is_configured() is False
    assert PostgresConnector(database_url="postgres://example").is_configured() is True

    assert N8nConnector(base_url="http://n8n:5678", api_key=None).is_configured() is False
    assert N8nConnector(base_url="http://n8n:5678", api_key="key").is_configured() is True

    assert TelegramConnector(bot_token="token", allowed_user_ids="").is_configured() is False
    assert TelegramConnector(bot_token="token", allowed_user_ids="123").is_configured() is True


def test_telegram_unknown_users_are_rejected() -> None:
    connector = TelegramConnector(bot_token="token", allowed_user_ids="123,456")

    assert connector.is_allowed_user(123) is True
    assert connector.is_allowed_user("456") is True
    assert connector.is_allowed_user(789) is False
    assert connector.is_allowed_user("not-a-number") is False


def test_postgres_connector_converts_malformed_dsn_errors(monkeypatch) -> None:
    async def raise_client_configuration_error(*args: object, **kwargs: object) -> None:
        raise asyncpg.ClientConfigurationError("invalid DSN contains secret")

    monkeypatch.setattr(asyncpg, "connect", raise_client_configuration_error)
    connector = PostgresConnector(database_url="postgres://user:secret@example/db")

    with pytest.raises(PostgresUnavailableError) as exc_info:
        anyio.run(connector.fetch, "SELECT id FROM jobs LIMIT 1")

    assert str(exc_info.value) == "Postgres is unavailable or misconfigured."
    assert "secret" not in str(exc_info.value)


def test_postgres_connector_converts_interface_errors(monkeypatch) -> None:
    async def raise_interface_error(*args: object, **kwargs: object) -> None:
        raise asyncpg.InterfaceError("invalid connection state")

    monkeypatch.setattr(asyncpg, "connect", raise_interface_error)
    connector = PostgresConnector(database_url="postgres://example")

    with pytest.raises(PostgresUnavailableError):
        anyio.run(connector.fetch, "SELECT id FROM jobs LIMIT 1")


def test_postgres_connector_converts_value_errors(monkeypatch) -> None:
    async def raise_value_error(*args: object, **kwargs: object) -> None:
        raise ValueError("malformed database URL")

    monkeypatch.setattr(asyncpg, "connect", raise_value_error)
    connector = PostgresConnector(database_url="not-a-valid-dsn")

    with pytest.raises(PostgresUnavailableError):
        anyio.run(connector.fetch, "SELECT id FROM jobs LIMIT 1")
