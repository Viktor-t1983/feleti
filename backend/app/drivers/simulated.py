"""Симулятор камеры для разработки и демо.

Имитирует поведение реальной камеры с простой физической моделью:
- T_chamber приближается к target_t_chamber с инерцией.
- T_product приближается к T_chamber медленнее.
- Время фазы = duration_min, переход к следующей по времени.
- Телеметрия генерируется каждую секунду.
- Электростатика включается, если electro_voltage_kv > 0 в фазе.
"""

import asyncio
import random
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from .base import (
    ChamberCapabilities,
    ChamberDriver,
    ChamberTelemetry,
)
from . import register


@register("SimulatedDriver")
class SimulatedDriver(ChamberDriver):
    """Мок камеры с физ-моделью для разработки UI без реального оборудования."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._running: bool = False
        self._paused: bool = False
        self._program: list[dict[str, Any]] = []
        self._current_recipe_version: dict[str, Any] | None = None
        self._phase_index: int = 0
        self._phase_started_at: datetime | None = None
        self._t_chamber: float = 20.0
        self._t_product: float = 20.0
        self._ambient_t: float = 20.0
        self._tick_task: asyncio.Task | None = None
        self._subscribers: list[asyncio.Queue] = []

    async def connect(self) -> None:
        await asyncio.sleep(0.05)
        self._connected = True
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def disconnect(self) -> None:
        self._connected = False
        if self._tick_task:
            self._tick_task.cancel()
            self._tick_task = None

    async def get_capabilities(self) -> ChamberCapabilities:
        return ChamberCapabilities(
            type=["горячее", "холодное", "электро"],
            max_load_kg=float(self.config.get("max_load_kg", 250)),
            volume_m3=float(self.config.get("volume_m3", 1.5)),
            power_kw=float(self.config.get("power_kw", 18)),
            voltage_v=int(self.config.get("voltage_v", 380)),
            max_phases=16,
            supports_electro=True,
            supports_static_smoke=True,
            supports_joint=True,
            supports_programs=True,
            supports_probes=2,
            supports_humidity_control=True,
            supports_smoke_density_control=True,
            protocols=["simulated"],
        )

    async def get_telemetry(self) -> ChamberTelemetry:
        phase = self._program[self._phase_index] if 0 <= self._phase_index < len(self._program) else {}
        phase_name = phase.get("phase", "")
        return ChamberTelemetry(
            chamber_id=self.chamber_id,
            ts=datetime.utcnow(),
            t_chamber=round(self._t_chamber, 1),
            t_product=round(self._t_product, 1),
            humidity=round(50.0 + random.uniform(-5, 5), 1),
            smoke_density=round(20.0 + random.uniform(-2, 2), 1) if self._running and phase.get("smoke", "none") != "none" else 0.0,
            electro_voltage=round(float(phase.get("electro_voltage_kv", 0)), 1) if self._running else 0.0,
            electro_current=round(25.0 + random.uniform(-3, 3), 1) if self._running and phase.get("electro_voltage_kv", 0) > 0 else 0.0,
            fan_rpm=1500 if self._running else 0,
            door_open=False,
            current_phase=self._phase_index,
            phase_progress=self._phase_progress(),
            errors=[],
            raw={"phase_name": phase_name},
        )

    def subscribe_telemetry(self) -> AsyncIterator[ChamberTelemetry]:
        return self._subscribe()

    async def _subscribe(self) -> AsyncIterator[ChamberTelemetry]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._subscribers.append(queue)
        try:
            while self._connected:
                telemetry = await queue.get()
                yield telemetry
        finally:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    async def load_recipe(self, recipe_version: dict[str, Any]) -> None:
        self._current_recipe_version = recipe_version
        self._program = recipe_version.get("program", [])
        self._phase_index = 0
        self._phase_started_at = None

    async def start(self) -> None:
        if not self._program:
            raise RuntimeError("No program loaded")
        self._running = True
        self._paused = False
        self._phase_index = 0
        self._phase_started_at = datetime.utcnow()

    async def pause(self) -> None:
        self._paused = True

    async def resume(self) -> None:
        if self._running and self._paused:
            self._paused = False
            if self._phase_started_at is not None:
                elapsed = (datetime.utcnow() - self._phase_started_at).total_seconds() / 60
                self._phase_started_at = datetime.utcnow()

    async def stop(self) -> None:
        self._running = False
        self._paused = False
        self._phase_index = 0
        self._phase_started_at = None
        self._t_chamber = self._ambient_t
        self._t_product = self._ambient_t

    async def get_status(self) -> dict[str, Any]:
        phase = self._program[self._phase_index] if 0 <= self._phase_index < len(self._program) else {}
        return {
            "running": self._running,
            "paused": self._paused,
            "phase": self._phase_index,
            "phase_name": phase.get("phase", ""),
            "phase_progress": self._phase_progress(),
            "total_phases": len(self._program),
        }

    def _phase_progress(self) -> float:
        if not self._program or self._phase_started_at is None:
            return 0.0
        phase = self._program[self._phase_index]
        duration = phase.get("duration_min", 60)
        if duration <= 0:
            return 1.0
        elapsed = (datetime.utcnow() - self._phase_started_at).total_seconds() / 60
        return round(min(elapsed / duration, 1.0), 3)

    async def _tick_loop(self) -> None:
        """Физическая модель: тик каждую секунду."""
        try:
            while self._connected:
                await asyncio.sleep(1.0)
                if self._running and not self._paused and self._program:
                    self._advance_physics()
                    self._advance_phase()
                telemetry = await self.get_telemetry()
                for queue in list(self._subscribers):
                    try:
                        queue.put_nowait(telemetry)
                    except asyncio.QueueFull:
                        pass
        except asyncio.CancelledError:
            pass

    def _advance_physics(self) -> None:
        phase = self._program[self._phase_index]
        target_t = float(phase.get("t_chamber", self._ambient_t))
        inertia = 0.05
        self._t_chamber += (target_t - self._t_chamber) * inertia
        product_inertia = 0.02
        self._t_product += (self._t_chamber - self._t_product) * product_inertia
        self._t_chamber += random.uniform(-0.2, 0.2)
        self._t_product += random.uniform(-0.1, 0.1)

    def _advance_phase(self) -> None:
        if self._phase_started_at is None:
            self._phase_started_at = datetime.utcnow()
            return
        phase = self._program[self._phase_index]
        duration = phase.get("duration_min", 60)
        elapsed = (datetime.utcnow() - self._phase_started_at).total_seconds() / 60
        if elapsed >= duration:
            self._phase_index += 1
            if self._phase_index >= len(self._program):
                self._running = False
                self._phase_index = len(self._program) - 1
            else:
                self._phase_started_at = datetime.utcnow()
