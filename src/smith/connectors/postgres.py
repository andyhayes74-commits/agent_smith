from dataclasses import dataclass
from typing import Any

import asyncpg


class PostgresUnavailableError(RuntimeError):
    """Raised when Postgres cannot serve a supervisor read request."""


class UnsafeReadOnlyQueryError(ValueError):
    """Raised when a connector caller attempts a non-read-only query."""


_READ_ONLY_QUERY_PREFIXES = ("select", "with")
_MUTATING_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "merge",
    "create",
    "alter",
    "drop",
    "truncate",
    "grant",
    "revoke",
    "copy",
    "call",
    "do",
    "execute",
)


@dataclass(slots=True)
class PostgresConnector:
    """Read-only Postgres connector interface for Smith v1."""

    database_url: str | None
    command_timeout_seconds: float = 10.0

    def is_configured(self) -> bool:
        return bool(self.database_url and self.database_url.strip())

    async def fetch(self, query: str, *args: object) -> list[dict[str, Any]]:
        """Run a guarded read-only query and return rows as dictionaries."""

        if not self.is_configured():
            raise PostgresUnavailableError("Postgres is not configured for Agent Smith.")

        self._validate_read_only_query(query)

        connection: asyncpg.Connection | None = None
        try:
            connection = await asyncpg.connect(
                self.database_url,
                command_timeout=self.command_timeout_seconds,
            )
            async with connection.transaction(readonly=True):
                records = await connection.fetch(query, *args)
        except (
            asyncpg.ClientConfigurationError,
            asyncpg.InterfaceError,
            asyncpg.PostgresError,
            OSError,
            ValueError,
        ) as exc:
            raise PostgresUnavailableError("Postgres is unavailable or misconfigured.") from exc
        finally:
            if connection is not None:
                await connection.close()

        return [dict(record) for record in records]

    def _validate_read_only_query(self, query: str) -> None:
        normalized = " ".join(query.strip().lower().split())
        if not normalized.startswith(_READ_ONLY_QUERY_PREFIXES):
            raise UnsafeReadOnlyQueryError("Postgres connector only allows SELECT/CTE reads.")

        padded = f" {normalized} "
        for keyword in _MUTATING_KEYWORDS:
            if f" {keyword} " in padded:
                raise UnsafeReadOnlyQueryError(
                    f"Postgres connector blocked non-read-only keyword: {keyword}."
                )
