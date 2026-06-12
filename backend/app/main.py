"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.db.session import engine
from app.services.chamber_gateway import get_chamber_gateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup / shutdown."""
    yield
    gateway = await get_chamber_gateway()
    await gateway.shutdown()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Платформа управления коптильным производством и база знаний о копчении",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Роутеры (включая /api/v1/health внутри api_router) ---
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# --- Преобразование validation errors в строку ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = []
    for err in exc.errors():
        loc = " → ".join(str(l) for l in err.get("loc", []) if l not in ("body", "query", "path"))
        msg = err.get("msg", "")
        if loc:
            messages.append(f"{loc}: {msg}")
        else:
            messages.append(msg)
    detail = "; ".join(messages) if messages else "Ошибка валидации"
    return JSONResponse(status_code=422, content={"detail": detail})
