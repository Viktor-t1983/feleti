# 🤖 SKILL_DEV.md — Скилл: разработка современной программы

> **Назначение:** держать в одном месте все конвенции, паттерны, лучшие практики и анти-паттерны для разработки FELETI-SMOK. Этот файл — «мозг» любого разработчика (человека или AI-агента), который подключается к проекту.

---

## 1. Принципы (не подлежат обсуждению)

1. **Пользователь — в цеху.** Грязные руки, перчатки, шум, плохой Wi-Fi. Каждый экран должен работать при t=0 (кеш), t=1сек (быстрый ответ), в перчатках (кнопки ≥56px).
2. **Визуал = продажа.** Без хорошего UI даже Ижица останется лидером. Делаем в стиле Apple/Stripe/Figma: чисто, много воздуха, типографика решает.
3. **Тип-безопасность.** TypeScript strict. Python type hints. Любая ошибка типа = баг.
4. **Async по умолчанию** (Python). Sync только для легаси-библиотек (Telethon, PDF).
5. **Тесты = страховка.** Хотя бы критичные пути (аутентификация, драйвер камеры, расчёт себестоимости).
6. **Документация = код.** OpenAPI автогенерируется. Сложные места — docstring + комментарий «зачем».
7. **Без магии.** Если что-то делается неявно — это баг, не фича.

---

## 2. Frontend (Next.js 14)

### 2.1. Стек
- **Next.js 14.2+** (App Router, RSC, Server Actions)
- **TypeScript 5+** (strict, noImplicitAny, noUncheckedIndexedAccess)
- **shadcn/ui** (не Material UI, не Chakra — shadcn лучше кастомизируется)
- **TailwindCSS 3.4+** + **CSS variables** для темы
- **Framer Motion** для анимаций
- **Zustand** для глобального стейта (НЕ Redux)
- **React Hook Form** + **Zod** для форм
- **TanStack Query** (React Query) для серверного стейта
- **Recharts** для графиков (если не хватит — Visx, но не Chart.js — он устарел)
- **Lucide Icons** (НЕ FontAwesome)
- **date-fns** (НЕ Moment.js)
- **Sonner** для toast'ов

### 2.2. Структура (App Router)
```
frontend/
├── app/
│   ├── (auth)/           # login, register (без layout'а)
│   ├── (dashboard)/      # защищённые роуты
│   │   ├── layout.tsx    # sidebar + header
│   │   ├── page.tsx      # /
│   │   ├── chambers/
│   │   ├── recipes/
│   │   ├── chamber-control/
│   │   ├── batches/
│   │   ├── cost/
│   │   ├── knowledge/
│   │   └── compare/
│   ├── api/              # Next.js API routes (опц., лучше всё в backend)
│   ├── layout.tsx        # root layout
│   ├── globals.css       # Tailwind base
│   └── providers.tsx     # QueryClient, ThemeProvider, Toaster
├── components/
│   ├── ui/               # shadcn (Button, Card, Dialog, ...)
│   ├── chamber/          # специфика
│   ├── recipe/
│   ├── charts/
│   └── layout/           # Sidebar, Header, ...
├── lib/
│   ├── api/              # типизированный API-клиент (сгенерированный из OpenAPI)
│   ├── utils.ts
│   ├── format.ts
│   └── ws.ts             # WebSocket-клиент
├── stores/               # Zustand stores
├── hooks/                # кастомные React-хуки
├── public/
│   ├── manifest.json     # PWA
│   ├── sw.js             # service worker (опц.)
│   ├── logo.svg
│   └── icons/
├── styles/
├── types/
├── tailwind.config.ts
├── next.config.mjs
├── package.json
└── Dockerfile
```

### 2.3. Правила компонентов
- **Один файл — один компонент** (кроме мелких UI-блоков)
- **Server Components по умолчанию**, Client только когда нужны: state, эффекты, браузерные API
- **Props** — типизированный `interface`, не `type`
- **Именование**: `PascalCase` для компонентов, `camelCase` для хуков (`useXxx`), `kebab-case` для файлов и папок URL
- **Избегать** `useEffect` где можно — лучше `useMemo`, `useCallback`, server data
- **Анимации** — Framer Motion `<motion.div>` для интерактивных, Tailwind `transition` для статичных

### 2.4. Состояние
- **Глобальное** (Zustand): текущая камера, текущий пользователь, theme
- **Серверное** (TanStack Query): все списки, детали, фильтры
- **Локальное** (useState): модалки, формы в процессе редактирования
- **URL** (searchParams): фильтры, пагинация, активные табы

### 2.5. Формы
```typescript
const schema = z.object({
  name: z.string().min(2).max(100),
  load_kg: z.number().positive().max(1000),
  steps: z.array(z.object({
    t_c: z.number().min(0).max(200),
    duration_min: z.number().int().positive(),
    mode: z.enum(['drying', 'smoking_hot', 'cooking', 'cooling']),
  })).min(1),
});

const form = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema),
  defaultValues: { ... },
});
```

### 2.6. Графики (Recharts)
- Один компонент-обёртка `<TelemetryChart>` с типизированными пропсами
- Real-time: обновление через `setData` каждые 1 сек
- Цвета: красный FELETI `#E30613` для активной линии, серый для истории

### 2.7. PWA
- `manifest.json` + иконки 192/512 + maskable
- Service worker (опц., для офлайна — Workbox или кастомный)
- `next-pwa` пакет или ручной SW
- `theme-color` + `viewport` + `apple-touch-icon`

### 2.8. Доступность (a11y)
- Все интерактивные элементы фокусируемы
- `aria-label` для иконок-кнопок
- Контраст ≥ 4.5:1 (проверять в Chrome DevTools)
- Keyboard navigation

### 2.9. Анти-паттерны
- ❌ `any` в TypeScript
- ❌ Inline-стили (только Tailwind / CSS modules)
- ❌ `useEffect` для трансформации данных (вынести в `useMemo` или server)
- ❌ Огромные компоненты 500+ строк — разбивать
- ❌ «Умный» prop drilling — Zustand/Context
- ❌ CSS-in-JS (только Tailwind)
- ❌ Moment.js / Lodash (только date-fns, native)

---

## 3. Backend (FastAPI + SQLAlchemy 2.0)

### 3.1. Стек
- **Python 3.11+**
- **FastAPI 0.115+** (async, Pydantic v2)
- **SQLAlchemy 2.0** (async, новый стиль `Mapped[...]`)
- **Alembic** для миграций
- **Pydantic v2** для валидации
- **structlog** или **loguru** для логирования (НЕ print)
- **httpx** для внешних запросов
- **python-socketio** или FastAPI WebSocket
- **passlib[bcrypt]** + **python-jose** для JWT
- **pymodbustcp** или **pymodbus** для Modbus
- **asyncua** для OPC UA
- **aiomqtt** или **paho-mqtt** для MQTT
- **Telethon** для Telegram-парсинга
- **pdfplumber** для PDF-каталогов

### 3.2. Структура
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py        # api_router
│   │       ├── auth.py
│   │       ├── chambers.py
│   │       ├── manufacturers.py
│   │       ├── recipes.py
│   │       ├── batches.py
│   │       ├── ingredients.py
│   │       ├── cost.py
│   │       ├── knowledge.py
│   │       ├── chamber_control.py # WS + REST
│   │       └── ...
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── deps.py                # Depends()
│   │   └── logging.py
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── redis.py
│   ├── models/                    # SQLAlchemy
│   ├── schemas/                   # Pydantic
│   ├── services/
│   │   ├── chamber_gateway/       # ← Драйверы камер
│   │   ├── recipe_service.py
│   │   ├── cost_service.py
│   │   ├── telegram_parser.py
│   │   └── ...
│   ├── scripts/
│   │   └── seed.py
│   ├── websocket/
│   │   └── manager.py
│   └── main.py
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── conftest.py
│   ├── test_chambers.py
│   ├── test_recipes.py
│   └── test_chamber_driver.py
├── pyproject.toml
├── alembic.ini
└── Dockerfile
```

### 3.3. Модели (SQLAlchemy 2.0)
```python
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    chamber_id: Mapped[int | None] = mapped_column(ForeignKey("chambers.id"))
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    parent_version_id: Mapped[int | None] = mapped_column(ForeignKey("recipes.id"))
    status: Mapped[str] = mapped_column(default="draft")  # draft / pending / approved / archived
    yield_pct: Mapped[float] = mapped_column(default=100.0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    steps: Mapped[list["RecipeStep"]] = relationship(back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeStep.order")
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe", cascade="all, delete-orphan")
```

### 3.4. Pydantic v2
```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class RecipeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    product_id: int
    chamber_id: int | None = None
    yield_pct: float = Field(default=100.0, ge=0, le=200)
    notes: str | None = None

class RecipeCreate(RecipeBase):
    steps: list["RecipeStepCreate"]
    ingredients: list["RecipeIngredientCreate"] = []

class RecipeRead(RecipeBase):
    id: int
    version: int
    status: str
    created_at: datetime
    steps: list["RecipeStepRead"] = []
    ingredients: list["RecipeIngredientRead"] = []
    model_config = ConfigDict(from_attributes=True)
```

### 3.5. API conventions
- Префикс `/api/v1/`
- REST: GET (list с пагинацией), GET /:id, POST, PATCH, DELETE
- POST/PATCH/DELETE возвращают обновлённый объект
- Ошибки: `HTTPException(status_code=..., detail=...)`
- Валидация: Pydantic + 422
- Пагинация: `?page=1&page_size=20` (default 20, max 100)
- Фильтры: `?product_id=5&status=approved`
- Поиск: `?q=скумбрия`
- Сортировка: `?sort=-created_at` (минус = DESC)

### 3.6. WebSocket (телеметрия камеры в реал-тайме)
```python
# app/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, Set

class WSManager:
    def __init__(self):
        self.active: Dict[int, Set[WebSocket]] = {}  # chamber_id -> connections
    
    async def connect(self, chamber_id: int, ws: WebSocket): ...
    async def disconnect(self, chamber_id: int, ws: WebSocket): ...
    async def broadcast(self, chamber_id: int, data: dict): ...
```

### 3.7. Анти-паттерны (Python)
- ❌ `from app.models import *`
- ❌ Sync-код в async-роутах (`time.sleep`, `requests`)
- ❌ Pydantic v1 (только v2)
- ❌ SQLAlchemy 1.x (только 2.0)
- ❌ `os.environ.get` напрямую (только через `settings`)
- ❌ `print()` для логов (только `logger`)
- ❌ `try: ... except: pass` (всегда с конкретным исключением + лог)

---

## 4. База данных

### 4.1. Соглашения
- Имена таблиц: `snake_case` мн. число (`recipes`, `chambers`, `users`)
- PK: `id int autoincrement` (везде)
- FK: `table_id` (например `product_id`)
- Времена: `DateTime(timezone=True)`, UTC, snake_case
- Bool: `is_*` или `has_*`
- Enum: отдельный `SAEnum(..., name="...")`, snake_case значения
- Audit: `created_at`, `updated_at`, `created_by_id` где уместно
- Soft delete: `deleted_at` (только если реально нужно)

### 4.2. Индексы
- Все FK индексируются
- Поля для поиска: `index=True`
- Составные индексы: `Index('idx_recipe_chamber_status', 'chamber_id', 'status')`

### 4.3. Миграции (Alembic)
```bash
# Создать миграцию
docker compose exec backend alembic revision --autogenerate -m "add recipes"

# Применить
docker compose exec backend alembic upgrade head

# Откатить
docker compose exec backend alembic downgrade -1
```

---

## 5. Безопасность

- **Пароли**: bcrypt, cost ≥ 12
- **JWT**: HS256, exp 24ч, refresh 7д
- **CORS**: явно по origins
- **Rate limiting**: `slowapi` или Nginx
- **SQL injection**: только ORM, без raw SQL
- **XSS**: React экранирует, но осторожно с `dangerouslySetInnerHTML`
- **CSRF**: для форм (опц., для JWT не критично)
- **Audit log**: пишем все мутации в таблицу `audit_log`

---

## 6. Тестирование

- **pytest + pytest-asyncio** (Python)
- **Vitest + Testing Library** (TS/React)
- **Coverage** ≥ 60% для критичных модулей (auth, chamber_driver, cost)
- **E2E** Playwright (опц., позже)

---

## 7. DevOps

### 7.1. Docker
- Multi-stage build для frontend (Node build → Nginx)
- Slim images (alpine)
- `.dockerignore` обязателен
- Healthchecks для всех сервисов

### 7.2. CI/CD (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: cd backend && pip install -e ".[dev]" && ruff check . && pytest
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm run lint && npm run build
```

### 7.3. Бэкапы
```bash
# cron: каждый день в 3:00
docker compose exec -T db pg_dump -U feleti feleti_smok | gzip > /backups/db_$(date +%F).sql.gz
# Хранить 30 дней, на внешнем S3-совместимом
```

---

## 8. Производительность

- Backend: кеш через Redis для частых запросов (каталог камер)
- Frontend: RSC + кеш, только клиент для интерактива
- WebSocket: троттлинг телеметрии до 1-2 Hz
- Изображения: Next/Image, WebP
- Bundle: < 250 KB initial JS

---

## 9. Полезные ссылки и референсы

- [Next.js docs](https://nextjs.org/docs)
- [FastAPI docs](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [shadcn/ui](https://ui.shadcn.com)
- [Vercel design](https://vercel.com/design) — для UI-референса
- [Stripe docs](https://stripe.com/docs) — для UX-референса
- [Linear](https://linear.app) — для UX-референса
- [Tailwind UI](https://tailwindui.com) — для компонентов
- [Recharts](https://recharts.org)
