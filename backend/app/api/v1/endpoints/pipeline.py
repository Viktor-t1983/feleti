"""Knowledge Pipeline API — запуск парсинга и просмотр статуса."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.core.deps import CurrentUser, DBSession
from app.core.celery_app import get_celery
from app.tasks.knowledge_tasks import (
    crawl_web,
    crawl_competitor,
    transcribe_youtube,
    parse_pdf,
)
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
from app.models.knowledge import KnowledgeArticle
from app.services.web_crawler import COMPETITOR_CONFIG, WebCrawler
from app.services.llm_extractor import LlmExtractor
from app.services.knowledge_saver import KnowledgeSaver
from app.schemas.knowledge import KnowledgeArticleRead

router = APIRouter()

CELERY = get_celery()

COMPETITOR_NAMES = list(COMPETITOR_CONFIG.keys())


@router.post(
    "/crawl/competitor/{name}",
    summary="Запустить парсинг конкурента (sitemap + страницы)",
)
async def api_crawl_competitor(
    name: str,
    _user: CurrentUser,
) -> dict:
    """Запустить парсинг всех страниц конкурента через Celery-задачу."""
    if name not in COMPETITOR_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный конкурент. Доступны: {', '.join(COMPETITOR_NAMES)}",
        )
    task = crawl_competitor.delay(competitor_name=name)
    return {"task_id": task.id, "competitor": name, "status": "queued"}


@router.post(
    "/crawl/web",
    summary="Запустить парсинг одного URL",
)
async def api_crawl_web(
    _user: CurrentUser,
    url: Annotated[str, Query(min_length=5)],
    competitor_name: Annotated[str, Query()] = "",
) -> dict:
    task = crawl_web.delay(url=url, competitor_name=competitor_name)
    return {"task_id": task.id, "url": url, "status": "queued"}


@router.post(
    "/transcribe/youtube",
    summary="Транскрибация YouTube-видео по запросу",
)
async def api_transcribe_youtube(
    _user: CurrentUser,
    query: Annotated[str, Query(min_length=3)],
    max_videos: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict:
    task = transcribe_youtube.delay(query=query, max_videos=max_videos)
    return {"task_id": task.id, "query": query, "max_videos": max_videos, "status": "queued"}


@router.post(
    "/parse/pdf",
    summary="Скачать и распарсить PDF",
)
async def api_parse_pdf(
    _user: CurrentUser,
    url: Annotated[str, Query(min_length=5)],
    source_name: Annotated[str, Query()] = "",
) -> dict:
    task = parse_pdf.delay(url=url, source_name=source_name)
    return {"task_id": task.id, "url": url, "status": "queued"}


@router.get(
    "/tasks/{task_id}",
    summary="Статус задачи",
)
async def get_task_status(
    task_id: str,
    _user: CurrentUser,
) -> dict:
    result = CELERY.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }


@router.get(
    "/tasks",
    summary="Список активных/недавних задач (last 100)",
)
async def list_tasks(
    _user: CurrentUser,
) -> list[dict]:
    inspect = CELERY.control.inspect()
    active = inspect.active() or {}
    reserved = inspect.reserved() or {}
    scheduled = inspect.scheduled() or {}

    tasks = []
    for worker, worker_tasks in active.items():
        for t in worker_tasks:
            tasks.append({"worker": worker, "state": "active", **t})
    for worker, worker_tasks in reserved.items():
        for t in worker_tasks:
            tasks.append({"worker": worker, "state": "reserved", **t})
    for worker, worker_tasks in scheduled.items():
        for t in worker_tasks:
            tasks.append({"worker": worker, "state": "scheduled", **t})

    return tasks[:100]


@router.post(
    "/crawl/competitor/{name}/sync",
    summary="Парсинг конкурента (синхронно, без Celery)",
)
async def api_crawl_competitor_sync(
    name: str,
    db: DBSession,
    _user: CurrentUser,
) -> dict:
    """Запустить парсинг конкурента непосредственно в запросе (без Celery)."""
    if name not in COMPETITOR_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный конкурент. Доступны: {', '.join(COMPETITOR_NAMES)}",
        )

    results_summary = {"articles": 0, "models": 0, "errors": 0, "pages_crawled": 0}

    crawler = WebCrawler()

    try:
        raw_results = await crawler.crawl_competitor(name)
        source_name = name.title()
        all_extracted = []

        for raw in raw_results:
            results_summary["pages_crawled"] += 1
            if raw.errors:
                results_summary["errors"] += 1
                continue

            from app.services.llm_extractor import _extract_by_rules
            extracted = _extract_by_rules(raw)
            for item in extracted:
                item.manufacturer = source_name
            all_extracted.extend(extracted)

        await crawler.close()

        saver = KnowledgeSaver(db)
        save_result = await saver.save_batch(all_extracted, source_name=source_name)
        await db.commit()

        results_summary["articles"] = save_result.get("articles", 0)
        results_summary["models"] = save_result.get("models", 0)

    except Exception as e:
        await crawler.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка парсинга: {e}",
        )

    return {
        "competitor": name,
        "status": "completed",
        **results_summary,
    }


@router.get(
    "/results",
    summary="Результаты парсинга (статьи и модели по источнику)",
)
async def get_pipeline_results(
    db: DBSession,
    _user: CurrentUser,
    source: str | None = Query(None),
) -> dict:
    """Последние результаты парсинга: статьи, модели, ошибки."""
    articles_query = select(KnowledgeArticle).order_by(KnowledgeArticle.created_at.desc()).limit(50)
    models_query = (
        select(CompetitorModel)
        .join(Competitor)
        .order_by(CompetitorModel.id.desc())
        .limit(50)
    )
    competitors_query = select(Competitor).order_by(Competitor.id)

    if source:
        pattern = f"%{source}%"
        articles_query = (
            select(KnowledgeArticle)
            .where(KnowledgeArticle.source_url.ilike(pattern))
            .order_by(KnowledgeArticle.created_at.desc())
            .limit(50)
        )

    articles = (await db.scalars(articles_query)).all()
    models = (await db.scalars(models_query)).all()
    competitors = (await db.scalars(competitors_query)).all()

    return {
        "competitors": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "model_count": len(c.models) if hasattr(c, "models") else 0,
                "problem_count": len(c.problems) if hasattr(c, "problems") else 0,
            }
            for c in competitors
        ],
        "articles": [
            KnowledgeArticleRead.model_validate(a) for a in articles[:20]
        ],
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "competitor_id": m.competitor_id,
                "max_load_kg": m.max_load_kg,
                "power_kw": m.power_kw,
            }
            for m in models[:20]
        ],
        "totals": {
            "competitors": len(competitors),
            "articles": len(articles),
            "models": len(models),
        },
    }
