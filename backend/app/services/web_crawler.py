"""Web Crawler — парсинг сайтов конкурентов.

Поддерживает:
    - Статические HTML-страницы (httpx + beautifulsoup4)
    - JS-рендеренные страницы (Playwright — опционально)
    - Sitemap.xml для обнаружения всех URL
    - Извлечение контента (заголовки, текст, таблицы, изображения)
"""

import logging
import re
from urllib.parse import urljoin, urlparse
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .knowledge_pipeline import CrawlResult, SourceType

logger = logging.getLogger(__name__)

# Конфигурация сайтов конкурентов
COMPETITOR_CONFIG: dict[str, dict[str, Any]] = {
    "ijiza": {
        "base_url": "https://ijiza.ru",
        "sitemap": "https://ijiza.ru/sitemap.xml",
        "catalog": "https://ijiza.ru/catalog",
        "use_playwright": True,
        "selectors": {
            "product_title": "h1, .product-title, .catalog-item-title",
            "product_description": ".product-description, .catalog-item-description, .content",
            "specs_table": "table, .product-specs, .characteristics",
            "article": "article, .article, .post, .content",
        },
    },
    "mauting": {
        "base_url": "https://www.mauting.com",
        "sitemap": None,
        "use_playwright": False,
        "selectors": {
            "product_title": "h1",
            "product_description": ".product-description, .description, .content",
            "specs_table": "table, .specifications",
        },
    },
    "fessmann": {
        "base_url": "https://www.fessmann.com",
        "sitemap": None,
        "use_playwright": False,
        "selectors": {
            "product_title": "h1",
            "product_description": ".product-text, .description, main",
            "specs_table": "table",
        },
    },
    "kerres": {
        "base_url": "https://www.kerres.de",
        "sitemap": None,
        "use_playwright": False,
        "selectors": {
            "product_title": "h1",
            "product_description": ".product-description, .text, main",
            "specs_table": "table, .technical-data",
        },
    },
    "agros": {
        "base_url": "https://agros.su",
        "sitemap": None,
        "use_playwright": False,
        "selectors": {
            "product_title": "h1",
            "product_description": "main, .content, .description",
            "specs_table": "table",
        },
    },
}


def _clean_text(html: str) -> str:
    """Очистить HTML от скриптов, стилей, лишних пробелов."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _extract_tables(soup: BeautifulSoup) -> list[list[list[str]]]:
    """Извлечь таблицы из HTML."""
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Извлечь изображения из HTML."""
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            images.append({
                "url": urljoin(base_url, src),
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
            })
    return images


class WebCrawler:
    """Краулер веб-сайтов. HTTP-only (без JS). Для JS использует playwright."""

    def __init__(self, timeout: int = 30):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )

    async def crawl(self, url: str, source_type: SourceType = SourceType.WEB) -> CrawlResult:
        """Скраулить URL."""
        result = CrawlResult(source_type=source_type, source_url=url)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            result.raw_html = response.text
            result.metadata["status_code"] = response.status_code
            result.metadata["content_type"] = response.headers.get("content-type", "")
            result.metadata["final_url"] = str(response.url)

            soup = BeautifulSoup(response.text, "lxml")
            result.raw_text = _clean_text(response.text)
            result.tables = _extract_tables(soup)
            result.images = _extract_images(soup, str(response.url))

            title = soup.find("title")
            if title:
                result.metadata["title"] = title.get_text(strip=True)

            desc = soup.find("meta", attrs={"name": "description"})
            if desc:
                result.metadata["description"] = desc.get("content", "")

        except httpx.HTTPStatusError as e:
            result.errors.append(f"HTTP {e.response.status_code}: {url}")
        except httpx.RequestError as e:
            result.errors.append(f"RequestError: {e}")
        except Exception as e:
            result.errors.append(f"Unexpected: {e}")

        return result

    async def crawl_sitemap(self, sitemap_url: str) -> list[str]:
        """Распарсить sitemap.xml и вернуть список URL."""
        urls = []
        try:
            response = await self._client.get(sitemap_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "xml")
            for loc in soup.find_all("loc"):
                url = loc.get_text(strip=True)
                if url:
                    urls.append(url)
        except Exception as e:
            logger.warning(f"Sitemap parse error {sitemap_url}: {e}")
        return urls

    async def crawl_competitor(self, name: str) -> list[CrawlResult]:
        """Скраулить все страницы конкурента по его конфигу."""
        config = COMPETITOR_CONFIG.get(name)
        if not config:
            raise ValueError(f"Неизвестный конкурент: {name}")

        base = config["base_url"]
        sitemap_url = config.get("sitemap")
        urls_to_crawl = [base]

        if sitemap_url:
            sitemap_urls = await self.crawl_sitemap(sitemap_url)
            urls_to_crawl.extend(sitemap_urls[:50])

        results = []
        for url in urls_to_crawl[:50]:
            result = await self.crawl(url)
            results.append(result)

        return results

    async def close(self):
        await self._client.aclose()
