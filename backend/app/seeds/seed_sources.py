"""Seed source_reputation from the hardcoded SOURCE_REPUTATION dict."""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.source_reputation import SourceReputation

# Initial data matching knowledge_collector.SOURCE_REPUTATION
INITIAL_SOURCES = [
    ("vseokopchenii.ru", 3, "Всё о копчении — базовый источник"),
    ("smokehouse.ru", 3, "Оборудование и технологии копчения"),
    ("vniro.ru", 3, "ВНИРО — технологии переработки рыбы"),
    ("vniimp.ru", 3, "ВНИИМП — мясопереработка"),
    ("feleti.ru", 3, "FELETI — коптильные камеры"),
    ("eda.ru", 2, "Рецепты"),
    ("povarenok.ru", 2, "Кулинарные рецепты"),
    ("meatclub.ru", 2, "Форум мясопереработчиков"),
    ("fishnews.ru", 2, "Новости рыбной отрасли"),
    ("youtube.com", 1, "YouTube — видео"),
    ("youtu.be", 1, "YouTube — короткие ссылки"),
    ("habr.com", 1, "Habr — IT и рецепты"),
    ("pikabu.ru", 1, "Pikabu — пользовательский контент"),
    ("ozon.ru", 1, "Маркетплейс"),
    ("wildberries.ru", 1, "Маркетплейс"),
    ("market.yandex.ru", 1, "Яндекс Маркет"),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(SourceReputation.domain))
        existing_domains = {row[0] for row in existing}

        count = 0
        for domain, score, label in INITIAL_SOURCES:
            if domain not in existing_domains:
                db.add(SourceReputation(domain=domain, score=score, label=label))
                count += 1

        if count:
            await db.commit()
            print(f"Seeded {count} sources")
        else:
            print("All sources already exist")
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
    sys.exit(0)
