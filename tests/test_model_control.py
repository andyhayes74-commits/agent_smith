from datetime import UTC, datetime, timedelta

import pytest

from smith.config import Settings
from smith.core.model_control import (
    ModelCommandError,
    ModelRuntimeState,
    TelegramModelCommandService,
)
from smith.policies.permissions import ActionDeniedError

NOW = datetime(2026, 5, 14, 12, 0, tzinfo=UTC)


def _service(
    settings: Settings | None = None,
    state: ModelRuntimeState | None = None,
    *,
    now: datetime = NOW,
) -> tuple[TelegramModelCommandService, ModelRuntimeState]:
    runtime_state = state or ModelRuntimeState()
    service = TelegramModelCommandService(
        settings
        or Settings(
            smith_permission_level=1,
            telegram_allowed_user_ids="123",
            smith_llm_provider="openai",
            smith_llm_model="gpt-5-mini",
            smith_allowed_models="gpt-5-mini,gpt-5-nano,gpt-5.5",
            llm_api_key="test-key",
            _env_file=None,
        ),
        runtime_state,
        now_factory=lambda: now,
        code_factory=lambda: "ABCD",
    )
    return service, runtime_state


def test_model_command_reports_current_model_without_secrets() -> None:
    service, _state = _service()

    response = service.handle(text="/model", user_id=123)

    assert "Provider: openai" in response
    assert "Model: gpt-5-mini" in response
    assert "Source: environment config" in response
    assert "LLM access configured: yes" in response
    assert "test-key" not in response


def test_models_command_lists_allowed_models_and_marks_current() -> None:
    service, _state = _service()

    response = service.handle(text="/models", user_id=123)

    assert "- gpt-5-mini (current; available)" in response
    assert "- gpt-5-nano (available)" in response
    assert "- gpt-5.5 (available)" in response


def test_models_command_marks_current_model_blocked_when_not_allowed() -> None:
    service, _state = _service(
        Settings(
            telegram_allowed_user_ids="123",
            smith_llm_provider="openai",
            smith_llm_model="gpt-4-legacy",
            smith_allowed_models="gpt-5-mini",
            llm_api_key="test-key",
            _env_file=None,
        )
    )

    response = service.handle(text="/models", user_id=123)

    assert "- gpt-4-legacy (current; blocked: not in SMITH_ALLOWED_MODELS)" in response


def test_model_set_requires_permission_level_one() -> None:
    service, _state = _service(
        Settings(
            smith_permission_level=0,
            telegram_allowed_user_ids="123",
            smith_llm_provider="openai",
            smith_llm_model="gpt-5-mini",
            smith_allowed_models="gpt-5-mini,gpt-5-nano",
            llm_api_key="test-key",
            _env_file=None,
        )
    )

    with pytest.raises(ActionDeniedError):
        service.handle(text="/model set gpt-5-nano", user_id=123)


def test_model_set_rejects_unallowed_model() -> None:
    service, _state = _service()

    with pytest.raises(ModelCommandError, match="SMITH_ALLOWED_MODELS"):
        service.handle(text="/model set arbitrary-model", user_id=123)


def test_model_set_creates_pending_change_with_confirmation_code() -> None:
    service, state = _service()

    response = service.handle(text="/model set gpt-5-nano", user_id=123)

    assert "Pending model change to gpt-5-nano" in response
    assert "/model confirm ABCD" in response
    assert state.pending_change is not None
    assert state.pending_change.model_name == "gpt-5-nano"
    assert state.model_override is None


def test_model_confirm_requires_same_allowed_telegram_user() -> None:
    service, _state = _service(
        Settings(
            smith_permission_level=1,
            telegram_allowed_user_ids="123,456",
            smith_llm_provider="openai",
            smith_llm_model="gpt-5-mini",
            smith_allowed_models="gpt-5-mini,gpt-5-nano",
            llm_api_key="test-key",
            _env_file=None,
        )
    )
    service.handle(text="/model set gpt-5-nano", user_id=123)

    with pytest.raises(ModelCommandError, match="requesting Telegram user"):
        service.handle(text="/model confirm ABCD", user_id=456)


def test_model_confirm_applies_runtime_override_and_writes_audit_event() -> None:
    service, state = _service()
    service.handle(text="/model set gpt-5-nano", user_id=123)

    response = service.handle(text="/model confirm ABCD", user_id=123)

    assert response == "Runtime model override applied: gpt-5-nano."
    assert state.model_override == "gpt-5-nano"
    assert state.pending_change is None
    assert state.audit_events[-1].action == "model_override_confirmed"
    assert state.audit_events[-1].user_id == 123
    assert state.audit_events[-1].model_name == "gpt-5-nano"
    assert "Source: runtime override" in service.handle(text="/model", user_id=123)


def test_model_confirm_expires_pending_change() -> None:
    state = ModelRuntimeState()
    service, _state = _service(state=state, now=NOW)
    service.handle(text="/model set gpt-5-nano", user_id=123)
    expired_service, _state = _service(state=state, now=NOW + timedelta(minutes=6))

    with pytest.raises(ModelCommandError, match="expired"):
        expired_service.handle(text="/model confirm ABCD", user_id=123)

    assert state.model_override is None
    assert state.pending_change is None


def test_model_reset_clears_runtime_override_and_writes_audit_event() -> None:
    state = ModelRuntimeState(model_override="gpt-5-nano")
    service, _state = _service(state=state)

    response = service.handle(text="/model reset", user_id=123)

    assert response == "Runtime model override cleared. Active model is now gpt-5-mini."
    assert state.model_override is None
    assert state.audit_events[-1].action == "model_override_reset"
    assert state.audit_events[-1].model_name == "gpt-5-nano"


def test_model_commands_require_allowed_telegram_user() -> None:
    service, _state = _service()

    with pytest.raises(ModelCommandError, match="not allowed"):
        service.handle(text="/model", user_id=999)
