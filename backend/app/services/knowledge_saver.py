"""Knowledge Saver — сохранение извлечённых знаний в БД.

Превращает ExtractedData → SQLAlchemy модели (KnowledgeArticle, CompetitorModel, etc).
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeArticle, ArticleCategory
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
from .knowledge_pipeline import ExtractedData

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Простой slug из текста."""
    import re
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:200] or "untitled"


_CATEGORY_MAP: dict[str, ArticleCategory] = {
    "product": ArticleCategory.REVIEW,
    "recipe": ArticleCategory.RECIPE,
    "article": ArticleCategory.GUIDE,
    "theory": ArticleCategory.THEORY,
    "troubleshooting": ArticleCategory.TROUBLESHOOTING,
    "comparison": ArticleCategory.COMPARISON,
    "news": ArticleCategory.NEWS,
}


class KnowledgeSaver:
    """Сохранение данных в БД."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_article(self, data: ExtractedData) -> KnowledgeArticle | None:
        """Сохранить одну статью."""
        if not data.title:
            logger.warning("Empty title, skipping")
            return None

        # Проверяем дубликат по source_url
        if data.source_url:
            existing = await self._session.execute(
                select(KnowledgeArticle).where(KnowledgeArticle.source_url == data.source_url)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Duplicate article skipped: {data.source_url}")
                return None

        slug = _slugify(data.title)
        # Уникализируем slug
        counter = 1
        while True:
            existing = await self._session.execute(
                select(KnowledgeArticle).where(KnowledgeArticle.slug == slug)
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{_slugify(data.title)}-{counter}"
            counter += 1

        category = _CATEGORY_MAP.get(data.category, ArticleCategory.GUIDE)

        article = KnowledgeArticle(
            title=data.title,
            slug=slug,
            body_md=data.body_md or data.excerpt or "",
            excerpt=data.excerpt[:1000] if data.excerpt else None,
            category=category,
            tags=data.tags,
            chamber_model=data.chamber_model,
            source_url=data.source_url,
            is_published=False,
        )

        self._session.add(article)
        await self._session.commit()
        await self._session.refresh(article)
        logger.info(f"Saved article {article.id}: {article.title}")
        return article

    async def save_competitor_model(self, competitor_name: str, data: ExtractedData) -> CompetitorModel | None:
        """Сохранить модель конкурента."""
        if not data.chamber_model:
            return None

        # Находим или создаём Competitor
        result = await self._session.execute(
            select(Competitor).where(Competitor.slug == _slugify(competitor_name))
        )
        competitor = result.scalar_one_or_none()
        if not competitor:
            competitor = Competitor(
                slug=_slugify(competitor_name),
                name=competitor_name,
            )
            self._session.add(competitor)
            await self._session.flush()

        # Извлекаем характеристики
        specs = data.specs or {}
        model = CompetitorModel(
            competitor_id=competitor.id,
            name=data.chamber_model,
            max_load_kg=specs.get("max_load_kg") or specs.get("load"),
            power_kw=specs.get("power_kw") or specs.get("power"),
            voltage_v=specs.get("voltage_v") or specs.get("voltage"),
            weight_kg=specs.get("weight_kg") or specs.get("weight"),
            dimensions=specs.get("dimensions"),
            description=data.body_md[:2000] if data.body_md else None,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        logger.info(f"Saved competitor model {model.id}: {model.name}")
        return model

    async def save_batch(self, items: list[ExtractedData], source_name: str = "") -> dict[str, int]:
        """Сохранить пачку извлечённых данных. Возвращает счётчики."""
        counts = {"articles": 0, "models": 0, "errors": 0}
        for item in items:
            try:
                article = await self.save_article(item)
                if article:
                    counts["articles"] += 1

                if item.chamber_model:
                    model = await self.save_competitor_model(source_name, item)
                    if model:
                        counts["models"] += 1

            except Exception as e:
                logger.exception(f"Save error for {item.title}: {e}")
                counts["errors"] += 1

        return counts
