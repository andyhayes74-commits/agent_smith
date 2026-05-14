from smith.config import Settings, parse_allowed_models, parse_telegram_allowed_user_ids


def test_default_config_is_safe() -> None:
    settings = Settings(_env_file=None)

    assert settings.smith_permission_level == 0
    assert settings.is_read_only is True
    assert settings.postgres_configured is False
    assert settings.n8n_configured is False
    assert settings.telegram_configured is False
    assert settings.normalized_llm_provider == "none"
    assert settings.llm_configured is False


def test_telegram_allowlist_parsing_works() -> None:
    assert parse_telegram_allowed_user_ids("123, 456,,not-a-number,123") == {123, 456}


def test_settings_telegram_allowlist_parsing_works() -> None:
    settings = Settings(telegram_allowed_user_ids="123, 456", _env_file=None)

    assert settings.telegram_allowed_user_id_set == {123, 456}


def test_allowed_models_parsing_preserves_order_and_removes_duplicates() -> None:
    assert parse_allowed_models("gpt-5-mini, gpt-5-nano,,gpt-5-mini,gpt-5.5") == [
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-5.5",
    ]


def test_smith_llm_config_overrides_legacy_llm_names() -> None:
    settings = Settings(
        llm_provider="none",
        llm_model="legacy-model",
        smith_llm_provider="openai",
        smith_llm_model="gpt-5-mini",
        smith_allowed_models="gpt-5-mini,gpt-5-nano",
        _env_file=None,
    )

    assert settings.normalized_llm_provider == "openai"
    assert settings.configured_llm_model == "gpt-5-mini"
    assert settings.allowed_models == ["gpt-5-mini", "gpt-5-nano"]
