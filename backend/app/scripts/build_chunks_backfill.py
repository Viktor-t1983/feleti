"""Фоновый скрипт: нарезка чанков для статей, у которых их ещё нет.

Запуск: python -m app.scripts.build_chunks_backfill
"""
from __future__ import annotations

import asyncio
import logging
import sys

from sqlalchemy import select, func

from app.db.session import AsyncSessionLocal
from app.models.knowledge import KnowledgeArticle, ArticleAnalysis
from app.models.knowledge_fact import KnowledgeFact, KnowledgeChunk
from app.services.chunker import build_chunks

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("build_chunks_backfill")

CONCURRENCY = 10

sem: asyncio.Semaphore | None = None


async def worker(article_id: int) -> str:
    async with sem:
        try:
            async with AsyncSessionLocal() as db:
                # Пропускаем если чанки уже есть
                existing = await db.scalar(
                    select(func.count()).select_from(
                        select(KnowledgeChunk)
                        .where(KnowledgeChunk.article_id == article_id)
                        .limit(1)
                        .subquery()
                    )
                )
                if existing:
                    return f"SKIP {article_id} (has chunks)"

                article = await db.get(KnowledgeArticle, article_id)
                if not article or not article.body_md:
                    return f"SKIP {article_id} (no body)"

                chunks = await build_chunks(article_id, db)

                # Привязываем существующие факты к чанкам
                facts = (
                    await db.scalars(
                        select(KnowledgeFact)
                        .where(
                            KnowledgeFact.article_id == article_id,
                            KnowledgeFact.chunk_id.is_(None),
                        )
                    )
                ).all()

                relinked = 0
                for fact in facts:
                    if fact.source_text:
                        for ch in chunks:
                            if fact.source_text in ch.content:
                                fact.chunk_id = ch.id
                                relinked += 1
                                break

                await db.commit()
                return f"DONE {article_id} ({len(chunks)} chunks, {relinked} relinked)"
        except Exception as e:
            logger.exception("Error processing article %d", article_id)
            return f"FAIL {article_id}: {e}"


async def main():
    global sem
    sem = asyncio.Semaphore(CONCURRENCY)

    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count(KnowledgeArticle.id)))
        analyzed = await db.scalar(
            select(func.count()).select_from(
                select(ArticleAnalysis.article_id).distinct().subquery()
            )
        )
        has_chunks = select(KnowledgeChunk.article_id).distinct()
        need_chunks = await db.scalar(
            select(func.count()).select_from(
                select(KnowledgeArticle.id)
                .where(
                    KnowledgeArticle.id.in_(
                        select(ArticleAnalysis.article_id)
                    ),
                    ~KnowledgeArticle.id.in_(has_chunks),
                )
                .subquery()
            )
        )
        logger.info(f"Total articles: {total}")
        logger.info(f"Analyzed: {analyzed}")
        logger.info(f"Need chunks: {need_chunks}")

        # IDs статей, которым нужны чанки
        stmt = (
            select(KnowledgeArticle.id)
            .where(
                KnowledgeArticle.id.in_(
                    select(ArticleAnalysis.article_id)
                ),
                ~KnowledgeArticle.id.in_(has_chunks),
            )
            .order_by(KnowledgeArticle.id)
        )
        all_ids = (await db.scalars(stmt)).all()
        logger.info(f"Articles to chunk: {len(all_ids)}")

    # Пакетная обработка
    chunk_size = CONCURRENCY * 10
    processed = 0
    for chunk_start in range(0, len(all_ids), chunk_size):
        batch = all_ids[chunk_start:chunk_start + chunk_size]
        results = await asyncio.gather(*[worker(aid) for aid in batch], return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error("Worker exception: %s", r)
            else:
                logger.info(r)
        processed += len(batch)
        logger.info(f"Progress: {processed}/{len(all_ids)}")

    logger.info("Done! Processed %d articles", processed)


if __name__ == "__main__":
    asyncio.run(main())
