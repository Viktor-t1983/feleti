"""Knowledge Collector — оркестратор сбора знаний.

Принимает запрос, определяет источники, запускает краулеры параллельно,
извлекает структуру, сохраняет статьи. SSE-прогресс.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.knowledge import ArticleTopic, KnowledgeArticle
from app.services.knowledge_pipeline import (
    CrawlResult,
    ExtractedData,
    KnowledgePipeline,
    SourceType,
    get_pipeline,
)
from app.services.web_crawler import WebCrawler
from app.services.llm_extractor import LlmExtractor
from app.services.article_analyzer import ArticleAnalyzer

logger = logging.getLogger(__name__)


class CollectionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CollectionJob:
    """Задача на сбор знаний."""

    def __init__(
        self,
        query: str,
        source_types: list[SourceType] | None = None,
        topic_ids: list[int] | None = None,
        max_results: int = 20,
    ):
        self.id: str = uuid.uuid4().hex[:12]
        self.query: str = query
        self.source_types: list[SourceType] = source_types or [SourceType.WEB]
        self.topic_ids: list[int] | None = topic_ids
        self.max_results: int = max_results
        self.status: CollectionStatus = CollectionStatus.PENDING
        self.total: int = 0
        self.processed: int = 0
        self.skipped: int = 0
        self.created: list[int] = []
        self.errors: list[str] = []
        self.created_at: datetime = datetime.utcnow()


ProgressCallback = Callable[[CollectionJob], None]


class KnowledgeCollector:
    """Оркестратор сбора знаний."""

    def __init__(self):
        self._jobs: dict[str, CollectionJob] = {}
        self._callbacks: list[ProgressCallback] = []

    def on_progress(self, cb: ProgressCallback) -> None:
        self._callbacks.append(cb)

    def _notify(self, job: CollectionJob) -> None:
        for cb in self._callbacks:
            try:
                cb(job)
            except Exception:
                logger.exception("Callback error")

    def get_job(self, job_id: str) -> CollectionJob | None:
        return self._jobs.get(job_id)

    async def collect(self, query: str, source_types: list[SourceType] | None = None,
                      topic_ids: list[int] | None = None, max_results: int = 20) -> CollectionJob:
        """Запустить сбор знаний."""
        job = CollectionJob(query, source_types, topic_ids, max_results)
        self._jobs[job.id] = job
        asyncio.create_task(self._run(job))
        return job

    async def _run(self, job: CollectionJob) -> None:
        """Выполнить сбор (фоновый таск)."""
        job.status = CollectionStatus.RUNNING
        self._notify(job)

        try:
            crawler = WebCrawler()
            extractor = LlmExtractor()
            analyzer = ArticleAnalyzer()
            pipeline = get_pipeline()

            urls = await self._resolve_sources(job)
            job.total = len(urls)
            self._notify(job)

            if not urls:
                job.status = CollectionStatus.COMPLETED
                self._notify(job)
                return

            sem = asyncio.Semaphore(3)

            async def process(source_type: SourceType, url: str) -> None:
                async with sem:
                    try:
                        raw = await crawler.crawl(url, source_type)
                        if not raw.errors and len(raw.raw_text) > 100:
                            extracted_list = await extractor.extract(raw)
                            for extracted in extracted_list[:3]:
                                article_id = await self._save_article(extracted, job, analyzer)
                                if article_id:
                                    job.created.append(article_id)
                                else:
                                    job.skipped += 1
                        else:
                            job.skipped += 1
                    except Exception as e:
                        job.errors.append(f"{url}: {e}")
                        job.skipped += 1
                    finally:
                        job.processed += 1
                        self._notify(job)

            tasks = [process(st, url) for st, url in urls]
            await asyncio.gather(*tasks, return_exceptions=True)

            job.status = CollectionStatus.COMPLETED
        except Exception as e:
            logger.exception("Collector failed")
            job.errors.append(str(e))
            job.status = CollectionStatus.FAILED

        self._notify(job)

    async def _resolve_sources(self, job: CollectionJob) -> list[tuple[SourceType, str]]:
        """Определить URL для сбора по запросу."""
        results: list[tuple[SourceType, str]] = []
        q = job.query.strip().lower()

        if SourceType.WEB in job.source_types:
            sites = [
                f"https://vseokopchenii.ru/?s={q}",
                f"https://smokehouse.ru/?s={q}",
            ]
            if "рыб" in q or "осётр" in q or "скумбр" in q:
                sites.append(f"https://vniro.ru/search?q={q}")
            if "мяс" in q or "свин" in q or "говяд" in q:
                sites.append(f"https://vniimp.ru/search?q={q}")
            if "коптильн" in q or "камер" in q:
                sites.append(f"https://feleti.ru/search?q={q}")
            if "рецепт" in q:
                sites.append(f"https://eda.ru/search?q={q}")
            if "проблем" in q or "гореч" in q or "плесен" in q:
                sites.append(f"https://meatclub.ru/search?q={q}")

            for url in sites:
                results.append((SourceType.WEB, url))

        if SourceType.YOUTUBE in job.source_types:
            results.append((SourceType.YOUTUBE, f"ytsearch:{q}"))

        return results[:job.max_results]

    async def _save_article(self, extracted: ExtractedData, job: CollectionJob,
                            analyzer: ArticleAnalyzer) -> int | None:
        """Сохранить извлечённые данные как KnowledgeArticle."""
        if not extracted.title or not extracted.body_md:
            return None

        async with AsyncSessionLocal() as db:
            try:
                # проверка дубликата по URL
                if extracted.source_url:
                    existing = await db.scalar(
                        select(KnowledgeArticle).where(
                            KnowledgeArticle.source_url == extracted.source_url
                        ).limit(1)
                    )
                    if existing:
                        logger.info("Дубликат (URL): %s", extracted.source_url)
                        return None

                article = KnowledgeArticle(
                    title=extracted.title[:500],
                    slug=self._slugify(extracted.title)[:500],
                    body_md=extracted.body_md,
                    excerpt=extracted.excerpt[:500] if extracted.excerpt else None,
                    category=extracted.category or "theory",
                    tags=extracted.tags,
                    source_url=extracted.source_url or "",
                    is_published=True,
                )
                db.add(article)
                await db.flush()

                # привязка к темам
                if job.topic_ids:
                    for tid in job.topic_ids:
                        db.add(ArticleTopic(article_id=article.id, topic_id=tid))

                await db.commit()
                await db.refresh(article)

                # AI-анализ в фоне
                try:
                    await analyzer.analyze(article.id)
                except Exception:
                    logger.exception("AI-анализ не удался для статьи %d", article.id)

                return article.id
            except Exception as e:
                await db.rollback()
                logger.error("Ошибка сохранения статьи: %s", e)
                return None

    @staticmethod
    def _slugify(text: str) -> str:
        import re
        s = text.lower().strip()
        s = re.sub(r"[^a-z0-9а-яё\s-]", "", s)
        s = re.sub(r"\s+", "-", s)
        s = re.sub(r"-+", "-", s)
        s = s.strip("-")
        if not s:
            s = "article"
        return s


# Singleton
_collector: KnowledgeCollector | None = None


def get_collector() -> KnowledgeCollector:
    global _collector
    if _collector is None:
        _collector = KnowledgeCollector()
    return _collector
