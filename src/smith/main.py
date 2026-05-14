from fastapi import FastAPI

from smith.api.health import router as health_router
from smith.api.status import router as status_router
from smith.api.supervisor import router as supervisor_router
from smith.config import get_settings
from smith.core.model_control import ModelRuntimeState


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agent Smith",
        description="Custom AI supervisor agent for automation systems.",
        version="0.1.0",
    )

    app.state.settings = settings
    app.state.model_runtime_state = ModelRuntimeState()
    app.include_router(health_router)
    app.include_router(status_router)
    app.include_router(supervisor_router)

    return app


app = create_app()
