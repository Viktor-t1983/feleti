"""Модель камеры (коптильной)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Float, Integer, Boolean, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.manufacturer import Manufacturer
    from app.models.batch import Batch


class ChamberType(str, PyEnum):
    HOT = "горячее"
    COLD = "холодное"
    ELECTRO = "электро"
    UNIVERSAL = "универсальное"
    SEMI_HOT = "полугорячее"
    SMOKE = "дымогенератор"
    UNKNOWN = "неизвестно"


class Chamber(Base):
    __tablename__ = "chambers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    type: Mapped[ChamberType] = mapped_column(
        SAEnum(ChamberType, name="chamber_type"), default=ChamberType.UNKNOWN, nullable=False
    )

    max_load_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)
    voltage_v: Mapped[int | None] = mapped_column(Integer, nullable=True)

    supports_static_smoke: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_electro: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_cold_smoke: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_cooling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_freezing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_joint: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    supported_protocols: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    driver_class: Mapped[str] = mapped_column(String(100), default="SimulatedDriver", nullable=False)
    default_driver_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    num_chambers: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    num_carts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    num_probes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_program_phases: Mapped[int] = mapped_column(Integer, default=16, nullable=False)

    price_rrp_rub: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_dealer_rub: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_rrp_eur: Mapped[float | None] = mapped_column(Float, nullable=True)

    images: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="chambers", lazy="joined")
    batches: Mapped[list["Batch"]] = relationship(back_populates="chamber", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Chamber {self.id} {self.manufacturer.name if self.manufacturer else '?'} {self.model}>"
