"""Seed recipes and batches for dashboard demo."""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.models.chamber import Chamber
from app.models.product import Product
from app.models.recipe import Recipe, RecipeStatus, RecipeVersion
from app.models.batch import Batch, BatchStatus
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def seed_recipes(session) -> list[Recipe]:
    products = (await session.scalars(select(Product))).all()
    by_slug = {p.slug: p for p in products}
    user = await session.scalar(select(User).where(User.username == "admin"))
    user_id = user.id if user else None

    recipes_data = [
        {
            "slug": "doktorskaya-gk-v1",
            "name": "Докторская ГК — классическая",
            "product_slug": "doktorskaya",
            "description": "Классический рецепт докторской колбасы с горячим копчением.",
            "tags": ["колбаса", "ГК", "классика"],
            "version": {
                "version_number": 1,
                "program": [
                    {"phase": "drying", "temp": 60, "time_min": 30, "humidity": 0},
                    {"phase": "smoking", "temp": 80, "time_min": 45, "humidity": 40},
                    {"phase": "cooking", "temp": 82, "time_min": 60, "humidity": 100},
                    {"phase": "shower", "temp": 15, "time_min": 10, "humidity": 0},
                ],
                "yield_percent": 92.0,
                "losses_percent": 8.0,
                "notes": "Температура внутри продукта должна достичь 72°C.",
                "gost": "ГОСТ Р 52196-2011",
            },
        },
        {
            "slug": "skumbriya-gk-v1",
            "name": "Скумбрия ГК — быстрая",
            "product_slug": "skumbria-gk",
            "description": "Быстрый рецепт горячего копчения скумбрии.",
            "tags": ["рыба", "ГК", "быстрый"],
            "version": {
                "version_number": 1,
                "program": [
                    {"phase": "drying", "temp": 50, "time_min": 20, "humidity": 0},
                    {"phase": "smoking", "temp": 70, "time_min": 30, "humidity": 30},
                    {"phase": "cooking", "temp": 75, "time_min": 20, "humidity": 80},
                ],
                "yield_percent": 85.0,
                "losses_percent": 15.0,
                "notes": "Не пересушивать — рыба должна оставаться сочной.",
            },
        },
        {
            "slug": "semga-hk-v1",
            "name": "Сёмга ХК — элитная",
            "product_slug": "semga-hk",
            "description": "Холодное копчение сёмги с длительным посолом.",
            "tags": ["рыба", "ХК", "премиум"],
            "version": {
                "version_number": 1,
                "program": [
                    {"phase": "salting", "temp": 4, "time_min": 1440, "humidity": 80},
                    {"phase": "drying", "temp": 18, "time_min": 120, "humidity": 60},
                    {"phase": "smoking", "temp": 22, "time_min": 720, "humidity": 75},
                ],
                "yield_percent": 78.0,
                "losses_percent": 22.0,
                "notes": "Температура дыма не выше 25°C.",
            },
        },
    ]

    result: list[Recipe] = []
    for item in recipes_data:
        existing = await session.scalar(
            select(Recipe).where(Recipe.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue

        product = by_slug.get(item["product_slug"])
        if not product:
            logger.warning("Product %s not found, skipping recipe", item["product_slug"])
            continue

        recipe = Recipe(
            product_id=product.id,
            name=item["name"],
            slug=item["slug"],
            status=RecipeStatus.APPROVED,
            description=item["description"],
            tags=item["tags"],
            created_by_id=user_id,
        )
        session.add(recipe)
        await session.flush()

        ver_data = item["version"]
        version = RecipeVersion(
            recipe_id=recipe.id,
            version_number=ver_data["version_number"],
            program=ver_data["program"],
            yield_percent=ver_data.get("yield_percent"),
            losses_percent=ver_data.get("losses_percent"),
            notes=ver_data.get("notes"),
            gost=ver_data.get("gost"),
            status=RecipeStatus.APPROVED,
            created_by_id=user_id,
            verified=True,
            verified_by_id=user_id,
            verified_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(version)
        await session.flush()

        recipe.current_version_id = version.id
        result.append(recipe)

    await session.flush()
    logger.info("Recipes: %s", len(result))
    return result


async def seed_batches(session) -> list[Batch]:
    chambers = (await session.scalars(select(Chamber))).all()
    recipes = (await session.scalars(select(Recipe))).all()
    user = await session.scalar(select(User).where(User.username == "admin"))
    user_id = user.id if user else None

    if not chambers or not recipes:
        logger.info("No chambers or recipes, skipping batches")
        return []

    batches_data = [
        {
            "batch_number": "B-2026-001",
            "recipe_idx": 0,
            "chamber_idx": 0,
            "status": BatchStatus.COMPLETED,
            "product_weight_kg": 80.0,
            "yield_kg": 73.5,
            "losses_percent": 8.1,
        },
        {
            "batch_number": "B-2026-002",
            "recipe_idx": 1,
            "chamber_idx": 1,
            "status": BatchStatus.RUNNING,
            "product_weight_kg": 45.0,
        },
        {
            "batch_number": "B-2026-003",
            "recipe_idx": 2,
            "chamber_idx": 2,
            "status": BatchStatus.PLANNED,
            "product_weight_kg": 120.0,
        },
    ]

    result: list[Batch] = []
    for item in batches_data:
        existing = await session.scalar(
            select(Batch).where(Batch.batch_number == item["batch_number"])
        )
        if existing:
            result.append(existing)
            continue

        recipe = recipes[item["recipe_idx"]]
        chamber = chambers[item["chamber_idx"]]

        batch = Batch(
            recipe_version_id=recipe.current_version_id,
            chamber_id=chamber.id,
            operator_id=user_id,
            batch_number=item["batch_number"],
            status=item["status"],
            product_weight_kg=item.get("product_weight_kg"),
            yield_kg=item.get("yield_kg"),
            losses_percent=item.get("losses_percent"),
        )
        session.add(batch)
        result.append(batch)

    await session.flush()
    logger.info("Batches: %s", len(result))
    return result


async def main():
    async with AsyncSessionLocal() as session:
        try:
            recipes = await seed_recipes(session)
            batches = await seed_batches(session)
            await session.commit()
            logger.info("=== Recipes & batches seed committed ===")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed")
            raise
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
