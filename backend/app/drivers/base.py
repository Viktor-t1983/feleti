"""Базовый интерфейс драйвера коптильной камеры.

Любой драйвер (Simulated, Varmen, Fessmann, Kerres, FELETI_SMOK и др.)
должен наследовать от ChamberDriver и реализовать все абстрактные методы.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ChamberCapabilities:
    """Что умеет камера: типы копчения, максимумы, опции."""

    type: list[str]                       # ["горячее", "холодное", "электро"]
    max_load_kg: float
    volume_m3: float
    power_kw: float
    voltage_v: int
    max_phases: int
    supports_electro: bool = False        # электростатика 10-30 кВ
    supports_static_smoke: bool = True    # классический дым
    supports_joint: bool = False          # варка+копчение в одной камере
    supports_programs: bool = True        # многофазные программы
    supports_probes: int = 1              # кол-во Pt100 в продукте
    supports_humidity_control: bool = True
    supports_smoke_density_control: bool = True
    protocols: list[str] = field(default_factory=lambda: ["modbus_tcp"])


@dataclass(frozen=True)
class ChamberTelemetry:
    """Снимок телеметрии камеры в конкретный момент."""

    chamber_id: int
    ts: datetime
    t_chamber: float | None
    t_product: float | None
    humidity: float | None
    smoke_density: float | None
    electro_voltage: float | None
    electro_current: float | None
    fan_rpm: float | None
    door_open: bool
    current_phase: int
    phase_progress: float
    errors: list[str]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChamberProgramPhase:
    """Фаза программы копчения."""

    index: int
    name: str
    duration_min: float
    target_t_chamber: float | None = None
    target_t_product: float | None = None
    humidity_percent: float | None = None
    smoke: str = "none"                    # none|light|medium|heavy
    wood_species: str | None = None
    wood_form: str | None = None           # щепа|опилки|стружка
    electro_voltage_kv: float = 0.0
    fan_speed_percent: int = 0
    transition: str = "time"               # time|product_temp|delta_t


class ChamberDriver(ABC):
    """Абстрактный драйвер камеры.

    Конфиг передаётся через __init__ (dict), не через env — для тестируемости.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.chamber_id: int = config.get("chamber_id", 0)
        self._connected: bool = False

    @abstractmethod
    async def connect(self) -> None:
        """Установить соединение с камерой."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Разорвать соединение."""
        ...

    @abstractmethod
    async def get_capabilities(self) -> ChamberCapabilities:
        """Вернуть capabilities камеры."""
        ...

    @abstractmethod
    async def get_telemetry(self) -> ChamberTelemetry:
        """Снять текущие показания."""
        ...

    @abstractmethod
    def subscribe_telemetry(self) -> AsyncIterator[ChamberTelemetry]:
        """Подписаться на поток телеметрии (AsyncIterator)."""
        ...

    @abstractmethod
    async def load_recipe(self, recipe_version: dict[str, Any]) -> None:
        """Загрузить программу в камеру (без запуска)."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Запустить выполнение загруженной программы."""
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Поставить на паузу."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Снять с паузы."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Остановить выполнение."""
        ...

    @abstractmethod
    async def get_status(self) -> dict[str, Any]:
        """Вернуть статус: {running, paused, phase, phase_name, ...}."""
        ...

    @property
    def is_connected(self) -> bool:
        return self._connected


__all__ = [
    "ChamberCapabilities",
    "ChamberTelemetry",
    "ChamberProgramPhase",
    "ChamberDriver",
]
