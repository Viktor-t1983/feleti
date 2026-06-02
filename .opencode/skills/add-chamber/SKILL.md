# SKILL: add-chamber

> Добавление коптильной камеры в каталог. Используй при добавлении новой модели (своей или конкурента) в базу данных.

## 1. Структура камеры

```python
Chamber:
  - id: int
  - manufacturer_id: int
  - model: str                       # "Varmen-1"
  - slug: str                        # "ijiza-varmen-1"
  - type: enum[горячее|холодное|электро|универсальное]
  - max_load_kg: float
  - volume_m3: float
  - power_kw: float
  - voltage_v: int
  - supports_static_smoke: bool
  - supports_electro: bool           # электростатика
  - supports_joint: bool             # варка+копчение в одной камере
  - supported_protocols: list[str]   # ["modbus_tcp", "mqtt", "opc_ua", ...]
  - driver_class: str                # "VarmenDriver" | "FELETI_SMOKDriver" | ...
  - default_driver_config: dict      # {"host": "192.168.1.100", "port": 502, ...}
  - num_chambers: int                # для туннельных — сколько секций
  - num_carts: int                   # для туннельных — сколько вагонеток
  - images: list[str]                # URLs/paths
  - description: str
  - created_at, updated_at
```

## 2. Алгоритм добавления камеры

### 2.1. Сбор данных
1. **Источник:** сайт производителя, каталог (PDF), YouTube-обзор, инженер, даташит.
2. **Поля для заполнения:**
   - Производитель (если нет в `seed/manufacturers.json` — создать).
   - Модель, slug, тип камеры.
   - ТТХ: max_load_kg, volume_m3, power_kw, voltage_v.
   - Поддерживаемые режимы (горячее/холодное/электро/комби).
   - Протоколы (Modbus TCP, OPC UA, MQTT, HTTP, proprietary).
   - Драйвер: существующий или новый.
   - Картинки (3–5 шт: внешний вид, внутренний, панель управления, ТТХ-табличка).
3. **Проверка:** указываем источник и `verified: false`.

### 2.2. Создание в коде
1. **Найти `manufacturer_id`** — если производителя нет, создать.
2. **Определить `driver_class`:**
   - Существующий: `SimulatedDriver`, `VarmenDriver`, `FessmannDriver`, `KerresDriver`, `MautingDriver`, `FELETI_SMOKDriver`.
   - Новый — добавить через скилл `camera-driver`.
3. **Заполнить `default_driver_config`** (IP, порт, ID, опции).
4. **Сохранить** в `data/seed/chambers/<slug>.json`.

### 2.3. Шаблон JSON (для seed)
```json
{
  "manufacturer": "Ижица",
  "model": "Varmen-1",
  "slug": "ijiza-varmen-1",
  "type": "электро",
  "max_load_kg": 50,
  "volume_m3": 0.5,
  "power_kw": 8,
  "voltage_v": 380,
  "supports_static_smoke": true,
  "supports_electro": true,
  "supports_joint": true,
  "supported_protocols": ["modbus_tcp"],
  "driver_class": "VarmenDriver",
  "default_driver_config": {
    "host": "192.168.1.100",
    "port": 502,
    "unit_id": 1,
    "timeout_ms": 3000
  },
  "num_chambers": 1,
  "num_carts": 1,
  "source": "https://ijiza.ru/catalog/varmen-1/ + каталог 2024",
  "verified": false,
  "images": [
    "/seed/chambers/varmen-1-1.jpg",
    "/seed/chambers/varmen-1-2.jpg"
  ],
  "description": "Универсальная камера с электростатикой. 50 кг загрузки, 8 кВт. Для Horeca и малых производств."
}
```

## 3. Драйверы — карта соответствия

| Производитель | Модели | Драйвер | Протокол | Контроллер |
|---|---|---|---|---|
| **Ижица** | Varmen Mini, Varmen-1, Varmen-2, UTR.30–500, DL400–1200, Z115-25/50 | `VarmenDriver` | Modbus TCP | Varmen-1 |
| **Fessmann** | T1900/T2500/T3000, Turbomat, FES.APP | `FessmannDriver` | OPC UA | FOOD.CON 2 |
| **Kerres** | KK 2800, Jet Smoke, Hybrid Airflow | `KerresDriver` | HTTP/REST | собственный |
| **Mauting** | Туннели 1–8 вагонеток | `MautingDriver` | Modbus TCP | Siemens S7 |
| **AGROS** | Универсальные | `AGROSDriver` | Modbus TCP | собственный |
| **Reich** | Термокамеры | `ReichDriver` | Modbus/Profinet | собственный |
| **FELETI-SMOK** | Profi/Industrial (своя разработка) | `FELETI_SMOKDriver` | Modbus TCP | Kinco + свой модуль |
| **Generic** | Клоны | `SimulatedDriver` | — | — |

## 4. Спецификации камер FELETI-SMOK

> Заполняется в `docs/cameras/feleti-smok/SPEC.md`. Детали hardware — там.

**Структура спецификации:**
```
docs/cameras/feleti-smok/
├── SPEC.md                  # Общая спецификация
├── KINCO_REGISTER_MAP.md    # Карта Modbus-регистров Kinco
├── EXTENSION_MODULE.md      # Модуль расширения
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

Скрипты парсинга — `backend/app/services/{web_parser,pdf_parser,telegram_parser}.py`.

## 6. Изображения

- **Хранилище:** MinIO bucket `chambers-images/`.
- **Форматы:** JPEG/PNG, max 2 МБ каждое.
- **Размеры:** 1920×1080 (full), 512×288 (thumb).
- **Оптимизация:** через `Pillow` (compress_level=82, progressive=True).
- **Alt-текст:** обязателен, описывает что на фото.

## 7. Чек-лист перед сохранением

- [ ] Производитель есть в `data/seed/manufacturers.json`.
- [ ] Модель уникальна в рамках производителя.
- [ ] Slug уникален.
- [ ] Тип из справочника (горячее/холодное/электро/универсальное).
- [ ] ТТХ реалистичны (проверить диапазоны).
- [ ] `driver_class` существует в `backend/app/drivers/`.
- [ ] `default_driver_config` валиден для выбранного драйвера.
- [ ] `supported_protocols` соответствует драйверу.
- [ ] Источник указан (`source`).
- [ ] `verified: false` (до проверки инженером).
- [ ] 3–5 изображений загружены в MinIO.
- [ ] `description` понятен (3–5 предложений).

## 8. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `camera-driver` — если нужен новый драйвер.
- `seed-data` — для сидирования.
- `research-competitor` — для парсинга каталогов конкурентов.

---

**Версия:** 0.1.0
**Загружай:** при добавлении камеры в каталог.
