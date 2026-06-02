"""ChamberGateway: пул инстансов драйверов камер с авто-переподключением.

Архитектура:
  - Один gateway инстанс на всё приложение (singleton в deps).
  - Драйвер создаётся лениво при первом обращении к камере.
  - При ошибке драйвер автоматически реконнектится при следующем вызове.
  - Телеметрия буферизуется in-memory (кольцевой буфер N последних точек на камеру).
  - AsyncIterator подписки для WebSocket — fan-out ко всем подписчикам.

Конфиг драйвера берётся из Chamber.connection (JSON в БД).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from app.drivers import create_driver, list_drivers
from app.drivers.base import ChamberDriver, ChamberTelemetry

logger = logging.getLogger(__name__)

# Размер кольцевого буфера телеметрии на камеру (точек).
TELEMETRY_BUFFER_SIZE = 3600  # 1 час при 1 Hz


class ChamberConnectionError(RuntimeError):
    """Не удалось подключиться к камере."""


@dataclass
class _BufferedSample:
    ts: float
    telemetry: ChamberTelemetry


class ChamberGateway:
    """Пул драйверов и шина телеметрии для всех камер платформы."""

    def __init__(self) -> None:
        self._drivers: dict[int, ChamberDriver] = {}
        self._locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._buffer: dict[int, deque[_BufferedSample]] = defaultdict(
            lambda: deque(maxlen=TELEMETRY_BUFFER_SIZE)
        )
        self._subscribers: dict[int, list[asyncio.Queue[ChamberTelemetry]]] = defaultdict(list)
        self._tasks: dict[int, asyncio.Task] = {}
        self._closed = False

    @staticmethod
    def available_drivers() -> list[str]:
        """Список зарегистрированных драйверов (для /chambers/drivers endpoint)."""
        return list_drivers()

    async def get_driver(
        self, chamber_id: int, driver_class: str, connection: dict[str, Any]
    ) -> ChamberDriver:
        """Получить (или создать+подключить) драйвер для камеры."""
        if self._closed:
            raise ChamberConnectionError("Gateway is closed")
        if chamber_id in self._drivers and self._drivers[chamber_id].is_connected:
            return self._drivers[chamber_id]

        async with self._locks[chamber_id]:
            # double-check после захвата лока
            if chamber_id in self._drivers and self._drivers[chamber_id].is_connected:
                return self._drivers[chamber_id]

            config = {"chamber_id": chamber_id, **connection}
            try:
                driver = create_driver(driver_class, config)
            except KeyError as e:
                raise ChamberConnectionError(str(e)) from e
            try:
                await driver.connect()
            except Exception as e:
                logger.exception("Не удалось подключиться к камере %s", chamber_id)
                raise ChamberConnectionError(
                    f"Ошибка подключения к камере {chamber_id}: {e}"
                ) from e
            self._drivers[chamber_id] = driver
            logger.info("Камера %s подключена через %s", chamber_id, driver_class)

            if chamber_id not in self._tasks or self._tasks[chamber_id].done():
                self._tasks[chamber_id] = asyncio.create_task(
                    self._telemetry_loop(chamber_id, driver),
                    name=f"chamber-telemetry-{chamber_id}",
                )
            return driver

    async def release(self, chamber_id: int) -> None:
        """Отключить камеру и убрать драйвер из пула."""
        async with self._locks[chamber_id]:
            driver = self._drivers.pop(chamber_id, None)
            task = self._tasks.pop(chamber_id, None)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if driver:
                try:
                    await driver.disconnect()
                except Exception:
                    logger.exception("Ошибка disconnect камеры %s", chamber_id)
            self._buffer.pop(chamber_id, None)
            for q in self._subscribers.pop(chamber_id, []):
                try:
                    q.put_nowait(None)  # type: ignore[arg-type]
                except asyncio.QueueFull:
                    pass

    async def shutdown(self) -> None:
        """Закрыть gateway (при остановке приложения)."""
        self._closed = True
        for chamber_id in list(self._drivers.keys()):
            await self.release(chamber_id)

    async def start_batch(
        self, chamber_id: int, driver_class: str, connection: dict, recipe_program: list[dict]
    ) -> None:
        """Загрузить программу и запустить камеру."""
        driver = await self.get_driver(chamber_id, driver_class, connection)
        await driver.load_recipe({"program": recipe_program})
        await driver.start()

    async def pause_batch(self, chamber_id: int) -> None:
        driver = self._require(chamber_id)
        await driver.pause()

    async def resume_batch(self, chamber_id: int) -> None:
        driver = self._require(chamber_id)
        await driver.resume()

    async def stop_batch(self, chamber_id: int) -> None:
        driver = self._require(chamber_id)
        await driver.stop()

    async def get_status(self, chamber_id: int) -> dict[str, Any]:
        driver = self._require(chamber_id)
        return await driver.get_status()

    async def get_telemetry(self, chamber_id: int) -> ChamberTelemetry:
        """Свежий снимок (не из буфера)."""
        driver = self._require(chamber_id)
        return await driver.get_telemetry()

    def latest_telemetry(self, chamber_id: int) -> ChamberTelemetry | None:
        """Последний сэмпл из кольцевого буфера (или None)."""
        buf = self._buffer.get(chamber_id)
        if not buf:
            return None
        return buf[-1].telemetry

    def telemetry_history(self, chamber_id: int, limit: int = 600) -> list[ChamberTelemetry]:
        """Последние N точек телеметрии из буфера (старые→новые)."""
        buf = self._buffer.get(chamber_id)
        if not buf:
            return []
        return [s.telemetry for s in list(buf)[-limit:]]

    def subscribe(self, chamber_id: int) -> asyncio.Queue[ChamberTelemetry]:
        """Подписаться на live-телеметрию. None в очереди = конец потока."""
        queue: asyncio.Queue[ChamberTelemetry] = asyncio.Queue(maxsize=120)
        self._subscribers[chamber_id].append(queue)
        return queue

    def unsubscribe(self, chamber_id: int, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(chamber_id, [])
        if queue in subs:
            subs.remove(queue)

    def _require(self, chamber_id: int) -> ChamberDriver:
        driver = self._drivers.get(chamber_id)
        if driver is None or not driver.is_connected:
            raise ChamberConnectionError(
                f"Камера {chamber_id} не подключена. Сначала get_driver()."
            )
        return driver

    async def _telemetry_loop(self, chamber_id: int, driver: ChamberDriver) -> None:
        """Фоновый тик: опрашиваем driver и кладём в буфер + fan-out подписчикам."""
        try:
            while driver.is_connected and not self._closed:
                try:
                    telemetry = await driver.get_telemetry()
                except Exception:
                    logger.exception("Ошибка опроса телеметрии камеры %s", chamber_id)
                    await asyncio.sleep(1.0)
                    continue
                self._buffer[chamber_id].append(
                    _BufferedSample(ts=time.time(), telemetry=telemetry)
                )
                for queue in list(self._subscribers.get(chamber_id, [])):
                    try:
                        queue.put_nowait(telemetry)
                    except asyncio.QueueFull:
                        # Медленный подписчик — пропускаем точку.
                        pass
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Телеметрия-цикл камеры %s упал", chamber_id)


# Singleton
_gateway: ChamberGateway | None = None
_gateway_lock = asyncio.Lock()


async def get_chamber_gateway() -> ChamberGateway:
    """Получить singleton gateway (для FastAPI Depends)."""
    global _gateway
    if _gateway is None:
        async with _gateway_lock:
            if _gateway is None:
                _gateway = ChamberGateway()
    return _gateway


__all__ = [
    "ChamberGateway",
    "ChamberConnectionError",
    "TELEMETRY_BUFFER_SIZE",
    "get_chamber_gateway",
]
