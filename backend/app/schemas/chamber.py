"""Схемы коптильной камеры."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, HttpUrl

from app.schemas.common import APIModel


class ChamberTypeEnum(str, Enum):
    HOT = "горячее"
    COLD = "холодное"
    ELECTRO = "электро"
    UNIVERSAL = "универсальное"
    SEMI_HOT = "полугорячее"
    SMOKE = "дымогенератор"
    UNKNOWN = "неизвестно"


class ChamberRead(APIModel):
    id: int
    manufacturer_id: int
    manufacturer_name: str | None = None
    model: str
    slug: str
    type: ChamberTypeEnum

    max_load_kg: float | None = None
    volume_m3: float | None = None
    power_kw: float | None = None
    voltage_v: int | None = None

    supports_static_smoke: bool
    supports_electro: bool
    supports_cold_smoke: bool
    supports_cooling: bool
    supports_freezing: bool
    supports_joint: bool

    supported_protocols: list[str] = []
    driver_class: str
    default_driver_config: dict = {}

    num_chambers: int
    num_carts: int
    num_probes: int
    max_program_phases: int

    price_rrp_rub: float | None = None
    price_dealer_rub: float | None = None
    price_rrp_eur: float | None = None

    images: list[str] = []
    description: str | None = None
    source_url: str | None = None
    source: str | None = None
    verified: bool

    created_at: datetime
    updated_at: datetime | None = None


class ChamberCreate(APIModel):
    manufacturer_id: int = Field(..., ge=1)
    model: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200, pattern=r"^[a-z0-9-]+$")
    type: ChamberTypeEnum = ChamberTypeEnum.UNKNOWN

    max_load_kg: float | None = Field(default=None, ge=0)
    volume_m3: float | None = Field(default=None, ge=0)
    power_kw: float | None = Field(default=None, ge=0)
    voltage_v: int | None = Field(default=None, ge=0)

    supports_static_smoke: bool = True
    supports_electro: bool = False
    supports_cold_smoke: bool = False
    supports_cooling: bool = False
    supports_freezing: bool = False
    supports_joint: bool = False

    supported_protocols: list[str] = []
    driver_class: str = "SimulatedDriver"
    default_driver_config: dict = {}

    num_chambers: int = 1
    num_carts: int = 1
    num_probes: int = 1
    max_program_phases: int = 16

    price_rrp_rub: float | None = None
    price_dealer_rub: float | None = None
    price_rrp_eur: float | None = None

    images: list[HttpUrl] = []
    description: str | None = Field(default=None, max_length=2000)
    source_url: HttpUrl | None = None
    source: str | None = None
    verified: bool = False


class ChamberUpdate(APIModel):
    model: str | None = None
    type: ChamberTypeEnum | None = None
    max_load_kg: float | None = None
    volume_m3: float | None = None
    power_kw: float | None = None
    voltage_v: int | None = None

    supports_static_smoke: bool | None = None
    supports_electro: bool | None = None
    supports_cold_smoke: bool | None = None
    supports_cooling: bool | None = None
    supports_freezing: bool | None = None
    supports_joint: bool | None = None

    supported_protocols: list[str] | None = None
    driver_class: str | None = None
    default_driver_config: dict | None = None

    num_chambers: int | None = None
    num_carts: int | None = None
    num_probes: int | None = None
    max_program_phases: int | None = None

    price_rrp_rub: float | None = None
    price_dealer_rub: float | None = None
    price_rrp_eur: float | None = None

    images: list[HttpUrl] | None = None
    description: str | None = None
    source_url: HttpUrl | None = None
    source: str | None = None
    verified: bool | None = None
