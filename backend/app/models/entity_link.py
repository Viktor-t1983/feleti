"""EntityLink — рёбра графа знаний между сущностями платформы."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class EntityLink(Base):
    """Связь между двумя сущностями в графе знаний.

    Пример: article(42) --mentions--> product(7)
    """

    __tablename__ = "entity_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    relation: Mapped[str] = mapped_column(String(50), nullable=False, default="mentions")

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "target_type", "target_id", "relation",
                         name="uq_entity_link"),
    )

    def __repr__(self) -> str:
        return f"<EntityLink {self.source_type}:{self.source_id} --{self.relation}--> {self.target_type}:{self.target_id}>"
