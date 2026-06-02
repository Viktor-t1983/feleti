"""Телеметрия камер: live-стрим (WebSocket) + REST (latest, history, status).

WebSocket авторизуется по токену в query (?token=...) — это стандартная практика,
поскольку браузерные WebSocket API не умеют передавать кастомные headers.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DBSession
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.drivers.base import ChamberTelemetry
from app.models.batch import Batch, BatchStatus
from app.models.chamber import Chamber
from app.models.user import User
from app.services.chamber_gateway import (
    ChamberConnectionError,
    ChamberGateway,
    get_chamber_gateway,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _telemetry_to_dict(t: ChamberTelemetry) -> dict:
    """Безопасная сериализация телеметрии для JSON / WebSocket."""
    return {
        "chamber_id": t.chamber_id,
        "ts": t.ts.isoformat() if t.ts else None,
        "t_chamber": t.t_chamber,
        "t_product": t.t_product,
        "humidity": t.humidity,
        "smoke_density": t.smoke_density,
        "electro_voltage": t.electro_voltage,
        "electro_current": t.electro_current,
        "fan_rpm": t.fan_rpm,
        "door_open": t.door_open,
        "current_phase": t.current_phase,
        "phase_progress": t.phase_progress,
        "errors": t.errors,
        "raw": t.raw,
    }


@router.get(
    "/{chamber_id}/status",
    summary="Текущий статус камеры (running/paused/phase)",
)
async def get_chamber_status(
    chamber_id: int,
    _user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> dict:
    try:
        return await gateway.get_status(chamber_id)
    except ChamberConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Камера {chamber_id} не подключена: {e}",
        ) from e


@router.get(
    "/{chamber_id}/telemetry/latest",
    summary="Последний сэмпл телеметрии из кольцевого буфера",
)
async def get_latest_telemetry(
    chamber_id: int,
    _user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> dict:
    sample = gateway.latest_telemetry(chamber_id)
    if sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нет данных телеметрии (камера не опрашивается или буфер пуст)",
        )
    return _telemetry_to_dict(sample)


@router.get(
    "/{chamber_id}/telemetry/history",
    summary="История телеметрии из кольцевого буфера (последние N точек)",
)
async def get_telemetry_history(
    chamber_id: int,
    _user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
    limit: Annotated[int, Query(ge=1, le=3600)] = 600,
) -> dict:
    history = gateway.telemetry_history(chamber_id, limit=limit)
    return {
        "chamber_id": chamber_id,
        "count": len(history),
        "items": [_telemetry_to_dict(t) for t in history],
    }


async def _authenticate_ws(websocket: WebSocket, db: AsyncSession) -> User | None:
    """Аутентификация WebSocket по query-параметру token.

    Возвращает User или None. Закрывает соединение с 1008 при ошибке.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing token")
        return None
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid token")
        return None
    sub = payload.get("sub")
    if not sub:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid sub")
        return None
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid sub")
        return None
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="user disabled")
        return None
    return user


@router.websocket("/{chamber_id}/telemetry/ws")
async def telemetry_websocket(
    websocket: WebSocket,
    chamber_id: int,
) -> None:
    """WebSocket-стрим телеметрии камеры.

    Авторизация: токен в query (?token=...).
    Клиент может послать JSON-команды:
      - {"action": "ping"} — сервер ответит {"type": "pong"}
      - {"action": "subscribe", "interval_s": 1.0} — изменить интервал (мин 0.5)
    """
    # Открываем сессию БД вручную (WebSocket не использует Depends).
    async with AsyncSessionLocal() as db:
        user = await _authenticate_ws(websocket, db)
        if user is None:
            return
        await websocket.accept()
        gateway = await get_chamber_gateway()

        # Убеждаемся, что драйвер подключён (если камера существует в БД).
        chamber = await db.scalar(select(Chamber).where(Chamber.id == chamber_id))
        if chamber is None:
            await websocket.send_json(
                {"type": "error", "message": f"Камера {chamber_id} не найдена"}
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            await gateway.get_driver(
                chamber_id,
                chamber.driver_class,
                chamber.default_driver_config or {},
            )
        except ChamberConnectionError as e:
            await websocket.send_json(
                {"type": "error", "message": f"Камера недоступна: {e}"}
            )
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        # Подписываемся на live-поток.
        queue = gateway.subscribe(chamber_id)
        interval_s = 1.0
        try:
            await websocket.send_json(
                {
                    "type": "ready",
                    "chamber_id": chamber_id,
                    "user_id": user.id,
                    "interval_s": interval_s,
                }
            )
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
                    try:
                        result = task.result()
                    except Exception:
                        result = None
                    if task is receive_task and result is not None:
                        # Команда от клиента.
                        try:
                            msg = json.loads(result)
                            action = msg.get("action")
                            if action == "ping":
                                await websocket.send_json(
                                    {"type": "pong", "ts": asyncio.get_event_loop().time()}
                                )
                            elif action == "subscribe" and "interval_s" in msg:
                                new_interval = float(msg["interval_s"])
                                if 0.5 <= new_interval <= 60.0:
                                    interval_s = new_interval
                                await websocket.send_json(
                                    {"type": "ack", "interval_s": interval_s}
                                )
                        except json.JSONDecodeError:
                            await websocket.send_json(
                                {"type": "error", "message": "invalid json"}
                            )
                    elif task is get_task and result is not None:
                        # Телеметрия из подписки.
                        await websocket.send_json(
                            {"type": "telemetry", "data": _telemetry_to_dict(result)}
                        )
                await asyncio.sleep(interval_s)
        except WebSocketDisconnect:
            logger.info("WS отключен: chamber=%s user=%s", chamber_id, user.id)
        except Exception:
            logger.exception("WS ошибка: chamber=%s", chamber_id)
        finally:
            gateway.unsubscribe(chamber_id, queue)


# Вспомогательный эндпоинт: получить текущий активный batch камеры (для UI).
@router.get(
    "/{chamber_id}/active-batch",
    summary="Текущая активная партия (RUNNING/PAUSED) для камеры",
)
async def get_active_batch(
    chamber_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> dict:
    batch = await db.scalar(
        select(Batch)
        .where(
            Batch.chamber_id == chamber_id,
            Batch.status.in_([BatchStatus.RUNNING, BatchStatus.PAUSED]),
        )
        .order_by(Batch.id.desc())
        .limit(1)
    )
    if batch is None:
        return {"active_batch": None}
    return {
        "active_batch": {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "status": batch.status.value,
            "actual_start": batch.actual_start.isoformat() if batch.actual_start else None,
            "recipe_version_id": batch.recipe_version_id,
        }
    }
