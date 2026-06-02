"""Реестр драйверов камер.

DriverRegistry позволяет по строковому имени (driver_class) получить
инстанс соответствующего драйвера с переданным конфигом.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ChamberDriver


_REGISTRY: dict[str, type[ChamberDriver]] = {}


def register(name: str):
    """Декоратор для регистрации драйвера в реестре."""

    def decorator(cls: type[ChamberDriver]) -> type[ChamberDriver]:
        _REGISTRY[name] = cls
        cls._driver_name = name
        return cls

    return decorator


def get_driver_class(name: str) -> type[ChamberDriver]:
    """Получить класс драйвера по имени."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown driver: {name}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]


def create_driver(name: str, config: dict) -> ChamberDriver:
    """Создать инстанс драйвера по имени и конфигу."""
    cls = get_driver_class(name)
    return cls(config)


def list_drivers() -> list[str]:
    """Список зарегистрированных драйверов."""
    return list(_REGISTRY.keys())


# Импорт драйверов для их регистрации через декоратор @register
# (в конце файла — чтобы избежать циркулярных импортов)
from .simulated import SimulatedDriver
from .feleti_smok import FELETI_SMOKDriver
from .varmen import VarmenDriver


__all__ = [
    "register",
    "get_driver_class",
    "create_driver",
    "list_drivers",
    "SimulatedDriver",
    "FELETI_SMOKDriver",
    "VarmenDriver",
]
