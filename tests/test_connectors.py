from smith.connectors.n8n import N8nConnector
from smith.connectors.postgres import PostgresConnector
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
