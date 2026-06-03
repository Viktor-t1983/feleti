"""Запуск первого парсинга конкурентов через Knowledge Pipeline.

Использование (из контейнера):
    docker compose exec backend python -m app.scripts.crawl_competitors --name ijiza
    docker compose exec backend python -m app.scripts.crawl_competitors --name all

Парсинг синхронный (без Celery), сохраняет в БД.
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawl_competitors")

# Список конкурентов для парсинга
COMPETITORS = {
    "ijiza": {
        "sitemap": "https://ijiza.ru/sitemap.xml",
        "base_url": "https://ijiza.ru",
        "max_pages": 50,
    },
    "mauting": {
        "sitemap": None,
        "base_url": "https://www.mauting.com",
        "max_pages": 20,
    },
    "fessmann": {
        "sitemap": None,
        "base_url": "https://www.fessmann.com",
        "max_pages": 20,
    },
    "kerres": {
        "sitemap": None,
        "base_url": "https://www.kerres.de",
        "max_pages": 20,
    },
}


async def crawl_competitor(name: str, config: dict) -> dict:
    """Скраулить конкурента и сохранить в БД."""
    from app.db.session import AsyncSessionLocal
    from app.services.web_crawler import WebCrawler
    from app.services.llm_extractor import LlmExtractor
    from app.services.knowledge_saver import KnowledgeSaver

    logger.info(f"=== Парсинг {name} ===")

    urls_to_crawl = [config["base_url"]]

    crawler = WebCrawler()

    # Sitemap
    if config.get("sitemap"):
        logger.info(f"Скачиваю sitemap: {config['sitemap']}")
        sitemap_urls = await crawler.crawl_sitemap(config["sitemap"])
        logger.info(f"Найдено URL в sitemap: {len(sitemap_urls)}")
        urls_to_crawl.extend(sitemap_urls[: config["max_pages"]])

    # Краулим
    all_extracted = []
    for i, url in enumerate(urls_to_crawl):
        logger.info(f"[{i+1}/{len(urls_to_crawl)}] Краулю: {url}")
        try:
            raw = await crawler.crawl(url)
            if raw.errors:
                logger.warning(f"  Ошибки: {raw.errors}")

            # Rule-based extraction (без LLM)
            from app.services.llm_extractor import _extract_by_rules
            extracted = _extract_by_rules(raw)

            # Добавляем производителя
            for item in extracted:
                item.manufacturer = name.title()

            all_extracted.extend(extracted)
            logger.info(f"  → {len(extracted)} объектов извлечено")

        except Exception as e:
            logger.error(f"  Ошибка краулинга {url}: {e}")
            continue

    await crawler.close()

    # Сохраняем в БД
    logger.info(f"Сохраняю {len(all_extracted)} объектов в БД...")
    async with AsyncSessionLocal() as session:
        saver = KnowledgeSaver(session)
        result = await saver.save_batch(all_extracted, source_name=name)
        await session.commit()

    logger.info(f"Сохранено: {result}")
    return result


async def main():
    parser = argparse.ArgumentParser(description="Парсинг конкурентов")
    parser.add_argument(
        "--name",
        choices=list(COMPETITORS.keys()) + ["all"],
        default="ijiza",
        help="Конкурент для парсинга (all — все)",
    )
    args = parser.parse_args()

    start = datetime.now()

    if args.name == "all":
        results = {}
        for name, config in COMPETITORS.items():
            try:
                result = await crawl_competitor(name, config)
                results[name] = result
            except Exception as e:
                logger.exception(f"{name} упал: {e}")
                results[name] = {"errors": str(e)}

        total_articles = sum(r.get("articles", 0) for r in results.values())
        total_models = sum(r.get("models", 0) for r in results.values())
        total_errors = sum(r.get("errors", 0) for r in results.values())
        logger.info(
            f"\n=== ИТОГО ==="
            f"\nСтатей: {total_articles}"
            f"\nМоделей: {total_models}"
            f"\nОшибок: {total_errors}"
            f"\nВремя: {datetime.now() - start}"
        )
    else:
        result = await crawl_competitor(args.name, COMPETITORS[args.name])
        elapsed = datetime.now() - start
        logger.info(
            f"\n=== {args.name.title()} ==="
            f"\nСтатей: {result.get('articles', 0)}"
            f"\nМоделей: {result.get('models', 0)}"
            f"\nОшибок: {result.get('errors', 0)}"
            f"\nВремя: {elapsed}"
        )


if __name__ == "__main__":
    asyncio.run(main())
