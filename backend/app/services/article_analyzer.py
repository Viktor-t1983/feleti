"""Сервис AI-анализа статей: категоризация, извлечение структурированных фактов."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brine import Brine
from app.models.chamber import Chamber
from app.models.knowledge import ArticleAnalysis, AnalysisStatus, KnowledgeArticle
from app.models.knowledge_fact import (
    KnowledgeFact, KnowledgeChunk,
    FactSubjectType, FactPredicate, FactObjectType, FactStatus,
)
from app.models.product import Product
from app.services.ai_service import AIService
from app.services.chunker import build_chunks


logger = logging.getLogger("article_analyzer")

STRUCTURED_CONTEXT_PROMPT = """
СПРАВОЧНЫЕ ДАННЫЕ (существующие сущности в системе):
Используй эти названия для полей "subject" и "object" в facts.

-- Продукты --
{products_str}

-- Камеры --
{chambers_str}

-- Рассолы (посолы) --
{brines_str}
"""

def _find_chunk_for_text(source_text: str, chunks: list[KnowledgeChunk]) -> int | None:
    """Найти ID чанка, содержащего заданный source_text (по подстроке)."""
    for ch in chunks:
        if source_text in ch.content:
            return ch.id
    # Fallback: ищем по первому предложению
    first_sentence = source_text.split(".")[0]
    if len(first_sentence) > 20:
        for ch in chunks:
            if first_sentence in ch.content:
                return ch.id
    return None


PREDICATE_MAP = {
    "uses_brine": FactPredicate.USES_BRINE,
    "uses_equipment": FactPredicate.USES_EQUIPMENT,
    "uses_technology": FactPredicate.USES_TECHNOLOGY,
    "has_parameter": FactPredicate.HAS_PARAMETER,
    "regulated_by": FactPredicate.REGULATED_BY,
    "has_category": FactPredicate.HAS_CATEGORY,
    "contains": FactPredicate.CONTAINS,
    "derived_from": FactPredicate.DERIVED_FROM,
    "shelf_life": FactPredicate.SHELF_LIFE,
    "storage_condition": FactPredicate.STORAGE_CONDITION,
    "process_step": FactPredicate.PROCESS_STEP,
    "mentions": FactPredicate.MENTIONS,
}

SUBJECT_TYPE_MAP = {
    "product": FactSubjectType.PRODUCT,
    "brine": FactSubjectType.BRINE,
    "chamber": FactSubjectType.CHAMBER,
    "technology": FactSubjectType.TECHNOLOGY,
    "ingredient": FactSubjectType.INGREDIENT,
    "regulation": FactSubjectType.REGULATION,
    "article": FactSubjectType.ARTICLE,
}

OBJECT_TYPE_MAP = {
    "product": FactObjectType.PRODUCT,
    "brine": FactObjectType.BRINE,
    "chamber": FactObjectType.CHAMBER,
    "technology": FactObjectType.TECHNOLOGY,
    "regulation": FactObjectType.REGULATION,
    "ingredient": FactObjectType.INGREDIENT,
    "literal": FactObjectType.LITERAL,
}


async def _load_structured_context(db: AsyncSession) -> str:
    """Загрузить из БД существующие продукты, камеры и рассолы для контекста AI."""
    products = (await db.scalars(select(Product).order_by(Product.name))).all()
    chambers = (await db.scalars(select(Chamber).order_by(Chamber.model))).all()
    brines = (await db.scalars(select(Brine).order_by(Brine.name))).all()

    products_str = "\n".join(
        f"  - {p.name} ({p.category.value if hasattr(p.category, 'value') else p.category})"
        for p in products
    ) if products else "  (нет данных)"

    chambers_str = "\n".join(
        f"  - {c.model} ({c.type.value if hasattr(c.type, 'value') else c.type}, "
        f"{c.manufacturer.name if hasattr(c, 'manufacturer') and c.manufacturer else 'бренд не указан'})"
        for c in chambers
    ) if chambers else "  (нет данных)"

    brines_str = "\n".join(
        f"  - {b.name} ({b.method.value if hasattr(b.method, 'value') else b.method})"
        for b in brines
    ) if brines else "  (нет данных)"

    return STRUCTURED_CONTEXT_PROMPT.format(
        products_str=products_str,
        chambers_str=chambers_str,
        brines_str=brines_str,
    )


class ArticleAnalyzer:
    """Запускает AI-анализ статьи и сохраняет результат + факты."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def analyze(self, article_id: int) -> ArticleAnalysis:
        article = await self.db.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
        )
        if not article:
            raise ValueError(f"Статья {article_id} не найдена")

        analysis = await self.db.scalar(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        )
        if not analysis:
            analysis = ArticleAnalysis(article_id=article_id)
            self.db.add(analysis)

        analysis.status = AnalysisStatus.RUNNING
        await self.db.flush()

        try:
            settings = await AIService.get_settings(self.db)
            ai = AIService(settings)

            structured_ctx = await _load_structured_context(self.db)
            text = f"{article.title}\n\n{article.body_md or ''}\n\n{structured_ctx}"
            result = await ai.analyze(text)

            # Строим чанки ДО парсинга фактов, чтобы привязать source_text к фрагменту
            chunks = await build_chunks(article_id, self.db)

            analysis.products = result.get("products", [])
            analysis.technologies = result.get("technologies", [])
            problems_raw = result.get("problems", [])
            analysis.problems = [
                {
                    "title": p.get("title", ""),
                    "description": p.get("description", ""),
                    "severity": p.get("severity", "medium"),
                }
                for p in problems_raw
            ]
            equipment_raw = result.get("equipment", [])
            analysis.equipment = [
                {
                    "name": e.get("name", ""),
                    "specs": e.get("specs", {}),
                }
                for e in equipment_raw
            ]
            analysis.key_insights = result.get("key_insights", [])
            mentions_raw = result.get("competitor_mentions", [])
            analysis.competitor_mentions = [
                {
                    "name": m.get("name", ""),
                    "products": m.get("products", []),
                    "pricing": m.get("pricing"),
                }
                for m in mentions_raw
            ]
            analysis.target_markets = result.get("target_markets", [])
            analysis.ai_category = result.get("category")
            analysis.topic_path = result.get("topic_path")
            analysis.raw_response = result
            analysis.model_used = settings.model_name
            analysis.status = AnalysisStatus.DONE
            analysis.error = None
            analysis.analyzed_at = datetime.utcnow()

            # NEW: parse structured facts
            facts_data = result.get("facts", [])
            if facts_data:
                await self._save_facts(article_id, facts_data, chunks)

        except Exception as exc:
            logger.exception("AI-анализ статьи %d провалился", article_id)
            analysis.status = AnalysisStatus.ERROR
            analysis.error = str(exc)

        await self.db.flush()

        return analysis

    async def _save_facts(
        self, article_id: int, facts_data: list[dict],
        chunks: list[KnowledgeChunk] | None = None,
    ) -> int:
        """Парсинг и сохранение фактов из ответа AI."""
        saved = 0
        for f in facts_data:
            try:
                predicate_str = f.get("predicate", "")
                predicate = PREDICATE_MAP.get(predicate_str)
                if not predicate:
                    logger.warning("Unknown predicate: %s", predicate_str)
                    continue

                subject_type_str = f.get("subject_type", "")
                subject_type = SUBJECT_TYPE_MAP.get(subject_type_str)
                if not subject_type:
                    continue

                object_type_str = f.get("object_type", "literal")
                object_type = OBJECT_TYPE_MAP.get(object_type_str, FactObjectType.LITERAL)

                source_text = (f.get("source_text") or "")[:2000]
                source_hash = hashlib.sha256(source_text.encode()).hexdigest()[:64] if source_text else None

                # Привязка к чанку
                chunk_id = None
                if chunks and source_text:
                    chunk_id = _find_chunk_for_text(source_text, chunks)

                fact = KnowledgeFact(
                    article_id=article_id,
                    subject_type=subject_type,
                    subject_name=(f.get("subject") or "")[:200],
                    predicate=predicate,
                    object_type=object_type,
                    object_name=(f.get("object") or "")[:500],
                    params=f.get("params", {}),
                    source_text=source_text or None,
                    confidence=min(max(float(f.get("confidence", 0.3)), 0.0), 1.0),
                    status=FactStatus.CANDIDATE,
                    source_hash=source_hash,
                    chunk_id=chunk_id,
                )
                self.db.add(fact)
                saved += 1
            except Exception as e:
                logger.warning("Failed to save fact: %s — %s", f, e)
                continue

        await self.db.flush()
        logger.info("Saved %d facts for article %d", saved, article_id)
        return saved

    async def get_analysis(self, article_id: int) -> ArticleAnalysis | None:
        return await self.db.scalar(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        )

    async def get_unanalyzed_ids(self, limit: int = 50) -> list[int]:
        analyzed = select(ArticleAnalysis.article_id)
        stmt = (
            select(KnowledgeArticle.id)
            .where(
                ~KnowledgeArticle.id.in_(analyzed),
            )
            .limit(limit)
        )
        rows = (await self.db.scalars(stmt)).all()
        return list(rows)
