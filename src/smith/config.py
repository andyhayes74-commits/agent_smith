from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _has_value(value: str | None) -> bool:
    return bool(value and value.strip())


def parse_telegram_allowed_user_ids(raw_user_ids: str | None) -> set[int]:
    """Parse a comma-separated Telegram user allowlist into integer IDs.

    Invalid entries are ignored so a malformed optional allowlist cannot prevent
    Smith from booting in its safe default mode.
    """

    if not raw_user_ids:
        return set()

    parsed_user_ids: set[int] = set()
    for raw_user_id in raw_user_ids.split(","):
        user_id = raw_user_id.strip()
        if not user_id:
            continue
        try:
            parsed_user_ids.add(int(user_id))
        except ValueError:
            continue

    return parsed_user_ids


class Settings(BaseSettings):
    """Runtime settings for Agent Smith.

    Defaults are intentionally safe: Smith can boot without external services,
    without an LLM, and with read-only permission level 0.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    smith_env: Literal["development", "test", "production"] = "development"
    smith_permission_level: int = Field(default=0, ge=0, le=4)
    smith_service_name: str = "agent-smith"

    database_url: str | None = None

    n8n_base_url: str | None = None
    n8n_api_key: str | None = None

    telegram_bot_token: str | None = None
    telegram_allowed_user_ids: str | None = None

    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None

    log_level: str = "INFO"

    @property
    def postgres_configured(self) -> bool:
        return _has_value(self.database_url)

    @property
    def n8n_configured(self) -> bool:
        return _has_value(self.n8n_base_url) and _has_value(self.n8n_api_key)

    @property
    def telegram_allowed_user_id_set(self) -> set[int]:
        return parse_telegram_allowed_user_ids(self.telegram_allowed_user_ids)

    @property
    def telegram_configured(self) -> bool:
        return _has_value(self.telegram_bot_token) and bool(self.telegram_allowed_user_id_set)

    @property
    def normalized_llm_provider(self) -> str:
        provider = self.llm_provider.strip().lower() if self.llm_provider else "none"
        return provider or "none"

    @property
    def llm_configured(self) -> bool:
        return self.normalized_llm_provider != "none" and _has_value(self.llm_api_key)

    @property
    def is_read_only(self) -> bool:
        return self.smith_permission_level == 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
