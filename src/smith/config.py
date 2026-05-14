from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for Agent Smith."""

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
    def telegram_allowed_user_id_set(self) -> set[str]:
        if not self.telegram_allowed_user_ids:
            return set()
        return {
            user_id.strip()
            for user_id in self.telegram_allowed_user_ids.split(",")
            if user_id.strip()
        }

    @property
    def is_read_only(self) -> bool:
        return self.smith_permission_level == 0


@lru_cache
def get_settings() -> Settings:
    return Settings()
