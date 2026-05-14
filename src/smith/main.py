from fastapi import FastAPI

from smith.api.health import router as health_router
from smith.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Agent Smith",
        description="Custom AI supervisor agent for automation systems.",
        version="0.1.0",
    )

    app.state.settings = settings
    app.include_router(health_router)

    return app


app = create_app()
