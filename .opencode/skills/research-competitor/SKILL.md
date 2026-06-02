# SKILL: research-competitor

> Парсинг сайта/каталога конкурента для наполнения базы знаний и каталога камер/рецептов. Используй при исследовании Ижицы, Mauting, Fessmann, Kerres и др.

## 1. Цели парсинга

1. **Каталог камер** — модели, ТТХ, цены, изображения.
2. **Контроллер и протокол** — Modbus-карта регистров, OPC UA, HTTP API.
3. **Рецепты** — программы копчения для разных продуктов.
4. **Маркетинг** — УТП, целевая аудитория, цены, каналы продаж.
5. **Технологии** — патенты, ноу-хау, white papers.
6. **Контент** — статьи, YouTube-обзоры, Telegram-каналы.

## 2. Источники

| Источник | Тип | Инструменты |
|---|---|---|
| **Сайт производителя** | HTML | `httpx` + `BeautifulSoup4` |
| **PDF-каталог** | PDF | `pdfplumber` (текст), `PyMuPDF` (таблицы) |
| **YouTube-обзор** | Видео | `yt-dlp` + `Whisper` (транскрибация) |
| **Telegram-канал** | Посты | `Telethon` |
| **Статья на сайте** | HTML/MD | `httpx` + `readability-lxml` |
| **Документация контроллера** | PDF/HTML | `pdfplumber` / `BeautifulSoup4` |
| **GitHub-репо** | Код | `git clone` + `ripgrep` |

## 3. Алгоритм парсинга

### 3.1. Подготовка
1. **Создать каталог** `docs/research/<manufacturer>/<YYYY-MM-DD>/`.
2. **Составить список URL** для парсинга (с сайта конкурента).
3. **Сохранить `urls.txt`** — все URL, что будем парсить.
4. **Согласовать** с пользователем (если сайт требует авторизации или может блокировать).

### 3.2. Парсинг HTML

```python
# backend/app/services/web_parser.py
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re
from pathlib import Path

class WebParser:
    def __init__(self, base_url: str, output_dir: Path):
        self.base_url = base_url
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; FELETI-SMOK-Bot/1.0)"},
            timeout=30.0,
            follow_redirects=True,
        )
    
    async def fetch(self, url: str) -> str:
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.text
    
    async def parse_chamber_page(self, url: str) -> dict:
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        return {
            "url": url,
            "title": soup.title.string if soup.title else None,
            "model": self._extract_model(soup),
            "type": self._extract_type(soup),
            "max_load_kg": self._extract_number(soup, r"загрузк[аи]?\s*(\d+)\s*кг"),
            "volume_m3": self._extract_number(soup, r"объ[её]м\s*(\d+\.?\d*)\s*м"),
            "power_kw": self._extract_number(soup, r"мощност[ьи]\s*(\d+\.?\d*)\s*кВт"),
            "voltage_v": self._extract_number(soup, r"(\d{3})\s*В"),
            "supports_electro": "электростат" in html.lower(),
            "description": self._extract_description(soup),
            "images": self._extract_images(soup, url),
            "price": self._extract_price(soup),
        }
    
    def _extract_model(self, soup) -> str:
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else None
    
    def _extract_type(self, soup) -> str:
        text = soup.get_text().lower()
        if "электростат" in text:
            return "электро"
        if "горяч" in text and "холодн" in text:
            return "универсальное"
        if "горяч" in text:
            return "горячее"
        if "холодн" in text:
            return "холодное"
        return "неизвестно"
    
    def _extract_number(self, soup, pattern: str) -> float | None:
        text = soup.get_text()
        m = re.search(pattern, text, re.IGNORECASE)
        return float(m.group(1)) if m else None
    
    def _extract_description(self, soup) -> str:
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            return desc.get("content", "").strip()
        # Fallback: первый <p> длиннее 100 символов
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 100:
                return text
        return ""
    
    def _extract_images(self, soup, base_url: str) -> list[str]:
        return [
            urljoin(base_url, img["src"])
            for img in soup.find_all("img", src=True)
            if "logo" not in img["src"].lower() and "icon" not in img["src"].lower()
        ]
    
    def _extract_price(self, soup) -> str | None:
        # Поиск цены в формате "X XXX руб" или "X XXX ₽"
        text = soup.get_text()
        m = re.search(r"(\d[\d\s]+)\s*(руб|₽|р\.)", text)
        return m.group(0) if m else None
    
    async def parse_catalog(self, urls: list[str]) -> list[dict]:
        results = []
        for url in urls:
            try:
                data = await self.parse_chamber_page(url)
                results.append(data)
                # Сохраняем HTML
                html_file = self.output_dir / f"{self._slug(url)}.html"
                html_file.write_text(await self.fetch(url), encoding="utf-8")
                # Сохраняем JSON
                json_file = self.output_dir / f"{self._slug(url)}.json"
                json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"Error parsing {url}: {e}")
        return results
    
    def _slug(self, url: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:100]
```

### 3.3. Парсинг PDF

```python
# backend/app/services/pdf_parser.py
import pdfplumber
import json
from pathlib import Path

class PDFParser:
    def __init__(self, pdf_path: Path, output_dir: Path):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text(self) -> str:
        text_parts = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        full_text = "\n\n".join(text_parts)
        (self.output_dir / f"{self.pdf_path.stem}.txt").write_text(full_text, encoding="utf-8")
        return full_text
    
    def extract_tables(self) -> list[list[list[str]]]:
        all_tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    all_tables.append({
                        "page": page_num + 1,
                        "data": table,
                    })
        (self.output_dir / f"{self.pdf_path.stem}.tables.json").write_text(
            json.dumps(all_tables, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return all_tables
    
    def extract_chambers(self) -> list[dict]:
        """Извлечь данные о камерах из PDF-каталога."""
        text = self.extract_text()
        # Здесь — специфичная логика под формат каталога
        # Например: регулярки для "Модель: ...", "Загрузка: ...", "Мощность: ..."
        chambers = []
        # ... парсинг
        return chambers
```

### 3.4. Парсинг YouTube (транскрибация)

```python
# backend/app/services/youtube_parser.py
import yt_dlp
from pathlib import Path
import subprocess

class YouTubeParser:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_audio(self, url: str) -> Path:
        """Скачать аудиодорожку видео."""
        out_path = self.output_dir / f"{self._video_id(url)}.mp3"
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": str(out_path.with_suffix("")),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return out_path
    
    def transcribe(self, audio_path: Path, lang: str = "ru") -> str:
        """Транскрибация через Whisper API."""
        from openai import OpenAI
        client = OpenAI()
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=lang,
                response_format="text",
            )
        text_file = audio_path.with_suffix(".txt")
        text_file.write_text(transcript, encoding="utf-8")
        return transcript
    
    def _video_id(self, url: str) -> str:
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        return url.split("/")[-1]
```

### 3.5. Парсинг Telegram (Telethon)

```python
# backend/app/services/telegram_parser.py
from telethon import TelegramClient
from datetime import datetime
import json
from pathlib import Path

class TelegramParser:
    def __init__(self, api_id: int, api_hash: str, output_dir: Path):
        self.api_id = api_id
        self.api_hash = api_hash
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = TelegramClient("session_feleti", api_id, api_hash)
    
    async def parse_channel(self, channel: str, limit: int = 1000):
        await self.client.start()
        messages = []
        async for msg in self.client.iter_messages(channel, limit=limit):
            messages.append({
                "id": msg.id,
                "date": msg.date.isoformat(),
                "text": msg.text,
                "views": msg.views,
                "forwards": msg.forwards,
                "replies": msg.replies.replies if msg.replies else 0,
                "media": bool(msg.media),
            })
        out_file = self.output_dir / f"{channel.replace('@', '')}.json"
        out_file.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
        await self.client.disconnect()
        return messages
```

## 4. Структура результатов

```
docs/research/ijiza/2026-06-02/
├── urls.txt                       # Список URL
├── raw/
│   ├── varmen-1.html
│   ├── varmen-2.html
│   ├── catalog-2024.pdf
│   ├── catalog-2024.txt
│   └── catalog-2024.tables.json
├── parsed/
│   ├── chambers.json              # Структурированные данные
│   ├── recipes.json
│   └── prices.json
├── transcripts/
│   ├── ijiza-z115a-review.txt
│   └── kerres-systems-overview.txt
└── SUMMARY.md                     # Резюме: что узнали
```

## 5. Шаблон `SUMMARY.md`

```markdown
# Исследование [Производитель] — YYYY-MM-DD

## Источники
- https://... (каталог)
- https://... (карточка товара)
- YouTube: ...
- Telegram: ...

## Что узнали
1. **Камеры:** список моделей, ТТХ, цены.
2. **Технологии:** электростатика, Turbomat, Jet Smoke.
3. **Рецепты:** типовые программы для скумбрии, салаки и т.д.
4. **Контроллер:** Varmen-1 / FOOD.CON 2 / ...
5. **Протокол:** Modbus TCP (адрес/порт), OPC UA, HTTP.
6. **Цены:** диапазон, опции.
7. **Маркетинг:** УТП, целевая аудитория.

## Что НЕ узнали
- Точная Modbus-карта регистров (нужен Wireshark).
- Рецепты для Industrial-моделей.
- Цены на Profi/Industrial (по запросу).

## Что сделать дальше
- [ ] Сидировать камеры в БД.
- [ ] Сидировать рецепты в БД.
- [ ] Проверить Modbus-регистры на реальной камере.
- [ ] Добавить источник в `docs/COMPETITORS.md`.
```

## 6. Чек-лист

- [ ] Список URL сохранён в `urls.txt`.
- [ ] Robots.txt и Terms of Service проверены.
- [ ] User-Agent указан (хороший бот, не вредоносный).
- [ ] Rate-limit: не чаще 1 запроса в 2 секунды.
- [ ] Сырые HTML/PDF/видео сохранены в `raw/`.
- [ ] Структурированный JSON в `parsed/`.
- [ ] Транскрибация видео через Whisper.
- [ ] `SUMMARY.md` написан.
- [ ] Источник данных указан.
- [ ] В БД засеяно через `seed-data`.
- [ ] В `COMPETITORS.md` обновлено.

## 7. Этика и право

- ✅ **Разрешено:** парсить публично доступные данные (без авторизации).
- ✅ **Разрешено:** парсить PDF-каталоги, разосланные публично.
- ✅ **Разрешено:** индексировать Telegram-каналы, где есть подписка.
- ❌ **Запрещено:** обходить авторизацию, CAPTCHA, robots.txt disallow.
- ❌ **Запрещено:** перепубликовывать данные под своим брендом.
- ✅ **Можно:** использовать данные как reference для своих рецептов (с указанием источника).
- ❌ **Запрещено:** копировать рецепты дословно (нарушение авторских прав).
- ⚠️ **Осторожно:** GDPR/PД-данные — не собирать личные данные пользователей.

## 8. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `add-chamber` — для сидирования камер.
- `add-recipe` — для сидирования рецептов.
- `seed-data` — для запуска сидирования.
- `knowledge-search` — для индексации распарсенных статей в БД.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при парсинге сайта/каталога конкурента.
