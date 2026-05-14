from dataclasses import dataclass


@dataclass(slots=True)
class N8nConnector:
    """n8n connector interface for Smith.

    Smith v1 should use read-only inspection first. Action methods should be added only
    after permission checks and audit logging exist.
    """

    base_url: str | None
    api_key: str | None

    def is_configured(self) -> bool:
        return bool(
            self.base_url and self.base_url.strip() and self.api_key and self.api_key.strip()
        )
