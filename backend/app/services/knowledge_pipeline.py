"""Knowledge Pipeline — единый сборщик знаний о продуктах и технологиях копчения.

Архитектура:
    Source (web/yt/pdf/tg) → Crawler → Raw (dict) → Extractor (LLM/rule) → KnowledgeArticle/CompetitorModel/Recipe

Поток:
    1. Pipeline.run(source) — запускает парсинг источника
    2. Crawler забирает сырые данные (HTML/текст/метаданные)
    3. Extractor превращает сырые данные в структуру
    4. Структура сохраняется в БД (KnowledgeArticle, CompetitorModel, Recipe etc.)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    WEB = "web"
    YOUTUBE = "youtube"
    PDF = "pdf"
    TELEGRAM = "telegram"


class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CrawlResult:
    """Сырой результат краулера — что достали из источника."""
    source_type: SourceType
    source_url: str
    raw_text: str = ""
    raw_html: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    images: list[dict] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    crawled_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExtractedData:
    """Структурированные данные, готовые к сохранению в БД."""
    title: str = ""
    body_md: str = ""
    excerpt: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    source_url: str = ""
    manufacturer: str = ""
    chamber_model: str = ""
    recipes: list[dict] = field(default_factory=list)
    problems: list[dict] = field(default_factory=list)
    specs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class Crawler(Protocol):
    """Интерфейс краулера источника."""
    async def crawl(self, url: str) -> CrawlResult: ...


class Extractor(Protocol):
    """Интерфейс экстрактора — сырой текст → структура."""
    async def extract(self, raw: CrawlResult) -> list[ExtractedData]: ...


class KnowledgePipeline:
    """Главный координатор сбора знаний."""

    def __init__(self):
        self._status: dict[str, PipelineStatus] = {}
        self._results: dict[str, list[ExtractedData]] = {}

    @property
    def status(self) -> dict[str, PipelineStatus]:
        return dict(self._status)

    async def run(self, source_type: SourceType, url: str, crawler: Crawler, extractor: Extractor) -> list[ExtractedData]:
        """Запустить полный цикл: crawl → extract."""
        key = f"{source_type.value}:{url}"
        self._status[key] = PipelineStatus.RUNNING
        logger.info(f"Pipeline: запуск {key}")

        try:
            raw = await crawler.crawl(url)
            if raw.errors:
                logger.warning(f"Pipeline: ошибки краулера {key}: {raw.errors}")

            extracted = await extractor.extract(raw)
            self._results[key] = extracted
            self._status[key] = PipelineStatus.COMPLETED
            logger.info(f"Pipeline: завершён {key} → {len(extracted)} объектов")
            return extracted

        except Exception as e:
            logger.exception(f"Pipeline: ошибка {key}: {e}")
            self._status[key] = PipelineStatus.FAILED
            raise

    async def run_batch(self, tasks: list[tuple[SourceType, str, Crawler, Extractor]]) -> dict[str, list[ExtractedData]]:
        """Запустить несколько источников параллельно."""
        coros = [self.run(st, url, c, e) for st, url, c, e in tasks]
        results = await asyncio.gather(*coros, return_exceptions=True)
        output: dict[str, list[ExtractedData]] = {}
        for (st, url, _, _), result in zip(tasks, results):
            key = f"{st.value}:{url}"
            if isinstance(result, Exception):
                logger.error(f"Pipeline batch: {key} упал: {result}")
                output[key] = []
            else:
                output[key] = result
        return output

    def get_results(self, key: str | None = None) -> dict[str, list[ExtractedData]]:
        if key:
            return {key: self._results.get(key, [])}
        return dict(self._results)


# Singleton
_pipeline: KnowledgePipeline | None = None


def get_pipeline() -> KnowledgePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = KnowledgePipeline()
    return _pipeline
