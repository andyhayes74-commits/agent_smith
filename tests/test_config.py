from smith.config import Settings, parse_telegram_allowed_user_ids


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
