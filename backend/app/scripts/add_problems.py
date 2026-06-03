"""Добавить новые проблемы Ижицы из YouTube-анализа."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.base import Base  # noqa: F401
from app.db.session import AsyncSessionLocal, engine
from app.models.competitor import Competitor, CompetitorProblem

logger = logging.getLogger(__name__)

NEW_PROBLEMS = [
    {"title": "Нагар и перегрев", "description": "При длительной работе нагревательных элементов образуется нагар, снижающий эффективность. Перегрев приводит к подгоранию продукта.", "severity": "high", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
    {"title": "Плесень на продукции", "description": "При холодном копчении и нарушении режима влажности на поверхности продукта появляется плесень. Проблема особенно актуальна для начинающих.", "severity": "high", "frequency": "Иногда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
    {"title": "Капли конденсата", "description": "Во время охлаждения и при резком перепаде температур внутри камеры образуются капли конденсата, падающие на продукт и ухудшающие его внешний вид.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
    {"title": "Неправильный цвет продукта", "description": "Продукт получается желтым или серым вместо золотисто-коричневого. Причины: неправильный режим, некачественная щепа, проблемы с дымогенератором.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
    {"title": "Проблемы с шибером и зольником", "description": "Шибер заклинивает, зольник забивается золой. Требуется частая чистка и обслуживание. Нет инструкции по правильной чистке.", "severity": "medium", "frequency": "Всегда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
]


async def add_problems() -> None:
    async with AsyncSessionLocal() as session:
        competitor = await session.scalar(select(Competitor).where(Competitor.slug == "ijiza"))
        if not competitor:
            logger.error("Competitor 'ijiza' not found")
            return

        existing_titles = {p.title for p in competitor.problems}
        added = 0
        for p in NEW_PROBLEMS:
            if p["title"] in existing_titles:
                logger.info("Skipping existing problem: %s", p["title"])
                continue
            competitor.problems.append(CompetitorProblem(**p))
            added += 1

        await session.commit()
        logger.info("Added %d new problems to Ижица", added)
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(add_problems())
