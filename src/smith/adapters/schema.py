from dataclasses import dataclass, field
from re import Pattern, compile
from typing import Protocol


class InvalidSchemaIdentifierError(ValueError):
    """Raised when a schema table or column identifier is unsafe."""


class SchemaAdapterConfigurationError(RuntimeError):
    """Raised when supervisor queries cannot be safely generated from schema config."""


_IDENTIFIER_PATTERN: Pattern[str] = compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_DANGEROUS_IDENTIFIER_KEYWORDS = {
    "all",
    "alter",
    "and",
    "any",
    "as",
    "call",
    "copy",
    "create",
    "delete",
    "do",
    "drop",
    "execute",
    "from",
    "grant",
    "group",
    "insert",
    "into",
    "join",
    "merge",
    "or",
    "order",
    "revoke",
    "select",
    "table",
    "truncate",
    "union",
    "update",
    "where",
    "with",
}


class SchemaSettings(Protocol):
    smith_schema_profile: str
    smith_jobs_table: str
    smith_errors_table: str
    smith_approvals_table: str
    smith_jobs_id_column: str
    smith_jobs_status_column: str
    smith_jobs_created_at_column: str
    smith_jobs_updated_at_column: str | None
    smith_jobs_title_column: str | None
    smith_jobs_client_id_column: str | None
    smith_jobs_workflow_run_id_column: str | None
    smith_errors_id_column: str
    smith_errors_job_id_column: str | None
    smith_errors_tool_id_column: str | None
    smith_errors_created_at_column: str
    smith_errors_message_column: str
    smith_errors_severity_column: str | None
    smith_errors_raw_payload_column: str | None
    smith_approvals_id_column: str
    smith_approvals_job_id_column: str | None
    smith_approvals_status_column: str
    smith_approvals_approval_type_column: str | None
    smith_approvals_created_at_column: str
    smith_approvals_requested_by_column: str | None


def normalize_optional_identifier(identifier: str | None) -> str | None:
    """Normalize optional identifiers, treating blanks as omitted."""

    if identifier is None:
        return None
    normalized = identifier.strip()
    return normalized or None


def validate_identifier(identifier: str, *, label: str) -> str:
    """Validate a table or column identifier before interpolating it into SQL."""

    normalized = identifier.strip()
    if not _IDENTIFIER_PATTERN.fullmatch(normalized):
        raise InvalidSchemaIdentifierError(
            f"Invalid schema identifier for {label}: "
            "only simple unqualified identifiers are allowed."
        )
    if normalized.lower() in _DANGEROUS_IDENTIFIER_KEYWORDS:
        raise InvalidSchemaIdentifierError(
            f"Invalid schema identifier for {label}: reserved or dangerous SQL keyword."
        )
    return normalized


def validate_optional_identifier(identifier: str | None, *, label: str) -> str | None:
    """Validate an optional identifier when configured."""

    normalized = normalize_optional_identifier(identifier)
    if normalized is None:
        return None
    return validate_identifier(normalized, label=label)


@dataclass(frozen=True, slots=True)
class SupervisorTableMap:
    jobs: str = "jobs"
    errors: str = "errors"
    approvals: str = "approvals"

    def validate(self) -> list[str]:
        warnings: list[str] = []
        for field_name, value in (
            ("jobs table", self.jobs),
            ("errors table", self.errors),
            ("approvals table", self.approvals),
        ):
            try:
                validate_identifier(value, label=field_name)
            except InvalidSchemaIdentifierError as exc:
                warnings.append(str(exc))
        return warnings


@dataclass(frozen=True, slots=True)
class SupervisorJobColumnMap:
    id: str = "id"
    status: str = "status"
    created_at: str = "created_at"
    updated_at: str | None = "updated_at"
    title: str | None = None
    client_id: str | None = None
    workflow_run_id: str | None = None

    def validate(self) -> list[str]:
        return _validate_column_map(
            required={
                "jobs id column": self.id,
                "jobs status column": self.status,
                "jobs created_at column": self.created_at,
            },
            optional={
                "jobs updated_at column": self.updated_at,
                "jobs title column": self.title,
                "jobs client_id column": self.client_id,
                "jobs workflow_run_id column": self.workflow_run_id,
            },
        )


@dataclass(frozen=True, slots=True)
class SupervisorErrorColumnMap:
    id: str = "id"
    job_id: str | None = None
    tool_id: str | None = None
    created_at: str = "created_at"
    message: str = "message"
    severity: str | None = None
    raw_payload: str | None = None

    def validate(self) -> list[str]:
        return _validate_column_map(
            required={
                "errors id column": self.id,
                "errors created_at column": self.created_at,
                "errors message column": self.message,
            },
            optional={
                "errors job_id column": self.job_id,
                "errors tool_id column": self.tool_id,
                "errors severity column": self.severity,
                "errors raw_payload column": self.raw_payload,
            },
        )


@dataclass(frozen=True, slots=True)
class SupervisorApprovalColumnMap:
    id: str = "id"
    job_id: str | None = None
    status: str = "status"
    approval_type: str | None = None
    created_at: str = "created_at"
    requested_by: str | None = None

    def validate(self) -> list[str]:
        return _validate_column_map(
            required={
                "approvals id column": self.id,
                "approvals status column": self.status,
                "approvals created_at column": self.created_at,
            },
            optional={
                "approvals job_id column": self.job_id,
                "approvals approval_type column": self.approval_type,
                "approvals requested_by column": self.requested_by,
            },
        )


@dataclass(frozen=True, slots=True)
class SupervisorSchemaAdapter:
    """Maps Smith supervisor concepts to supervised-system tables and columns."""

    profile: str = "generic"
    tables: SupervisorTableMap = field(default_factory=SupervisorTableMap)
    jobs: SupervisorJobColumnMap = field(default_factory=SupervisorJobColumnMap)
    errors: SupervisorErrorColumnMap = field(default_factory=SupervisorErrorColumnMap)
    approvals: SupervisorApprovalColumnMap = field(default_factory=SupervisorApprovalColumnMap)

    @classmethod
    def from_settings(cls, settings: SchemaSettings) -> "SupervisorSchemaAdapter":
        return cls(
            profile=(settings.smith_schema_profile or "generic").strip() or "generic",
            tables=SupervisorTableMap(
                jobs=settings.smith_jobs_table,
                errors=settings.smith_errors_table,
                approvals=settings.smith_approvals_table,
            ),
            jobs=SupervisorJobColumnMap(
                id=settings.smith_jobs_id_column,
                status=settings.smith_jobs_status_column,
                created_at=settings.smith_jobs_created_at_column,
                updated_at=normalize_optional_identifier(settings.smith_jobs_updated_at_column),
                title=normalize_optional_identifier(settings.smith_jobs_title_column),
                client_id=normalize_optional_identifier(settings.smith_jobs_client_id_column),
                workflow_run_id=normalize_optional_identifier(
                    settings.smith_jobs_workflow_run_id_column
                ),
            ),
            errors=SupervisorErrorColumnMap(
                id=settings.smith_errors_id_column,
                job_id=normalize_optional_identifier(settings.smith_errors_job_id_column),
                tool_id=normalize_optional_identifier(settings.smith_errors_tool_id_column),
                created_at=settings.smith_errors_created_at_column,
                message=settings.smith_errors_message_column,
                severity=normalize_optional_identifier(settings.smith_errors_severity_column),
                raw_payload=normalize_optional_identifier(settings.smith_errors_raw_payload_column),
            ),
            approvals=SupervisorApprovalColumnMap(
                id=settings.smith_approvals_id_column,
                job_id=normalize_optional_identifier(settings.smith_approvals_job_id_column),
                status=settings.smith_approvals_status_column,
                approval_type=normalize_optional_identifier(
                    settings.smith_approvals_approval_type_column
                ),
                created_at=settings.smith_approvals_created_at_column,
                requested_by=normalize_optional_identifier(
                    settings.smith_approvals_requested_by_column
                ),
            ),
        )

    @property
    def supervisor_tables(self) -> dict[str, str]:
        return {
            "jobs": self.tables.jobs,
            "errors": self.tables.errors,
            "approvals": self.tables.approvals,
        }

    @property
    def warnings(self) -> list[str]:
        return self.validate()

    @property
    def is_valid(self) -> bool:
        return not self.warnings

    def validate(self) -> list[str]:
        warnings: list[str] = []
        warnings.extend(_validate_profile(self.profile))
        warnings.extend(self.tables.validate())
        warnings.extend(self.jobs.validate())
        warnings.extend(self.errors.validate())
        warnings.extend(self.approvals.validate())
        return warnings

    def validate_or_raise(self) -> None:
        warnings = self.validate()
        if warnings:
            raise SchemaAdapterConfigurationError("; ".join(warnings))


def _validate_profile(profile: str) -> list[str]:
    try:
        validate_identifier(profile, label="schema profile")
    except InvalidSchemaIdentifierError as exc:
        return [str(exc)]
    return []


def _validate_column_map(
    *,
    required: dict[str, str],
    optional: dict[str, str | None],
) -> list[str]:
    warnings: list[str] = []
    for label, value in required.items():
        try:
            validate_identifier(value, label=label)
        except InvalidSchemaIdentifierError as exc:
            warnings.append(str(exc))
    for label, value in optional.items():
        try:
            validate_optional_identifier(value, label=label)
        except InvalidSchemaIdentifierError as exc:
            warnings.append(str(exc))
    return warnings
