"""API для авторизации и парсинга Telegram."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import CurrentUser, DBSession
from app.services.knowledge_saver import KnowledgeSaver
from app.services.knowledge_pipeline import CrawlResult, ExtractedData, SourceType
from app.models.knowledge import KnowledgeArticle
from app.services.telegram_parser import (
    check_password,
    crawl_channel_messages,
    get_channel_messages,
    get_dialogs,
    is_authorized,
    logout as tg_logout,
    send_code,
    verify_code,
)

router = APIRouter()


class SendCodeRequest(BaseModel):
    phone: str


class SendCodeResponse(BaseModel):
    success: bool
    already_authorized: bool = False
    need_password: bool = False
    error: str | None = None


class VerifyCodeRequest(BaseModel):
    code: str


class PasswordRequest(BaseModel):
    password: str


class StatusResponse(BaseModel):
    authorized: bool
    has_api_credentials: bool


class DialogItem(BaseModel):
    id: int
    name: str
    username: str
    kind: str
    unread_count: int


class MessageItem(BaseModel):
    id: int
    date: str | None = None
    text: str
    media: dict | None = None
    views: int | None = None
    forwards: int | None = None
    reply_to: int | None = None


class ChannelParseRequest(BaseModel):
    channel: str
    limit: int = 100
    offset_date: str | None = None


class LogoutResponse(BaseModel):
    success: bool
    message: str


def _creds_or_400():
    if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
        raise HTTPException(status_code=400, detail="TELEGRAM_API_ID или TELEGRAM_API_HASH не настроены")
    return int(settings.TELEGRAM_API_ID), settings.TELEGRAM_API_HASH


async def _ensure_auth():
    api_id, api_hash = _creds_or_400()
    auth = await is_authorized(api_id=api_id, api_hash=api_hash)
    if not auth:
        raise HTTPException(status_code=401, detail="Telegram: требуется авторизация")
    return api_id, api_hash


@router.get("/status", response_model=StatusResponse, summary="Статус Telegram-авторизации")
async def tg_status(_user: CurrentUser) -> StatusResponse:
    has_api = bool(settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH)
    if not has_api:
        return StatusResponse(authorized=False, has_api_credentials=False)
    auth = await is_authorized(
        api_id=int(settings.TELEGRAM_API_ID),
        api_hash=settings.TELEGRAM_API_HASH,
    )
    return StatusResponse(authorized=auth, has_api_credentials=True)


@router.post("/send-code", response_model=SendCodeResponse, summary="Отправить код подтверждения")
async def tg_send_code(payload: SendCodeRequest, _user: CurrentUser) -> SendCodeResponse:
    api_id, api_hash = _creds_or_400()
    result = await send_code(payload.phone, api_id, api_hash)
    if not result["success"]:
        return SendCodeResponse(success=False, error=result.get("error", "Неизвестная ошибка"))
    return SendCodeResponse(success=True, already_authorized=result.get("already_authorized", False))


@router.post("/verify-code", response_model=SendCodeResponse, summary="Подтвердить код")
async def tg_verify_code(payload: VerifyCodeRequest, _user: CurrentUser) -> SendCodeResponse:
    result = await verify_code(payload.code)
    if not result["success"]:
        return SendCodeResponse(success=False, error=result.get("error", "Неверный код"),
                                need_password=result.get("need_password", False))
    return SendCodeResponse(success=True)


@router.post("/check-password", response_model=SendCodeResponse, summary="Ввести пароль 2FA")
async def tg_check_password(payload: PasswordRequest, _user: CurrentUser) -> SendCodeResponse:
    result = await check_password(payload.password)
    if not result["success"]:
        return SendCodeResponse(success=False, error=result.get("error", "Неверный пароль"))
    return SendCodeResponse(success=True)


@router.get("/dialogs", response_model=list[DialogItem], summary="Список диалогов/каналов")
async def tg_dialogs(_user: CurrentUser) -> list[DialogItem]:
    api_id, api_hash = await _ensure_auth()
    dialogs = await get_dialogs(api_id=api_id, api_hash=api_hash)
    return [DialogItem(**d) for d in dialogs]


@router.post("/channel/messages", response_model=list[MessageItem], summary="Получить сообщения канала")
async def tg_channel_messages(payload: ChannelParseRequest, _user: CurrentUser) -> list[MessageItem]:
    api_id, api_hash = await _ensure_auth()
    offset_date = None
    if payload.offset_date:
        try:
            offset_date = datetime.fromisoformat(payload.offset_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат offset_date (ISO8601)")
    messages = await get_channel_messages(
        payload.channel, limit=payload.limit, offset_date=offset_date,
        api_id=api_id, api_hash=api_hash,
    )
    return [MessageItem(**m) for m in messages]


@router.post("/channel/parse", response_model=dict, summary="Спарсить канал в базу знаний")
async def tg_parse_channel(payload: ChannelParseRequest, _user: CurrentUser) -> dict:
    api_id, api_hash = await _ensure_auth()
    offset_date = None
    if payload.offset_date:
        try:
            offset_date = datetime.fromisoformat(payload.offset_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат offset_date (ISO8601)")
    results = await crawl_channel_messages(
        payload.channel, limit=payload.limit, offset_date=offset_date,
        api_id=api_id, api_hash=api_hash,
    )
    return {
        "channel": payload.channel,
        "parsed": len(results),
        "results": [
            {"url": r.source_url, "text_preview": r.raw_text[:200], "errors": r.errors}
            for r in results
        ],
    }


@router.post("/logout", response_model=LogoutResponse, summary="Выйти из Telegram")
async def tg_logout_endpoint(_user: CurrentUser) -> LogoutResponse:
    result = await tg_logout()
    return LogoutResponse(**result)


class ImportRequest(BaseModel):
    channel: str = ""
    channel_id: int | None = None
    limit: int = 100
    offset_date: str | None = None


class ImportItem(BaseModel):
    id: int | None = None
    title: str
    url: str
    status: str  # saved / duplicate / error
    error: str | None = None


class ImportResponse(BaseModel):
    channel: str
    total: int
    saved: int
    duplicates: int
    errors: int
    items: list[ImportItem]


@router.post("/channel/import", response_model=ImportResponse, summary="Импортировать канал в базу знаний")
async def tg_import_channel(payload: ImportRequest, db: DBSession, _user: CurrentUser) -> ImportResponse:
    api_id, api_hash = await _ensure_auth()
    offset_date = None
    if payload.offset_date:
        try:
            offset_date = datetime.fromisoformat(payload.offset_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Неверный формат offset_date (ISO8601)")

    identifier: int | str = payload.channel_id if payload.channel_id is not None else payload.channel
    channel_label = str(payload.channel_id) if payload.channel_id else payload.channel

    results = await crawl_channel_messages(
        identifier, limit=payload.limit, offset_date=offset_date,
        api_id=api_id, api_hash=api_hash,
    )

    items: list[ImportItem] = []
    saved = duplicates = errors = 0

    for r in results:
        text = r.raw_text.strip()
        if not text:
            continue
        title = text[:80].strip().split("\n")[0][:200]

        existing = await db.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_url == r.source_url)
        )
        if existing:
            duplicates += 1
            items.append(ImportItem(id=existing.id, title=title, url=r.source_url, status="duplicate"))
            continue

        excerpt = text[:1000] if len(text) > 1000 else text
        body = text.replace("\n", "\n\n")

        article = KnowledgeArticle(
            title=title,
            slug=_slugify(title),
            body_md=body,
            excerpt=excerpt,
            category="guide",
            tags=["telegram", channel_label],
            source_url=r.source_url,
            is_published=False,
        )

        slug_base = _slugify(title)
        counter = 1
        slug = slug_base
        while True:
            exists = await db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.slug == slug))
            if not exists:
                break
            slug = f"{slug_base}-{counter}"
            counter += 1
        article.slug = slug

        db.add(article)
        try:
            await db.commit()
            await db.refresh(article)
            saved += 1
            items.append(ImportItem(id=article.id, title=title, url=r.source_url, status="saved"))
        except Exception as e:
            await db.rollback()
            errors += 1
            items.append(ImportItem(title=title, url=r.source_url, status="error", error=str(e)))

    return ImportResponse(
        channel=channel_label,
        total=len(results),
        saved=saved,
        duplicates=duplicates,
        errors=errors,
        items=items,
    )


def _slugify(text: str) -> str:
    import re
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:200] or "untitled"
