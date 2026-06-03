"""Celery app — асинхронные задачи (парсинг, транскрибация, экстракция)."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "feleti_smok",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.knowledge_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TZ,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_max_tasks_per_child=10,
)


def get_celery() -> Celery:
    return celery_app
