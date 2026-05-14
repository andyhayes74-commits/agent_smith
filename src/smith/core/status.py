from pydantic import BaseModel

from smith.config import Settings
from smith.connectors.n8n import N8nConnector
from smith.connectors.postgres import PostgresConnector
from smith.connectors.telegram import TelegramConnector


class SmithStatus(BaseModel):
    service: str
    environment: str
    permission_level: int
    read_only: bool
    postgres_configured: bool
    n8n_configured: bool
    telegram_configured: bool
    llm_provider: str


class StatusService:
    """Builds Smith's deterministic status view."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_status(self) -> SmithStatus:
        postgres = PostgresConnector(database_url=self.settings.database_url)
        n8n = N8nConnector(base_url=self.settings.n8n_base_url, api_key=self.settings.n8n_api_key)
        telegram = TelegramConnector(
            bot_token=self.settings.telegram_bot_token,
            allowed_user_ids=self.settings.telegram_allowed_user_id_set,
        )

        return SmithStatus(
            service=self.settings.smith_service_name,
            environment=self.settings.smith_env,
            permission_level=self.settings.smith_permission_level,
            read_only=self.settings.is_read_only,
            postgres_configured=postgres.is_configured(),
            n8n_configured=n8n.is_configured(),
            telegram_configured=telegram.is_configured(),
            llm_provider=self.settings.llm_provider,
        )
