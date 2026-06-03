# FELETI-SMOK

**Платформа управления коптильным производством и база знаний о копчении**

Полноценный fullstack-проект (десктоп + PWA-мобильная) для технологов, операторов коптильных камер, владельцев крафтовых цехов и менеджеров по продажам оборудования.

## 🎯 Что внутри

| Модуль | Страницы | Статус |
|--------|----------|--------|
| **Dashboard** | `/` | ✅ KPI, графики, статус камер |
| **Камеры** | `/chambers`, `/chambers/[id]` | ✅ Каталог + HMI с WebSocket |
| **Рецепты** | `/recipes`, `/recipes/[slug]` | ✅ Библиотека + детали с фазами |
| **Партии** | `/batches`, `/batches/new` | ✅ Журнал + создание |
| **Конкуренты** | `/competitors` | ✅ Анализ 4 конкурентов, 18 моделей Ижицы |
| **База знаний** | `/knowledge`, `/knowledge/[slug]` | ✅ Статьи, markdown, фильтры |
| **Настройки** | `/settings` | ✅ Профиль, о системе |
| **Авторизация** | `/login` | ✅ JWT, роли (admin/tech/operator) |

## 🏗 Стек

- **Frontend**: Next.js 14 (App Router) + TypeScript + shadcn/ui + Tailwind + Recharts + Zustand + TanStack Query + React Hook Form + Zod
- **Backend**: FastAPI (Python 3.11+) + SQLAlchemy 2.0 + Alembic + Pydantic v2
- **DB**: PostgreSQL 16
- **Кэш/фон**: Redis 7
- **Хранилище**: MinIO (S3-совместимое)
- **MQTT**: Eclipse Mosquitto 2.0
- **WebSocket**: real-time telemetry с коптильных камер
- **PWA**: манифест + service worker (мобильная версия в браузере)
- **DevOps**: Docker Compose, Adminer (UI БД)

## 🎨 Дизайн

Стиль **FELETI**: чёрно-белая база + красный акцент (`#E30613` как в логотипе FELETI), плавные анимации, современная типографика (Inter / Geist), тёмная и светлая темы.

## 🚀 Запуск

```bash
# 1. Клонировать (или скопировать) проект
cd D:\Коптильные камеры\koptilnya-platform

# 2. Скопировать .env.example в .env и поправить под себя
cp .env.example .env

# 3. Поднять всё одной командой
docker compose up -d --build

# 4. Открыть
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000/api/v1/docs
# Adminer:   http://localhost:8080 (логин: feleti, БД: feleti_smok)
# MinIO:     http://localhost:9001
```

## 📁 Структура

```
koptilnya-platform/
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/v1/          # роутеры (auth, chambers, recipes, batches, telemetry, competitors, knowledge, dashboard)
│   │   ├── core/            # конфиг, безопасность, deps
│   │   ├── db/              # сессии, база, миграции
│   │   ├── models/          # SQLAlchemy 2.0 модели
│   │   ├── schemas/         # Pydantic v2 схемы
│   │   ├── services/        # бизнес-логика (gateway, audit)
│   │   ├── drivers/         # драйверы камер (Modbus, simulated)
│   │   ├── scripts/         # seed данных
│   │   └── main.py
│   ├── alembic/             # миграции Alembic
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # Next.js 14 (App Router)
│   ├── app/                 # страницы
│   │   ├── page.tsx         # Dashboard
│   │   ├── chambers/        # Каталог + HMI
│   │   ├── recipes/         # Рецепты + детали
│   │   ├── batches/         # Партии + создание
│   │   ├── competitors/     # Анализ конкурентов
│   │   ├── knowledge/       # База знаний
│   │   ├── settings/        # Профиль
│   │   └── login/           # Авторизация
│   ├── components/
│   │   ├── layout/          # Sidebar, Header, Providers
│   │   ├── ui/              # shadcn/ui компоненты
│   │   └── competitors/     # CompetitorCard, CompetitorDetails
│   ├── lib/
│   │   └── api/             # Axios client + JWT interceptors
│   ├── stores/              # Zustand (auth)
│   └── public/              # PWA манифест, иконки
├── scripts/                 # Парсеры и утилиты
│   ├── parse_ijiza_products_v2.py
│   ├── seed_recipes_batches.py
│   └── seed_knowledge.py
├── docs/                    # Документация и исследования
│   └── research/            # ijiza, конкуренты
├── docker-compose.yml
├── CHANGELOG.md
└── README.md
```

## 📊 Модули по приоритету

1. ✅ Dashboard с KPI и графиками
2. ✅ Камеры и производители (каталог + HMI)
3. ✅ Рецепты (конструктор + библиотека + детали)
4. ✅ Журнал партий (CRUD + фильтры)
5. ✅ База знаний (статьи с markdown)
6. ✅ Сравнение с конкурентами (Ижица, Mauting, Fessmann, Kerres)
7. ✅ Настройки и роли
8. 🔜 Интеграция Modbus с реальной камерой
9. 🔜 WebSocket production (Redis pub/sub)
10. 🔜 Telegram парсинг (нужен API_ID/API_HASH)

## 📜 Лицензия

© FELETI-SMOK, 2026. Внутренний проект.
