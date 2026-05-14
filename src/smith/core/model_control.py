from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from secrets import token_hex

from smith.config import Settings
from smith.connectors.telegram import TelegramConnector
from smith.policies.permissions import PermissionLevel, require_permission

MODEL_CHANGE_EXPIRY = timedelta(minutes=5)


class ModelCommandError(RuntimeError):
    """Raised when a Telegram model command cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class PendingModelChange:
    model_name: str
    requested_by_user_id: int
    confirmation_code: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ModelAuditEvent:
    action: str
    user_id: int
    model_name: str | None
    created_at: datetime


@dataclass(slots=True)
class ModelRuntimeState:
    """In-memory runtime state for Smith v1 model overrides.

    This state is intentionally process-local. Smith v1 never rewrites .env and does
    not persist model changes to the supervised Postgres database.
    """

    model_override: str | None = None
    pending_change: PendingModelChange | None = None
    audit_events: list[ModelAuditEvent] = field(default_factory=list)

    def active_model(self, settings: Settings) -> str | None:
        return self.model_override or settings.configured_llm_model

    def model_source(self) -> str:
        if self.model_override:
            return "runtime override"
        return "environment config"

    def request_change(
        self,
        *,
        model_name: str,
        user_id: int,
        now: datetime,
        code: str,
    ) -> PendingModelChange:
        self.pending_change = PendingModelChange(
            model_name=model_name,
            requested_by_user_id=user_id,
            confirmation_code=code,
            expires_at=now + MODEL_CHANGE_EXPIRY,
        )
        return self.pending_change

    def confirm_change(self, *, code: str, user_id: int, now: datetime) -> str:
        pending_change = self.pending_change
        if pending_change is None:
            raise ModelCommandError("No model change is pending.")
        if pending_change.requested_by_user_id != user_id:
            raise ModelCommandError("Only the requesting Telegram user can confirm this change.")
        if pending_change.expires_at < now:
            self.pending_change = None
            raise ModelCommandError("Pending model change has expired.")
        if pending_change.confirmation_code != code:
            raise ModelCommandError("Invalid confirmation code.")

        self.model_override = pending_change.model_name
        self.pending_change = None
        self.audit_events.append(
            ModelAuditEvent(
                action="model_override_confirmed",
                user_id=user_id,
                model_name=self.model_override,
                created_at=now,
            )
        )
        return self.model_override

    def reset_override(self, *, user_id: int, now: datetime) -> None:
        previous_model = self.model_override
        self.model_override = None
        self.pending_change = None
        self.audit_events.append(
            ModelAuditEvent(
                action="model_override_reset",
                user_id=user_id,
                model_name=previous_model,
                created_at=now,
            )
        )


class TelegramModelCommandService:
    """Handles Telegram model-control commands without exposing secrets."""

    def __init__(
        self,
        settings: Settings,
        runtime_state: ModelRuntimeState,
        *,
        now_factory: Callable[[], datetime] | None = None,
        code_factory: Callable[[], str] | None = None,
    ) -> None:
        self.settings = settings
        self.runtime_state = runtime_state
        self.now_factory = now_factory or (lambda: datetime.now(UTC))
        self.code_factory = code_factory or (lambda: token_hex(2).upper())

    def handle(self, *, text: str, user_id: int | str) -> str:
        parsed_user_id = self._require_allowed_user(user_id)
        command_parts = text.strip().split()
        if not command_parts:
            raise ModelCommandError("Empty Telegram command.")

        command = command_parts[0]
        if command == "/models" and len(command_parts) == 1:
            return self._models_response()
        if command != "/model":
            raise ModelCommandError("Unsupported model command.")
        if len(command_parts) == 1:
            return self._model_response()

        subcommand = command_parts[1]
        if subcommand == "set" and len(command_parts) == 3:
            return self._request_model_change(command_parts[2], parsed_user_id)
        if subcommand == "confirm" and len(command_parts) == 3:
            return self._confirm_model_change(command_parts[2], parsed_user_id)
        if subcommand == "reset" and len(command_parts) == 2:
            return self._reset_model(parsed_user_id)

        raise ModelCommandError("Unsupported /model syntax.")

    def _model_response(self) -> str:
        active_model = self.runtime_state.active_model(self.settings) or "not configured"
        return "\n".join(
            [
                "Smith model status",
                f"Provider: {self.settings.normalized_llm_provider}",
                f"Model: {active_model}",
                f"Source: {self.runtime_state.model_source()}",
                f"LLM access configured: {_yes_no(self.settings.llm_configured)}",
            ]
        )

    def _models_response(self) -> str:
        active_model = self.runtime_state.active_model(self.settings)
        allowed_models = self.settings.allowed_models
        lines = ["Smith allowed models"]
        if not allowed_models:
            lines.append("No models are configured in SMITH_ALLOWED_MODELS.")
        for model_name in allowed_models:
            markers: list[str] = []
            if model_name == active_model:
                markers.append("current")
            if not self.settings.llm_configured:
                markers.append("unavailable: LLM access not configured")
            else:
                markers.append("available")
            lines.append(f"- {model_name} ({'; '.join(markers)})")
        if active_model and active_model not in allowed_models:
            lines.append(f"- {active_model} (current; blocked: not in SMITH_ALLOWED_MODELS)")
        return "\n".join(lines)

    def _request_model_change(self, model_name: str, user_id: int) -> str:
        self._require_model_change_permission()
        if model_name not in self.settings.allowed_models:
            raise ModelCommandError("Requested model is not in SMITH_ALLOWED_MODELS.")
        pending_change = self.runtime_state.request_change(
            model_name=model_name,
            user_id=user_id,
            now=self.now_factory(),
            code=self.code_factory(),
        )
        return (
            f"Pending model change to {model_name}. "
            f"Confirm within 5 minutes with /model confirm {pending_change.confirmation_code}."
        )

    def _confirm_model_change(self, code: str, user_id: int) -> str:
        self._require_model_change_permission()
        model_name = self.runtime_state.confirm_change(
            code=code,
            user_id=user_id,
            now=self.now_factory(),
        )
        return f"Runtime model override applied: {model_name}."

    def _reset_model(self, user_id: int) -> str:
        self._require_model_change_permission()
        self.runtime_state.reset_override(user_id=user_id, now=self.now_factory())
        fallback_model = self.settings.configured_llm_model or "not configured"
        return f"Runtime model override cleared. Active model is now {fallback_model}."

    def _require_allowed_user(self, user_id: int | str) -> int:
        connector = TelegramConnector(
            bot_token=self.settings.telegram_bot_token,
            allowed_user_ids=self.settings.telegram_allowed_user_id_set,
        )
        if not connector.is_allowed_user(user_id):
            raise ModelCommandError("Telegram user is not allowed to control Smith models.")
        return int(user_id)

    def _require_model_change_permission(self) -> None:
        require_permission(
            self.settings.smith_permission_level,
            PermissionLevel.OPERATOR_ASSISTANT,
            "change_runtime_model",
        )


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
