"""PDF Parser — парсинг PDF-каталогов и техпаспортов конкурентов.

Поддерживает:
    - Извлечение текста (pdfplumber)
    - Извлечение таблиц (pdfplumber)
    - Извлечение изображений (pymupdf — опционально)
"""

import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from .knowledge_pipeline import CrawlResult, SourceType

logger = logging.getLogger(__name__)


class PdfParser:
    """Парсинг PDF-документов."""

    def __init__(self, output_dir: str = "data/pdf"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def crawl(self, url: str) -> CrawlResult:
        """Скачать PDF по URL и распарсить."""
        result = CrawlResult(source_type=SourceType.PDF, source_url=url)

        # Скачиваем
        import httpx
        filename = url.split("/")[-1] or "document.pdf"
        filepath = self._output_dir / filename

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                filepath.write_bytes(resp.content)
                result.metadata["file_size"] = len(resp.content)
                result.metadata["filename"] = filename
        except Exception as e:
            result.errors.append(f"Download error: {e}")
            return result

        # Парсим
        return await self.parse_file(filepath, url)

    async def parse_file(self, filepath: Path, source_url: str = "") -> CrawlResult:
        """Распарсить локальный PDF-файл."""
        result = CrawlResult(
            source_type=SourceType.PDF,
            source_url=source_url or str(filepath),
        )
        result.metadata["filename"] = filepath.name

        try:
            import pdfplumber

            with pdfplumber.open(filepath) as pdf:
                text_parts = []
                tables = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                    page_tables = page.extract_tables()
                    for table in page_tables:
                        rows = []
                        for row in table:
                            rows.append([str(c or "") for c in row])
                        if rows:
                            tables.append(rows)

                result.raw_text = "\n".join(text_parts)
                result.tables = tables
                result.metadata["page_count"] = len(pdf.pages)
                result.metadata["parsed_at"] = datetime.utcnow().isoformat()

        except ImportError:
            result.errors.append("pdfplumber not installed")
        except Exception as e:
            result.errors.append(f"PDF parse error: {e}")

        return result

    async def crawl_competitor_catalog(self, urls: list[str]) -> list[CrawlResult]:
        """Скачать и распарсить несколько PDF."""
        results = []
        for url in urls:
            result = await self.crawl(url)
            results.append(result)
        return results
