# 🔧 CAMERA_DRIVER.md — Универсальный драйвер коптильной камеры

> **Главный принцип:** UI не знает, какая камера подключена. Работает с абстрактным `ChamberGateway`. Каждый производитель = свой драйвер.

---

## 1. Архитектура (2 режима: локальный + облако)

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (PWA)                                  │
│   "Start", "Pause", "Stop", графики, рецепты — одинаково везде    │
└─────────────────────────────┬────────────────────────────────────┘
                              │ WebSocket + REST
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              Backend (FastAPI) — ChamberGateway                   │
│  • get_capabilities()                                             │
│  • get_telemetry() / subscribe_telemetry()                        │
│  • start_program(recipe) / pause() / resume() / stop()            │
│  • load_recipe(recipe_id)                                         │
└────────────┬─────────────────────────────────────┬───────────────┘
             │                                     │
   ┌─────────▼─────────┐                ┌─────────▼──────────┐
   │  LOCAL CONNECTOR  │                │  CLOUD CONNECTOR   │
   │  (в цеху, LAN)    │                │  (через интернет)  │
   │  Modbus TCP       │                │  MQTT / HTTPS      │
   │  + OPC UA (опц.)  │                │  + WebSocket       │
   └─────────┬─────────┘                └──────────┬──────────┘
             │                                     │
             ▼                                     ▼
   ┌─────────────────────┐              ┌─────────────────────┐
   │  Edge Box (RPi/PLC) │              │  FELETI Cloud       │
   │  в цеху у камеры    │              │  MQTT broker + API  │
   │  → Modbus TCP       │              │  → Bridge to UI     │
   │    master           │              │                     │
   └─────────┬───────────┘              └──────────┬──────────┘
              │                                     │
              └──────────────┬──────────────────────┘
                             ▼
                   ┌──────────────────────┐
                   │  Контроллер камеры   │
                   │  (Ижица Varmen-1,    │
                   │   Fessmann FOOD.CON, │
                   │   собственный FELETI)│
                   └──────────────────────┘
```

### Камера FELETI-SMOK: двухуровневая архитектура (Kinco + свой модуль)

Зафиксировано 2026-06-02: камеры FELETI-SMOK строятся на базе **Kinco HMI/PLC** (Китай) с **собственным модулем расширения** для опциональных функций (электростатика, доп. датчики, edge-AI).

```
        ┌─────────────────────────────────────────────────────┐
        │         Backend (ChamberGateway / FELETI_SMOKDriver)│
        │                  Modbus TCP master                  │
        └──────────────────┬──────────────────────────────────┘
                           │ Ethernet (LAN) / MQTT (cloud)
                           ▼
        ┌─────────────────────────────────────────────────────┐
        │   Свой модуль расширения FELETI-SMOK (Modbus slave) │
        │  • Электростатика 10–30 кВ (опция, апгрейд)         │
        │  • Доп. датчики: ΔP, газ, pH, термокарта (multi-Pt) │
        │  • Edge-cache рецептов (RPi CM4 / ESP32)             │
        │  • Локальный AI-инференс (TFLite, опц.)              │
        │  • MQTT-мост в облако (опц.)                        │
        └──────────────────┬──────────────────────────────────┘
                           │ Modbus TCP / RS-485 (внутри корпуса)
                           ▼
        ┌─────────────────────────────────────────────────────┐
        │   Kinco HMI + PLC (Китай) — базовый контроллер      │
        │  • HMI: Kinco MT series (сенсорный экран 7–10")    │
        │  • PLC: Kinco K5/K7 (дискретные/аналоговые I/O)     │
        │  • Modbus TCP server (порт 502)                     │
        │  • Modbus RTU master к нижнему уровню (Pt100, ТЭН)  │
        │  • Базовые датчики: Pt100 камера+продукт, влажн.,  │
        │    дым, дверь, вентилятор                           │
        │  • Управление: ТЭН, вентилятор, дымогенератор,     │
        │    клапаны, дверной замок                           │
        │  • Локальная программа (8–16 фаз), fallback         │
        └─────────────────────────────────────────────────────┘
```

**Зачем двухуровневая:**
- **Kinco** даёт надёжную промышленную базу, готовую HMI для оператора, сертификацию CE/EAC, Modbus TCP «из коробки». Разработка firmware — быстрая (LAD-логика или C).
- **Свой модуль расширения** — наша интеллектуальная собственность, IP, конкурентное преимущество. Сюда выносим всё, что отличает FELETI-SMOK от других камер на Kinco: электростатика, продвинутая телеметрия, edge-AI, MQTT-мост.
- **Backend общается** со своим модулем расширения (не с Kinco напрямую) — это даёт стабильный API, не зависящий от версии Kinco-прошивки.

Детали: `docs/cameras/feleti-smok/SPEC.md` (в плане).
```

### Зачем два режима (локальный + облако)

| Режим | Когда | Задержка | Надёжность |
|---|---|---|---|
| **Local Modbus TCP** | В цеху, оператор у камеры | <100 мс | Не зависит от интернета |
| **Cloud MQTT/HTTPS** | Удалённо, директор, аудит, аналитика | 0.5–2 с | Работает через NAT, мобильный интернет |

**Дублирование:** данные телеметрии летят в оба канала одновременно. Если локальный канал пропал — UI переключается на облачный (graceful degradation).

---

## 2. Абстрактный интерфейс (ChamberGateway)

```python
# backend/app/services/chamber_gateway/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable
from app.schemas.chamber import ChamberCapabilities, ChamberTelemetry, ChamberCommand, ChamberCommandResult

class ChamberGateway(ABC):
    """Абстрактный интерфейс к коптильной камере любого производителя."""

    def __init__(self, chamber_id: int, config: dict):
        self.chamber_id = chamber_id
        self.config = config
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def get_capabilities(self) -> ChamberCapabilities:
        """Что умеет камера: режимы, датчики, дымогенераторы, пределы."""

    @abstractmethod
    async def get_telemetry(self) -> ChamberTelemetry:
        """Снимок текущих показаний."""

    @abstractmethod
    async def subscribe_telemetry(self, callback: Callable[[ChamberTelemetry], None]) -> None:
        """Подписка на стрим телеметрии (вызывает callback каждые N мс)."""

    @abstractmethod
    async def start_program(self, program: "Program") -> ChamberCommandResult:
        """Загрузить и запустить программу копчения."""

    @abstractmethod
    async def pause(self) -> ChamberCommandResult: ...
    @abstractmethod
    async def resume(self) -> ChamberCommandResult: ...
    @abstractmethod
    async def stop(self) -> ChamberCommandResult: ...

    @abstractmethod
    async def set_temperature(self, t_c: float) -> ChamberCommandResult: ...
    @abstractmethod
    async def set_humidity(self, percent: float) -> ChamberCommandResult: ...
    @abstractmethod
    async def set_smoke_density(self, percent: float) -> ChamberCommandResult: ...
    @abstractmethod
    async def set_fan_speed(self, percent: float) -> ChamberCommandResult: ...
```

---

## 3. Реализованные драйверы

| Драйвер | Протокол | Статус | Файл |
|---|---|---|---|
| **SimulatedDriver** | нет (мок) | ✅ MVP | `simulated.py` |
| **VarmenDriver** | Modbus TCP | 🔄 в работе | `varmen.py` |
| **FessmannDriver** | OPC UA / FOOD.CON | ⏳ | `fessmann.py` |
| **KerresDriver** | HTTP/REST | ⏳ | `kerres.py` |
| **MautingDriver** | Modbus TCP / Profinet | ⏳ | `mauting.py` |
| **FELETI_SMOK_Driver** | Modbus TCP (свой) | ⏳ после ТЗ камеры | `feleti_smok.py` |

---

## 4. Modbus TCP — карта регистров Varmen (черновик)

> ⚠️ **Требует верификации** по фактической документации Varmen-1.

```
HOLDING REGISTERS (чтение/запись):
0x0000 (40001) — режим работы: 0=idle, 1=drying, 2=smoking_hot, 3=smoking_cold, 4=cooking, 5=baking, 6=cooling
0x0001 — целевая t °C (×10) (например 850 = 85.0°C)
0x0002 — целевая влажность % (×10)
0x0003 — целевая скорость вентилятора %
0x0004 — целевая плотность дыма %
0x0005 — команда: 0=stop, 1=start, 2=pause, 3=resume
0x0006-0x001F — 20 регистров для шагов программы (по 5 регистров на шаг: t, влажность, время_мин, вентилятор, дым)
0x0020-0x003F — параметры рецепта (строка, до 32 регистров)

INPUT REGISTERS (только чтение):
0x1000 — текущая t °C (×10)
0x1001 — текущая влажность % (×10)
0x1002 — текущая скорость вентилятора %
0x1003 — текущая плотность дыма %
0x1004 — t в центре продукта (зонд) ×10
0x1005 — текущий шаг программы
0x1006 — оставшееся время шага (мин)
0x1007 — статус: 0=idle, 1=running, 2=paused, 3=alarm, 4=done
0x1008 — код ошибки
0x1009 — уровень воды (бак парогенератора) %
0x100A — уровень щепы (дымогенератор) %
0x100B — дверь открыта/закрыта

COILS (bool):
0x2000 — дымогенератор включён
0x2001 — ТЭН включён
0x2002 — парогенератор включён
0x2003 — вентилятор включён
0x2004 — тревога
```

Эту карту нужно верифицировать по паспорту Varmen-1 (если найдём) или reverse-engineer по Wireshark-сниферу.

---

## 5. Telemetry model

```python
# backend/app/schemas/chamber.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ChamberMode(str, Enum):
    IDLE = "idle"
    DRYING = "drying"
    SMOKING_HOT = "smoking_hot"
    SMOKING_COLD = "smoking_cold"
    COOKING = "cooking"
    BAKING = "baking"
    COOLING = "cooling"
    DONE = "done"
    ALARM = "alarm"

class ChamberCapabilities(BaseModel):
    modes: list[ChamberMode]
    temp_range_c: tuple[float, float]   # (min, max)
    humidity_range_pct: tuple[float, float]
    fan_speed_range_pct: tuple[float, float]
    has_smoke_generator: bool
    has_steam_generator: bool
    has_core_probe: bool
    max_steps_per_program: int
    has_electrostatic_smoking: bool
    has_friction_smoke: bool
    has_atomizer: bool
    has_jet_smoke: bool

class ChamberTelemetry(BaseModel):
    chamber_id: int
    timestamp: datetime
    mode: ChamberMode
    status: str  # running / paused / stopped / alarm
    temperature_c: float
    humidity_pct: float
    fan_speed_pct: float
    smoke_density_pct: float
    core_temp_c: float | None
    current_step: int
    step_remaining_min: int
    alarm_code: str | None
    water_level_pct: float | None
    chip_level_pct: float | None
    door_open: bool
```

---

## 6. План реализации

- [x] Спроектировать `ChamberGateway` интерфейс
- [x] `SimulatedDriver` (мок с физ-моделью)
- [ ] `VarmenDriver` (Modbus TCP)
- [ ] Найти/составить карту регистров Varmen-1
- [ ] Протестировать на реальной камере (если есть доступ)
- [ ] `FessmannDriver` (OPC UA)
- [ ] `KerresDriver` (HTTP)
- [ ] `MautingDriver` (Modbus TCP/Profinet)
- [ ] `FELETI_SMOK_Driver` (собственный, после ТЗ камеры)
- [ ] Cloud connector (MQTT bridge)
- [ ] Graceful degradation: local → cloud fallback
