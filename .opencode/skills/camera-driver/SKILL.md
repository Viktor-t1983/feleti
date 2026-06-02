# SKILL: camera-driver

> Работа с драйверами камер. Используй при создании нового драйвера, отладке существующего или интеграции с новой камерой.

## 1. Архитектура

UI не знает, какая камера подключена. Работает с абстрактным **`ChamberGateway`**, который делегирует вызовы конкретному **`ChamberDriver`**.

```
┌──────────────────────────────────────────────────────┐
│  Frontend (PWA)                                       │
│  "Start", "Pause", "Stop", графики, рецепты            │
└──────────────────┬───────────────────────────────────┘
                   │ WebSocket + REST
┌──────────────────▼───────────────────────────────────┐
│  Backend (FastAPI) — ChamberGateway                   │
│  • get_capabilities()                                 │
│  • get_telemetry() / subscribe_telemetry()            │
│  • start_program(recipe) / pause() / resume() / stop()│
│  • load_recipe(recipe_id)                             │
└──────┬─────────────────────────────────────┬─────────┘
       │                                     │
 ┌─────▼──────────┐              ┌──────────▼──────────┐
 │  LOCAL CONNECTOR│              │  CLOUD CONNECTOR    │
 │  Modbus TCP     │              │  MQTT / HTTPS       │
 │  + OPC UA (опц.)│              │  + WebSocket        │
 └─────┬──────────┘              └──────────┬──────────┘
       │                                     │
       ▼                                     ▼
 ┌─────────────────┐                ┌────────────────────┐
 │ Kinco (FELETI)  │                │  FELETI Cloud      │
 │ Varmen (Ижица)  │                │  MQTT broker + API │
 │ Simulated (dev) │                └────────────────────┘
 └─────────────────┘
```

## 2. Интерфейс `ChamberDriver` (base.py)

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Any
from dataclasses import dataclass

@dataclass
class ChamberCapabilities:
    type: list[str]                       # ["горячее", "холодное", "электро"]
    max_load_kg: float
    max_phases: int
    supports_electro: bool
    supports_static_smoke: bool
    supports_joint: bool
    supports_programs: bool
    max_program_phases: int

@dataclass
class ChamberTelemetry:
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
    phase_progress: float                # 0..1
    errors: list[str]
    raw: dict[str, Any]

class ChamberDriver(ABC):
    @abstractmethod
    async def connect(self) -> None: ...
    
    @abstractmethod
    async def disconnect(self) -> None: ...
    
    @abstractmethod
    async def get_capabilities(self) -> ChamberCapabilities: ...
    
    @abstractmethod
    async def get_telemetry(self) -> ChamberTelemetry: ...
    
    @abstractmethod
    async def subscribe_telemetry(self) -> AsyncIterator[ChamberTelemetry]: ...
    
    @abstractmethod
    async def load_recipe(self, recipe_version: dict) -> None: ...
    
    @abstractmethod
    async def start(self) -> None: ...
    
    @abstractmethod
    async def pause(self) -> None: ...
    
    @abstractmethod
    async def resume(self) -> None: ...
    
    @abstractmethod
    async def stop(self) -> None: ...
    
    @abstractmethod
    async def get_status(self) -> dict: ...   # running|paused|stopped|error
```

## 3. Создание нового драйвера

### 3.1. Алгоритм
1. **Создать файл** `backend/app/drivers/<name>.py`.
2. **Наследовать** от `ChamberDriver`.
3. **Реализовать** все абстрактные методы.
4. **Зарегистрировать** в `backend/app/drivers/__init__.py`:
   ```python
   from .varmen import VarmenDriver
   from .feleti_smok import FELETI_SMOKDriver
   # ...
   
   DRIVERS = {
       "VarmenDriver": VarmenDriver,
       "FELETI_SMOKDriver": FELETI_SMOKDriver,
       # ...
   }
   ```
5. **Добавить конфиг** в `Chamber.default_driver_config` (в seed).
6. **Написать тесты** (моки, без реального устройства).
7. **Документация** в `docs/cameras/<manufacturer>/SPEC.md`.

### 3.2. Шаблон (на примере `SimulatedDriver`)

```python
import asyncio
import math
import random
from datetime import datetime
from .base import ChamberDriver, ChamberCapabilities, ChamberTelemetry

class SimulatedDriver(ChamberDriver):
    def __init__(self, config: dict):
        self.config = config
        self._connected = False
        self._running = False
        self._paused = False
        self._phase_index = 0
        self._phase_started_at = None
        self._t_chamber = 20.0
        self._t_product = 20.0
        self._program: list[dict] = []
        self._current_recipe_version: dict | None = None
    
    async def connect(self) -> None:
        await asyncio.sleep(0.05)
        self._connected = True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def get_capabilities(self) -> ChamberCapabilities:
        return ChamberCapabilities(
            type=["горячее", "холодное", "электро"],
            max_load_kg=250,
            max_phases=16,
            supports_electro=True,
            supports_static_smoke=True,
            supports_joint=True,
            supports_programs=True,
            max_program_phases=16,
        )
    
    async def get_telemetry(self) -> ChamberTelemetry:
        return ChamberTelemetry(
            chamber_id=self.config.get("chamber_id", 0),
            ts=datetime.utcnow(),
            t_chamber=round(self._t_chamber, 1),
            t_product=round(self._t_product, 1),
            humidity=50.0,
            smoke_density=20.0 if self._running else 0.0,
            electro_voltage=20.0 if self._running else 0.0,
            electro_current=25.0 if self._running else 0.0,
            fan_rpm=1500,
            door_open=False,
            current_phase=self._phase_index,
            phase_progress=0.0,
            errors=[],
            raw={},
        )
    
    async def subscribe_telemetry(self) -> AsyncIterator[ChamberTelemetry]:
        while self._connected:
            await self._tick()
            yield await self.get_telemetry()
            await asyncio.sleep(1.0)
    
    async def load_recipe(self, recipe_version: dict) -> None:
        self._current_recipe_version = recipe_version
        self._program = recipe_version.get("program", [])
        self._phase_index = 0
    
    async def start(self) -> None:
        self._running = True
        self._paused = False
        self._phase_index = 0
        self._phase_started_at = datetime.utcnow()
    
    async def pause(self) -> None:
        self._paused = True
    
    async def resume(self) -> None:
        self._paused = False
    
    async def stop(self) -> None:
        self._running = False
        self._paused = False
    
    async def get_status(self) -> dict:
        return {
            "running": self._running,
            "paused": self._paused,
            "phase": self._phase_index,
            "phase_name": self._program[self._phase_index]["phase"] if self._program else None,
        }
    
    async def _tick(self) -> None:
        if not self._running or self._paused or not self._program:
            return
        phase = self._program[self._phase_index]
        target_t = phase.get("t_chamber", 50)
        # Инерция: T_chamber приближается к target_t
        self._t_chamber += (target_t - self._t_chamber) * 0.05
        # T_product медленнее
        self._t_product += (self._t_chamber - self._t_product) * 0.02
        # Проверка перехода к следующей фазе
        elapsed = (datetime.utcnow() - self._phase_started_at).total_seconds() / 60
        if elapsed >= phase.get("duration_min", 60):
            self._phase_index += 1
            if self._phase_index >= len(self._program):
                self._running = False
            else:
                self._phase_started_at = datetime.utcnow()
```

### 3.3. Шаблон для реального Modbus TCP драйвера

```python
import asyncio
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from .base import ChamberDriver, ChamberCapabilities, ChamberTelemetry

class VarmenDriver(ChamberDriver):
    """Драйвер для камер Ижица Varmen-1 по Modbus TCP.
    
    Карта регистров — см. docs/cameras/varmen/REGISTER_MAP.md
    (DRAFT, требует верификации).
    """
    
    # Holding registers (read/write)
    REG_SET_T_CHAMBER = 0x0000
    REG_SET_HUMIDITY = 0x0001
    REG_SET_SMOKE = 0x0002
    REG_SET_FAN = 0x0003
    REG_COMMAND = 0x0004   # 1=start, 2=pause, 3=resume, 4=stop
    REG_PROGRAM_LOAD = 0x0010  # загрузить программу (16 фаз, по 8 регистров на фазу)
    
    # Input registers (read-only)
    REG_T_CHAMBER = 0x1000
    REG_T_PRODUCT = 0x1001
    REG_HUMIDITY = 0x1002
    REG_SMOKE_DENSITY = 0x1003
    REG_ELECTRO_V = 0x1004
    REG_ELECTRO_UA = 0x1005
    REG_FAN_RPM = 0x1006
    REG_DOOR_OPEN = 0x1007
    REG_CURRENT_PHASE = 0x1008
    REG_PHASE_PROGRESS = 0x1009  # 0..10000 (×100 для %)
    REG_ERRORS = 0x100A  # битовая маска
    REG_STATUS = 0x100B  # 0=idle, 1=running, 2=paused, 3=error
    
    def __init__(self, config: dict):
        self.config = config
        self.host = config["host"]
        self.port = config.get("port", 502)
        self.unit_id = config.get("unit_id", 1)
        self.timeout_ms = config.get("timeout_ms", 3000)
        self._client: AsyncModbusTcpClient | None = None
        self._connected = False
    
    async def connect(self) -> None:
        self._client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout_ms / 1000,
        )
        await self._client.connect()
        if not self._client.connected:
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}")
        self._connected = True
    
    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._connected = False
    
    async def _read_input(self, address: int) -> int:
        if not self._client or not self._connected:
            raise ConnectionError("Not connected")
        result = await self._client.read_input_registers(
            address=address, count=1, slave=self.unit_id
        )
        if result.isError():
            raise ModbusException(f"Read error at 0x{address:04X}: {result}")
        return result.registers[0]
    
    async def _write_holding(self, address: int, value: int) -> None:
        if not self._client or not self._connected:
            raise ConnectionError("Not connected")
        result = await self._client.write_register(
            address=address, value=value, slave=self.unit_id
        )
        if result.isError():
            raise ModbusException(f"Write error at 0x{address:04X}: {result}")
    
    async def get_telemetry(self) -> ChamberTelemetry:
        t_chamber = await self._read_input(self.REG_T_CHAMBER) / 10.0
        t_product = await self._read_input(self.REG_T_PRODUCT) / 10.0
        humidity = await self._read_input(self.REG_HUMIDITY) / 10.0
        smoke = await self._read_input(self.REG_SMOKE_DENSITY)
        electro_v = await self._read_input(self.REG_ELECTRO_V) / 10.0
        electro_ua = await self._read_input(self.REG_ELECTRO_UA)
        fan_rpm = await self._read_input(self.REG_FAN_RPM)
        door_open = bool(await self._read_input(self.REG_DOOR_OPEN))
        current_phase = await self._read_input(self.REG_CURRENT_PHASE)
        phase_progress = await self._read_input(self.REG_PHASE_PROGRESS) / 100.0
        errors_reg = await self._read_input(self.REG_ERRORS)
        errors = self._decode_errors(errors_reg)
        return ChamberTelemetry(
            chamber_id=self.config.get("chamber_id", 0),
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
            phase_progress=phase_progress,
            errors=errors,
            raw={"errors_reg": errors_reg},
        )
    
    async def start(self) -> None:
        await self._write_holding(self.REG_COMMAND, 1)
    
    async def pause(self) -> None:
        await self._write_holding(self.REG_COMMAND, 2)
    
    async def resume(self) -> None:
        await self._write_holding(self.REG_COMMAND, 3)
    
    async def stop(self) -> None:
        await self._write_holding(self.REG_COMMAND, 4)
    
    # ... остальные методы
```

## 4. Гибридный доступ (локальный + облако)

Драйвер может быть подключён через **два канала**:
1. **Локальный Modbus TCP** (LAN, приоритет) — `<100 мс`.
2. **Облако MQTT/HTTPS** (интернет) — `0.5–2 с`.

Реализация — в `services/chamber_gateway.py`:
```python
class ChamberGateway:
    def __init__(self, chamber: Chamber):
        self.chamber = chamber
        self.local_driver: ChamberDriver | None = None
        self.cloud_driver: ChamberDriver | None = None
        self._active = "local"  # local | cloud
    
    async def start(self):
        # Пробуем локальный
        try:
            self.local_driver = create_driver(self.chamber.driver_class, self.chamber.default_driver_config)
            await asyncio.wait_for(self.local_driver.connect(), timeout=2.0)
            self._active = "local"
            return
        except Exception:
            pass
        # Fallback на облако
        self.cloud_driver = create_driver(f"{self.chamber.driver_class}Cloud", self.chamber.default_driver_config)
        await self.cloud_driver.connect()
        self._active = "cloud"
    
    async def get_telemetry(self) -> ChamberTelemetry:
        if self._active == "local" and self.local_driver:
            try:
                return await asyncio.wait_for(self.local_driver.get_telemetry(), timeout=2.0)
            except Exception:
                # Switch to cloud
                self._active = "cloud"
        if self.cloud_driver:
            return await self.cloud_driver.get_telemetry()
        raise ConnectionError("No channel available")
```

## 5. Телеметрия: подписка и WebSocket

Драйвер → `subscribe_telemetry()` → AsyncIterator → `ChamberGateway` → Redis pub/sub → `FastAPI WebSocket` → Frontend.

```python
# backend/app/api/v1/telemetry.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

@router.websocket("/ws")
async def telemetry_ws(websocket: WebSocket, chamber_id: int):
    await websocket.accept()
    chamber = await get_chamber(chamber_id)
    gateway = ChamberGateway(chamber)
    await gateway.start()
    try:
        async for telemetry in gateway.local_driver.subscribe_telemetry():
            await websocket.send_json({
                "type": "telemetry",
                "chamber_id": chamber_id,
                "ts": telemetry.ts.isoformat(),
                "t_chamber": telemetry.t_chamber,
                "t_product": telemetry.t_product,
                "humidity": telemetry.humidity,
                "smoke_density": telemetry.smoke_density,
                "electro_voltage": telemetry.electro_voltage,
                "electro_current": telemetry.electro_current,
                "fan_rpm": telemetry.fan_rpm,
                "door_open": telemetry.door_open,
                "current_phase": telemetry.current_phase,
                "phase_progress": telemetry.phase_progress,
                "errors": telemetry.errors,
            })
    except WebSocketDisconnect:
        await gateway.disconnect()
```

## 6. Тестирование

- **Unit-тесты:** с моком (без реального устройства).
- **Integration-тесты:** с `SimulatedDriver` (фейк, но реалистичный).
- **Hardware-тесты:** только с реальной камерой (на стенде).

```python
# tests/test_varmen_driver.py
import pytest
from app.drivers.varmen import VarmenDriver

@pytest.fixture
def driver():
    return VarmenDriver({"host": "127.0.0.1", "port": 5020, "unit_id": 1})

@pytest.mark.asyncio
async def test_connect_success(driver, monkeypatch):
    # Mock pymodbus client
    class MockClient:
        connected = True
        async def connect(self): pass
        def close(self): pass
    monkeypatch.setattr(driver, "_client", MockClient())
    await driver.connect()
    assert driver._connected is True
```

## 7. ChamberGateway (уровень выше драйвера)

> Реализован в `backend/app/services/chamber_gateway.py` (сессия 5).

`ChamberGateway` — singleton, абстрагирует работу с пулом драйверов. UI/Endpoints не работают с драйверами напрямую — только через gateway.

### 7.1. Архитектура

```
┌──────────────────────────────────────────────────────────┐
│  FastAPI endpoints (batches, telemetry, ...)              │
│  Annotated[ChamberGateway, Depends(get_chamber_gateway)]  │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│  ChamberGateway (singleton)                               │
│  ├─ _drivers: dict[int, ChamberDriver]   # пул по chamber_id│
│  ├─ _buffer:  dict[int, deque[Sample]]   # 3600 точек/камера│
│  ├─ _subscribers: dict[int, list[Queue]] # fan-out для WS   │
│  └─ _tasks:   dict[int, asyncio.Task]    # telemetry loop    │
└──────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   SimulatedDriver  VarmenDriver  FELETI_SMOKDriver  ...
```

### 7.2. Публичный API

```python
class ChamberGateway:
    async def get_driver(chamber_id, driver_class, connection) -> ChamberDriver
    async def release(chamber_id) -> None
    async def shutdown() -> None

    # Управление партией
    async def start_batch(chamber_id, driver_class, connection, recipe_program) -> None
    async def pause_batch(chamber_id) -> None
    async def resume_batch(chamber_id) -> None
    async def stop_batch(chamber_id) -> None

    # Телеметрия
    async def get_telemetry(chamber_id) -> ChamberTelemetry
    async def get_status(chamber_id) -> dict
    def latest_telemetry(chamber_id) -> ChamberTelemetry | None
    def telemetry_history(chamber_id, limit=600) -> list[ChamberTelemetry]

    # Подписки
    def subscribe(chamber_id) -> asyncio.Queue[ChamberTelemetry]
    def unsubscribe(chamber_id, queue) -> None

    @staticmethod
    def available_drivers() -> list[str]
```

### 7.3. Особенности реализации

- **Lazy init**: драйвер создаётся при первом обращении, не при старте gateway.
- **Per-chamber Lock**: `asyncio.Lock` на каждую камеру, защита от двойного connect.
- **Auto-reconnect**: при ошибке `get_telemetry` — `await asyncio.sleep(1.0)` и повтор.
- **Кольцевой буфер**: `deque(maxlen=3600)` — 1 час при 1 Hz.
- **Fan-out**: каждый подписчик получает свою `asyncio.Queue(maxsize=120)`, медленный подписчик теряет точки.
- **Singleton**: `get_chamber_gateway()` — async singleton, инстанс на всё приложение.
- **Shutdown**: TODO вызвать в FastAPI lifespan (`app/main.py`).

### 7.4. Интеграция в FastAPI endpoint

```python
from app.services.chamber_gateway import ChamberGateway, get_chamber_gateway
from typing import Annotated
from fastapi import Depends

@router.post("/batches/{batch_id}/start")
async def start_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> BatchRead:
    # ... используем gateway.start_batch(...)
    pass
```

### 7.5. Когда НЕЛЬЗЯ напрямую работать с драйвером

- ❌ Из endpoint'ов — только через gateway.
- ❌ Создавать инстанс драйвера руками — `create_driver()` только внутри gateway.
- ❌ Хранить ссылку на драйвер в endpoint или request scope.

### 7.6. TODO для будущих сессий

- [ ] Подключить Redis pub/sub для синхронизации буфера между процессами (масштабирование).
- [ ] Persist telemetry в `TelemetryReading` и `BatchTelemetry` (для исторического анализа).
- [ ] Auto-recovery для драйверов при обрыве (exponential backoff).
- [ ] Метрики в Prometheus: кол-во активных драйверов, latency get_telemetry, размер буфера.

## 8. Чек-лист при создании драйвера

- [ ] Файл `backend/app/drivers/<name>.py` создан.
- [ ] Наследует от `ChamberDriver`.
- [ ] Реализованы все абстрактные методы.
- [ ] Конфиг через `__init__(config: dict)`, не через env.
- [ ] Timeout на каждую операцию (нельзя блокировать навсегда).
- [ ] Ошибки — специфичные исключения (`ConnectionError`, `ModbusException`).
- [ ] Reconnect при обрыве (exponential backoff).
- [ ] Зарегистрирован в `__init__.py` через `@register("Name")` (не DRIVERS dict).
- [ ] Карта регистров задокументирована в `docs/cameras/<manufacturer>/REGISTER_MAP.md`.
- [ ] Unit-тесты (с моком).
- [ ] Integration-тест с `SimulatedDriver` для проверки верхнего уровня.
- [ ] Логирование через `logging` (не print, не loguru пока).
- [ ] Telemetry: `ts` — UTC (`datetime.utcnow()` или `datetime.now(timezone.utc).replace(tzinfo=None)`).

## 9. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `add-chamber` — для регистрации камеры в каталоге.
- `seed-data` — для сидирования камер.
- `batches-lifecycle` — для управления партиями через gateway.
- `telemetry-websocket` — для live-стрима из gateway.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при создании/отладке драйвера камеры.
