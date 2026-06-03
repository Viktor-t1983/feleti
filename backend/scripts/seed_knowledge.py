"""Seed knowledge articles."""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, engine
from app.models.knowledge import KnowledgeArticle, ArticleCategory
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def seed_knowledge(session) -> list[KnowledgeArticle]:
    user = await session.scalar(select(User).where(User.username == "admin"))
    user_id = user.id if user else None

    articles = [
        {
            "slug": "temperaturnye-rezhimy-gk",
            "title": "Температурные режимы горячего копчения",
            "category": ArticleCategory.GUIDE,
            "summary": "Оптимальные температуры для различных продуктов при горячем копчении.",
            "body_md": "# Температурные режимы горячего копчения\n\n## Общие принципы\n\nГорячее копчение проводится при температурах 50–120°C. Основные фазы:\n\n1. **Сушка (прогрев)** — 50–60°C, 20–40 мин\n2. **Копчение** — 70–90°C, 30–60 мин\n3. **Варка (доведение)** — 80–95°C, до достижения температуры внутри продукта 72°C\n4. **Душирование** — холодная вода, 5–10 мин\n\n## Таблица режимов\n\n| Продукт | Сушка | Копчение | Варка | Итого |\n|---------|-------|----------|-------|-------|\n| Колбасы | 60°C/30мин | 80°C/45мин | 82°C/60мин | ~2.5ч |\n| Рыба | 50°C/20мин | 70°C/30мин | 75°C/20мин | ~1.2ч |\n| Сыр | 55°C/40мин | 75°C/60мин | — | ~1.7ч |\n| Курица | 55°C/30мин | 80°C/40мин | 85°C/30мин | ~1.7ч |\n\n## Важные замечания\n\n- Температура внутри продукта должна достичь безопасного уровня (72°C для мяса)\n- Влажность на этапе копчения 30–50%\n- После варки обязательно душирование для остановки термообработки\n",
            "tags": ["температура", "горячее копчение", "режимы", "руководство"],
        },
        {
            "slug": "holodnoe-kopchenie-osnovy",
            "title": "Холодное копчение: основы технологии",
            "category": ArticleCategory.THEORY,
            "summary": "Принципы холодного копчения, требования к температуре дыма и длительность процесса.",
            "body_md": "# Холодное копчение: основы\n\n## Что такое холодное копчение?\n\nХолодное копчение — процесс обработки продуктов дымом при температуре **не выше 25°C** (оптимально 18–22°C).\n\n## Ключевые отличия от горячего копчения\n\n| Параметр | Холодное | Горячее |\n|----------|----------|---------|\n| Температура дыма | 18–25°C | 50–120°C |\n| Длительность | 12–72 ч | 1–3 ч |\n| Консервация | Высокая | Средняя |\n| Текстура | Плотная | Мягкая |\n| Срок хранения | До 30 дней | 3–10 дней |\n\n## Этапы процесса\n\n1. **Посол** — 12–48 часов в холодильнике при 2–4°C\n2. **Просушка** — 2–4 часа при 18°C для образования плёнки\n3. **Копчение** — 12–72 часа в зависимости от продукта\n4. **Вызревание** — 24–48 часов для стабилизации вкуса\n\n## Щепа для холодного копчения\n\nЛучшие породы: ольха, груша, яблоня. Дуб и бук дают слишком интенсивный дым.\n",
            "tags": ["холодное копчение", "теория", "щепа", "посол"],
        },
        {
            "slug": "chasto-oshibki-kopchenie",
            "title": "10 частых ошибок при копчении",
            "category": ArticleCategory.TROUBLESHOOTING,
            "summary": "Типичные ошибки начинающих и опытных технологов при копчении продуктов.",
            "body_md": "# 10 частых ошибок при копчении\n\n## 1. Перегрев продукта\nТемпература выше рекомендуемой приводит к выделению жира и усадке.\n\n## 2. Неправильная влажность\nСлишком сухой воздух — корка, слишком влажный — плесень.\n\n## 3. Сырая щепа\nВлажность щепы должна быть 15–25%. Сырая щепа даёт белый едкий дым.\n\n## 4. Перекопчение\nИзбыток дыма даёт горький привкус. Оптимальная плотность дыма — светло-золотистый цвет.\n\n## 5. Неправильный посол\nНедосол — быстрая порча, пересол — жёсткая текстура.\n\n## 6. Плотная укладка\nПродукты должны иметь зазор 2–3 см для циркуляции воздуха.\n\n## 7. Игнорирование прогрева\nХолодная камера даёт конденсат на продукте.\n\n## 8. Неправильное хранение\nПосле копчения продукт нужно охладить до 4°C в течение 2 часов.\n\n## 9. Использование окрашенной щепы\nКраска и лак выделяют токсины при нагреве.\n\n## 10. Отсутствие журнала\nБез записи параметров невозможно воспроизвести успешный рецепт.\n",
            "tags": ["ошибки", "решение проблем", "советы", "начинающим"],
        },
        {
            "slug": "vybor-koptilnoy-kamery",
            "title": "Как выбрать коптильную камеру для бизнеса",
            "category": ArticleCategory.COMPARISON,
            "summary": "Сравнение типов камер, расчёт мощности и ключевые параметры выбора оборудования.",
            "body_md": "# Как выбрать коптильную камеру\n\n## Типы камер\n\n### По принципу работы\n- **Камерные** — универсальны, подходят для малых и средних объёмов\n- **Туннельные** — непрерывное производство, высокая производительность\n\n### По типу копчения\n- Горячее копчение (H)\n- Холодное копчение (C)\n- Универсальные (U)\n- Электростатические (E)\n\n## Расчёт загрузки\n\nСуточная потребность = Производство (кг/день) / Количество циклов\n\nПример: 500 кг/день, 2 цикла → камера на 250 кг\n\n## Ключевые параметры\n\n| Параметр | Минимум | Рекомендуемо |\n|----------|---------|--------------|\n| Точность температуры | ±2°C | ±0.5°C |\n| Управление влажностью | Нет | Да |\n| Автоматизация | Полуавтомат | Полная |\n| Материал корпуса | Оцинковка | AISI 304 |\n| Гарантия | 1 год | 2+ года |\n\n## Облако и мониторинг\n\nСовременные камеры поддерживают:\n- Удалённый мониторинг через мобильное приложение\n- Загрузку рецептов из облака\n- Уведомления об ошибках в Telegram\n- Экспорт отчётов для HACCP\n",
            "tags": ["выбор оборудования", "сравнение", "бизнес", "покупка"],
        },
    ]

    result: list[KnowledgeArticle] = []
    for item in articles:
        existing = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue

        article = KnowledgeArticle(
            slug=item["slug"],
            title=item["title"],
            category=item["category"],
            excerpt=item["summary"],
            body_md=item["body_md"],
            tags=item["tags"],
            author_id=user_id,
            is_published=True,
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(article)
        result.append(article)

    await session.flush()
    logger.info("Knowledge articles: %s", len(result))
    return result


async def main():
    async with AsyncSessionLocal() as session:
        try:
            articles = await seed_knowledge(session)
            await session.commit()
            logger.info("=== Knowledge seed committed ===")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed")
            raise
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
