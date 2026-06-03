"""LLM Extractor — извлечение структурированных данных из сырого текста.

Поддерживает:
    - Ollama (локально, бесплатно)
    - OpenAI API (если есть ключ)
    - Rule-based fallback (всегда работает, без LLM)
"""

import json
import logging
import re
from typing import Any

from .knowledge_pipeline import CrawlResult, ExtractedData

logger = logging.getLogger(__name__)


def _extract_by_rules(raw: CrawlResult) -> list[ExtractedData]:
    """Rule-based экстракция — без LLM, только по шаблонам."""
    results: list[ExtractedData] = []
    text = raw.raw_text
    metadata = raw.metadata

    # Пробуем извлечь из метаданных
    title = metadata.get("title", "") or ""
    desc = metadata.get("description", "") or ""

    data = ExtractedData(
        title=title,
        source_url=raw.source_url,
        body_md=text[:10000],
        excerpt=desc or text[:300],
        tags=[],
        confidence=0.3,
    )

    # Определяем категорию по URL и контенту
    url_lower = raw.source_url.lower()
    if any(w in url_lower for w in ["catalog", "product", "catalogue", "item"]):
        data.category = "product"
        data.tags = ["оборудование"]
    elif any(w in url_lower for w in ["recipe", "recept", "program"]):
        data.category = "recipe"
        data.tags = ["рецепт"]
    elif any(w in url_lower for w in ["article", "blog", "news", "stati"]):
        data.category = "article"
        data.tags = ["статья"]
    elif any(w in url_lower for w in ["about", "company", "o-kompanii"]):
        data.category = "article"
        data.tags = ["компания"]
    else:
        data.category = "article"

    # Извлекаем таблицы как спецификации
    if raw.tables:
        specs = {}
        for table in raw.tables:
            for row in table:
                if len(row) >= 2:
                    key = row[0].strip()
                    val = row[1].strip()
                    if key and val:
                        specs[key] = val
        if specs:
            data.specs = specs

    if title:
        results.append(data)

    return results


_EXTRACTION_PROMPT = """Извлеки структурированные данные из текста о коптильном оборудовании.
Верни JSON без пояснений.

Поля:
- title: название продукта/статьи
- category: "product" | "recipe" | "article"
- chamber_model: модель камеры (если есть)
- manufacturer: производитель (если есть)
- tags: массив тегов (макс 5)
- specs: объект с ТТХ (температура, объём, мощность, материал и т.д.)
- problems: массив проблем (если есть)
- recipes: массив рецептов (если есть)
- body_md: Markdown-версия основного контента (кратко, 2000 символов макс)

Текст:
{text}

JSON:"""


async def extract_with_llm(raw: CrawlResult, api_url: str | None = None) -> list[ExtractedData]:
    """Извлечение через LLM (Ollama или OpenAI)."""
    if not api_url:
        return _extract_by_rules(raw)

    text = raw.raw_text[:8000]
    prompt = _EXTRACTION_PROMPT.format(text=text)

    try:
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            if "localhost" in api_url or "ollama" in api_url:
                payload = {
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False,
                }
                resp = await client.post(f"{api_url}/api/generate", json=payload)
                resp.raise_for_status()
                result_text = resp.json().get("response", "")
            else:
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                headers = {"Authorization": f"Bearer {api_url}"}
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload, headers=headers,
                )
                resp.raise_for_status()
                result_text = resp.json()["choices"][0]["message"]["content"]

            # Извлекаем JSON из ответа
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                extracted = ExtractedData(
                    title=data.get("title", ""),
                    category=data.get("category", "article"),
                    chamber_model=data.get("chamber_model", ""),
                    manufacturer=data.get("manufacturer", ""),
                    tags=data.get("tags", []),
                    specs=data.get("specs", {}),
                    problems=data.get("problems", []),
                    recipes=data.get("recipes", []),
                    body_md=data.get("body_md", ""),
                    source_url=raw.source_url,
                    confidence=0.8,
                )
                return [extracted]

    except Exception as e:
        logger.warning(f"LLM extraction failed, falling back to rules: {e}")

    return _extract_by_rules(raw)


class LlmExtractor:
    """Экстрактор с поддержкой LLM + rule-based fallback."""

    def __init__(self, api_url: str | None = None):
        self._api_url = api_url

    async def extract(self, raw: CrawlResult) -> list[ExtractedData]:
        return await extract_with_llm(raw, self._api_url)
