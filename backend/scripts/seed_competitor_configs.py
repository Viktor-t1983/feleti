"""Seed existing COMPETITOR_CONFIG into DB."""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.models.competitor import Competitor
from app.services.web_crawler import COMPETITOR_CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NAME_MAP = {
    "ijiza": "Izhitsa",
    "mauting": "Mauting",
    "fessmann": "Fessmann",
    "kerres": "Kerres",
    "sorgo": "Sorgo Anlagenbau",
    "bastra": "Bastra",
    "agros": "Agros",
}


async def main():
    async with AsyncSessionLocal() as session:
        try:
            for slug, cfg in COMPETITOR_CONFIG.items():
                existing = await session.scalar(
                    select(Competitor).where(Competitor.slug == slug)
                )
                if existing:
                    existing.base_url = cfg["base_url"]
                    existing.sitemap_url = cfg.get("sitemap")
                    existing.crawl_config = {
                        "use_playwright": cfg.get("use_playwright", False),
                        "max_pages": cfg.get("max_pages", 50),
                        "selectors": cfg.get("selectors", {}),
                    }
                    if existing.crawl_status == "pending":
                        existing.crawl_status = "done"
                    logger.info("Updated: %s", slug)
                else:
                    competitor = Competitor(
                        slug=slug,
                        name=NAME_MAP.get(slug, slug.capitalize()),
                        base_url=cfg["base_url"],
                        sitemap_url=cfg.get("sitemap"),
                        crawl_config={
                            "use_playwright": cfg.get("use_playwright", False),
                            "max_pages": cfg.get("max_pages", 50),
                            "selectors": cfg.get("selectors", {}),
                        },
                        crawl_status="done",
                        is_main_competitor=False,
                        articles_count=0,
                    )
                    session.add(competitor)
                    logger.info("Created: %s", slug)

            await session.commit()
            logger.info("=== Seed completed ===")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed")
            raise
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
