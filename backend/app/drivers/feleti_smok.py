"""Драйвер камер FELETI-SMOK (Kinco HMI/PLC + свой модуль расширения).

Архитектура:
- Kinco PLC (Modbus TCP slave, порт 502) — базовый I/O: ТЭН, вентилятор,
  дымогенератор, дверь, Pt100, влажность, дым.
- Свой модуль расширения (Modbus TCP slave, порт 503) — электростатика,
  доп. датчики, edge-cache, MQTT-мост.

Драйвер общается со своим модулем расширения (приоритетный канал) и
зеркалит данные в Kinco для совместимости с унаследованным софтом.
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


@register("FELETI_SMOKDriver")
class FELETI_SMOKDriver(ChamberDriver):
    """Драйвер камер FELETI-SMOK по Modbus TCP.

    Конфиг (default_driver_config):
        kinco_host: str           # IP Kinco PLC (default 192.168.1.100)
        kinco_port: int           # Modbus TCP (default 502)
        extension_host: str       # IP своего модуля расширения
        extension_port: int       # default 503
        unit_id: int              # Modbus unit ID (default 1)
        timeout_ms: int           # default 3000
        reconnect_backoff_ms: int # default 1000
    """

    KINCO_REG_T_CHAMBER = 0x1000
    KINCO_REG_T_PRODUCT = 0x1001
    KINCO_REG_HUMIDITY = 0x1002
    KINCO_REG_SMOKE = 0x1003
    KINCO_REG_FAN_RPM = 0x1006
    KINCO_REG_DOOR = 0x1007
    KINCO_REG_PHASE = 0x1008
    KINCO_REG_PROGRESS = 0x1009
    KINCO_REG_ERRORS = 0x100A
    KINCO_REG_STATUS = 0x100B

    KINCO_REG_SET_T_CHAMBER = 0x0000
    KINCO_REG_SET_HUMIDITY = 0x0001
    KINCO_REG_SET_SMOKE = 0x0002
    KINCO_REG_SET_FAN = 0x0003
    KINCO_REG_COMMAND = 0x0004
    KINCO_REG_LOAD_PROGRAM = 0x0010

    EXT_REG_ELECTRO_V = 0x2000
    EXT_REG_ELECTRO_UA = 0x2001
    EXT_REG_DELTA_P = 0x2002
    EXT_REG_GAS_CO = 0x2003
    EXT_REG_PROBE_T2 = 0x2010
    EXT_REG_PROBE_T3 = 0x2011
    EXT_REG_MASS_KG = 0x2020
    EXT_REG_RECIPE_ID = 0x2030
    EXT_REG_RECIPE_VER = 0x2031
    EXT_REG_MQTT_STATUS = 0x2040

    CMD_START = 1
    CMD_PAUSE = 2
    CMD_RESUME = 3
    CMD_STOP = 4
    CMD_LOAD_RECIPE = 5

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.kinco_host = config.get("kinco_host", "192.168.1.100")
        self.kinco_port = config.get("kinco_port", 502)
        self.extension_host = config.get("extension_host", "192.168.1.101")
        self.extension_port = config.get("extension_port", 503)
        self.unit_id = config.get("unit_id", 1)
        self.timeout_ms = config.get("timeout_ms", 3000)
        self.reconnect_backoff_ms = config.get("reconnect_backoff_ms", 1000)
        self._kinco_client: Any = None
        self._ext_client: Any = None
        self._subscribers: list[asyncio.Queue] = []
        self._tick_task: asyncio.Task | None = None

    async def connect(self) -> None:
        try:
            from pymodbus.client import AsyncModbusTcpClient
        except ImportError as e:
            raise ImportError(
                "pymodbus is required for FELETI_SMOKDriver. "
                "Install with: uv add pymodbus"
            ) from e

        self._kinco_client = AsyncModbusTcpClient(
            host=self.kinco_host,
            port=self.kinco_port,
            timeout=self.timeout_ms / 1000,
        )
        self._ext_client = AsyncModbusTcpClient(
            host=self.extension_host,
            port=self.extension_port,
            timeout=self.timeout_ms / 1000,
        )
        kinco_ok = await self._kinco_client.connect()
        ext_ok = await self._ext_client.connect()
        if not kinco_ok and not ext_ok:
            raise ConnectionError(
                f"Cannot connect to Kinco ({self.kinco_host}:{self.kinco_port}) "
                f"or extension module ({self.extension_host}:{self.extension_port})"
            )
        self._connected = True
        self._tick_task = asyncio.create_task(self._tick_loop())

    async def disconnect(self) -> None:
        self._connected = False
        if self._tick_task:
            self._tick_task.cancel()
            self._tick_task = None
        if self._kinco_client:
            self._kinco_client.close()
        if self._ext_client:
            self._ext_client.close()

    async def get_capabilities(self) -> ChamberCapabilities:
        return ChamberCapabilities(
            type=["горячее", "холодное", "электро"],
            max_load_kg=float(self.config.get("max_load_kg", 250)),
            volume_m3=float(self.config.get("volume_m3", 1.5)),
            power_kw=float(self.config.get("power_kw", 24)),
            voltage_v=int(self.config.get("voltage_v", 380)),
            max_phases=16,
            supports_electro=bool(self.config.get("supports_electro", True)),
            supports_static_smoke=True,
            supports_joint=True,
            supports_programs=True,
            supports_probes=int(self.config.get("supports_probes", 3)),
            supports_humidity_control=True,
            supports_smoke_density_control=True,
            protocols=["modbus_tcp", "mqtt"],
        )

    async def get_telemetry(self) -> ChamberTelemetry:
        t_chamber = await self._read_kinco_input(self.KINCO_REG_T_CHAMBER, scale=0.1)
        t_product = await self._read_kinco_input(self.KINCO_REG_T_PRODUCT, scale=0.1)
        humidity = await self._read_kinco_input(self.KINCO_REG_HUMIDITY, scale=0.1)
        smoke = await self._read_kinco_input(self.KINCO_REG_SMOKE)
        fan_rpm = await self._read_kinco_input(self.KINCO_REG_FAN_RPM)
        door_open = bool(await self._read_kinco_input(self.KINCO_REG_DOOR))
        current_phase = await self._read_kinco_input(self.KINCO_REG_PHASE)
        progress_raw = await self._read_kinco_input(self.KINCO_REG_PROGRESS)
        errors_reg = await self._read_kinco_input(self.KINCO_REG_ERRORS)
        electro_v = await self._read_ext_input(self.EXT_REG_ELECTRO_V, scale=0.1, default=0.0)
        electro_ua = await self._read_ext_input(self.EXT_REG_ELECTRO_UA, default=0.0)
        return ChamberTelemetry(
            chamber_id=self.chamber_id,
            ts=datetime.utcnow(),
            t_chamber=t_chamber,
            t_product=t_product,
            humidity=humidity,
            smoke_density=smoke,
            electro_voltage=electro_v,
            electro_current=electro_ua,
            fan_rpm=fan_rpm,
            door_open=door_open,
            current_phase=current_phase,
            phase_progress=progress_raw / 100.0,
            errors=self._decode_errors(errors_reg),
            raw={"errors_reg": errors_reg, "source": "feleti-smok"},
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
        recipe_id = recipe_version.get("recipe_id", 0)
        version_number = recipe_version.get("version_number", 1)
        await self._write_ext_holding(self.EXT_REG_RECIPE_ID, recipe_id)
        await self._write_ext_holding(self.EXT_REG_RECIPE_VER, version_number)
        await self._write_kinco_holding(self.KINCO_REG_LOAD_PROGRAM, 1)
        await asyncio.sleep(0.1)
        await self._write_kinco_holding(self.KINCO_REG_LOAD_PROGRAM, 0)

    async def start(self) -> None:
        await self._write_kinco_holding(self.KINCO_REG_COMMAND, self.CMD_START)

    async def pause(self) -> None:
        await self._write_kinco_holding(self.KINCO_REG_COMMAND, self.CMD_PAUSE)

    async def resume(self) -> None:
        await self._write_kinco_holding(self.KINCO_REG_COMMAND, self.CMD_RESUME)

    async def stop(self) -> None:
        await self._write_kinco_holding(self.KINCO_REG_COMMAND, self.CMD_STOP)

    async def get_status(self) -> dict[str, Any]:
        status_reg = await self._read_kinco_input(self.KINCO_REG_STATUS)
        return {
            "running": status_reg == 1,
            "paused": status_reg == 2,
            "error": status_reg == 3,
            "current_phase": await self._read_kinco_input(self.KINCO_REG_PHASE),
            "phase_progress": (await self._read_kinco_input(self.KINCO_REG_PROGRESS)) / 100.0,
        }

    async def _read_kinco_input(self, address: int, scale: float = 1.0, default: float | None = None) -> float:
        if not self._kinco_client or not self._kinco_client.connected:
            if default is not None:
                return default
            raise ConnectionError("Kinco client not connected")
        try:
            result = await self._kinco_client.read_input_registers(
                address=address, count=1, slave=self.unit_id
            )
            if result.isError():
                if default is not None:
                    return default
                return 0.0
            return result.registers[0] * scale
        except Exception:
            if default is not None:
                return default
            return 0.0

    async def _read_ext_input(self, address: int, scale: float = 1.0, default: float | None = None) -> float:
        if not self._ext_client or not self._ext_client.connected:
            return default if default is not None else 0.0
        try:
            result = await self._ext_client.read_input_registers(
                address=address, count=1, slave=self.unit_id
            )
            if result.isError():
                return default if default is not None else 0.0
            return result.registers[0] * scale
        except Exception:
            return default if default is not None else 0.0

    async def _write_kinco_holding(self, address: int, value: int) -> None:
        if not self._kinco_client or not self._kinco_client.connected:
            raise ConnectionError("Kinco client not connected")
        result = await self._kinco_client.write_register(
            address=address, value=value, slave=self.unit_id
        )
        if result.isError():
            raise RuntimeError(f"Kinco write error at 0x{address:04X}: {result}")

    async def _write_ext_holding(self, address: int, value: int) -> None:
        if not self._ext_client or not self._ext_client.connected:
            return
        try:
            await self._ext_client.write_register(
                address=address, value=value, slave=self.unit_id
            )
        except Exception:
            pass

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
            8: "water_low",
            9: "power_fault",
            10: "communication_lost",
            11: "program_error",
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
