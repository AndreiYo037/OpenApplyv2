"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenApply Decision Engine API",
        version="0.1.0",
        description="Backend API for job decision engine orchestration.",
    )
    app.include_router(api_router)
    return app


app = create_app()
