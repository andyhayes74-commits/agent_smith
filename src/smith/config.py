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


def parse_allowed_models(raw_models: str | None) -> list[str]:
    """Parse allowed runtime LLM models while preserving order and removing duplicates."""

    if not raw_models:
        return []

    allowed_models: list[str] = []
    seen_models: set[str] = set()
    for raw_model in raw_models.split(","):
        model = raw_model.strip()
        if not model or model in seen_models:
            continue
        allowed_models.append(model)
        seen_models.add(model)

    return allowed_models


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

    smith_schema_profile: str = "generic"

    smith_jobs_table: str = "jobs"
    smith_errors_table: str = "errors"
    smith_approvals_table: str = "approvals"

    smith_jobs_id_column: str = "id"
    smith_jobs_status_column: str = "status"
    smith_jobs_created_at_column: str = "created_at"
    smith_jobs_updated_at_column: str | None = "updated_at"
    smith_jobs_title_column: str | None = None
    smith_jobs_client_id_column: str | None = None
    smith_jobs_workflow_run_id_column: str | None = None

    smith_errors_id_column: str = "id"
    smith_errors_job_id_column: str | None = None
    smith_errors_tool_id_column: str | None = None
    smith_errors_created_at_column: str = "created_at"
    smith_errors_message_column: str = "message"
    smith_errors_severity_column: str | None = None
    smith_errors_raw_payload_column: str | None = None

    smith_approvals_id_column: str = "id"
    smith_approvals_job_id_column: str | None = None
    smith_approvals_status_column: str = "status"
    smith_approvals_approval_type_column: str | None = None
    smith_approvals_created_at_column: str = "created_at"
    smith_approvals_requested_by_column: str | None = None

    n8n_base_url: str | None = None
    n8n_api_key: str | None = None

    telegram_bot_token: str | None = None
    telegram_allowed_user_ids: str | None = None

    llm_provider: str = "none"
    llm_api_key: str | None = None
    llm_model: str | None = None

    smith_llm_provider: str | None = None
    smith_llm_model: str | None = None
    smith_allowed_models: str = "gpt-5-mini,gpt-5-nano,gpt-5.5"
    smith_model_change_mode: Literal["runtime"] = "runtime"

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
    def configured_llm_provider(self) -> str:
        return self.smith_llm_provider or self.llm_provider

    @property
    def configured_llm_model(self) -> str | None:
        return self.smith_llm_model or self.llm_model

    @property
    def allowed_models(self) -> list[str]:
        return parse_allowed_models(self.smith_allowed_models)

    @property
    def normalized_llm_provider(self) -> str:
        provider = (
            self.configured_llm_provider.strip().lower()
            if self.configured_llm_provider
            else "none"
        )
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
