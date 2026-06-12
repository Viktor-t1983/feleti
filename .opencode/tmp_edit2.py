import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

with open('backend/app/services/knowledge_collector.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''            async def process(source_type: SourceType, url: str) -> None:
                async with sem:
                    try:
                        raw = await crawler.crawl(url, source_type)
                        if not raw.errors and len(raw.raw_text) > 100:
                            extracted_list = await extractor.extract(raw)
                            for extracted in extracted_list[:3]:
                                article_id = await self._save_article(extracted, job, analyzer)
                                if article_id:
                                    job.created.append(article_id)
                                else:
                                    job.skipped += 1
                        else:
                            job.skipped += 1
                    except Exception as e:
                        job.errors.append(f"{url}: {e}")
                        job.skipped += 1
                    finally:
                        job.processed += 1
                        self._notify(job)'''

new = '''            async def process(source_type: SourceType, url: str) -> None:
                async with sem:
                    try:
                        raw = await crawler.crawl(url, source_type)
                        proceed, reason = self.quality_gate(raw, url)
                        if not proceed:
                            logger.info("Quality gate rejected %s: %s", url, reason)
                            job.skipped += 1
                            return
                        extracted_list = await extractor.extract(raw)
                        for extracted in extracted_list[:3]:
                            article_id = await self._save_article(extracted, job, analyzer)
                            if article_id:
                                job.created.append(article_id)
                            else:
                                job.skipped += 1
                    except Exception as e:
                        job.errors.append(f"{url}: {e}")
                        job.skipped += 1
                    finally:
                        job.processed += 1
                        self._notify(job)'''

content = content.replace(old, new, 1)
with open('backend/app/services/knowledge_collector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("OK")
