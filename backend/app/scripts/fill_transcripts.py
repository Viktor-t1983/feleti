"""Обновить body_md YouTube-статей полными текстами транскриптов + создать FTS-индекс.

Запуск: docker compose exec backend python -m app.scripts.fill_transcripts
"""

import asyncio
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("fill_transcripts")

SUMMARY_PATH = "/app/summary.json"
TRANSCRIPTS_DIR = "/app/transcripts"


def clean_timestamps(text: str) -> str:
    return re.sub(r"\[\d{2}:\d{2}:\d{2}\s*-->\s*\d{2}:\d{2}:\d{2}\]\s*", "", text).strip()


async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeArticle
    from sqlalchemy import select, text

    async with AsyncSessionLocal() as session:
        # 1. Обновляем статьи YouTube полными транскриптами
        result = await session.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.source_url.like("%youtube.com%")
            )
        )
        articles = result.scalars().all()
        logger.info(f"YouTube-статей для обновления: {len(articles)}")

        updated = 0
        for a in articles:
            vid_id = None
            m = re.search(r"v=([\w-]+)", a.source_url or "")
            if m:
                vid_id = m.group(1)

            if not vid_id:
                continue

            tpath = os.path.join(TRANSCRIPTS_DIR, f"{vid_id}.txt")
            if not os.path.exists(tpath):
                continue

            with open(tpath, "r", encoding="utf-8") as f:
                raw = f.read()

            body = clean_timestamps(raw)
            if len(body) > len(a.body_md or ""):
                a.body_md = body[:100000]  # лимит 100К символов
                updated += 1

        await session.commit()
        logger.info(f"Обновлено body_md: {updated} статей")

        # 2. Создаём FTS-индекс (если нет)
        logger.info("Создаю FTS-индекс...")
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_fts
            ON knowledge_articles
            USING gin(to_tsvector('russian', body_md || ' ' || title));
        """))
        await session.commit()
        logger.info("FTS-индекс готов")

        # 3. Тестовый поиск
        test_queries = ["скумбрия", "электростатика", "дымогенератор", "колбаса", "температура"]
        for q in test_queries:
            result = await session.execute(
                text("""
                    SELECT id, title, ts_headline('russian', body_md, plainto_tsquery('russian', :q),
                        'MaxWords=30, MinWords=15, StartSel=**, StopSel=**') AS headline
                    FROM knowledge_articles
                    WHERE to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)
                    LIMIT 3
                """),
                {"q": q},
            )
            rows = result.fetchall()
            logger.info(f"  Поиск «{q}»: {len(rows)} результатов")
            for r in rows:
                hl = (r.headline or "")[:100].replace("**", "*")
                logger.info(f"    ID:{r.id} {r.title[:50]}: …{hl}…")

    logger.info("\nГотово! Теперь доступен FTS-поиск по всем 109 статьям.")


if __name__ == "__main__":
    asyncio.run(main())
