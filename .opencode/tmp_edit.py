import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

with open('backend/app/services/knowledge_collector.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '    async def _run(self, job: CollectionJob) -> None:'
new = '''    def quality_gate(self, raw: CrawlResult, url: str) -> tuple[bool, str]:
        """Quality gate: проверяет качество CrawlResult перед экстракцией."""
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
        return True, ""

    async def _run(self, job: CollectionJob) -> None:'''

count = content.count(old)
if count == 0:
    print("ERROR: old string not found")
    sys.exit(1)
if count > 1:
    print(f"ERROR: found {count} matches")
    sys.exit(1)

content = content.replace(old, new, 1)
with open('backend/app/services/knowledge_collector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("OK")
