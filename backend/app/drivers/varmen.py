"""Драйвер камер Ижица Varmen по Modbus TCP.

Карта регистров — DRAFT, требует верификации через Wireshark или
документацию от Ижица. Структура соответствует типичной для Varmen-1.
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from .base import (
    ChamberCapabilities,
    ChamberDriver,
    ChamberTelemetry,
)
from . import register


@register("VarmenDriver")
class VarmenDriver(ChamberDriver):
    """Драйвер Ижица Varmen-1 (Modbus TCP).

    Конфиг:
        host: str            # IP камеры (default 192.168.0.100)
        port: int            # 502
        unit_id: int         # 1
        timeout_ms: int      # 3000
    """

    REG_T_CHAMBER = 0x1000
    REG_T_PRODUCT = 0x1001
    REG_HUMIDITY = 0x1002
    REG_SMOKE = 0x1003
    REG_ELECTRO_V = 0x1004
    REG_ELECTRO_UA = 0x1005
    REG_FAN_RPM = 0x1006
    REG_DOOR = 0x1007
    REG_PHASE = 0x1008
    REG_PROGRESS = 0x1009
    REG_ERRORS = 0x100A
    REG_STATUS = 0x100B

    REG_SET_T_CHAMBER = 0x0000
    REG_SET_HUMIDITY = 0x0001
    REG_SET_SMOKE = 0x0002
    REG_SET_FAN = 0x0003
    REG_SET_ELECTRO = 0x0004
    REG_COMMAND = 0x0005
    REG_LOAD_PROGRAM = 0x0010

    CMD_START = 1
    CMD_PAUSE = 2
    CMD_RESUME = 3
    CMD_STOP = 4
    CMD_LOAD_RECIPE = 5

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "192.168.0.100")
        self.port = config.get("port", 502)
        self.unit_id = config.get("unit_id", 1)
        self.timeout_ms = config.get("timeout_ms", 3000)
        self._client: Any = None
        self._subscribers: list[asyncio.Queue] = []
        self._tick_task: asyncio.Task | None = None

    async def connect(self) -> None:
        try:
            from pymodbus.client import AsyncModbusTcpClient
        except ImportError as e:
            raise ImportError(
                "pymodbus is required for VarmenDriver. "
                "Install with: uv add pymodbus"
            ) from e

        self._client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout_ms / 1000,
        )
        connected = await self._client.connect()
        if not connected:
            raise ConnectionError(f"Cannot connect to Varmen at {self.host}:{self.port}")
        self._connected = True
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def disconnect(self) -> None:
        self._connected = False
        if self._tick_task:
            self._tick_task.cancel()
            self._tick_task = None
        if self._client:
            self._client.close()

    async def get_capabilities(self) -> ChamberCapabilities:
        return ChamberCapabilities(
            type=["горячее", "холодное", "электро"],
            max_load_kg=float(self.config.get("max_load_kg", 50)),
            volume_m3=float(self.config.get("volume_m3", 0.5)),
            power_kw=float(self.config.get("power_kw", 8)),
            voltage_v=int(self.config.get("voltage_v", 380)),
            max_phases=16,
            supports_electro=bool(self.config.get("supports_electro", True)),
            supports_static_smoke=True,
            supports_joint=True,
            supports_programs=True,
            supports_probes=1,
            supports_humidity_control=True,
            supports_smoke_density_control=True,
            protocols=["modbus_tcp"],
        )

    async def get_telemetry(self) -> ChamberTelemetry:
        return ChamberTelemetry(
            chamber_id=self.chamber_id,
            ts=datetime.utcnow(),
            t_chamber=await self._read_input(self.REG_T_CHAMBER, scale=0.1),
            t_product=await self._read_input(self.REG_T_PRODUCT, scale=0.1),
            humidity=await self._read_input(self.REG_HUMIDITY, scale=0.1),
            smoke_density=await self._read_input(self.REG_SMOKE),
            electro_voltage=await self._read_input(self.REG_ELECTRO_V, scale=0.1),
            electro_current=await self._read_input(self.REG_ELECTRO_UA),
            fan_rpm=await self._read_input(self.REG_FAN_RPM),
            door_open=bool(await self._read_input(self.REG_DOOR)),
            current_phase=await self._read_input(self.REG_PHASE),
            phase_progress=(await self._read_input(self.REG_PROGRESS)) / 100.0,
            errors=self._decode_errors(await self._read_input(self.REG_ERRORS)),
            raw={"source": "varmen"},
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
        await self._write_holding(self.REG_LOAD_PROGRAM, 1)
        await asyncio.sleep(0.1)
        await self._write_holding(self.REG_LOAD_PROGRAM, 0)

    async def start(self) -> None:
        await self._write_holding(self.REG_COMMAND, self.CMD_START)

    async def pause(self) -> None:
        await self._write_holding(self.REG_COMMAND, self.CMD_PAUSE)

    async def resume(self) -> None:
        await self._write_holding(self.REG_COMMAND, self.CMD_RESUME)

    async def stop(self) -> None:
        await self._write_holding(self.REG_COMMAND, self.CMD_STOP)

    async def get_status(self) -> dict[str, Any]:
        status = await self._read_input(self.REG_STATUS)
        return {
            "running": status == 1,
            "paused": status == 2,
            "error": status == 3,
            "current_phase": await self._read_input(self.REG_PHASE),
            "phase_progress": (await self._read_input(self.REG_PROGRESS)) / 100.0,
        }

    async def _read_input(self, address: int, scale: float = 1.0) -> float:
        if not self._client or not self._client.connected:
            raise ConnectionError("Varmen client not connected")
        result = await self._client.read_input_registers(
            address=address, count=1, slave=self.unit_id
        )
        if result.isError():
            return 0.0
        return result.registers[0] * scale

    async def _write_holding(self, address: int, value: int) -> None:
        if not self._client or not self._client.connected:
            raise ConnectionError("Varmen client not connected")
        result = await self._client.write_register(
            address=address, value=value, slave=self.unit_id
        )
        if result.isError():
            raise RuntimeError(f"Varmen write error at 0x{address:04X}: {result}")

    def _decode_errors(self, errors_reg: int) -> list[str]:
        if not errors_reg:
            return []
        error_bits = {
            0: "T_chamber_sensor_fault",
            1: "T_product_sensor_fault",
            2: "door_open",
            3: "overheat",
            4: "fan_fault",
            5: "smoke_generator_fault",
            6: "electro_overcurrent",
            7: "electro_fault",
        }
        return [name for bit, name in error_bits.items() if errors_reg & (1 << bit)]

    async def _tick_loop(self) -> None:
        try:
            while self._connected:
                await asyncio.sleep(1.0)
                try:
                    telemetry = await self.get_telemetry()
                except Exception:
                    continue
                for queue in list(self._subscribers):
                    try:
                        queue.put_nowait(telemetry)
                    except asyncio.QueueFull:
                        pass
        except asyncio.CancelledError:
            pass
