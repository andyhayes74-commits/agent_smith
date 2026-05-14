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
    llm_configured: bool
    ready_for_supervision: bool
    configured_integrations: list[str]
    missing_integrations: list[str]
    warnings: list[str]


class StatusService:
    """Builds Smith's deterministic status view from configuration only."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_status(self) -> SmithStatus:
        postgres = PostgresConnector(database_url=self.settings.database_url)
        n8n = N8nConnector(base_url=self.settings.n8n_base_url, api_key=self.settings.n8n_api_key)
        telegram = TelegramConnector(
            bot_token=self.settings.telegram_bot_token,
            allowed_user_ids=self.settings.telegram_allowed_user_id_set,
        )

        integration_states = {
            "postgres": postgres.is_configured(),
            "n8n": n8n.is_configured(),
            "telegram": telegram.is_configured(),
        }
        configured_integrations = [
            name for name, configured in integration_states.items() if configured
        ]
        missing_integrations = [
            name for name, configured in integration_states.items() if not configured
        ]
        llm_provider = self.settings.normalized_llm_provider
        llm_configured = self.settings.llm_configured
        warnings = self._build_warnings(
            postgres_configured=integration_states["postgres"],
            n8n_configured=integration_states["n8n"],
            telegram_configured=integration_states["telegram"],
            llm_provider=llm_provider,
            llm_configured=llm_configured,
        )

        return SmithStatus(
            service=self.settings.smith_service_name,
            environment=self.settings.smith_env,
            permission_level=self.settings.smith_permission_level,
            read_only=self.settings.is_read_only,
            postgres_configured=integration_states["postgres"],
            n8n_configured=integration_states["n8n"],
            telegram_configured=integration_states["telegram"],
            llm_provider=llm_provider,
            llm_configured=llm_configured,
            ready_for_supervision=all(integration_states.values()),
            configured_integrations=configured_integrations,
            missing_integrations=missing_integrations,
            warnings=warnings,
        )

    def _build_warnings(
        self,
        *,
        postgres_configured: bool,
        n8n_configured: bool,
        telegram_configured: bool,
        llm_provider: str,
        llm_configured: bool,
    ) -> list[str]:
        warnings: list[str] = []

        if self.settings.is_read_only:
            warnings.append("Smith is running in read-only mode.")
        if not postgres_configured:
            warnings.append("Postgres is not configured.")
        if not n8n_configured:
            warnings.append("n8n is not configured.")
        if not telegram_configured:
            warnings.append("Telegram is not configured.")
        if llm_provider != "none" and not llm_configured:
            warnings.append("LLM provider is set but not fully configured.")

        return warnings
