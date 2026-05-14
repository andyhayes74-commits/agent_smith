from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SmithSessionType(StrEnum):
    WORKFLOW_EVENT = "workflow_event"
    HUMAN_THREAD = "human_thread"
    MANUAL_QUERY = "manual_query"


class SmithSessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    FAILED = "failed"


class SmithSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_type: SmithSessionType
    status: SmithSessionStatus = SmithSessionStatus.OPEN
    job_id: str | None = None
    workflow_run_id: str | None = None
    trigger_event: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = None


class ContextPacket(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    smith_session_id: UUID
    task: str
    context: dict[str, Any]
    retrieved_context: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
