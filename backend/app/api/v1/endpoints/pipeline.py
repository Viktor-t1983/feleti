"""Knowledge Pipeline API — запуск парсинга и просмотр статуса."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser
from app.core.celery_app import get_celery
from app.tasks.knowledge_tasks import (
    crawl_web,
    crawl_competitor,
    transcribe_youtube,
    parse_pdf,
)

router = APIRouter()

CELERY = get_celery()

COMPETITOR_NAMES = ["ijiza", "mauting", "fessmann", "kerres", "agros"]


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
