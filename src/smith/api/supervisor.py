from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from smith.adapters.schema import SchemaAdapterConfigurationError, SupervisorSchemaAdapter
from smith.config import get_settings
from smith.connectors.postgres import PostgresConnector, PostgresUnavailableError
from smith.core.supervisor import SupervisorListResponse, SupervisorReadService

router = APIRouter(tags=["supervisor"])

EndpointHandler = Callable[..., Awaitable[SupervisorListResponse]]
LimitQuery = Annotated[int, Query(ge=1, le=200)]
StaleMinutesQuery = Annotated[int, Query(ge=1, le=10080)]


def get_supervisor_read_service() -> SupervisorReadService:
    settings = get_settings()
    return SupervisorReadService(
        PostgresConnector(database_url=settings.database_url),
        SupervisorSchemaAdapter.from_settings(settings),
    )


SupervisorServiceDependency = Annotated[
    SupervisorReadService,
    Depends(get_supervisor_read_service),
]


async def _run_supervisor_read(
    handler: EndpointHandler,
    **kwargs: object,
) -> SupervisorListResponse:
    try:
        return await handler(**kwargs)
    except PostgresUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "postgres_unavailable",
                "message": str(exc),
            },
        ) from exc
    except SchemaAdapterConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "schema_adapter_invalid",
                "message": str(exc),
            },
        ) from exc


@router.get("/jobs", response_model=SupervisorListResponse)
async def jobs(
    service: SupervisorServiceDependency,
    limit: LimitQuery = 50,
) -> SupervisorListResponse:
    return await _run_supervisor_read(service.list_jobs, limit=limit)


@router.get("/jobs/active", response_model=SupervisorListResponse)
async def active_jobs(
    service: SupervisorServiceDependency,
    limit: LimitQuery = 50,
) -> SupervisorListResponse:
    return await _run_supervisor_read(service.list_active_jobs, limit=limit)


@router.get("/jobs/stuck", response_model=SupervisorListResponse)
async def stuck_jobs(
    service: SupervisorServiceDependency,
    limit: LimitQuery = 50,
    stale_minutes: StaleMinutesQuery = 30,
) -> SupervisorListResponse:
    return await _run_supervisor_read(
        service.list_stuck_jobs,
        limit=limit,
        stale_minutes=stale_minutes,
    )


@router.get("/errors/recent", response_model=SupervisorListResponse)
async def recent_errors(
    service: SupervisorServiceDependency,
    limit: LimitQuery = 50,
) -> SupervisorListResponse:
    return await _run_supervisor_read(service.list_recent_errors, limit=limit)


@router.get("/approvals/pending", response_model=SupervisorListResponse)
async def pending_approvals(
    service: SupervisorServiceDependency,
    limit: LimitQuery = 50,
) -> SupervisorListResponse:
    return await _run_supervisor_read(service.list_pending_approvals, limit=limit)
