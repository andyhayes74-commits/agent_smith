import pytest

from smith.adapters.schema import (
    InvalidSchemaIdentifierError,
    SupervisorSchemaAdapter,
    validate_identifier,
)
from smith.config import Settings


def test_default_generic_schema_mapping_is_valid() -> None:
    adapter = SupervisorSchemaAdapter.from_settings(Settings(_env_file=None))

    assert adapter.profile == "generic"
    assert adapter.is_valid is True
    assert adapter.warnings == []
    assert adapter.supervisor_tables == {
        "jobs": "jobs",
        "errors": "errors",
        "approvals": "approvals",
    }
    assert adapter.jobs.id == "id"
    assert adapter.jobs.status == "status"
    assert adapter.errors.message == "message"
    assert adapter.approvals.status == "status"


def test_custom_table_names_from_settings_are_mapped() -> None:
    settings = Settings(
        smith_jobs_table="workflow_jobs",
        smith_errors_table="workflow_errors",
        smith_approvals_table="human_reviews",
        _env_file=None,
    )

    adapter = SupervisorSchemaAdapter.from_settings(settings)

    assert adapter.supervisor_tables == {
        "jobs": "workflow_jobs",
        "errors": "workflow_errors",
        "approvals": "human_reviews",
    }
    assert adapter.is_valid is True


def test_optional_blank_columns_are_allowed_and_omitted() -> None:
    settings = Settings(
        smith_jobs_updated_at_column=" ",
        smith_jobs_title_column="",
        smith_errors_job_id_column="",
        smith_approvals_requested_by_column=" ",
        _env_file=None,
    )

    adapter = SupervisorSchemaAdapter.from_settings(settings)

    assert adapter.jobs.updated_at is None
    assert adapter.jobs.title is None
    assert adapter.errors.job_id is None
    assert adapter.approvals.requested_by is None
    assert adapter.is_valid is True


@pytest.mark.parametrize(
    "identifier",
    [
        "bad table",
        "jobs;drop",
        "jobs.id",
        '"jobs"',
        "jobs--comment",
        "jobs/*comment*/",
        "jobs[0]",
        "lower(jobs)",
        "select",
        "update",
    ],
)
def test_dangerous_identifiers_are_rejected(identifier: str) -> None:
    with pytest.raises(InvalidSchemaIdentifierError):
        validate_identifier(identifier, label="test identifier")


def test_invalid_table_names_are_reported_without_raising_from_status_adapter() -> None:
    adapter = SupervisorSchemaAdapter.from_settings(
        Settings(smith_jobs_table="jobs; DROP TABLE jobs", _env_file=None)
    )

    assert adapter.is_valid is False
    assert "jobs table" in adapter.warnings[0]


def test_invalid_column_names_are_reported_without_raising_from_status_adapter() -> None:
    adapter = SupervisorSchemaAdapter.from_settings(
        Settings(smith_errors_message_column="message || secret", _env_file=None)
    )

    assert adapter.is_valid is False
    assert "errors message column" in adapter.warnings[0]
