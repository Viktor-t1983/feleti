"""Нарезка статей на чанки для точного AI-анализа.

Каждый чанк — связный фрагмент текста ~2000 символов.
Чанки перекрываются на 200 символов, чтобы не потерять контекст на стыках.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeArticle
from app.models.knowledge_fact import KnowledgeChunk

logger = logging.getLogger(__name__)

CHUNK_SIZE = 2000
OVERLAP = 200


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    """Разбить текст на чанки с перекрытием.

    Returns:
        Список {content, char_offset_start, char_offset_end, chunk_index}
    """
    if not text:
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            end = len(text)
        else:
            # Стараемся резать по границе предложения или абзаца
            boundary = _find_boundary(text, start, end)
            if boundary:
                end = boundary

        content = text[start:end]
        chunks.append({
            "content": content,
            "char_offset_start": start,
            "char_offset_end": end,
            "chunk_index": index,
        })
        index += 1

        # Следующий чанк начинается на overlap раньше конца текущего
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start

        # Защита от бесконечного цикла
        if index > 1000:
            logger.warning("Too many chunks (>1000), stopping")
            break

    return chunks


def _find_boundary(text: str, start: int, end: int) -> int | None:
    """Найти лучшую границу для разрезания — по концу предложения или абзаца."""
    segment = text[start:end]

    # Ищем конец абзаца (двойной перенос строки)
    para_match = re.search(r"\n\n", segment[::-1])
    if para_match:
        pos = end - para_match.start()
        if pos > start + chunk_size // 2:
            return pos

    # Ищем конец предложения (.!?)
    sent_match = re.search(r"[.!?]\s", segment[::-1])
    if sent_match:
        pos = end - sent_match.start()
        if pos > start + chunk_size // 2:
            return pos

    # Ищем конец строки
    line_match = re.search(r"\n", segment[::-1])
    if line_match:
        pos = end - line_match.start()
        if pos > start + chunk_size // 2:
            return pos

    return None


async def build_chunks(article_id: int, db: AsyncSession) -> list[KnowledgeChunk]:
    """Создать чанки для статьи. Идемпотентно — удаляет старые и создаёт новые."""
    article = await db.get(KnowledgeArticle, article_id)
    if not article:
        logger.warning("Article %d not found", article_id)
        return []

    text = article.body_md or ""
    if not text:
        return []

    # Удаляем старые чанки
    await db.execute(
        delete(KnowledgeChunk).where(KnowledgeChunk.article_id == article_id)
    )

    # Создаём новые
    raw_chunks = split_into_chunks(text)
    chunks = []
    for rc in raw_chunks:
        chunk = KnowledgeChunk(
            article_id=article_id,
            chunk_index=rc["chunk_index"],
            content=rc["content"],
            token_count=len(rc["content"]) // 4,  # приблизительно
            char_offset_start=rc["char_offset_start"],
            char_offset_end=rc["char_offset_end"],
        )
        db.add(chunk)
        chunks.append(chunk)

    await db.flush()
    logger.info("Built %d chunks for article %d", len(chunks), article_id)
    return chunks


async def get_article_chunks(article_id: int, db: AsyncSession) -> list[KnowledgeChunk]:
    """Получить чанки статьи, создав их если ещё нет."""
    chunks = (
        await db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.article_id == article_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
    ).all()

    if not chunks:
        chunks = await build_chunks(article_id, db)

    return list(chunks)


async def get_unanalyzed_chunk_ids(db: AsyncSession, limit: int = 50) -> list[int]:
    """ID статей, у которых нет чанков."""
    has_chunks = select(KnowledgeChunk.article_id).distinct()
    stmt = (
        select(KnowledgeArticle.id)
        .where(~KnowledgeArticle.id.in_(has_chunks))
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()
    return list(rows)
