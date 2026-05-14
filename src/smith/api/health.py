from fastapi import APIRouter
from pydantic import BaseModel

from smith.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    permission_level: int
    read_only: bool


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.smith_service_name,
        environment=settings.smith_env,
        permission_level=settings.smith_permission_level,
        read_only=settings.is_read_only,
    )
