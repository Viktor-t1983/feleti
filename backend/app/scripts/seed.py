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
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
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


async def seed_competitors(session) -> list[Competitor]:
    data = [
        {
            "slug": "ijiza",
            "name": "Ижица / Varmen",
            "country": "Россия",
            "founded_year": 1992,
            "segment": "Horeca / Profi / Industrial",
            "is_main_competitor": True,
            "client_count": 4000,
            "recipe_count": 200,
            "warranty_years": 1,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "description": "Российский производитель коптильного оборудования с 1992 года. Линейка от 20 до 1200 кг. Собственное производство в Санкт-Петербурге. 4000+ клиентов в 50+ странах. Облако, мобильное приложение и удаленный мониторинг — опция для малых моделей, стандарт для промышленных UTM/UTR.",
            "strengths": ["25+ лет на рынке", "200+ готовых рецептов", "Собственное производство", "Широкая линейка (20–1200 кг)", "Фрикционный дымогенератор", "Электростатическое копчение", "Облако / мобильное / удаленный мониторинг"],
            "weaknesses": ["Плохие инструкции", "Проблемы с электростатикой", "Заводской дефект вентилятора", "Нагар и перегрев", "Плесень при неправильной эксплуатации", "Капли конденсата", "Проблемы с цветом продукта", "Шибер/зольник"],
            "models": [
                {"name": "Varmen Mini", "max_load_kg": 20, "power_kw": 3.5, "voltage_v": 220, "weight_kg": 70, "dimensions": "0.65 x 0.65 x 1.1 м", "modes": ["горячее копчение", "проварка паром", "запекание", "сушка", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-Z115.2 (полуавтомат)", "max_load_kg": 100, "power_kw": 10, "voltage_v": 380, "weight_kg": 300, "dimensions": "1.51 x 1.1 x 1.9 м", "modes": ["горячее копчение", "проварка паром", "сушка", "запекание", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-Z115.2-A (автомат)", "max_load_kg": 250, "power_kw": 14, "voltage_v": 380, "weight_kg": 650, "dimensions": "1.6 x 1.3 x 2.25 м", "modes": ["горячее копчение", "проварка паром", "запекание", "холодное копчение"], "automation_level": "автомат"},
                {"name": "Ижица-Z115.2АС", "max_load_kg": 250, "power_kw": 12, "voltage_v": 380, "weight_kg": 650, "dimensions": "1.75 x 1.55 x 2.25 м", "modes": ["прогрев", "сушка", "сушка по влажности", "копчение", "варка", "обжарка"], "automation_level": "автомат"},
                {"name": "Ижица-Z200", "max_load_kg": 500, "power_kw": 30, "voltage_v": 380, "weight_kg": 600, "dimensions": "2.0 x 1.4 x 2.7 м", "modes": ["горячее копчение", "проварка паром", "запекание"], "automation_level": "полуавтомат"},
                {"name": "Ижица-UNI-100", "max_load_kg": 100, "power_kw": 11, "voltage_v": 380, "weight_kg": 340, "dimensions": "1.51 x 1.1 x 1.9 м", "modes": ["горячее копчение", "холодное копчение", "запекание", "проварка паром", "сушка", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-miniGK", "max_load_kg": 20, "power_kw": 3.5, "voltage_v": 220, "weight_kg": 70, "dimensions": "0.63 x 0.65 x 1.1 м", "modes": ["сушка", "копчение", "жарка", "варка паром", "проветривание"], "automation_level": "полуавтомат"},
                {"name": "Ижица-1200М4", "max_load_kg": 1200, "power_kw": 3.2, "voltage_v": 380, "weight_kg": 250, "dimensions": "1.3 x 0.95 x 2.0 м", "modes": ["холодное копчение"], "automation_level": "полуавтомат"},
                {"name": "Ижица-1200М4-А (электростатика)", "max_load_kg": 1200, "power_kw": 5, "voltage_v": 380, "weight_kg": 400, "dimensions": "1.4 x 1.2 x 2.25 м", "modes": ["холодное копчение"], "automation_level": "автомат"},
                {"name": "VARMEN UTM.250", "max_load_kg": 250, "power_kw": 31, "voltage_v": 380, "dimensions": "2.04 x 1.5 x 3.1 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTM.500", "max_load_kg": 500, "power_kw": 62, "voltage_v": 380, "dimensions": "2.04 x 2.5 x 3.5 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTR.250", "max_load_kg": 250, "power_kw": 31, "voltage_v": 380, "dimensions": "2.04 x 1.5 x 3.1 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "холодное копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTR.500", "max_load_kg": 500, "power_kw": 62, "voltage_v": 380, "dimensions": "2.04 x 2.5 x 3.5 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "холодное копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "Varmen Atomic 250", "max_load_kg": 250, "power_kw": 30, "voltage_v": 380, "dimensions": "1.97 x 1.5 x 3.05 м", "modes": ["сушка", "интервальная сушка", "копчение", "варка"], "automation_level": "полностью автоматизированная"},
                {"name": "BBQ Smoker Red Dolly", "max_load_kg": 100, "power_kw": 9, "voltage_v": 380, "dimensions": "1.4 x 1.0 x 1.85 м", "modes": ["горячее копчение", "проварка паром"], "automation_level": "сенсорная панель с удаленным доступом"},
                {"name": "Ижица-СВ-Н", "max_load_kg": 80, "power_kw": 0.7, "voltage_v": 220, "weight_kg": 80, "dimensions": "0.9 x 0.9 x 1.9 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
                {"name": "Ижица-СВ-Z", "max_load_kg": 100, "power_kw": 1.2, "voltage_v": 220, "dimensions": "0.95 x 1.2 x 1.6 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
                {"name": "Ижица-СВ2500", "max_load_kg": 250, "power_kw": 1.5, "voltage_v": 220, "dimensions": "1.48 x 1.6 x 2.25 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
            ],
            "problems": [
                {"title": "Вентилятор установлен вверх ногами", "description": "В сушильно-вялочной камере вентилятор стоит с лопастями для подачи воздуха вверх, а крутится вниз. Обдув идет по стенкам, в центре противоток.", "severity": "medium", "frequency": "Часто", "source": "me23.ru (фев 2018)"},
                {"title": "Электростатика не работает", "description": "Увеличилось время копчения. Статика на ноль ушла через 2 года. Искра на генераторе при полной загрузке — пара миллиметров.", "severity": "high", "frequency": "Часто", "source": "ijiza.userecho.ru (2024)"},
                {"title": "Плохие инструкции", "description": "Инструкция у производителя никакая, приходится звонить и спрашивать на завод. Не понятно как чистить коптильню.", "severity": "medium", "frequency": "Всегда", "source": "me23.ru (2018–2019)"},
                {"title": "Много дыма, толку мало", "description": "У двух одинаковых печей Ижица-М4 одна работает без претензий, во второй много дыма, толку мало. Напряжение везде одинаковое.", "severity": "high", "frequency": "Иногда", "source": "me23.ru (янв 2023)"},
                {"title": "Нагар и перегрев", "description": "При длительной работе нагревательных элементов образуется нагар, снижающий эффективность. Перегрев приводит к подгоранию продукта.", "severity": "high", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Плесень на продукции", "description": "При холодном копчении и нарушении режима влажности на поверхности продукта появляется плесень. Проблема особенно актуальна для начинающих.", "severity": "high", "frequency": "Иногда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Капли конденсата", "description": "Во время охлаждения и при резком перепаде температур внутри камеры образуются капли конденсата, падающие на продукт и ухудшающие его внешний вид.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Неправильный цвет продукта", "description": "Продукт получается желтым или серым вместо золотисто-коричневого. Причины: неправильный режим, некачественная щепа, проблемы с дымогенератором.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Проблемы с шибером и зольником", "description": "Шибер заклинивает, зольник забивается золой. Требуется частая чистка и обслуживание. Нет инструкции по правильной чистке.", "severity": "medium", "frequency": "Всегда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
            ],
        },
        {
            "slug": "mauting",
            "name": "Mauting",
            "country": "Чехия",
            "segment": "Industrial",
            "is_main_competitor": False,
            "recipe_count": 1000,
            "warranty_years": 2,
            "has_cloud": False,
            "has_mobile_app": False,
            "has_remote_monitoring": False,
            "has_video_camera": False,
            "description": "Чешский бренд, 70+ лет на рынке. Премиум-сегмент для крупных заводов. Туннельные камеры 1–8 вагонеток.",
            "strengths": ["70+ лет на рынке", "Премиум качество", "Туннели до 8 вагонеток"],
            "weaknesses": ["Высокая цена (от 5M ₽)", "Нет mobile/cloud", "Сложности с сервисом в РФ"],
            "models": [
                {"name": "Туннель 1 вагонетка", "max_load_kg": 500},
                {"name": "Туннель 4 вагонетки", "max_load_kg": 2000},
                {"name": "Туннель 8 вагонеток", "max_load_kg": 4000},
            ],
            "problems": [],
        },
        {
            "slug": "fessmann",
            "name": "Fessmann",
            "country": "Германия",
            "segment": "Industrial",
            "is_main_competitor": False,
            "recipe_count": 1000,
            "warranty_years": 3,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "description": "Немецкий бренд, 100+ лет на рынке. FES.APP — мобильное приложение, OPC UA интеграция. Флагман промышленного копчения.",
            "strengths": ["FES.APP — лучшее mobile в отрасли", "OPC UA", "100+ лет опыта", "Полная MES интеграция"],
            "weaknesses": ["Цены от 8M ₽", "Нет производства в РФ", "Таможенные риски"],
            "models": [
                {"name": "T1900", "max_load_kg": 1000},
                {"name": "T2500", "max_load_kg": 2000},
                {"name": "Turbomat", "max_load_kg": 3000},
            ],
            "problems": [],
        },
        {
            "slug": "kerres",
            "name": "Kerres",
            "country": "Германия",
            "segment": "Profi / Industrial",
            "is_main_competitor": False,
            "recipe_count": 500,
            "warranty_years": 2,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "description": "Немецкий производитель. Jet Smoke, Hybrid Airflow. Премиум сегмент.",
            "strengths": ["Jet Smoke технология", "Hybrid Airflow", "Облачная синхронизация"],
            "weaknesses": ["Высокие цены", "Нет в РФ"],
            "models": [
                {"name": "Jet Smoke 500", "max_load_kg": 500},
                {"name": "Hybrid Airflow 1000", "max_load_kg": 1000},
            ],
            "problems": [],
        },
    ]

    result: list[Competitor] = []
    for item in data:
        existing = await session.scalar(
            select(Competitor).where(Competitor.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        models = item.pop("models", [])
        problems = item.pop("problems", [])
        obj = Competitor(**item)
        for m in models:
            obj.models.append(CompetitorModel(**m))
        for p in problems:
            obj.problems.append(CompetitorProblem(**p))
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

            competitors = await seed_competitors(session)
            logger.info("Competitors: %s", len(competitors))

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
