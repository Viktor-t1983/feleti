"""Dashboard stats endpoint."""

from __future__ import annotations

from sqlalchemy import func, select
from app.core.deps import CurrentUser, DBSession
from app.models.batch import Batch
from app.models.chamber import Chamber
from app.models.competitor import Competitor
from app.models.ingredient import Ingredient
from app.models.product import Product
from app.models.recipe import Recipe
from app.models.user import User
from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(
    db: DBSession,
    _user: CurrentUser,
) -> dict:
    """Aggregated stats for the dashboard."""
    chambers_total = await db.scalar(select(func.count()).select_from(Chamber))
    recipes_total = await db.scalar(select(func.count()).select_from(Recipe))
    batches_total = await db.scalar(select(func.count()).select_from(Batch))
    batches_active = await db.scalar(
        select(func.count()).select_from(Batch).where(Batch.status == "running")
    )
    products_total = await db.scalar(select(func.count()).select_from(Product))
    ingredients_total = await db.scalar(select(func.count()).select_from(Ingredient))
    users_total = await db.scalar(select(func.count()).select_from(User))
    competitors_total = await db.scalar(select(func.count()).select_from(Competitor))

    # Recent chambers (last 6)
    chambers_result = await db.scalars(
        select(Chamber).order_by(Chamber.id.asc()).limit(6)
    )
    chambers = [
        {
            "id": c.id,
            "model": c.model,
            "manufacturer": c.manufacturer.name if c.manufacturer else None,
            "status": "idle",
            "max_load_kg": c.max_load_kg,
            "type": c.type.value if c.type else None,
        }
        for c in chambers_result.all()
    ]

    # Batch status distribution
    batch_statuses = {}
    for status in ["planned", "queued", "running", "paused", "completed", "cancelled", "failed"]:
        count = await db.scalar(
            select(func.count()).select_from(Batch).where(Batch.status == status)
        )
        batch_statuses[status] = count or 0

    return {
        "counts": {
            "chambers": chambers_total or 0,
            "recipes": recipes_total or 0,
            "batches": batches_total or 0,
            "batches_active": batches_active or 0,
            "products": products_total or 0,
            "ingredients": ingredients_total or 0,
            "users": users_total or 0,
            "competitors": competitors_total or 0,
        },
        "chambers": chambers,
        "batch_statuses": batch_statuses,
    }
