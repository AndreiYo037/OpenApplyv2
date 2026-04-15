"""Route registration module."""

from fastapi import APIRouter

from app.routes.evaluate import router as evaluate_router
from app.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(evaluate_router, tags=["evaluation"])
