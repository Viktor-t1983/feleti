#!/usr/bin/env python3
"""
Парсинг всех видео Ижицы с YouTube.
Этапы:
1. Поиск видео по запросам через yt-dlp
2. Скачивание аудиодорожек
3. Транскрибация через OpenAI Whisper API
4. Сохранение результатов в docs/research/ijiza/youtube/

Использование:
    python scripts/parse_ijiza_youtube.py --search-only
    python scripts/parse_ijiza_youtube.py --download
    python scripts/parse_ijiza_youtube.py --transcribe
    python scripts/parse_ijiza_youtube.py --all
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Конфигурация
OUTPUT_DIR = Path("docs/research/ijiza/youtube")
AUDIO_DIR = OUTPUT_DIR / "audio"
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
METADATA_FILE = OUTPUT_DIR / "videos.json"

# Запросы для поиска
SEARCH_QUERIES = [
    "ижица коптильная камера",
    "ижица копчение",
    "ижица рецепты",
    "ижица обзор",
    "ижица varmen",
    "ижица z115",
    "ижица электростатическое копчение",
    "ижица холодное копчение",
    "ижица горячее копчение",
    "ижица программа копчения",
    "varmen копчение",
    "varmen z115",
    "коптильня ижица",
    "дымогенератор ижица",
    "ижица колбаса",
    "ижица сало",
    "ижица рыба",
    "ижица скумбрия",
    "ижица сельдь",
    "ижица грудинка",
]


def search_videos(query: str, limit: int = 20) -> list[dict]:
    """Поиск видео на YouTube через yt-dlp."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--playlist-end", str(limit),
        f"ytsearch{limit}:{query}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            videos.append({
                "id": data.get("id"),
                "title": data.get("title"),
                "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                "duration": data.get("duration"),
                "channel": data.get("channel"),
                "channel_id": data.get("channel_id"),
                "upload_date": data.get("upload_date"),
                "view_count": data.get("view_count"),
                "query": query,
            })
        except json.JSONDecodeError:
            continue
    
    return videos


def search_all() -> list[dict]:
    """Поиск по всем запросам, дедупликация."""
    all_videos = {}
    
    for query in SEARCH_QUERIES:
        print(f"🔍 Поиск: {query}")
        videos = search_videos(query, limit=15)
        for v in videos:
            vid = v["id"]
            if vid not in all_videos:
                all_videos[vid] = v
                all_videos[vid]["queries"] = [query]
            else:
                all_videos[vid]["queries"].append(query)
        print(f"   Найдено: {len(videos)} видео")
    
    videos_list = list(all_videos.values())
    videos_list.sort(key=lambda x: x.get("view_count", 0) or 0, reverse=True)
    
    print(f"\n✅ Всего уникальных видео: {len(videos_list)}")
    return videos_list


def download_audio(video_id: str, url: str, title: str) -> Path | None:
    """Скачивание аудиодорожки видео."""
    output_path = AUDIO_DIR / f"{video_id}.mp3"
    
    if output_path.exists():
        print(f"   ⏭️ Аудио уже скачано: {title}")
        return output_path
    
    print(f"   ⬇️ Скачивание: {title}")
    
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "128K",
        "--output", str(AUDIO_DIR / "%(id)s.%(ext)s"),
        "--no-playlist",
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ Скачано: {size_mb:.1f} MB")
        return output_path
    else:
        print(f"   ❌ Ошибка скачивания: {title}")
        print(f"      stderr: {result.stderr[:200]}")
        return None


def transcribe_with_openai(audio_path: Path, video_id: str, title: str) -> str | None:
    """Транскрибация через OpenAI Whisper API."""
    transcript_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    
    if transcript_path.exists():
        print(f"   ⏭️ Транскрипция уже существует: {title}")
        return transcript_path.read_text(encoding="utf-8")
    
    print(f"   📝 Транскрибация: {title}")
    
    try:
        from openai import OpenAI
        client = OpenAI()
        
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ru",
                response_format="text",
            )
        
        transcript_path.write_text(transcript, encoding="utf-8")
        print(f"   ✅ Транскрибировано: {len(transcript)} символов")
        return transcript
    
    except Exception as e:
        print(f"   ❌ Ошибка транскрибации: {e}")
        return None


def transcribe_with_local(audio_path: Path, video_id: str, title: str) -> str | None:
    """Транскрибация через локальный faster-whisper (fallback)."""
    transcript_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
    
    if transcript_path.exists():
        print(f"   ⏭️ Транскрипция уже существует: {title}")
        return transcript_path.read_text(encoding="utf-8")
    
    print(f"   📝 Транскрибация (local): {title}")
    
    try:
        from faster_whisper import WhisperModel
        
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), language="ru", beam_size=5)
        
        transcript = "\n".join([seg.text for seg in segments])
        transcript_path.write_text(transcript, encoding="utf-8")
        print(f"   ✅ Транскрибировано: {len(transcript)} символов")
        return transcript
    
    except Exception as e:
        print(f"   ❌ Ошибка транскрибации (local): {e}")
        return None


def extract_structured_info(video_id: str, title: str, transcript: str) -> dict:
    """Извлечение структурированной информации из транскрипта."""
    info = {
        "video_id": video_id,
        "title": title,
        "products_mentioned": [],
        "technologies_mentioned": [],
        "problems_mentioned": [],
        "recipes_mentioned": [],
        "equipment_mentioned": [],
        "has_recipe_details": False,
        "has_program_details": False,
        "has_problem_details": False,
    }
    
    # Продукты
    products = [
        "скумбрия", "сельдь", "форель", "палтус", "ставрида", "мойва", "окунь",
        "сало", "грудинка", "шейка", "окорок", "рулька", "буженина", "карбонат",
        "колбаса", "сосиска", "сардельки", "ветчина", "бекон", "пастрома",
        "курица", "утка", "гусь", "индейка", "перепел",
        "сыр", "чечил", "косичка", "копченый сыр",
        "оленина", "косуля", "кабан",
    ]
    
    # Технологии
    technologies = [
        "электростатическое копчение", "холодное копчение", "горячее копчение",
        "сушка", "варка", "запекание", "жарка", "проветривание", "прогрев",
        "влажность", "температура", "время копчения", "дымогенератор",
        "щепа", "ольха", "бук", "черешня", "яблоня", "фруктовые породы",
        "оболочка", "натуральная оболочка", "искусственная оболочка",
        "посол", "соление", "маринование", "сушильно-вялочная",
    ]
    
    # Проблемы
    problems = [
        "пересушивание", "перекопчение", "недокопчение", "сухой", "жесткий",
        "трещины", "плесень", "конденсат", "капли", "желтый", "серый",
        "электростатика", "статика", "изолятор", "дым", "шибер", "вентилятор",
        "поломка", "ремонт", "чистка", "зольник", "нагар",
    ]
    
    # Оборудование
    equipment = [
        "varmen", "ижица", "z115", "dl400", "dl450", "ф10", "ф15",
        "дымогенератор", "камера", "коптильня", "термокамера",
        "панель управления", "контроллер", "датчик", "тэн",
    ]
    
    text_lower = transcript.lower()
    
    for p in products:
        if p in text_lower:
            info["products_mentioned"].append(p)
    
    for t in technologies:
        if t in text_lower:
            info["technologies_mentioned"].append(t)
    
    for p in problems:
        if p in text_lower:
            info["problems_mentioned"].append(p)
    
    for e in equipment:
        if e in text_lower:
            info["equipment_mentioned"].append(e)
    
    # Проверка на детали
    if "градус" in text_lower or "°c" in text_lower or "°с" in text_lower:
        info["has_recipe_details"] = True
    if "шаг" in text_lower and "программ" in text_lower:
        info["has_program_details"] = True
    if "проблем" in text_lower or "поломк" in text_lower or "не работает" in text_lower:
        info["has_problem_details"] = True
    
    return info


def main():
    parser = argparse.ArgumentParser(description="Парсинг видео Ижицы с YouTube")
    parser.add_argument("--search-only", action="store_true", help="Только поиск видео")
    parser.add_argument("--download", action="store_true", help="Скачать аудио")
    parser.add_argument("--transcribe", action="store_true", help="Транскрибировать")
    parser.add_argument("--all", action="store_true", help="Все этапы")
    parser.add_argument("--limit", type=int, default=None, help="Ограничение количества видео")
    parser.add_argument("--use-local", action="store_true", help="Использовать локальный whisper вместо OpenAI API")
    args = parser.parse_args()
    
    if not any([args.search_only, args.download, args.transcribe, args.all]):
        parser.print_help()
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Этап 1: Поиск
    if args.search_only or args.all:
        print("=" * 60)
        print("ЭТАП 1: Поиск видео на YouTube")
        print("=" * 60)
        
        videos = search_all()
        
        # Сохраняем метаданные
        METADATA_FILE.write_text(
            json.dumps(videos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n💾 Метаданные сохранены: {METADATA_FILE}")
        
        # Выводим список
        print("\n📋 Найденные видео (топ-20 по просмотрам):")
        for i, v in enumerate(videos[:20], 1):
            duration_min = (v.get("duration") or 0) // 60
            views = v.get("view_count") or 0
            print(f"  {i}. [{views:,} просмотров] {v['title'][:70]} ({duration_min} мин)")
        
        if args.search_only:
            return
    
    # Загружаем метаданные если пропустили поиск
    if not METADATA_FILE.exists():
        print("❌ Нет файла метаданных. Сначала запустите с --search-only или --all")
        return
    
    videos = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    
    if args.limit:
        videos = videos[:args.limit]
        print(f"\n⚙️ Ограничение: {args.limit} видео")
    
    # Этап 2: Скачивание
    if args.download or args.all:
        print("\n" + "=" * 60)
        print("ЭТАП 2: Скачивание аудио")
        print("=" * 60)
        
        downloaded = 0
        for v in videos:
            path = download_audio(v["id"], v["url"], v["title"])
            if path:
                downloaded += 1
        
        print(f"\n✅ Скачано аудио: {downloaded}/{len(videos)}")
        
        if args.download:
            return
    
    # Этап 3: Транскрибация
    if args.transcribe or args.all:
        print("\n" + "=" * 60)
        print("ЭТАП 3: Транскрибация")
        print("=" * 60)
        
        transcribe_fn = transcribe_with_local if args.use_local else transcribe_with_openai
        
        transcribed = 0
        structured_results = []
        
        for v in videos:
            audio_path = AUDIO_DIR / f"{v['id']}.mp3"
            
            if not audio_path.exists():
                print(f"   ⏭️ Нет аудио: {v['title']}")
                continue
            
            transcript = transcribe_fn(audio_path, v["id"], v["title"])
            
            if transcript:
                transcribed += 1
                info = extract_structured_info(v["id"], v["title"], transcript)
                structured_results.append(info)
        
        print(f"\n✅ Транскрибировано: {transcribed}/{len(videos)}")
        
        # Сохраняем структурированную информацию
        summary_file = OUTPUT_DIR / "summary.json"
        summary_file.write_text(
            json.dumps(structured_results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"💾 Сводка сохранена: {summary_file}")
        
        # Статистика
        print("\n📊 Статистика:")
        all_products = set()
        all_technologies = set()
        all_problems = set()
        
        for r in structured_results:
            all_products.update(r["products_mentioned"])
            all_technologies.update(r["technologies_mentioned"])
            all_problems.update(r["problems_mentioned"])
        
        print(f"  Продуктов найдено: {len(all_products)} — {', '.join(sorted(all_products))}")
        print(f"  Технологий найдено: {len(all_technologies)} — {', '.join(sorted(all_technologies))}")
        print(f"  Проблем найдено: {len(all_problems)} — {', '.join(sorted(all_problems))}")


if __name__ == "__main__":
    main()
