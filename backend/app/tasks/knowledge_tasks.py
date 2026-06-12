"""Knowledge Pipeline — Celery-задачи для асинхронного сбора знаний.

Каждая задача:
    1. Краулит источник (веб/YouTube/PDF/Telegram)
    2. Извлекает структуру (LLM или rules)
    3. Сохраняет в БД
"""

import asyncio
import logging

from celery import shared_task

from app.db.session import AsyncSessionLocal
from app.services.knowledge_pipeline import SourceType, get_pipeline
from app.services.web_crawler import WebCrawler
from app.services.llm_extractor import LlmExtractor
from app.services.youtube_transcriber import YouTubeTranscriber
from app.services.pdf_parser import PdfParser
from app.services.knowledge_saver import KnowledgeSaver
from app.services.article_analyzer import ArticleAnalyzer

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Запустить асинхронную корутину в синхронной Celery-задаче."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _save_results(extracted: list, source_name: str = "") -> dict:
    """Сохранить результаты в БД через сессию."""
    async with AsyncSessionLocal() as session:
        saver = KnowledgeSaver(session)
        result = await saver.save_batch(extracted, source_name=source_name)
        await session.commit()
        return result


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_web(self, url: str, competitor_name: str = ""):
    """Скраулить веб-страницу и сохранить как статью."""
    logger.info(f"Task crawl_web: {url}")

    async def _run():
        async with WebCrawler() as crawler:
            raw = await crawler.crawl(url)

        extractor = LlmExtractor()
        extracted = await extractor.extract(raw)

        return await _save_results(extracted, source_name=competitor_name)

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception(f"Task crawl_web failed: {url}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def crawl_competitor(self, competitor_name: str):
    """Скраулить все страницы конкурента (по sitemap)."""
    logger.info(f"Task crawl_competitor: {competitor_name}")

    async def _run():
        async with WebCrawler() as crawler:
            results = await crawler.crawl_competitor(competitor_name)

        extractor = LlmExtractor()
        all_extracted = []
        for raw in results:
            extracted = await extractor.extract(raw)
            all_extracted.extend(extracted)

        result = await _save_results(all_extracted, source_name=competitor_name)
        return {"competitor": competitor_name, **result}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception(f"Task crawl_competitor failed: {competitor_name}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=300)
def transcribe_youtube(self, query: str, max_videos: int = 10):
    """Найти видео по запросу, скачать и транскрибировать."""
    logger.info(f"Task transcribe_youtube: {query} ({max_videos} videos)")

    async def _run():
        transcriber = YouTubeTranscriber()
        results = await transcriber.crawl_competitor(query, max_videos)

        extractor = LlmExtractor()
        all_extracted = []
        for raw in results:
            extracted = await extractor.extract(raw)
            all_extracted.extend(extracted)

        result = await _save_results(all_extracted, source_name=query)
        return {"query": query, **result}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception(f"Task transcribe_youtube failed: {query}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def parse_pdf(self, url: str, source_name: str = ""):
    """Скачать и распарсить PDF."""
    logger.info(f"Task parse_pdf: {url}")

    async def _run():
        parser = PdfParser()
        raw = await parser.crawl(url)

        extractor = LlmExtractor()
        extracted = await extractor.extract(raw)

        return await _save_results(extracted, source_name=source_name)

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception(f"Task parse_pdf failed: {url}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def analyze_article(self, article_id: int):
    """Запустить AI-анализ статьи и сохранить результат."""
    logger.info(f"Task analyze_article: {article_id}")

    async def _run():
        async with AsyncSessionLocal() as session:
            analyzer = ArticleAnalyzer(session)
            await analyzer.analyze(article_id)
            await session.commit()
            return {"article_id": article_id}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception(f"Task analyze_article failed: {article_id}")
        raise self.retry(exc=exc)


DEFAULT_COLLECT_QUERIES = [
    "копчение рыбы оборудование технологии",
    "копчение мяса технологии рецепты",
    "коптильные камеры промышленные оборудование",
    "проблемы копчения горечь плесень решения",
    "посол рыбы перед копчением рецепты",
]


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def collect_knowledge(self, query: str = "", topic_ids: list[int] | None = None):
    """Сбор знаний по запросу (плановый или ручной)."""
    from app.services.knowledge_collector import KnowledgeCollector

    logger.info(f"Task collect_knowledge: query='{query}' topic_ids={topic_ids}")

    async def _run():
        collector = KnowledgeCollector()
        job = await collector.collect(
            query=query,
            source_types=[SourceType.WEB, SourceType.YOUTUBE],
            topic_ids=topic_ids,
            max_results=15,
        )
        while job.status in ("pending", "running"):
            await asyncio.sleep(2)
        return {
            "job_id": job.id,
            "status": job.status.value,
            "total": job.total,
            "processed": job.processed,
            "created": len(job.created),
            "skipped": job.skipped,
            "errors": job.errors[:5],
        }

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception("Task collect_knowledge failed")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=600)
def scheduled_collect(self):
    """Плановый сбор знаний — выполняет все DEFAULT_COLLECT_QUERIES."""
    from app.services.knowledge_collector import KnowledgeCollector

    logger.info("Task scheduled_collect: starting scheduled knowledge collection")

    async def _run():
        results = []
        for q in DEFAULT_COLLECT_QUERIES:
            try:
                collector = KnowledgeCollector()
                job = await collector.collect(
                    query=q,
                    source_types=[SourceType.WEB, SourceType.YOUTUBE],
                    max_results=10,
                )
                while job.status in ("pending", "running"):
                    await asyncio.sleep(2)
                results.append({
                    "query": q,
                    "status": job.status.value,
                    "created": len(job.created),
                    "skipped": job.skipped,
                })
            except Exception as exc:
                results.append({"query": q, "error": str(exc)})
        return {"queries": len(results), "results": results}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.exception("Task scheduled_collect failed")
        raise self.retry(exc=exc)
