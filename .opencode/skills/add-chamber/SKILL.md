# SKILL: add-chamber

> Добавление коптильной камеры в каталог. Используй при добавлении новой модели (своей или конкурента) в базу данных.
> Загружай совместно с `camera-driver` если нужен новый драйвер.

## 1. Структура камеры (реальная)

```python
Manufacturer:
  - id: int
  - name: str                       # "Ижица"
  - slug: str                       # "ijiza", уникальный
  - country: str | None             # "Россия"
  - website: str | None
  - description: str | None
  - is_our_brand: bool              # True для FELETI
  - is_competitor: bool             # True для Ижица/Mauting/...
  - sort_order: int                 # для отображения в каталоге
  - logo_url, created_at, updated_at

Chamber:
  - id: int
  - manufacturer_id: int            # FK на Manufacturer
  - model: str                      # "Varmen-1"
  - slug: str                       # "ijiza-varmen-1", уникальный ^[a-z0-9-]+$
  - type: enum[горячее|холодное|электро|универсальное|полугорячее|дымогенератор|неизвестно]
  - max_load_kg: float | None
  - volume_m3: float | None
  - power_kw: float | None
  - voltage_v: int | None           # 220/380
  - supports_static_smoke: bool
  - supports_electro: bool          # электростатика 10-30 кВ
  - supports_cold_smoke: bool
  - supports_cooling: bool          # холодильный агрегат
  - supports_freezing: bool         # заморозка
  - supports_joint: bool            # варка+копчение в одной камере
  - supported_protocols: list[str]  # ["modbus_tcp", "mqtt", "opc_ua", ...]
  - driver_class: str               # "VarmenDriver" | "FELETI_SMOKDriver" | ...
  - default_driver_config: dict     # {"host": "192.168.1.100", "port": 502, ...}
  - num_chambers: int               # для туннельных — сколько секций
  - num_carts: int                  # для туннельных — сколько вагонеток
  - num_probes: int                 # кол-во Pt100 в продукте
  - max_program_phases: int         # макс. фаз в программе
  - price_rrp_rub, price_dealer_rub, price_rrp_eur
  - images: list[str]               # URLs/paths
  - description: str
  - source_url, source
  - verified: bool                  # проверено инженером
  - created_at, updated_at
```

## 2. Алгоритм добавления камеры

### 2.1. Сбор данных
1. **Источник:** сайт производителя, каталог (PDF), YouTube-обзор, инженер, даташит.
2. **Поля для заполнения:**
   - Производитель (если нет в `seed/manufacturers` — создать).
   - Модель, slug, тип камеры.
   - ТТХ: max_load_kg, volume_m3, power_kw, voltage_v.
   - Поддерживаемые режимы (горячее/холодное/электро/комби/cooling/freezing).
   - Протоколы (Modbus TCP, OPC UA, MQTT, HTTP, proprietary).
   - Драйвер: существующий или новый.
   - Картинки (3–5 шт: внешний вид, внутренний, панель управления, ТТХ-табличка).
3. **Проверка:** указываем источник и `verified: false`.

### 2.2. Создание в коде (3 способа)

#### Способ 1: Seed (рекомендуемый для dev)
1. Открыть `backend/app/scripts/seed.py`.
2. Добавить производителя в `MANUFACTURERS` (если нового нет).
3. Добавить камеру в `CHAMBERS` (словарь по slug).
4. Запустить `python -m app.scripts.seed` — идемпотентно (по slug).

#### Способ 2: REST API (для production)
```
POST /api/v1/manufacturers  { "name": "...", "slug": "...", "is_competitor": true, ... }
POST /api/v1/chambers
{
  "manufacturer_id": 1,
  "model": "Varmen-1",
  "slug": "ijiza-varmen-1",
  "type": "электро",
  "max_load_kg": 50,
  "driver_class": "VarmenDriver",  # проверяется через реестр драйверов
  "default_driver_config": { "host": "192.168.1.100", "port": 502, "unit_id": 1 }
}
```

#### Способ 3: CSV/Excel импорт (TODO, для будущей сессии)

### 2.3. Шаблон для seed (CHAMBERS)
```python
"ijiza-varmen-1": {
    "manufacturer_slug": "ijiza",
    "model": "Varmen-1",
    "slug": "ijiza-varmen-1",
    "type": ChamberType.ELECTRO,
    "max_load_kg": 50.0,
    "volume_m3": 0.5,
    "power_kw": 8.0,
    "voltage_v": 380,
    "supports_static_smoke": True,
    "supports_electro": True,
    "supports_joint": True,
    "supported_protocols": ["modbus_tcp"],
    "driver_class": "VarmenDriver",
    "default_driver_config": {
        "host": "192.168.1.100",
        "port": 502,
        "unit_id": 1,
        "timeout_ms": 3000,
    },
    "num_chambers": 1,
    "num_carts": 1,
    "num_probes": 1,
    "max_program_phases": 16,
    "source": "https://ijiza.ru/catalog/varmen-1/ + каталог 2024",
    "verified": False,
    "images": ["/seed/chambers/varmen-1-1.jpg"],
    "description": "Универсальная камера с электростатикой. 50 кг загрузки, 8 кВт.",
},
```

## 3. Драйверы — карта соответствия

| Производитель | Модели | Драйвер | Протокол | Контроллер | Статус |
|---|---|---|---|---|---|
| **Ижица** | Varmen Mini, Varmen-1, Varmen-2, UTR.30–500, DL400–1200, Z115-25/50 | `VarmenDriver` | Modbus TCP | Varmen-1 | ✅ Реализован |
| **FELETI-SMOK** | Profi H/C/U, C-Ultra, U-Frost | `FELETI_SMOKDriver` | Modbus TCP :503 | Kinco + свой модуль | ✅ Реализован |
| **Fessmann** | T1900/T2500/T3000, Turbomat, FES.APP | `FessmannDriver` | OPC UA | FOOD.CON 2 | ⏳ TODO stub |
| **Kerres** | KK 2800, Jet Smoke, Hybrid Airflow | `KerresDriver` | HTTP/REST | собственный | ⏳ TODO stub |
| **Mauting** | Туннели 1–8 вагонеток | `MautingDriver` | Modbus TCP | Siemens S7 | ⏳ TODO stub |
| **AGROS** | Универсальные | `AGROSDriver` | Modbus TCP | собственный | ⏳ TODO stub |
| **Reich** | Термокамеры | `ReichDriver` | Modbus/Profinet | собственный | ⏳ TODO stub |
| **Generic** | Клоны (dev/test) | `SimulatedDriver` | — | — | ✅ Реализован |

**Регистрация**: `@register("Name")` декоратор + импорт в `app/drivers/__init__.py`.
**Список драйверов**: `GET /api/v1/chambers/drivers` → `["SimulatedDriver", "FELETI_SMOKDriver", "VarmenDriver"]`.

## 4. Спецификации камер FELETI-SMOK

> Заполняется в `docs/cameras/feleti-smok/`. Детали hardware — там.

**Структура спецификации:**
```
docs/cameras/feleti-smok/
├── SPEC.md                  # Общая спецификация (Profi H/C/U, C-Ultra, U-Frost)
├── KINCO_REGISTER_MAP.md    # Карта Modbus-регистров Kinco :502
├── EXTENSION_MODULE.md      # Модуль расширения :503 (RPi CM4)
├── SCHEMATIC.md             # Электрическая схема
├── BOM.md                   # Bill of Materials
├── HMI_PROGRAM.md           # Программа HMI-экрана
└── TEST_PROCEDURE.md        # Процедура приёмочных испытаний
```

## 5. Источники данных

| Источник | Тип | Как парсить |
|---|---|---|
| **Сайт производителя** | HTML | `beautifulsoup4`, `httpx` |
| **PDF-каталог** | PDF | `pdfplumber` для текста, `PyMuPDF` для таблиц |
| **YouTube-обзор** | Видео | `yt-dlp` + `whisper` для транскрибации |
| **Telegram-канал** | Посты | `Telethon` |
| **Инженер FELETI** | Устно | Записать, перевести в структурированный JSON |

Скрипты парсинга — `backend/app/services/{web_parser,pdf_parser,telegram_parser}.py` (TODO, сессия 6+).

## 6. Изображения

- **Хранилище:** MinIO bucket `chambers-images/`.
- **Форматы:** JPEG/PNG, max 2 МБ каждое.
- **Размеры:** 1920×1080 (full), 512×288 (thumb).
- **Оптимизация:** через `Pillow` (compress_level=82, progressive=True).
- **Alt-текст:** обязателен, описывает что на фото.

## 7. Чек-лист перед сохранением

- [ ] Производитель есть в `MANUFACTURERS` seed (с `is_our_brand` или `is_competitor`).
- [ ] Модель уникальна в рамках производителя.
- [ ] Slug уникален, формат `^[a-z0-9-]+$`.
- [ ] Тип из справочника (`ChamberType` enum: горячее/холодное/электро/универсальное/полугорячее/дымогенератор/неизвестно).
- [ ] ТТХ реалистичны (проверить диапазоны: max_load_kg 5–500, power_kw 2–50, voltage_v 220/380).
- [ ] `driver_class` зарегистрирован в `app/drivers/__init__.py`.
- [ ] `default_driver_config` валиден для выбранного драйвера.
- [ ] `supported_protocols` соответствует драйверу.
- [ ] Источник указан (`source_url`, `source`).
- [ ] `verified: false` (до проверки инженером).
- [ ] 3–5 изображений (опц., для production).
- [ ] `description` понятен (3–5 предложений).

## 8. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `camera-driver` — если нужен новый драйвер (см. SKILL camera-driver).
- `seed-data` — для сидирования.
- `research-competitor` — для парсинга каталогов конкурентов.
- `batches-lifecycle` — для запуска партий на этой камере.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при добавлении камеры в каталог.
