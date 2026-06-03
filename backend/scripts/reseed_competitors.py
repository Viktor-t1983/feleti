import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
from app.scripts.seed import seed_competitors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

async def main():
    async with AsyncSessionLocal() as session:
        # Delete all competitors (cascade deletes models and problems)
        result = await session.execute(delete(Competitor))
        logger.info(f"Deleted {result.rowcount} competitors")
        await session.commit()
        
        # Re-seed
        competitors = await seed_competitors(session)
        logger.info(f"Created {len(competitors)} competitors")
        await session.commit()
        
        # Refresh with eager loading to count relationships
        for c in competitors:
            await session.refresh(c, attribute_names=["models", "problems"])
            logger.info(f"  {c.name}: {len(c.models)} models, {len(c.problems)} problems")
        
        logger.info("=== Competitors re-seeded ===")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
