import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

with open('backend/app/services/knowledge_collector.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
old_import = "from app.services.article_analyzer import ArticleAnalyzer"
new_import = "from app.services.article_analyzer import ArticleAnalyzer\nfrom app.services import simhash as sh"
content = content.replace(old_import, new_import, 1)

# 2. Add simhash dedup check in _save_article
old_save = '''                # проверка дубликата по URL
                if extracted.source_url:
                    existing = await db.scalar(
                        select(KnowledgeArticle).where(
                            KnowledgeArticle.source_url == extracted.source_url
                        ).limit(1)
                    )
                    if existing:
                        logger.info("Дубликат (URL): %s", extracted.source_url)
                        return None

                article = KnowledgeArticle(
                    title=extracted.title[:500],
                    slug=self._slugify(extracted.title)[:500],
                    body_md=extracted.body_md,
                    excerpt=extracted.excerpt[:500] if extracted.excerpt else None,
                    category=extracted.category or "theory",
                    tags=extracted.tags,
                    source_url=extracted.source_url or "",
                    is_published=True,
                )'''

new_save = '''                # проверка дубликата по URL
                if extracted.source_url:
                    existing = await db.scalar(
                        select(KnowledgeArticle).where(
                            KnowledgeArticle.source_url == extracted.source_url
                        ).limit(1)
                    )
                    if existing:
                        logger.info("Дубликат (URL): %s", extracted.source_url)
                        return None

                # SimHash de-duplication
                body_for_hash = (extracted.title + " " + extracted.body_md) if extracted.excerpt is None else (extracted.title + " " + extracted.excerpt + " " + extracted.body_md)
                fp = sh.compute(body_for_hash)
                if fp != 0:
                    existing_hashes = await db.scalars(
                        select(KnowledgeArticle.simhash_value).where(
                            KnowledgeArticle.simhash_value.isnot(None)
                        ).limit(1000)
                    )
                    if sh.is_duplicate(fp, existing_hashes.all()):
                        logger.info("Дубликат (SimHash): %s", extracted.title)
                        return None

                article = KnowledgeArticle(
                    title=extracted.title[:500],
                    slug=self._slugify(extracted.title)[:500],
                    body_md=extracted.body_md,
                    excerpt=extracted.excerpt[:500] if extracted.excerpt else None,
                    category=extracted.category or "theory",
                    tags=extracted.tags,
                    source_url=extracted.source_url or "",
                    is_published=True,
                    simhash_value=fp,
                )'''

content = content.replace(old_save, new_save, 1)
with open('backend/app/services/knowledge_collector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("OK")
