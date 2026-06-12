import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

with open('backend/app/services/knowledge_collector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded SOURCE_REPUTATION + BLACKLISTED_DOMAINS with a loader class
old = """# Репутация источников (доверие к доменам)
SOURCE_REPUTATION: dict[str, int] = {
    "vseokopchenii.ru": 3,
    "smokehouse.ru": 3,
    "vniro.ru": 3,
    "vniimp.ru": 3,
    "feleti.ru": 3,
    "eda.ru": 2,
    "povarenok.ru": 2,
    "meatclub.ru": 2,
    "fishnews.ru": 2,
    "youtube.com": 1,
    "youtu.be": 1,
    "habr.com": 1,
    "pikabu.ru": 1,
    "ozon.ru": 1,
    "wildberries.ru": 1,
    "market.yandex.ru": 1,
}

BLACKLISTED_DOMAINS: set[str] = set()

MIN_CONTENT_LENGTH: int = 200"""

new = """# Репутация источников (fallback, если БД недоступна)
FALLBACK_SOURCE_REPUTATION: dict[str, int] = {
    "vseokopchenii.ru": 3,
    "smokehouse.ru": 3,
    "vniro.ru": 3,
    "vniimp.ru": 3,
    "feleti.ru": 3,
    "eda.ru": 2,
    "povarenok.ru": 2,
    "meatclub.ru": 2,
    "fishnews.ru": 2,
    "youtube.com": 1,
    "youtu.be": 1,
    "habr.com": 1,
    "pikabu.ru": 1,
    "ozon.ru": 1,
    "wildberries.ru": 1,
    "market.yandex.ru": 1,
}

MIN_CONTENT_LENGTH: int = 200


async def _load_reputation_from_db() -> tuple[dict[str, int], set[str]]:
    \"\"\"Load source reputation + blacklist from database.\"\"\"
    try:
        from app.models.source_reputation import SourceReputation
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SourceReputation).order_by(SourceReputation.id)
            )
            rows = result.scalars().all()
            reputation: dict[str, int] = {}
            blacklist: set[str] = set()
            for r in rows:
                reputation[r.domain] = r.score
                if r.is_blacklisted:
                    blacklist.add(r.domain)
            if reputation:
                return reputation, blacklist
    except Exception as exc:
        logger.warning("Failed to load source reputation from DB, using fallback: %s", exc)
    return dict(FALLBACK_SOURCE_REPUTATION), set()"""

content = content.replace(old, new, 1)

# Update quality_gate to load reputation on first call
old_qg = """    def quality_gate(self, raw: CrawlResult, url: str) -> tuple[bool, str]:
        \"\"\"Quality gate: проверяет качество CrawlResult перед экстракцией.\"\"\"
        from urllib.parse import urlparse
        text_len = len(raw.raw_text.strip())
        if text_len < MIN_CONTENT_LENGTH:
            return False, f"Слишком короткий текст ({text_len} < {MIN_CONTENT_LENGTH})"
        if raw.errors:
            return False, f"Ошибки краулера: {'; '.join(raw.errors[:3])}"
        domain = urlparse(url).netloc.lower()
        for bd in BLACKLISTED_DOMAINS:
            if bd in domain:
                return False, f"Домен в чёрном списке: {domain}"
        reputation = 0
        for d, score in SOURCE_REPUTATION.items():
            if d in domain:
                reputation = score
                break
        if reputation == 0 and domain:
            logger.info("Неизвестный домен (score=0): %s", domain)
        return True, ""\""""

new_qg = """    async def _ensure_reputation(self) -> None:
        if not hasattr(self, '_reputation_cache') or self._reputation_cache is None:
            rep, bl = await _load_reputation_from_db()
            self._reputation_cache: dict[str, int] = rep
            self._blacklist_cache: set[str] = bl

    def quality_gate(self, raw: CrawlResult, url: str) -> tuple[bool, str]:
        \"\"\"Quality gate: проверяет качество CrawlResult перед экстракцией.\"\"\"
        from urllib.parse import urlparse
        text_len = len(raw.raw_text.strip())
        if text_len < MIN_CONTENT_LENGTH:
            return False, f"Слишком короткий текст ({text_len} < {MIN_CONTENT_LENGTH})"
        if raw.errors:
            return False, f"Ошибки краулера: {'; '.join(raw.errors[:3])}"
        domain = urlparse(url).netloc.lower()
        blacklist = getattr(self, '_blacklist_cache', set())
        for bd in blacklist:
            if bd in domain:
                return False, f"Домен в чёрном списке: {domain}"
        reputation = getattr(self, '_reputation_cache', FALLBACK_SOURCE_REPUTATION)
        score = 0
        for d, s in reputation.items():
            if d in domain:
                score = s
                break
        if score == 0 and domain:
            logger.info("Неизвестный домен (score=0): %s", domain)
        return True, ""\""""

content = content.replace(old_qg, new_qg, 1)

# Add _ensure_reputation call before the processing loop in _run
old_run = """            if not urls:
                job.status = CollectionStatus.COMPLETED
                self._notify(job)
                return

            sem = asyncio.Semaphore(3)"""

new_run = """            if not urls:
                job.status = CollectionStatus.COMPLETED
                self._notify(job)
                return

            await self._ensure_reputation()
            sem = asyncio.Semaphore(3)"""

content = content.replace(old_run, new_run, 1)

with open('backend/app/services/knowledge_collector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("OK")
