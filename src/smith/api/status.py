from fastapi import APIRouter

from smith.config import get_settings
from smith.core.status import SmithStatus, StatusService

router = APIRouter(tags=["status"])


@router.get("/status", response_model=SmithStatus)
def status() -> SmithStatus:
    settings = get_settings()
    return StatusService(settings).build_status()
