"""Telegram Parser — парсинг Telegram-каналов через Telethon."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import Message, Channel, Chat, User

from .knowledge_pipeline import CrawlResult, SourceType

logger = logging.getLogger(__name__)

SESSION_DIR = Path("/app/.telegram_session")


class LoginState:
    phone: str = ""
    phone_code_hash: str = ""


_phone_code_hash: str | None = None
_phone: str | None = None


def _get_session_path() -> str:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return str(SESSION_DIR / "feleti_user")


def _channel_label(channel_identifier: int | str) -> str:
    if isinstance(channel_identifier, int):
        return str(channel_identifier)
    return channel_identifier.strip("@")


_client: TelegramClient | None = None
_lock = asyncio.Lock()


async def _ensure_client(api_id: int, api_hash: str) -> TelegramClient:
    global _client
    if _client is not None:
        if _client.is_connected():
            return _client
        try:
            await _client.disconnect()
        except Exception:
            pass
    session_path = _get_session_path()
    _client = TelegramClient(session_path, api_id, api_hash)
    await _client.connect()
    return _client


async def _with_lock(api_id: int, api_hash: str, fn):
    async with _lock:
        cl = await _ensure_client(api_id, api_hash)
        return await fn(cl)


async def disconnect_client() -> None:
    async with _lock:
        global _client
        if _client:
            await _client.disconnect()
            _client = None


async def send_code(phone: str, api_id: int, api_hash: str) -> dict[str, Any]:
    async def _do(cl):
        if await cl.is_user_authorized():
            return {"success": True, "already_authorized": True}

        result = await cl.send_code_request(phone)
        global _phone_code_hash, _phone
        _phone_code_hash = result.phone_code_hash
        _phone = phone
        logger.info(f"Code sent to {phone}")
        return {"success": True, "already_authorized": False}

    try:
        return await _with_lock(api_id, api_hash, _do)
    except Exception as e:
        logger.error(f"Failed to send code: {e}")
        return {"success": False, "error": str(e)}


async def verify_code(code: str) -> dict[str, Any]:
    global _phone_code_hash, _phone

    if not _phone or not _phone_code_hash:
        return {"success": False, "error": "Сначала отправьте код через send_code"}

    async with _lock:
        cl = _client
        if cl is None:
            return {"success": False, "error": "Клиент не инициализирован"}

        try:
            await cl.sign_in(phone=_phone, code=code, phone_code_hash=_phone_code_hash)
            logger.info(f"Successfully signed in as {_phone}")
            _phone_code_hash = None
            _phone = None
            return {"success": True}
        except SessionPasswordNeededError:
            return {"success": False, "need_password": True}
        except Exception as e:
            logger.error(f"Verify code failed: {e}")
            return {"success": False, "error": str(e)}


async def check_password(password: str) -> dict[str, Any]:
    async with _lock:
        cl = _client
        if cl is None:
            return {"success": False, "error": "Клиент не инициализирован"}
        try:
            await cl.sign_in(password=password)
            logger.info("2FA password accepted")
            return {"success": True}
        except Exception as e:
            logger.error(f"Password check failed: {e}")
            return {"success": False, "error": str(e)}


async def get_dialogs(*, api_id: int = 0, api_hash: str = "") -> list[dict[str, Any]]:
    async def _do(cl):
        dialogs = await cl.get_dialogs()
        result = []
        for d in dialogs:
            entity = d.entity
            if isinstance(entity, Channel):
                kind = "channel"
            elif isinstance(entity, Chat):
                kind = "chat"
            elif isinstance(entity, User):
                kind = "user"
            else:
                kind = "unknown"
            result.append({
                "id": entity.id,
                "name": d.name or "",
                "username": getattr(entity, "username", None) or "",
                "kind": kind,
                "unread_count": d.unread_count,
            })
        return result

    return await _with_lock(api_id, api_hash, _do)


async def get_channel_messages(
    channel_identifier: int | str,
    limit: int = 100,
    offset_date: datetime | None = None,
    *,
    api_id: int = 0,
    api_hash: str = "",
) -> list[dict[str, Any]]:
    async def _do(cl):
        entity = await cl.get_entity(channel_identifier)

        messages: list[Message] = []
        async for msg in cl.iter_messages(entity, limit=limit, offset_date=offset_date):
            messages.append(msg)

        result = []
        for msg in messages:
            if not msg.text and not msg.media:
                continue
            media_info = None
            if msg.media:
                try:
                    media_info = {}
                    if hasattr(msg.media, "photo"):
                        media_info["type"] = "photo"
                    elif hasattr(msg.media, "document"):
                        doc = msg.media.document
                        mime = doc.mime_type if hasattr(doc, "mime_type") else ""
                        media_info["type"] = "document"
                        media_info["mime_type"] = mime
                    elif hasattr(msg.media, "webpage"):
                        media_info["type"] = "webpage"
                        media_info["url"] = getattr(msg.media.webpage, "url", "")
                    else:
                        media_info["type"] = "other"
                except Exception:
                    media_info = {"type": "unknown"}

            result.append({
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "text": msg.text or "",
                "media": media_info,
                "views": getattr(msg, "views", None),
                "forwards": getattr(msg, "forwards", None),
                "reply_to": msg.reply_to_msg_id,
            })
        return result

    try:
        return await _with_lock(api_id, api_hash, _do)
    except Exception as e:
        logger.error(f"Channel error {channel_identifier}: {e}")
        return []


async def crawl_channel_messages(
    channel_identifier: int | str,
    limit: int = 100,
    offset_date: datetime | None = None,
    *,
    api_id: int = 0,
    api_hash: str = "",
) -> list[CrawlResult]:
    messages = await get_channel_messages(
        channel_identifier, limit, offset_date,
        api_id=api_id, api_hash=api_hash,
    )
    results = []
    for m in messages:
        if not m["text"]:
            continue
        title = m["text"][:80].strip().split("\n")[0]
        results.append(CrawlResult(
            source_type=SourceType.TELEGRAM,
            source_url=f"https://t.me/{_channel_label(channel_identifier)}/{m['id']}",
            raw_text=m["text"],
            metadata={
                "channel": channel_identifier,
                "message_id": m["id"],
                "date": m["date"],
                "views": m["views"],
                "forwards": m["forwards"],
                "media": m["media"],
            },
            crawled_at=datetime.utcnow(),
        ))
    return results


async def is_authorized(*, api_id: int = 0, api_hash: str = "") -> bool:
    async with _lock:
        global _client
        if _client is not None:
            if _client.is_connected():
                try:
                    return await _client.is_user_authorized()
                except Exception:
                    return False
            try:
                await _client.disconnect()
            except Exception:
                pass
        if not api_id or not api_hash:
            return False
        session_path = _get_session_path()
        _client = TelegramClient(session_path, api_id, api_hash)
        try:
            await _client.connect()
            return await _client.is_user_authorized()
        except Exception:
            return False


async def logout() -> dict[str, Any]:
    async with _lock:
        global _client
        cl = _client
        if cl is None:
            return {"success": True, "message": "Уже не авторизован"}
        try:
            await cl.log_out()
        except Exception as e:
            logger.warning(f"Logout error (may be OK): {e}")
        await cl.disconnect()
        _client = None

        session_path = _get_session_path()
        for f in Path(session_path).parent.glob("feleti_user*"):
            try:
                f.unlink()
            except Exception:
                pass
        return {"success": True, "message": "Выход выполнен"}


class TelegramParser:
    def __init__(self, api_id: str | None = None, api_hash: str | None = None):
        self._api_id = int(api_id) if api_id else 0
        self._api_hash = api_hash or ""

    async def crawl(self, url: str) -> CrawlResult:
        if not self._api_id or not self._api_hash:
            return CrawlResult(
                source_type=SourceType.TELEGRAM,
                source_url=url,
                errors=["API_ID и API_HASH не настроены"],
            )
        ok = await is_authorized(api_id=self._api_id, api_hash=self._api_hash)
        if not ok:
            return CrawlResult(
                source_type=SourceType.TELEGRAM,
                source_url=url,
                errors=["Telegram: требуется авторизация"],
            )
        return CrawlResult(
            source_type=SourceType.TELEGRAM,
            source_url=url,
            errors=["Telegram parser: use crawl_channel for batch parsing"],
        )

    async def crawl_channel(self, channel: str, limit: int = 100,
                            offset_date: datetime | None = None) -> list[CrawlResult]:
        if not self._api_id or not self._api_hash:
            logger.warning(f"Telegram parser skipped: {channel} (API keys needed)")
            return []
        ok = await is_authorized(api_id=self._api_id, api_hash=self._api_hash)
        if not ok:
            logger.warning(f"Telegram parser skipped: {channel} (not authorized)")
            return []
        return await crawl_channel_messages(
            channel, limit, offset_date,
            api_id=self._api_id, api_hash=self._api_hash,
        )

    def is_ready(self) -> bool:
        return bool(self._api_id and self._api_hash)
