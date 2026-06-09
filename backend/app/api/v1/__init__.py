"""API v1: единый роутер, агрегирующий все эндпоинты."""

from fastapi import APIRouter

api_router = APIRouter()

# Подключаем все эндпоинты
from app.api.v1.endpoints import (  # noqa: E402, F401
    ai,
    auth,
    batches,
    brines,
    chambers,
    competitors,
    dashboard,
    health,
    ingredients,
    knowledge,
    manufacturers,
    pipeline,
    products,
    recipes,
    telemetry,
    telegram,
    users,
)

api_router.include_router(health.router, tags=["system"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(manufacturers.router, prefix="/manufacturers", tags=["manufacturers"])
api_router.include_router(chambers.router, prefix="/chambers", tags=["chambers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])
api_router.include_router(brines.router, prefix="/brines", tags=["brines"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(batches.router, prefix="/batches", tags=["batches"])
api_router.include_router(telemetry.router, prefix="/chambers", tags=["telemetry"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(competitors.router, prefix="/competitors", tags=["competitors"])
api_router.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
