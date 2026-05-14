from dataclasses import dataclass


@dataclass(slots=True)
class TelegramConnector:
    """Telegram connector configuration and allowlist helper."""

    bot_token: str | None
    allowed_user_ids: set[str]

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.allowed_user_ids)

    def is_allowed_user(self, user_id: str | int) -> bool:
        return str(user_id) in self.allowed_user_ids
