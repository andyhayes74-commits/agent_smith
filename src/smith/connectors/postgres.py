from dataclasses import dataclass


@dataclass(slots=True)
class PostgresConnector:
    """Read-only Postgres connector interface for Smith v1.

    This class intentionally starts small. Real query methods should be added alongside
    migrations and integration tests when Smith is connected to a live system schema.
    """

    database_url: str | None

    def is_configured(self) -> bool:
        return bool(self.database_url)
