"""Настройки AI-провайдера (Ollama/OpenAI/Custom)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)  # всегда 1
    provider: Mapped[str] = mapped_column(String(20), default="ollama", nullable=False)
    endpoint: Mapped[str] = mapped_column(String(500), default="http://host.docker.internal:11434/v1", nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), default="qwen2.5:7b", nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    system_prompt: Mapped[str] = mapped_column(
        Text,
        default="""Ты — FELETI-SMOK, AI-ассистент технолога коптильного производства.
Ты помогаешь с рецептами, технологиями, проблемами и оборудованием для копчения.
Отвечай на русском языке, профессионально, по делу.
Используй контекст из базы знаний, если он предоставлен.
Если не знаешь — скажи честно, не выдумывай.""",
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AISettings provider={self.provider} model={self.model_name} enabled={self.enabled}>"
