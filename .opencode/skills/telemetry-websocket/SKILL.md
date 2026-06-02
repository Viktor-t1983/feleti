# SKILL: telemetry-websocket

> Live-стрим телеметрии камеры через WebSocket + REST. Загружай при работе с эндпоинтами `/chambers/{id}/telemetry/*`.
> Загружай совместно с `camera-driver` (для ChamberGateway).

## 1. Архитектура

```
┌──────────────────────────────────────────────────────────┐
│  Клиент (PWA / desktop)                                   │
│  - WebSocket: ws://api/chambers/{id}/telemetry/ws?token=  │
│  - REST: GET /chambers/{id}/telemetry/latest             │
│  - REST: GET /chambers/{id}/telemetry/history?limit=600   │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│  FastAPI endpoints (api/v1/endpoints/telemetry.py)        │
│  - WS handler с auth в query                              │
│  - REST handlers                                          │
└──────────────────┬───────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────┐
│  ChamberGateway (singleton)                               │
│  - latest_telemetry() / telemetry_history()               │
│  - subscribe() / unsubscribe() (fan-out)                  │
│  - _telemetry_loop (1 Hz фоновый тик)                     │
└──────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   SimulatedDriver  VarmenDriver  FELETI_SMOKDriver
```

## 2. Структура данных

```python
ChamberTelemetry (dataclass, drivers/base.py):
  - chamber_id: int
  - ts: datetime
  - t_chamber: float | None           # температура в камере
  - t_product: float | None           # температура в продукте (Pt100)
  - humidity: float | None            # % относительной влажности
  - smoke_density: float | None       # оптическая плотность дыма
  - electro_voltage: float | None     # кВ (если электро)
  - electro_current: float | None     # мкА (если электро)
  - fan_rpm: float | None             # обороты вентилятора
  - door_open: bool
  - current_phase: int                # 0..N
  - phase_progress: float             # 0..1
  - errors: list[str]
  - raw: dict                         # сырые регистры для отладки
```

## 3. REST Endpoints

### 3.1. Status
```
GET /api/v1/chambers/{chamber_id}/status
```
Возвращает текущий статус камеры (требует подключения драйвера):
```json
{
  "running": true,
  "paused": false,
  "phase": 1,
  "phase_name": "Копчение",
  "phase_progress": 0.45,
  "total_phases": 4
}
```

### 3.2. Latest
```
GET /api/v1/chambers/{chamber_id}/telemetry/latest
```
Возвращает последний сэмпл из кольцевого буфера (без обращения к камере):
```json
{
  "chamber_id": 1,
  "ts": "2026-06-02T12:34:56",
  "t_chamber": 75.3,
  "t_product": 68.1,
  "humidity": 52.0,
  "smoke_density": 18.5,
  "electro_voltage": 0.0,
  "electro_current": 0.0,
  "fan_rpm": 1500,
  "door_open": false,
  "current_phase": 1,
  "phase_progress": 0.45,
  "errors": [],
  "raw": {"phase_name": "Копчение"}
}
```

### 3.3. History
```
GET /api/v1/chambers/{chamber_id}/telemetry/history?limit=600
```
Возвращает последние N точек из буфера (старые→новые):
```json
{
  "chamber_id": 1,
  "count": 600,
  "items": [ ... 600 сэмплов ... ]
}
```

- `limit`: 1..3600 (default 600, max — размер буфера).

### 3.4. Active batch
```
GET /api/v1/chambers/{chamber_id}/active-batch
```
Возвращает текущую активную партию (RUNNING или PAUSED) или `null`:
```json
{
  "active_batch": {
    "id": 42,
    "batch_number": "B-20260602-ABC1",
    "status": "running",
    "actual_start": "2026-06-02T08:00:00",
    "recipe_version_id": 1
  }
}
```

## 4. WebSocket Protocol

### 4.1. Подключение
```
WS /api/v1/chambers/{chamber_id}/telemetry/ws?token=<JWT>
```

**Аутентификация:** токен передаётся в query-параметре (стандарт для WS, т.к. браузерные WS API не умеют headers).

**Ошибки подключения (закрытие без accept):**
- `1008` — отсутствует/невалиден токен.
- `1008` — камера не найдена.
- `1011` — камера недоступна (драйвер не подключился).

### 4.2. Сообщения сервера

#### 4.2.1. Ready (сразу после accept)
```json
{
  "type": "ready",
  "chamber_id": 1,
  "user_id": 1,
  "interval_s": 1.0
}
```

#### 4.2.2. Telemetry (каждую секунду по умолчанию)
```json
{
  "type": "telemetry",
  "data": {
    "chamber_id": 1,
    "ts": "2026-06-02T12:34:56",
    "t_chamber": 75.3,
    "t_product": 68.1,
    ...
  }
}
```

#### 4.2.3. Pong (ответ на ping)
```json
{
  "type": "pong",
  "ts": 1234567890.123
}
```

#### 4.2.4. Ack (ответ на subscribe)
```json
{
  "type": "ack",
  "interval_s": 0.5
}
```

#### 4.2.5. Error
```json
{
  "type": "error",
  "message": "invalid json"
}
```

### 4.3. Команды клиента

#### 4.3.1. Ping (keep-alive)
```json
{"action": "ping"}
```
Сервер отвечает `{"type": "pong", "ts": ...}`.

#### 4.3.2. Subscribe (изменить интервал)
```json
{"action": "subscribe", "interval_s": 0.5}
```
- `interval_s`: 0.5..60.0.
- Сервер отвечает `{"type": "ack", "interval_s": ...}`.
- Фактический интервал может отличаться (если выходит за границы).

## 5. Реализация (api/v1/endpoints/telemetry.py)

### 5.1. WS handler
```python
@router.websocket("/{chamber_id}/telemetry/ws")
async def telemetry_websocket(websocket: WebSocket, chamber_id: int):
    async with AsyncSessionLocal() as db:
        user = await _authenticate_ws(websocket, db)
        if user is None:
            return
        await websocket.accept()
        gateway = await get_chamber_gateway()

        chamber = await db.scalar(select(Chamber).where(Chamber.id == chamber_id))
        if chamber is None:
            await websocket.send_json({"type": "error", "message": "..."})
            await websocket.close(code=1008)
            return
        try:
            await gateway.get_driver(chamber_id, chamber.driver_class, chamber.default_driver_config or {})
        except ChamberConnectionError as e:
            await websocket.send_json({"type": "error", "message": f"Камера недоступна: {e}"})
            await websocket.close(code=1011)
            return

        queue = gateway.subscribe(chamber_id)
        interval_s = 1.0
        try:
            await websocket.send_json({"type": "ready", ...})
            while True:
                receive_task = asyncio.create_task(websocket.receive_text())
                get_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {receive_task, get_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    if task is receive_task and not task.cancelled():
                        # обработка команды клиента
                        ...
                    elif task is get_task and not task.cancelled():
                        # отправка телеметрии
                        await websocket.send_json({"type": "telemetry", "data": ...})
                await asyncio.sleep(interval_s)
        except WebSocketDisconnect:
            pass
        finally:
            gateway.unsubscribe(chamber_id, queue)
```

### 5.2. Fan-out pattern

`telemetry_loop` в gateway пишет в буфер + рассылает всем подписчикам:
```python
async def _telemetry_loop(self, chamber_id, driver):
    while driver.is_connected and not self._closed:
        try:
            telemetry = await driver.get_telemetry()
        except Exception:
            await asyncio.sleep(1.0)
            continue
        self._buffer[chamber_id].append(_BufferedSample(time.time(), telemetry))
        for queue in list(self._subscribers.get(chamber_id, [])):
            try:
                queue.put_nowait(telemetry)
            except asyncio.QueueFull:
                pass  # медленный подписчик — пропускаем точку
        await asyncio.sleep(1.0)
```

## 6. Frontend (TODO) — использование в PWA

```typescript
// frontend/lib/ws/chamber-telemetry.ts
import { useEffect, useState } from 'react';
import { getAccessToken } from '@/lib/auth/token';

export function useChamberTelemetry(chamberId: number) {
  const [telemetry, setTelemetry] = useState<ChamberTelemetry | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/api/v1/chambers/${chamberId}/telemetry/ws?token=${token}`
    );

    ws.onopen = () => console.log('WS connected');
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'telemetry') {
        setTelemetry(msg.data);
      } else if (msg.type === 'error') {
        setError(msg.message);
      }
    };
    ws.onerror = (e) => setError('WS error');
    ws.onclose = () => console.log('WS closed');

    // keep-alive ping каждые 30 сек
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [chamberId]);

  return { telemetry, error };
}
```

## 7. Графики (TODO — recharts)

- **Line chart** для t_chamber / t_product (за период).
- **Gauge** для текущей t_chamber (setpoint vs actual).
- **Heatmap** для влажности по фазам.
- **Status badge** для статуса камеры (running/paused/idle/error).

## 8. Чек-лист

- [ ] WS аутентификация через query token (не headers).
- [ ] Закрытие WS с правильными кодами (1008/1011).
- [ ] Fan-out через `asyncio.Queue`, медленные подписчики не блокируют loop.
- [ ] Cleanup подписки в `finally` блоке.
- [ ] Обработка `WebSocketDisconnect` без traceback.
- [ ] Интервал подписки клиента валидируется (0.5..60.0).
- [ ] REST endpoints возвращают данные из буфера (не обращаются к камере).
- [ ] Latency WS < 1.1s при интервале 1.0s (один тик + overhead).

## 9. TODO для будущих сессий

- [ ] Persist `BatchTelemetry` в БД (буферизация + batch insert каждые 10 сек).
- [ ] Persist `TelemetryReading` для не-партийной телеметрии (мониторинг камеры в простое).
- [ ] Redis pub/sub для синхронизации между процессами (масштабирование).
- [ ] Server-Sent Events (SSE) как альтернатива WS (для простых случаев).
- [ ] Метрики: latency, потерянные точки, кол-во подписчиков.
- [ ] Webhook при `door_open=true` или `errors!=[]`.

## 10. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `camera-driver` — для понимания ChamberGateway.
- `batches-lifecycle` — для связи телеметрии с партиями.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при работе с live-телеметрией или создании UI дашборда.
