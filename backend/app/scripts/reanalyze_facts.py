"""Пакетный переанализ статей для заполнения KnowledgeFacts.
Запуск: `docker compose exec backend python -m app.scripts.reanalyze_facts`
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
import time

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.models.knowledge import KnowledgeArticle
from app.models.knowledge_fact import KnowledgeFact
from app.services.article_analyzer import ArticleAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

CONCURRENCY = 3


async def get_ids_without_facts() -> list[int]:
    async with AsyncSessionLocal() as db:
        has_facts = select(KnowledgeFact.article_id).distinct()
        stmt = (
            select(KnowledgeArticle.id)
            .where(~KnowledgeArticle.id.in_(has_facts))
            .order_by(KnowledgeArticle.id)
        )
        rows = (await db.scalars(stmt)).all()
        return list(rows)


async def analyze_one(aid: int) -> bool:
    try:
        async with AsyncSessionLocal() as db:
            analyzer = ArticleAnalyzer(db)
            await analyzer.analyze(aid)
            await db.commit()
        return True
    except IntegrityError:
        logger.warning("Article %d already analyzed (race), skipping", aid)
        return True
    except Exception as exc:
        logger.error("Failed to analyze article %d: %s", aid, exc)
        return False


async def main():
    start = time.time()
    logger.info("Loading article IDs without facts...")

    all_ids = await get_ids_without_facts()
    total = len(all_ids)
    logger.info("Found %d articles without facts", total)

    if total == 0:
        logger.info("All articles already have facts.")
        return

    sem = asyncio.Semaphore(CONCURRENCY)

    async def worker(aid: int):
        async with sem:
            return await analyze_one(aid)

    processed = 0
    ok_count = 0
    fail_count = 0

    chunk_size = CONCURRENCY * 10
    for chunk_start in range(0, total, chunk_size):
        chunk = all_ids[chunk_start:chunk_start + chunk_size]
        results = await asyncio.gather(*[worker(aid) for aid in chunk], return_exceptions=True)
        for r in results:
            if r is True:
                ok_count += 1
            else:
                fail_count += 1
        processed += len(chunk)
        elapsed = time.time() - start
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total - processed) / rate if rate > 0 else 0
        logger.info(
            "Progress: %d/%d (ok=%d, fail=%d) | %.1f арт/с | ETA: %.0f с (% .1f мин)",
            processed, total, ok_count, fail_count, rate, eta, eta / 60,
        )

    elapsed = time.time() - start
    logger.info(
        "Done: %d analyzed, %d failed, %.1f min elapsed",
        ok_count, fail_count, elapsed / 60,
    )


if __name__ == "__main__":
    asyncio.run(main())
