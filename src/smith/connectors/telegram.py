from collections.abc import Iterable
from dataclasses import dataclass, field

from smith.config import parse_telegram_allowed_user_ids


@dataclass(slots=True)
class TelegramConnector:
    """Telegram connector configuration and allowlist helper.

    Smith v1 does not poll Telegram or send messages yet. This helper only inspects
    configuration and enforces the configured operator allowlist.
    """

    bot_token: str | None
    allowed_user_ids: Iterable[int | str] | str | None = field(default_factory=set)

    @property
    def parsed_allowed_user_ids(self) -> set[int]:
        if isinstance(self.allowed_user_ids, str) or self.allowed_user_ids is None:
            return parse_telegram_allowed_user_ids(self.allowed_user_ids)

        parsed_user_ids: set[int] = set()
        for raw_user_id in self.allowed_user_ids:
            try:
                parsed_user_ids.add(int(raw_user_id))
            except (TypeError, ValueError):
                continue
        return parsed_user_ids

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.bot_token.strip() and self.parsed_allowed_user_ids)

    def is_allowed_user(self, user_id: str | int) -> bool:
        try:
            parsed_user_id = int(user_id)
        except (TypeError, ValueError):
            return False
        return parsed_user_id in self.parsed_allowed_user_ids
