"""Router aggregator."""

from fastapi import APIRouter

from app.routes.evaluate import router as evaluate_router
from app.routes.generate_message import router as generate_message_router
from app.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(evaluate_router, tags=["evaluation"])
api_router.include_router(generate_message_router, tags=["messaging"])
