"""YouTube Transcriber — транскрибация видео-обзоров конкурентов.

Обёртка над yt-dlp + faster-whisper.
Превращает видеообзоры в структурированные данные о продуктах и технологиях.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any
from datetime import datetime

from .knowledge_pipeline import CrawlResult, SourceType

logger = logging.getLogger(__name__)


class YouTubeTranscriber:
    """Транскрибация YouTube-видео через yt-dlp + faster-whisper."""

    def __init__(self, output_dir: str = "data/youtube"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def search_videos(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Поиск видео по запросу через yt-dlp."""
        cmd = [
            "yt-dlp",
            f"ytsearch{max_results}:{query}",
            "--dump-json",
            "--no-download",
            "--flat-playlist",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        videos.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return videos
        except subprocess.TimeoutExpired:
            logger.error(f"yt-dlp search timeout for: {query}")
            return []
        except Exception as e:
            logger.error(f"yt-dlp search error: {e}")
            return []

    async def download_audio(self, video_url: str, video_id: str) -> Path | None:
        """Скачать аудиодорожку видео."""
        output_path = self._output_dir / f"{video_id}.mp3"
        if output_path.exists():
            return output_path

        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", str(self._output_dir / f"{video_id}.%(ext)s"),
            video_url,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=300)
            if output_path.exists():
                return output_path
            return None
        except Exception as e:
            logger.error(f"Audio download error {video_url}: {e}")
            return None

    async def transcribe(self, audio_path: Path) -> str:
        """Транскрибация аудио через faster-whisper."""
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(str(audio_path), language="ru")
            return " ".join(seg.text for seg in segments)
        except ImportError:
            logger.warning("faster-whisper not installed, trying whisper")
            return await self._transcribe_fallback(audio_path)
        except Exception as e:
            logger.error(f"Transcription error {audio_path}: {e}")
            return ""

    async def _transcribe_fallback(self, audio_path: Path) -> str:
        """Fallback на системный whisper."""
        cmd = ["whisper", str(audio_path), "--model", "tiny", "--language", "ru", "--output_format", "txt"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return result.stdout or ""
        except Exception as e:
            logger.error(f"Whisper fallback error: {e}")
            return ""

    async def crawl(self, url: str) -> CrawlResult:
        """Полный цикл: поиск → скачивание → транскрибация."""
        result = CrawlResult(source_type=SourceType.YOUTUBE, source_url=url)

        # Извлекаем video_id из URL
        video_id = ""
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]

        if not video_id:
            result.errors.append(f"Не удалось извлечь video_id из: {url}")
            return result

        result.metadata["video_id"] = video_id

        # Скачиваем
        audio_path = await self.download_audio(url, video_id)
        if not audio_path:
            result.errors.append(f"Не удалось скачать аудио: {url}")
            return result

        # Транскрибируем
        text = await self.transcribe(audio_path)
        result.raw_text = text
        result.metadata["transcribed_at"] = datetime.utcnow().isoformat()
        result.metadata["audio_path"] = str(audio_path)

        # Получаем метаданные видео
        videos = await self.search_videos(url, max_results=1)
        if videos:
            result.metadata["title"] = videos[0].get("title", "")
            result.metadata["channel"] = videos[0].get("channel", "")
            result.metadata["duration"] = videos[0].get("duration", 0)
            result.metadata["view_count"] = videos[0].get("view_count", 0)

        return result

    async def crawl_competitor(self, query: str, max_videos: int = 30) -> list[CrawlResult]:
        """Найти и транскрибировать видео по запросу."""
        videos = await self.search_videos(query, max_results=max_videos)
        results = []
        for video in videos:
            url = f"https://youtube.com/watch?v={video['id']}"
            result = await self.crawl(url)
            results.append(result)
        return results
