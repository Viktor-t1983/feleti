"""Manufacturer (producer) model."""
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    founded_year: Mapped[int | None] = mapped_column()
    website: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    is_our_brand: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_competitor: Mapped[bool] = mapped_column(default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chambers: Mapped[list["Chamber"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="manufacturer", cascade="all, delete-orphan"
    )
