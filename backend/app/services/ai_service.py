"""Универсальный AI-сервис: Ollama / OpenAI / Custom.

Использует OpenAI-совместимый HTTP API (chat/completions).
Настройки читает из БД (AISettings).
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from app.models.ai_settings import AISettings

logger = logging.getLogger("ai_service")

SYSTEM_PROMPT_DEFAULT = """Ты — FELETI-SMOK, AI-ассистент технолога коптильного производства.
Ты помогаешь с рецептами, технологиями, проблемами и оборудованием для копчения.
Отвечай на русском языке, профессионально, по делу.
Используй контекст из базы знаний, если он предоставлен.
Если не знаешь — скажи честно, не выдумывай."""

ANALYZE_PROMPT = """Проанализируй следующий текст и извлеки структурированную информацию.
Ответь ТОЛЬКО в формате JSON, без лишнего текста.

Поля JSON:
- "products": ["продукт1", "продукт2"] — какие продукты упоминаются
- "technologies": ["технология1"] — какие технологии копчения/обработки
- "problems": [{"title": "проблема", "description": "описание", "severity": "high/medium/low"}] — проблемы и их серьёзность
- "recipes": [{"name": "название", "ingredients": ["ингр1"], "steps": ["шаг1"]}] — рецепты
- "equipment": ["оборудование1"] — какое оборудование упоминается
- "key_insights": ["инсайт1"] — ключевые выводы

Если информации нет — оставь пустой массив.

Текст для анализа:
"""


class AIService:
    def __init__(self, settings: AISettings):
        self.settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.settings.api_key:
            h["Authorization"] = f"Bearer {self.settings.api_key}"
        return h

    @property
    def _payload_base(self) -> dict[str, Any]:
        return {
            "model": self.settings.model_name,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }

    def _chat_url(self) -> str:
        endpoint = self.settings.endpoint.rstrip("/")
        if endpoint.endswith("/v1"):
            return f"{endpoint}/chat/completions"
        return f"{endpoint}/v1/chat/completions"

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
    ) -> dict[str, Any]:
        """Отправить сообщения в LLM и получить ответ."""
        payload = {**self._payload_base, "messages": messages, "stream": stream}

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.settings.max_tokens // 10 + 30)) as client:
            resp = await client.post(
                self._chat_url(),
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def ask(
        self,
        question: str,
        context: str | None = None,
        stream: bool = False,
    ) -> str:
        """Задать вопрос с опциональным контекстом из БЗ."""
        system = self.settings.system_prompt or SYSTEM_PROMPT_DEFAULT
        messages = [{"role": "system", "content": system}]

        if context:
            messages.append({
                "role": "user",
                "content": f"Вот контекст из базы знаний:\n\n{context[:8000]}\n\n---\n\nВопрос: {question}",
            })
        else:
            messages.append({"role": "user", "content": question})

        data = await self.chat(messages, stream=stream)
        return data["choices"][0]["message"]["content"]

    async def ask_stream(
        self,
        question: str,
        context: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Задать вопрос и получать ответ по токенам (SSE-стриминг)."""
        system = self.settings.system_prompt or SYSTEM_PROMPT_DEFAULT
        messages = [{"role": "system", "content": system}]

        if context:
            messages.append({
                "role": "user",
                "content": f"Вот контекст из базы знаний:\n\n{context[:8000]}\n\n---\n\nВопрос: {question}",
            })
        else:
            messages.append({"role": "user", "content": question})

        payload = {
            **self._payload_base,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            async with client.stream(
                "POST",
                self._chat_url(),
                headers=self._headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def analyze(self, text: str) -> dict[str, Any]:
        """Проанализировать текст и извлечь структуру."""
        system = SYSTEM_PROMPT_DEFAULT
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": ANALYZE_PROMPT + text[:15000]},
        ]
        data = await self.chat(messages)
        content = data["choices"][0]["message"]["content"]

        # Пробуем извлечь JSON из ответа
        try:
            # Ищем JSON в ответе
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            logger.warning("AI вернул не-JSON: %s...", content[:200])
            return {"raw": content}

    async def test(self) -> dict[str, Any]:
        """Проверить подключение к AI-провайдеру."""
        try:
            start = __import__("time").time()
            data = await self.chat([
                {"role": "system", "content": "Answer only OK."},
                {"role": "user", "content": "Say OK"},
            ])
            elapsed = __import__("time").time() - start
            return {
                "success": True,
                "model": data.get("model", self.settings.model_name),
                "latency_ms": round(elapsed * 1000),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    async def get_settings(db_session) -> AISettings:
        """Получить настройки AI (создать дефолтные если нет)."""
        from sqlalchemy import select
        result = await db_session.execute(select(AISettings).where(AISettings.id == 1))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = AISettings(id=1)
            db_session.add(settings)
            await db_session.flush()
            await db_session.commit()
        return settings
