"""API v1: единый роутер, агрегирующий все эндпоинты."""

from fastapi import APIRouter

api_router = APIRouter()

# Подключаем все эндпоинты
from app.api.v1.endpoints import (  # noqa: E402, F401
    auth,
    brines,
    chambers,
    health,
    ingredients,
    manufacturers,
    products,
    recipes,
)

api_router.include_router(health.router, tags=["system"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(manufacturers.router, prefix="/manufacturers", tags=["manufacturers"])
api_router.include_router(chambers.router, prefix="/chambers", tags=["chambers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])
api_router.include_router(brines.router, prefix="/brines", tags=["brines"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
