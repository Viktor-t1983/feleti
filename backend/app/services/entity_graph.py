"""Knowledge Graph — построение и запрос графа связей между сущностями.

Извлекает из ArticleAnalysis упоминания продуктов, конкурентов, оборудования
и создаёт явные связи (EntityLink) в базе данных.
"""
from __future__ import annotations

import logging
import re

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.competitor import Competitor
from app.models.entity_link import EntityLink
from app.models.knowledge import ArticleAnalysis, KnowledgeArticle
from app.models.product import Product

logger = logging.getLogger(__name__)

# Типы сущностей
SOURCE_ARTICLE = "article"
TARGET_PRODUCT = "product"
TARGET_COMPETITOR = "competitor"
TARGET_CHAMBER = "chamber"
TARGET_MANUFACTURER = "manufacturer"
TARGET_TOPIC = "topic"

REL_MENTIONS = "mentions"
REL_DISCUSSES = "discusses"
REL_COMPARES = "compares"
REL_DESCRIBES = "describes"


def _normalize(name: str) -> str:
    """Lowercase, strip, remove extra spaces."""
    return re.sub(r"\s+", " ", name.strip().lower())


def _match_by_name(
    names: list[str],
    db_rows: list,
    name_attr: str = "name",
    threshold: float = 0.6,
) -> list[int]:
    """Match list of names against DB rows by substring similarity."""
    ids: list[int] = []
    norm_names = [_normalize(n) for n in names if n]
    for row in db_rows:
        row_name = _normalize(getattr(row, name_attr))
        for nn in norm_names:
            # exact match or one contains the other
            if nn == row_name or (len(nn) > 3 and (nn in row_name or row_name in nn)):
                ids.append(row.id)
                break
    return ids


async def build_entity_links(article_id: int) -> int:
    """Parse ArticleAnalysis for article_id and create EntityLink rows.
    Returns the number of links created.
    """
    async with AsyncSessionLocal() as db:
        article = await db.get(KnowledgeArticle, article_id)
        if not article:
            logger.warning("Article %d not found", article_id)
            return 0

        analysis = await db.scalar(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        )
        if not analysis:
            logger.info("No analysis for article %d, skipping graph", article_id)
            return 0

        # Remove old links for this article
        await db.execute(
            delete(EntityLink).where(
                EntityLink.source_type == SOURCE_ARTICLE,
                EntityLink.source_id == article_id,
            )
        )

        links: list[EntityLink] = []

        # 1. Link products from analysis.products
        if analysis.products:
            products_result = await db.execute(select(Product))
            product_ids = _match_by_name(analysis.products, products_result.scalars().all())
            for pid in product_ids:
                links.append(EntityLink(
                    source_type=SOURCE_ARTICLE, source_id=article_id,
                    target_type=TARGET_PRODUCT, target_id=pid,
                    relation=REL_MENTIONS,
                ))

        # 2. Link competitors from analysis.competitor_mentions
        if analysis.competitor_mentions:
            mention_names = [
                m.get("name", "") for m in analysis.competitor_mentions if isinstance(m, dict)
            ]
            if mention_names:
                comps_result = await db.execute(select(Competitor))
                comp_ids = _match_by_name(mention_names, comps_result.scalars().all())
                for cid in comp_ids:
                    links.append(EntityLink(
                        source_type=SOURCE_ARTICLE, source_id=article_id,
                        target_type=TARGET_COMPETITOR, target_id=cid,
                        relation=REL_COMPARES,
                    ))

        # 3. Link equipment → Chamber (by chamber_model or equipment names)
        if analysis.equipment:
            for eq in analysis.equipment:
                if isinstance(eq, dict):
                    eq_name = eq.get("name", "") or eq.get("model", "")
                    if eq_name:
                        chamber = await db.scalar(
                            select(KnowledgeArticle.chamber_model).where(
                                KnowledgeArticle.id == article_id
                            )
                        )
                        if chamber and _normalize(eq_name) in _normalize(chamber):
                            # We can't directly link to Chamber model from here easily,
                            # skip for now — Chamber linking needs chamber_id
                            pass

        # 4. Link manufacturer if article has manufacturer_id
        if article.manufacturer_id:
            links.append(EntityLink(
                source_type=SOURCE_ARTICLE, source_id=article_id,
                target_type=TARGET_MANUFACTURER, target_id=article.manufacturer_id,
                relation=REL_DISCUSSES,
            ))

        # 5. Link competitor if article has competitor_id
        if article.competitor_id:
            links.append(EntityLink(
                source_type=SOURCE_ARTICLE, source_id=article_id,
                target_type=TARGET_COMPETITOR, target_id=article.competitor_id,
                relation=REL_DISCUSSES,
            ))

        # Bulk create
        for link in links:
            db.add(link)

        await db.commit()
        count = len(links)
        logger.info("Created %d entity links for article %d", count, article_id)
        return count
