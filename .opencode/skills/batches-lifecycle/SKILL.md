# SKILL: batches-lifecycle

> Создание и управление партиями (запусками рецептов на камерах). Загружай при работе с эндпоинтами `/batches/*`.
> Загружай совместно с `camera-driver` (для ChamberGateway) и `add-recipe` (для RecipeVersion).

## 1. Что такое партия

`Batch` — конкретный запуск программы рецепта в конкретной камере. Имеет жизненный цикл и накапливает телеметрию, фазы, ошибки.

**Жизненный цикл:**
```
PLANNED ──start──► RUNNING ──pause──► PAUSED ──resume──► RUNNING
   │                  │                  │                  │
   │                  ├──cancel──────────┴──cancel──────────┤
   │                  │                                      │
   │                  ├──complete──────┐                     │
   │                  │                ▼                     │
   │                  │           COMPLETED                  │
   ▼                  ▼                                      ▼
CANCELLED         CANCELLED                              CANCELLED
   │                  │                                      │
   ▼                  ▼                                      ▼
DELETE          DELETE (если CANCELLED/COMPLETED)        DELETE
```

## 2. Структура модели (реальная)

```python
Batch:
  - id: int
  - recipe_version_id: int         # FK на RecipeVersion
  - chamber_id: int                # FK на Chamber
  - operator_id: int | None        # FK на User
  - batch_number: str              # "B-20260602-XYZ", уникальный
  - status: BatchStatus            # planned|queued|running|paused|completed|cancelled|failed
  - product_weight_kg: float | None
  - yield_kg: float | None
  - losses_percent: float | None
  - planned_start, actual_start, actual_end: datetime | None
  - notes: str | None
  - errors: list[str]              # JSON-массив строк
  - created_at, updated_at

BatchPhase:
  - id, batch_id, phase_index
  - name, planned_duration_min, actual_duration_min
  - actual_start, actual_end
  - set_t_chamber, set_humidity, set_smoke, set_electro_voltage_kv, set_fan_speed_percent
  - avg_t_chamber, avg_t_product, avg_humidity
  - notes

BatchTelemetry:
  - id, batch_id, ts
  - t_chamber, t_product, humidity, smoke_density
  - electro_voltage, electro_current, fan_rpm
  - door_open, current_phase, phase_progress
  - errors
```

## 3. API Endpoints (реальные)

### 3.1. CRUD
```
GET    /api/v1/batches                              # список с пагинацией
GET    /api/v1/batches/{id}                         # детальная карточка (с фазами)
POST   /api/v1/batches                              # создать в PLANNED
PATCH  /api/v1/batches/{id}                         # обновить метаданные
DELETE /api/v1/batches/{id}                         # удалить (только PLANNED/CANCELLED/COMPLETED)
```

### 3.2. Lifecycle
```
POST /api/v1/batches/{id}/start                     # загрузить программу в камеру и стартовать
POST /api/v1/batches/{id}/pause                     # пауза (только из RUNNING)
POST /api/v1/batches/{id}/resume                    # снять с паузы (только из PAUSED)
POST /api/v1/batches/{id}/cancel                    # остановить + CANCELLED (опц. note)
POST /api/v1/batches/{id}/complete                  # остановить + COMPLETED (опц. note)
```

### 3.3. Фильтры для list
- `chamber_id: int` — камеры
- `recipe_id: int` — по `Recipe.id` (через subquery в `RecipeVersion`)
- `status: BatchStatus` — planned/running/paused/...

## 4. Алгоритм создания партии

### 4.1. Предусловия
1. **Камера** существует в `chambers` (с валидным `driver_class` и `default_driver_config`).
2. **Версия рецепта** существует в `recipe_versions` со статусом `APPROVED` или `PENDING`.
3. **batch_number** уникален (рекомендуемый формат: `B-{YYYYMMDD}-{short_uuid}`).

### 4.2. Создание
```python
# Через REST API
POST /api/v1/batches
{
  "recipe_version_id": 1,
  "chamber_id": 1,
  "batch_number": "B-20260602-ABC1",
  "product_weight_kg": 50.0,
  "planned_start": "2026-06-03T08:00:00Z",
  "notes": "Тестовая партия для Докторской"
}
```

Backend проверяет:
- Версия рецепта в `APPROVED/PENDING` → иначе 400.
- Камера существует → иначе 400.
- Уникальность `batch_number` → иначе 409.
- Пишет в `audit_logs` (action=CREATE).

### 4.3. Запуск
```python
POST /api/v1/batches/{id}/start
# Без body (опц. {"note": "..."} — игнорируется пока)
```

Backend:
1. Загружает `Batch` + `RecipeVersion.program` (joinedload).
2. Берёт `Chamber.driver_class` и `Chamber.default_driver_config`.
3. Вызывает `ChamberGateway.start_batch(chamber_id, driver_class, connection, program)`.
4. `gateway.start_batch`:
   - lazy init драйвера (connect через Modbus TCP или мок).
   - `driver.load_recipe({"program": program})`.
   - `driver.start()`.
5. Устанавливает `Batch.status = RUNNING`, `actual_start = now`.
6. Audit (action=START).
7. При ошибке подключения к камере → 502 (но НЕ откатывает БД-изменения, кроме audit).

### 4.4. Жизненный цикл FSM

```python
# В коде endpoints/batches.py
async def start_batch(batch_id, ...):
    if obj.status not in (PLANNED, PAUSED):  # можно restart
        raise 409
    await gateway.start_batch(...)
    obj.status = RUNNING
    obj.actual_start = obj.actual_start or utcnow()

async def pause_batch(batch_id, ...):
    if obj.status != RUNNING:
        raise 409
    await gateway.pause_batch(obj.chamber_id)
    obj.status = PAUSED

async def resume_batch(batch_id, ...):
    if obj.status != PAUSED:
        raise 409
    await gateway.resume_batch(obj.chamber_id)
    obj.status = RUNNING

async def cancel_batch(batch_id, payload=None, ...):
    if obj.status in (COMPLETED, CANCELLED):
        raise 409
    try:
        await gateway.stop_batch(obj.chamber_id)
    except ChamberConnectionError:
        pass  # отменяем партию даже если камера недоступна
    obj.status = CANCELLED
    obj.actual_end = utcnow()
    if payload and payload.note:
        obj.notes += f"\n[Отмена] {payload.note}"

async def complete_batch(batch_id, payload=None, ...):
    if obj.status not in (RUNNING, PAUSED):
        raise 409
    try:
        await gateway.stop_batch(obj.chamber_id)
    except ChamberConnectionError:
        pass
    obj.status = COMPLETED
    obj.actual_end = utcnow()
    if payload and payload.note:
        obj.notes += f"\n[Завершение] {payload.note}"
```

## 5. Удаление

```python
DELETE /api/v1/batches/{id}
```

- **Разрешено** для: PLANNED, CANCELLED, COMPLETED.
- **Запрещено** для: RUNNING, PAUSED (нужно сначала cancel/complete).
- **Каскадно** удаляются `BatchPhase` (через `ondelete="CASCADE"`).
- **BatchTelemetry** также каскадно удаляется.

## 6. Чек-лист при работе с партиями

- [ ] Проверить, что версия рецепта в `APPROVED` (или `PENDING`).
- [ ] Проверить, что `Chamber.driver_class` зарегистрирован.
- [ ] `batch_number` уникален.
- [ ] `product_weight_kg` ≤ `Chamber.max_load_kg`.
- [ ] При `start` — камера доступна (иначе 502).
- [ ] При `cancel/complete` — камера может быть недоступна, партия всё равно отменяется.
- [ ] Удалять только финальные статусы (PLANNED/CANCELLED/COMPLETED).
- [ ] Каждое действие пишет в `audit_logs`.

## 7. TODO для будущих сессий

- [ ] Автоматическое создание `BatchPhase` при старте (на основе `RecipeVersion.program`).
- [ ] Запись `BatchTelemetry` от gateway (буферизация + batch insert в БД).
- [ ] WebSocket-уведомление о смене статуса партии (`/ws/batches/{id}`).
- [ ] Метрики: время выполнения, средние t_chamber/t_product, отклонения от программы.
- [ ] Расчёт `yield_kg` и `losses_percent` на основе actual_start/end и product_weight_kg.
- [ ] REST hook / webhook при завершении партии (email/telegram).

## 8. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `camera-driver` — для понимания ChamberGateway.
- `add-recipe` — для понимания RecipeVersion.
- `telemetry-websocket` — для live-телеметрии во время выполнения.
- `audit` (service) — для журналирования.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при работе с эндпоинтами `/batches/*` или создании UI для управления партиями.
