"""Telegram Parser — парсинг Telegram-каналов конкурентов (через Telethon).

Заглушка — для работы нужны API_ID и API_HASH от my.telegram.org.

Каналы для парсинга:
    - @ijiza_chat — обсуждение Ижицы
    - @smoking_technology — технологии копчения
    - @meat_industry — мясная промышленность
"""

import logging
from typing import Any
from datetime import datetime

from .knowledge_pipeline import CrawlResult, SourceType

logger = logging.getLogger(__name__)

# Каналы по умолчанию
DEFAULT_CHANNELS = [
    "@ijiza_chat",
]


class TelegramParser:
    """Парсинг Telegram-каналов."""

    def __init__(self, api_id: str | None = None, api_hash: str | None = None):
        self._api_id = api_id
        self._api_hash = api_hash

    async def crawl(self, url: str) -> CrawlResult:
        """Парсинг одного сообщения/поста (заглушка)."""
        if not self._api_id or not self._api_hash:
            return CrawlResult(
                source_type=SourceType.TELEGRAM,
                source_url=url,
                errors=["API_ID и API_HASH не настроены. Добавьте их в .env"],
            )

        result = CrawlResult(
            source_type=SourceType.TELEGRAM,
            source_url=url,
            errors=["Telegram parser: not yet implemented"],
        )
        return result

    async def crawl_channel(self, channel: str, limit: int = 100) -> list[CrawlResult]:
        """Парсинг канала (заглушка)."""
        logger.info(f"Telegram parser skipped: {channel} (API keys needed)")
        return []

    def is_ready(self) -> bool:
        """Готов ли парсер к работе."""
        return bool(self._api_id and self._api_hash)
