"""Сид-данные: производители, камеры, рецепты, ингредиенты.

Запуск: `python -m app.scripts.seed`
Идемпотентен — повторный запуск не дублирует (по slug).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base  # noqa: F401 — регистрация моделей в metadata
from app.db.session import AsyncSessionLocal, engine
from app.models.chamber import Chamber, ChamberType
from app.models.ingredient import Ingredient, IngredientType
from app.models.manufacturer import Manufacturer
from app.models.product import Product, ProductCategory
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def seed_manufacturers(session) -> list[Manufacturer]:
    data = [
        {"slug": "feleti", "name": "FELETI", "country": "Беларусь", "city": "Брест",
         "website": "https://feleti.by", "founded_year": 2008,
         "description": "FELETI (Брест) — производитель коптильного оборудования. Собственная линейка FELETI-SMOK.",
         "is_our_brand": True, "is_competitor": False, "sort_order": 0},
        {"slug": "ijiza", "name": "Ижица / Varmen", "country": "Россия", "city": "Санкт-Петербург",
         "website": "https://ijiza.ru", "founded_year": 1995,
         "description": "Ижица — российский производитель коптильно-варочного оборудования (Horeca, Profi, Industrial). Контроллер Varmen-1.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 10},
        {"slug": "mauting", "name": "Mauting", "country": "Чехия", "city": "Valašské Meziříčí",
         "website": "https://mauting.com", "founded_year": 1933,
         "description": "Mauting — чешский производитель туннельных и камерных коптилен, лидер сегмента Industrial.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 20},
        {"slug": "fessmann", "name": "Fessmann", "country": "Германия", "city": "Murr",
         "website": "https://fessmann.com", "founded_year": 1900,
         "description": "Fessmann — премиум-сегмент коптильного оборудования. Turbomat, FOOD.CON 2, FES.APP.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 30},
        {"slug": "kerres", "name": "Kerres Anlagensysteme", "country": "Германия", "city": "Backnang",
         "website": "https://kerres.de", "founded_year": 1960,
         "description": "Kerres — модульные коптильные системы. Технологии Jet Smoke, Hybrid Airflow.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 40},
        {"slug": "agros", "name": "AGROS GROUP", "country": "Россия", "city": "Москва",
         "website": "https://agrosgroup.ru", "founded_year": 1991,
         "description": "AGROS — российский интегратор коптильного оборудования (представитель нескольких производителей).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 50},
        {"slug": "reich", "name": "Reich Thermoprozesstechnik", "country": "Германия",
         "website": "https://reich-gmbh.de", "founded_year": 1923,
         "description": "Reich — термо-процесс техника: копчение, обжарка, варка. Серия MULTIMAT, INJECTA.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 60},
    ]

    result: list[Manufacturer] = []
    for item in data:
        existing = await session.scalar(
            select(Manufacturer).where(Manufacturer.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Manufacturer(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_chambers(session, manufacturers: list[Manufacturer]) -> list[Chamber]:
    by_slug = {m.slug: m for m in manufacturers}
    data: list[dict[str, Any]] = [
        # FELETI-SMOK собственная линейка
        {"manufacturer": "feleti", "model": "Profi H-100", "slug": "feleti-profih-100",
         "type": ChamberType.HOT, "max_load_kg": 100, "volume_m3": 1.2, "power_kw": 12,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": False,
         "driver_class": "FELETI_SMOKDriver", "description": "FELETI-SMOK Profi H-100 — горячее копчение, 100 кг загрузки."},
        {"manufacturer": "feleti", "model": "Profi H-200", "slug": "feleti-profih-200",
         "type": ChamberType.HOT, "max_load_kg": 200, "volume_m3": 2.4, "power_kw": 18,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": False,
         "driver_class": "FELETI_SMOKDriver", "description": "FELETI-SMOK Profi H-200 — горячее копчение, 200 кг."},
        {"manufacturer": "feleti", "model": "Profi C-200", "slug": "feleti-profic-200",
         "type": ChamberType.COLD, "max_load_kg": 200, "volume_m3": 2.4, "power_kw": 6,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": True,
         "supports_cooling": True, "driver_class": "FELETI_SMOKDriver",
         "description": "FELETI-SMOK Profi C-200 — холодное копчение + охлаждение, 200 кг."},
        {"manufacturer": "feleti", "model": "Profi U-250", "slug": "feleti-profiu-250",
         "type": ChamberType.UNIVERSAL, "max_load_kg": 250, "volume_m3": 3.0, "power_kw": 24,
         "voltage_v": 380, "supports_electro": True, "supports_cold_smoke": True,
         "supports_cooling": True, "supports_joint": True,
         "driver_class": "FELETI_SMOKDriver",
         "description": "FELETI-SMOK Profi U-250 — универсал: горячее + холодное + электро + охлаждение."},
        # Ижица
        {"manufacturer": "ijiza", "model": "Ижица 1200М4", "slug": "ijiza-1200m4",
         "type": ChamberType.ELECTRO, "max_load_kg": 120, "volume_m3": 1.4, "power_kw": 14,
         "voltage_v": 380, "supports_electro": True,
         "driver_class": "VarmenDriver",
         "description": "Ижица 1200М4 — электростатическое копчение, контроллер Varmen-1."},
        {"manufacturer": "ijiza", "model": "Ижица UTR-C 250", "slug": "ijiza-utr-c-250",
         "type": ChamberType.COLD, "max_load_kg": 250, "volume_m3": 3.0, "power_kw": 7,
         "voltage_v": 380, "supports_cold_smoke": True, "supports_cooling": True,
         "driver_class": "VarmenDriver",
         "description": "Ижица UTR-C 250 — холодное копчение + охлаждение готовой продукции."},
    ]
    result: list[Chamber] = []
    for item in data:
        existing = await session.scalar(
            select(Chamber).where(Chamber.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        manuf_slug = item.pop("manufacturer")
        manuf = by_slug.get(manuf_slug)
        if not manuf:
            continue
        obj = Chamber(manufacturer_id=manuf.id, **item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_ingredients(session) -> list[Ingredient]:
    data = [
        {"slug": "govyadina-zhel", "name": "Говядина жилованная", "type": IngredientType.MEAT,
         "protein_per_100g": 19.0, "fat_per_100g": 12.0, "kcal_per_100g": 187, "price_per_kg": 850},
        {"slug": "svinina-poluzhirn", "name": "Свинина полужирная", "type": IngredientType.MEAT,
         "protein_per_100g": 16.0, "fat_per_100g": 27.0, "kcal_per_100g": 305, "price_per_kg": 650},
        {"slug": "sheel-olkha", "name": "Щепа ольхи", "type": IngredientType.WOOD,
         "wood_species": "ольха", "wood_form": "щепа", "fraction_mm": "4-8",
         "price_per_kg": 180, "unit": "кг"},
        {"slug": "sheel-dub", "name": "Щепа дуба", "type": IngredientType.WOOD,
         "wood_species": "дуб", "wood_form": "щепа", "fraction_mm": "4-8",
         "price_per_kg": 220, "unit": "кг"},
        {"slug": "sol-povarennaya", "name": "Соль поваренная", "type": IngredientType.SALT,
         "price_per_kg": 25},
        {"slug": "nitritnaya-sol", "name": "Нитритная соль", "type": IngredientType.ADDITIVE,
         "price_per_kg": 350},
    ]
    result: list[Ingredient] = []
    for item in data:
        existing = await session.scalar(
            select(Ingredient).where(Ingredient.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Ingredient(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_products(session) -> list[Product]:
    data = [
        {"slug": "doktorskaya", "name": "Докторская колбаса", "category": ProductCategory.SAUSAGE_BOILD,
         "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "polukopchenaya-moskovskaya", "name": "Московская полукопчёная", "category": ProductCategory.SAUSAGE_SEMI_SMOKED,
         "gost": "ГОСТ 31785-2012", "shelf_life_days": 10,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "syrokopchenaya-braunschweig", "name": "Брауншвейгская сырокопчёная", "category": ProductCategory.SAUSAGE_RAW_SMOKED,
         "gost": "ГОСТ 31785-2012", "shelf_life_days": 30,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "skumbria-gk", "name": "Скумбрия горячего копчения", "category": ProductCategory.FISH_HOT,
         "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "semga-hk", "name": "Сёмга холодного копчения", "category": ProductCategory.FISH_COLD,
         "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
        {"slug": "kuritsa-gk", "name": "Курица горячего копчения", "category": ProductCategory.POULTRY,
         "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "syr-kopcheniy-gouda", "name": "Сыр копчёный Гауда", "category": ProductCategory.CHEESE,
         "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "salo-kopchenoe", "name": "Сало копчёное", "category": ProductCategory.BACON,
         "shelf_life_days": 14, "storage_temp_min": 2, "storage_temp_max": 6},
    ]
    result: list[Product] = []
    for item in data:
        existing = await session.scalar(
            select(Product).where(Product.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Product(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_demo_users(session) -> list[User]:
    data = [
        {"email": "admin@feleti.by", "username": "admin", "full_name": "Администратор",
         "hashed_password": hash_password("admin"), "role": UserRole.ADMIN,
         "is_superuser": True},
        {"email": "tech@feleti.by", "username": "technologist", "full_name": "Технолог",
         "hashed_password": hash_password("tech"), "role": UserRole.TECHNOLOGIST},
        {"email": "operator@feleti.by", "username": "operator", "full_name": "Оператор",
         "hashed_password": hash_password("operator"), "role": UserRole.OPERATOR},
    ]
    result: list[User] = []
    for item in data:
        existing = await session.scalar(
            select(User).where(User.email == item["email"])
        )
        if existing:
            result.append(existing)
            continue
        obj = User(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def run_seed() -> None:
    logger.info("=== FELETI-SMOK: seed start ===")
    async with AsyncSessionLocal() as session:
        try:
            manufacturers = await seed_manufacturers(session)
            logger.info("Manufacturers: %s", len(manufacturers))

            chambers = await seed_chambers(session, manufacturers)
            logger.info("Chambers: %s", len(chambers))

            ingredients = await seed_ingredients(session)
            logger.info("Ingredients: %s", len(ingredients))

            products = await seed_products(session)
            logger.info("Products: %s", len(products))

            users = await seed_demo_users(session)
            logger.info("Users: %s", len(users))

            await session.commit()
            logger.info("=== seed committed ===")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed, rolled back")
            raise
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_seed())
