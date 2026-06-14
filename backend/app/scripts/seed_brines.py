"""Сид промышленных рассолов: 18 рецептур на основе данных Ижицы и ГОСТ.

Запуск: `docker compose exec backend python -m app.scripts.seed_brines`
Идемпотентен — повторный запуск не дублирует (по slug).
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.brine import Brine, BrineMethod

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BRINES = [
    # === Рыба: смешанный посол (по данным Ижицы) ===
    {
        "slug": "skumbria-mixed",
        "name": "Посол скумбрии смешанный (тузлук 1.17)",
        "method": BrineMethod.MIXED,
        "salt_percent": 15.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец чёрный горошком", "гвоздика"],
        "duration_hours": 96,
        "temp_c": 6,
        "water_percent": 60,
        "description": "Смешанный посол скумбрии: сухой натёр + заливка тузлуком плотностью 1.17.",
        "notes": "Источник: Ижица, технологическая карта. Выход: 3-5 суток при +5…+8°C.",
    },
    {
        "slug": "seld-mixed",
        "name": "Посол сельди смешанный (тузлук 1.17)",
        "method": BrineMethod.MIXED,
        "salt_percent": 15.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец чёрный горошком", "кориандр"],
        "duration_hours": 72,
        "temp_c": 10,
        "water_percent": 60,
        "description": "Смешанный посол сельди с пряностями.",
        "notes": "Источник: Ижица, +10°C, 3 суток.",
    },
    {
        "slug": "gorbusha-mixed",
        "name": "Посол горбуши смешанный с засыпкой в брюшко",
        "method": BrineMethod.MIXED,
        "salt_percent": 18.0,
        "sugar_percent": 1.5,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец душистый", "лимон"],
        "duration_hours": 96,
        "temp_c": 6,
        "water_percent": 55,
        "description": "Смешанный посол горбуши с дополнительной засыпкой соли в брюшко. Тузлук 1.20.",
        "notes": "Источник: Ижица. 3-5 суток при +5…+8°C.",
    },
    {
        "slug": "keta-mixed",
        "name": "Посол кеты смешанный (тузлук 1.20)",
        "method": BrineMethod.MIXED,
        "salt_percent": 18.0,
        "sugar_percent": 1.5,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец душистый"],
        "duration_hours": 96,
        "temp_c": 6,
        "water_percent": 55,
        "description": "Смешанный посол для кеты. Плотность тузлука 1.20.",
        "notes": "Источник: Ижица. 3-5 суток при +5…+8°C.",
    },
    {
        "slug": "maslyanaya-mixed",
        "name": "Посол масляной рыбы смешанный (тузлук 1.20)",
        "method": BrineMethod.MIXED,
        "salt_percent": 18.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец чёрный"],
        "duration_hours": 12,
        "temp_c": 6,
        "water_percent": 55,
        "description": "Смешанный посол масляной рыбы. Быстрый посол 12 ч.",
        "notes": "Источник: Ижица. +5…+8°C, 12 часов.",
    },
    # === Рыба: тузлучный посол ===
    {
        "slug": "salaka-wet",
        "name": "Тузлучный посол салаки (тузлук 1.10)",
        "method": BrineMethod.WET,
        "salt_percent": 10.0,
        "sugar_percent": 0.5,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": [],
        "duration_hours": 12,
        "temp_c": 6,
        "water_percent": 70,
        "description": "Тузлучный посол мелкой рыбы (салака, килька). Плотность тузлука 1.10.",
        "notes": "Источник: Ижица. 12 ч при +5…+8°C.",
    },
    {
        "slug": "forel-hk-wet",
        "name": "Тузлучный посол форели под холодное копчение",
        "method": BrineMethod.WET,
        "salt_percent": 14.0,
        "sugar_percent": 2.0,
        "nitrite_ppm": 50,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец душистый", "можжевельник"],
        "duration_hours": 48,
        "temp_c": 4,
        "water_percent": 65,
        "description": "Посол форели/сёмги для холодного копчения. Плотность тузлука 1.15.",
        "notes": "Промышленный стандарт. Сёмга выдерживается 48-72 ч.",
    },
    {
        "slug": "ugor-hk-wet",
        "name": "Тузлучный посол угря под холодное копчение",
        "method": BrineMethod.WET,
        "salt_percent": 16.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": [],
        "duration_hours": 24,
        "temp_c": 4,
        "water_percent": 60,
        "description": "Тузлучный посол угря. Плотность тузлука 1.18.",
        "notes": "Угорь — жирная рыба, требует плотного тузлука.",
    },
    {
        "slug": "paltus-wet",
        "name": "Тузлучный посол палтуса (тузлук 1.18)",
        "method": BrineMethod.WET,
        "salt_percent": 16.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец чёрный"],
        "duration_hours": 36,
        "temp_c": 5,
        "water_percent": 60,
        "description": "Посол палтуса для горячего и холодного копчения.",
        "notes": "Источник: Ижица. 1.5 суток при +5°C.",
    },
    {
        "slug": "omul-wet",
        "name": "Тузлучный посол омуля/сига (тузлук 1.12)",
        "method": BrineMethod.WET,
        "salt_percent": 12.0,
        "sugar_percent": 0.5,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": [],
        "duration_hours": 6,
        "temp_c": 5,
        "water_percent": 70,
        "description": "Слабый тузлук для нежирных сиговых рыб.",
        "notes": "Омуль, сиг, ряпушка — 4-6 ч в тузлуке 1.12.",
    },
    # === Рыба: сухой посол ===
    {
        "slug": "kilka-dry",
        "name": "Сухой посол кильки/мойвы",
        "method": BrineMethod.DRY,
        "salt_percent": 8.0,
        "sugar_percent": 0.5,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": [],
        "duration_hours": 10,
        "temp_c": 6,
        "water_percent": None,
        "description": "Сухой посол мелкой рыбы. Соль пересыпью слоями.",
        "notes": "Источник: Ижица. До 10 ч при +5…+8°C. Соль 8% от массы рыбы.",
    },
    # === Колбасы: нитритный посол ===
    {
        "slug": "sausage-raw-smoked-dry",
        "name": "Посол сырокопчёных колбас (нитритный)",
        "method": BrineMethod.DRY,
        "salt_percent": 3.0,
        "sugar_percent": 0.8,
        "nitrite_ppm": 100,
        "nitrate_ppm": 50,
        "spices": ["перец чёрный молотый", "чеснок сушёный", "мускатный орех"],
        "duration_hours": 48,
        "temp_c": 4,
        "water_percent": None,
        "description": "Сухой посол для сырокопчёных колбас с нитритной солью. Выдержка 48 ч при 0-4°C.",
        "notes": "ГОСТ 31785-2012. Нитрит натрия 100 ppm, нитрат 50 ppm для длительного созревания.",
    },
    {
        "slug": "sausage-boiled-smoked-dry",
        "name": "Посол варёно-копчёных колбас (нитритный)",
        "method": BrineMethod.DRY,
        "salt_percent": 2.5,
        "sugar_percent": 0.5,
        "nitrite_ppm": 75,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный молотый", "чеснок", "кардамон"],
        "duration_hours": 24,
        "temp_c": 4,
        "water_percent": None,
        "description": "Сухой посол для варёно-копчёных и полукопчёных колбас.",
        "notes": "ГОСТ 31785-2012. Нитрит 75 ppm. Выдержка 24 ч.",
    },
    {
        "slug": "sausage-semi-smoked-brine",
        "name": "Тузлук для полукопчёных колбас",
        "method": BrineMethod.WET,
        "salt_percent": 12.0,
        "sugar_percent": 0.5,
        "nitrite_ppm": 75,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный", "чеснок"],
        "duration_hours": 4,
        "temp_c": 4,
        "water_percent": 70,
        "description": "Тузлучный посол для полукопчёных колбас (плотность 1.10).",
        "notes": "Быстрый посол 2-4 ч в тузлуке перед термообработкой.",
    },
    # === Мясо ===
    {
        "slug": "pork-belly-dry",
        "name": "Сухой посол грудинки/корейки",
        "method": BrineMethod.DRY,
        "salt_percent": 3.5,
        "sugar_percent": 1.0,
        "nitrite_ppm": 50,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный", "чеснок", "паприка", "тимьян"],
        "duration_hours": 24,
        "temp_c": 4,
        "water_percent": None,
        "description": "Сухой посол свиной грудинки/корейки для горячего копчения.",
        "notes": "3.5% соли от массы. 24 ч при 0-4°C.",
    },
    {
        "slug": "beef-brisket-injection",
        "name": "Шприцевание говяжьей грудинки",
        "method": BrineMethod.INJECTION,
        "salt_percent": 10.0,
        "sugar_percent": 2.0,
        "nitrite_ppm": 50,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный", "чеснок", "лук"],
        "duration_hours": 12,
        "temp_c": 4,
        "water_percent": 80,
        "description": "Шприцевание рассолом 10% крупных кусков говядины перед копчением.",
        "notes": "10% от массы мяса. После шприцевания — массирование 30 мин.",
    },
    # === Птица ===
    {
        "slug": "chicken-hot-wet",
        "name": "Тузлучный посол курицы для горячего копчения",
        "method": BrineMethod.WET,
        "salt_percent": 8.0,
        "sugar_percent": 2.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["лавровый лист", "перец чёрный", "чеснок", "розмарин"],
        "duration_hours": 6,
        "temp_c": 4,
        "water_percent": 80,
        "description": "Посол курицы/утки/индейки в тузлуке перед горячим копчением.",
        "notes": "Промышленный стандарт. 6-12 ч при 0-4°C.",
    },
    # === Сало ===
    {
        "slug": "salo-dry",
        "name": "Сухой посол сала для копчения",
        "method": BrineMethod.DRY,
        "salt_percent": 8.0,
        "sugar_percent": 1.0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный", "чеснок", "паприка"],
        "duration_hours": 168,
        "temp_c": 4,
        "water_percent": None,
        "description": "Сухой посол шпика/сала. Соль 8% от массы, выдержка 7 суток.",
        "notes": "Стандартный промысловый посол. 5-7 суток при 0-4°C.",
    },
    # === Сыр ===
    {
        "slug": "cheese-wet-quick",
        "name": "Быстрый тузлук для сыра",
        "method": BrineMethod.WET,
        "salt_percent": 20.0,
        "sugar_percent": 0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 0,
        "spices": [],
        "duration_hours": 2,
        "temp_c": 10,
        "water_percent": 75,
        "description": "Концентрированный тузлук для посола твёрдых и полутвёрдых сыров перед копчением.",
        "notes": "20% соли (насыщенный раствор). 1-2 ч при 10°C.",
    },
    {
        "slug": "syr-gouda-wet",
        "name": "Посол сыра Гауда в тузлуке",
        "method": BrineMethod.WET,
        "salt_percent": 18.0,
        "sugar_percent": 0,
        "nitrite_ppm": 0,
        "nitrate_ppm": 50,
        "spices": [],
        "duration_hours": 6,
        "temp_c": 10,
        "water_percent": 75,
        "description": "Традиционный тузлук для сыров типа Гауда. Калийная селитра 50 ppm.",
        "notes": "Классический рецепт. 6-12 ч в зависимости от размера головки.",
    },
    # === Снеки ===
    {
        "slug": "jerky-dry",
        "name": "Сухой посол для джерки/снеков",
        "method": BrineMethod.DRY,
        "salt_percent": 3.0,
        "sugar_percent": 3.0,
        "nitrite_ppm": 50,
        "nitrate_ppm": 0,
        "spices": ["перец чёрный", "паприка", "чили", "чеснок", "имбирь"],
        "duration_hours": 12,
        "temp_c": 4,
        "water_percent": None,
        "description": "Посол для мясных снеков (джерки, чипсы). Сухой натёр со специями.",
        "notes": "12 ч в холодильнике. Нитрит 50 ppm для цвета.",
    },
]


async def seed_brines(session) -> list[Brine]:
    result = []
    for item in BRINES:
        existing = await session.scalar(
            select(Brine).where(Brine.slug == item["slug"])
        )
        if existing:
            logger.info("  Brine already exists: %s", item["slug"])
            result.append(existing)
            continue
        obj = Brine(**item)
        session.add(obj)
        await session.flush()
        result.append(obj)
        logger.info("  Created brine: %s — %s", item["slug"], item["name"])
    return result


async def main():
    logger.info("Seeding brines...")
    async with AsyncSessionLocal() as session:
        created = await seed_brines(session)
        await session.commit()
    logger.info("Done: %d brines in DB", len(created))


if __name__ == "__main__":
    asyncio.run(main())
