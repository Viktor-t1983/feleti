"""Сервис онбординга конкурентов: discovery → crawl → save."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competitor import Competitor
from app.models.knowledge import KnowledgeArticle, ArticleCategory
from app.schemas.competitor import CompetitorDiscoveredInfo, CompetitorOnboardResponse, CompetitorRead
from app.services.web_crawler import WebCrawler

logger = logging.getLogger(__name__)

SLUG_MAX_LENGTH = 100
MAX_SITEMAP_URLS = 200


def _url_to_slug(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = domain.replace("www.", "")
    slug_part = domain.split(".")[0] if "." in domain else domain
    slug = re.sub(r"[^a-z0-9-]", "", slug_part.lower())[:SLUG_MAX_LENGTH]
    return slug or "unknown"


def _domain_to_name(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = domain.replace("www.", "")
    name = domain.split(".")[0] if "." in domain else domain
    return name.capitalize()


def _make_article_slug(title: str, prefix: str) -> str:
    slug = re.sub(r"[^a-zA-Zа-яА-Я0-9-]", "-", title.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")[:80]
    return f"{prefix}-{slug}" if slug else f"{prefix}-article"


class CompetitorOnboarder:
    """Оркестратор: URL → разведка → краулинг → БД."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.crawler = WebCrawler()
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(15),
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    async def discover(self, url: str) -> CompetitorDiscoveredInfo:
        """Разведка сайта: достижимость, кодировка, title, sitemap."""
        parsed = urlparse(url)
        scheme = parsed.scheme or "https"
        base_url = f"{scheme}://{parsed.netloc}" if parsed.netloc else f"{scheme}://{parsed.path}"
        info = CompetitorDiscoveredInfo(
            name=_domain_to_name(base_url),
            slug=_url_to_slug(base_url),
            base_url=base_url,
        )

        try:
            resp = await self._http.get(base_url)
            resp.raise_for_status()
            info.encoding = resp.encoding
            soup = BeautifulSoup(resp.content, "lxml")

            title_tag = soup.find("title")
            if title_tag:
                info.title = title_tag.get_text(strip=True)

            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag:
                info.description = desc_tag.get("content", "")

            info.page_count = len(soup.find_all("a"))

            sitemap_urls = [
                urljoin(base_url, link.get("href"))
                for link in soup.find_all("a", href=True)
                if "sitemap" in link.get("href", "").lower()
            ]

            for candidate in sitemap_urls + [
                urljoin(base_url, "/sitemap.xml"),
                urljoin(base_url, "/sitemap_index.xml"),
            ]:
                try:
                    sresp = await self._http.get(candidate)
                    if sresp.status_code == 200 and "xml" in sresp.headers.get("content-type", ""):
                        info.sitemap_url = candidate
                        break
                except Exception:
                    continue

        except httpx.HTTPStatusError as e:
            info.error = f"HTTP {e.response.status_code}: {base_url}"
        except httpx.RequestError as e:
            info.error = f"RequestError: {e}"
        except Exception as e:
            info.error = f"Unexpected: {e}"

        return info

    async def onboard(self, url: str, name: str | None = None) -> CompetitorOnboardResponse:
        """Полный цикл онбординга: discovery → crawl → save."""
        info = await self.discover(url)
        if name:
            info.name = name
            info.slug = _url_to_slug(name)

        if info.error:
            raise ValueError(f"Сайт недоступен: {info.error}")

        slug = info.slug
        base_slug = slug
        counter = 1
        while await self.db.scalar(select(Competitor).where(Competitor.slug == slug)):
            slug = f"{base_slug}-{counter}"
            counter += 1

        competitor = Competitor(
            slug=slug,
            name=info.name,
            base_url=info.base_url,
            sitemap_url=info.sitemap_url,
            crawl_status="pending",
            is_main_competitor=False,
        )
        self.db.add(competitor)
        await self.db.flush()

        competitor.crawl_status = "crawling"
        await self.db.flush()
        await self.db.commit()

        articles_created = 0
        articles_skipped = 0

        try:
            urls_to_crawl = [info.base_url]
            if info.sitemap_url:
                sitemap_urls = await self.crawler.crawl_sitemap(info.sitemap_url)
                urls_to_crawl.extend(sitemap_urls[:MAX_SITEMAP_URLS])
                urls_to_crawl = urls_to_crawl[:MAX_SITEMAP_URLS]

            for page_url in urls_to_crawl:
                crawl_result = await self.crawler.crawl(page_url)
                if crawl_result.errors:
                    articles_skipped += 1
                    continue

                raw_text = crawl_result.raw_text or ""
                if len(raw_text) < 50:
                    articles_skipped += 1
                    continue

                title = crawl_result.metadata.get("title") or raw_text[:100].strip()
                article_slug = _make_article_slug(title, slug)

                try:
                    async with self.db.begin_nested():
                        existing = await self.db.scalar(
                            select(KnowledgeArticle).where(KnowledgeArticle.slug == article_slug)
                        )
                        if existing:
                            articles_skipped += 1
                            raise _SkipArticle

                        article = KnowledgeArticle(
                            title=title,
                            slug=article_slug,
                            body_md=raw_text,
                            category=ArticleCategory.REVIEW,
                            tags=[],
                            source_url=page_url,
                            competitor_id=competitor.id,
                            is_published=True,
                        )
                        self.db.add(article)
                    articles_created += 1
                except _SkipArticle:
                    continue
                except IntegrityError:
                    articles_skipped += 1
                    continue

            competitor.crawl_status = "done"
            competitor.articles_count = articles_created
            competitor.last_crawled_at = datetime.utcnow()
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            competitor.crawl_status = "error"
            competitor.crawl_error = str(e)
            await self.db.commit()
            raise

        await self.db.refresh(competitor)
        return CompetitorOnboardResponse(
            competitor=CompetitorRead.model_validate(competitor),
            discovery=info,
            articles_created=articles_created,
            articles_skipped=articles_skipped,
        )

    async def close(self):
        await self.crawler.close()
        await self._http.aclose()


class _SkipArticle(Exception):
    pass
