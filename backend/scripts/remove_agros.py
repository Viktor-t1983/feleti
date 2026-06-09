"""Remove Agros competitor + its articles from DB."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.models.competitor import Competitor
from app.models.knowledge import KnowledgeArticle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    async with AsyncSessionLocal() as s:
        agros = await s.scalar(select(Competitor).where(Competitor.slug == "agros"))
        if agros is None:
            logger.info("Agros not found in DB")
            return

        articles = (
            await s.scalars(
                select(KnowledgeArticle).where(KnowledgeArticle.competitor_id == agros.id)
            )
        ).all()
        logger.info("Agros articles: %d", len(articles))

        for a in articles:
            await s.delete(a)

        # Delete competitor models and problems (cascade)
        await s.delete(agros)
        await s.commit()
        logger.info("Agros removed: competitor + %d articles", len(articles))

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
