"""Health-check эндпоинт."""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.get("/health", summary="Проверка работоспособности")
async def healthcheck() -> dict:
    return {
        "status": "ok",
        "service": "feleti-smok-backend",
        "version": "0.1.0",
    }


@router.get("/health/db", summary="Проверка соединения с PostgreSQL")
async def healthcheck_db() -> dict:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar_one()
        return {"status": "ok", "db": "ok", "check": value}
    except Exception as exc:
        return {"status": "degraded", "db": "error", "error": str(exc)}
