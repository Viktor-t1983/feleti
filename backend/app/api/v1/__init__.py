"""API v1: единый роутер, агрегирующий все эндпоинты."""

from fastapi import APIRouter

api_router = APIRouter()

# Подключаем реальные роутеры по мере их появления
from app.api.v1.endpoints import health  # noqa: E402, F401

api_router.include_router(health.router, tags=["system"])
