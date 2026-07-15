"""AI Content Manager — модуль генерации сценариев Reels из длинного видео.

Первая версия. Единственная задача модуля: из одного длинного видео (или его
транскрипта) автоматически сделать 10 готовых сценариев Reels. Каждый сценарий
содержит:
    - сильный хук (первые 1–3 секунды, которые останавливают скролл);
    - тайм-коды исходного видео (какой фрагмент нарезать);
    - цепляющий заголовок;
    - текст сценария, готовую подпись, хэштеги и призыв к действию.

Работает поверх Google Gemini. Поддерживает два вида входных данных:
    1. Видео-файл (mp4/mov/…): загружается в Gemini File API, тайм-коды берутся
       из нативного анализа видео — они точные.
    2. Транскрипт: обычный текст или субтитры (.srt/.vtt) с тайм-кодами.

Использование из кода:
    from content_manager import generate_reels_scripts
    reels = generate_reels_scripts("lecture.mp4")

Использование из терминала:
    python content_manager.py lecture.mp4
    python content_manager.py transcript.srt --num 10 --output reels.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_NUM_REELS = 10
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mpeg", ".mpg"}
TRANSCRIPT_EXTENSIONS = {".txt", ".srt", ".vtt", ".md"}

# Контекст ниши. По умолчанию — кинезиолог Александр Бондарь (под проект бота),
# но легко переопределяется параметром `context`.
DEFAULT_CONTEXT = (
    "Автор — кинезиолог Александр Бондарь. Ниша: устранение боли в теле, "
    "работа с мышцами, суставами, осанкой. Сильное УТП: «устранение боли за "
    "1 приём или бесплатно». Аудитория — люди с болями в спине, шее, суставах, "
    "которые устали от таблеток и врачей. Тон: экспертный, уверенный, простой "
    "человеческий язык без сложных терминов."
)


# ---------------------------------------------------------------------------
# Модель данных
# ---------------------------------------------------------------------------

@dataclass
class ReelScript:
    """Один готовый сценарий Reels."""

    number: int
    title: str                 # Заголовок ролика
    hook: str                  # Сильный хук — первая фраза (1–3 сек)
    start: str                 # Тайм-код начала фрагмента в исходном видео (MM:SS)
    end: str                   # Тайм-код конца фрагмента (MM:SS)
    topic: str                 # О чём этот Reels
    script: str                # Текст сценария / раскадровка по секундам
    caption: str               # Готовая подпись под видео
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""              # Призыв к действию

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        tags = " ".join(self.hashtags)
        return (
            f"## Reels #{self.number}: {self.title}\n\n"
            f"**Тайм-код в видео:** {self.start} – {self.end}\n\n"
            f"**🎣 Хук (0–3 сек):** {self.hook}\n\n"
            f"**Тема:** {self.topic}\n\n"
            f"**Сценарий:**\n{self.script}\n\n"
            f"**Подпись:** {self.caption}\n\n"
            f"**CTA:** {self.cta}\n\n"
            f"**Хэштеги:** {tags}\n"
        )


# ---------------------------------------------------------------------------
# Промпт
# ---------------------------------------------------------------------------

def _build_prompt(num_reels: int, context: str) -> str:
    return f"""Ты — сильный контент-менеджер и сценарист коротких вертикальных видео
(Reels / Shorts / TikTok). Тебе дан ИСХОДНИК — длинное видео или его транскрипт.

{context}

ЗАДАЧА: разбей исходник и собери ровно {num_reels} ГОТОВЫХ сценариев Reels.
Каждый Reels — это самостоятельный вертикальный ролик 20–60 секунд, вырезанный
из исходного видео. Выбирай самые сильные, полезные и цепляющие моменты: боли
аудитории, инсайты, мифы, ошибки, «до/после», конкретные приёмы.

ТРЕБОВАНИЯ К КАЖДОМУ СЦЕНАРИЮ:
1. hook — СИЛЬНЫЙ хук на первые 1–3 секунды. Он должен останавливать скролл:
   провокация, боль, любопытство, обещание результата или неожиданный факт.
   Никаких «Привет, меня зовут…». Хук = первая произнесённая фраза.
2. start / end — тайм-коды фрагмента в ИСХОДНОМ видео в формате MM:SS
   (или HH:MM:SS для длинных). Это отрезок, который нужно вырезать. Если на входе
   транскрипт без тайм-кодов — оцени их по позиции текста как можно точнее.
3. title — короткий цепляющий заголовок ролика (до 60 символов).
4. topic — одна строка: о чём ролик.
5. script — раскадровка/текст по секундам: что говорит и показывает автор.
   Пиши разговорным языком, готовым к озвучке. Структура: Хук → Суть → Пример →
   Вывод → CTA.
6. caption — готовая подпись под публикацию (1–3 предложения, с эмодзи по делу).
7. hashtags — 5–8 релевантных хэштегов на русском/латинице.
8. cta — призыв к действию (записаться, подписаться, написать в директ).

ВАЖНО:
- Ровно {num_reels} сценариев, без повторов по смыслу.
- Тайм-коды не должны пересекаться и должны идти по возрастанию времени.
- Всё на русском языке.
- Верни ТОЛЬКО валидный JSON без markdown-обёртки, строго по схеме:

{{
  "reels": [
    {{
      "number": 1,
      "title": "…",
      "hook": "…",
      "start": "MM:SS",
      "end": "MM:SS",
      "topic": "…",
      "script": "…",
      "caption": "…",
      "hashtags": ["#…", "#…"],
      "cta": "…"
    }}
  ]
}}
"""


# ---------------------------------------------------------------------------
# Определение типа входных данных
# ---------------------------------------------------------------------------

def _classify_source(source: str) -> str:
    """Возвращает 'video', 'transcript_file' или 'text'."""
    if os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()
        if ext in VIDEO_EXTENSIONS:
            return "video"
        if ext in TRANSCRIPT_EXTENSIONS:
            return "transcript_file"
        # Неизвестное расширение файла — читаем как текст
        return "transcript_file"
    # Не файл — считаем, что это переданный напрямую текст транскрипта
    return "text"


def _read_transcript(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Взаимодействие с Gemini
# ---------------------------------------------------------------------------

def _get_client(api_key: str):
    try:
        from google import genai  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Не установлен пакет google-genai. Установите: pip install google-genai"
        ) from exc
    return genai.Client(api_key=api_key)


def _upload_video(client, video_path: str, poll_interval: float = 3.0, timeout: float = 600.0):
    """Загружает видео в Gemini File API и ждёт, пока оно станет ACTIVE."""
    uploaded = client.files.upload(file=video_path)
    waited = 0.0
    while getattr(uploaded.state, "name", str(uploaded.state)) == "PROCESSING":
        if waited >= timeout:
            raise TimeoutError("Gemini слишком долго обрабатывает видео (таймаут).")
        time.sleep(poll_interval)
        waited += poll_interval
        uploaded = client.files.get(name=uploaded.name)
    state = getattr(uploaded.state, "name", str(uploaded.state))
    if state == "FAILED":
        raise RuntimeError("Gemini не смог обработать загруженное видео (FAILED).")
    return uploaded


def _generate_content(client, model: str, contents: list[Any]) -> str:
    """Вызывает модель и возвращает сырой текст ответа."""
    try:
        from google.genai import types  # type: ignore
        config = types.GenerateContentConfig(response_mime_type="application/json")
        response = client.models.generate_content(
            model=model, contents=contents, config=config
        )
    except Exception:
        # Совместимость со старыми версиями SDK: без config
        response = client.models.generate_content(model=model, contents=contents)
    return response.text or ""


# ---------------------------------------------------------------------------
# Парсинг ответа
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> dict[str, Any]:
    """Достаёт JSON из ответа модели, снимая возможную markdown-обёртку."""
    text = raw.strip()
    if text.startswith("```"):
        # Убираем ```json … ```
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    # Берём фрагмент от первой { до последней }
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        text = text[first : last + 1]
    return json.loads(text)


def _parse_reels(raw: str) -> list[ReelScript]:
    data = _extract_json(raw)
    items = data.get("reels", data if isinstance(data, list) else [])
    reels: list[ReelScript] = []
    for idx, item in enumerate(items, start=1):
        reels.append(
            ReelScript(
                number=int(item.get("number", idx)),
                title=str(item.get("title", "")).strip(),
                hook=str(item.get("hook", "")).strip(),
                start=str(item.get("start", "")).strip(),
                end=str(item.get("end", "")).strip(),
                topic=str(item.get("topic", "")).strip(),
                script=str(item.get("script", "")).strip(),
                caption=str(item.get("caption", "")).strip(),
                hashtags=[str(h).strip() for h in item.get("hashtags", []) if str(h).strip()],
                cta=str(item.get("cta", "")).strip(),
            )
        )
    return reels


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------

def generate_reels_scripts(
    source: str,
    *,
    num_reels: int = DEFAULT_NUM_REELS,
    context: str = DEFAULT_CONTEXT,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> list[ReelScript]:
    """Главная функция модуля.

    Args:
        source: путь к видео-файлу, к файлу транскрипта или сам текст транскрипта.
        num_reels: сколько сценариев Reels сделать (по умолчанию 10).
        context: описание ниши/автора для попадания в тон.
        api_key: ключ Gemini. По умолчанию берётся из env GEMINI_API_KEY.
        model: модель Gemini.

    Returns:
        Список из `num_reels` объектов ReelScript.
    """
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан GEMINI_API_KEY (переменная окружения или аргумент api_key)."
        )

    client = _get_client(api_key)
    prompt = _build_prompt(num_reels, context)
    kind = _classify_source(source)

    if kind == "video":
        video = _upload_video(client, source)
        contents = [video, prompt]
    else:
        transcript = _read_transcript(source) if kind == "transcript_file" else source
        contents = [prompt + "\n\n=== ИСХОДНИК (транскрипт) ===\n" + transcript]

    raw = _generate_content(client, model, contents)
    reels = _parse_reels(raw)
    if not reels:
        raise RuntimeError(
            "Модель не вернула ни одного сценария. Ответ:\n" + raw[:1000]
        )
    return reels


# ---------------------------------------------------------------------------
# Форматирование результата
# ---------------------------------------------------------------------------

def reels_to_markdown(reels: list[ReelScript]) -> str:
    header = f"# Сценарии Reels ({len(reels)} шт.)\n\n"
    return header + "\n---\n\n".join(r.to_markdown() for r in reels)


def reels_to_json(reels: list[ReelScript]) -> str:
    return json.dumps(
        {"reels": [r.to_dict() for r in reels]}, ensure_ascii=False, indent=2
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Content Manager — 10 сценариев Reels из одного длинного видео."
    )
    parser.add_argument("source", help="Путь к видео, к транскрипту или текст транскрипта.")
    parser.add_argument("--num", type=int, default=DEFAULT_NUM_REELS, help="Сколько Reels (по умолчанию 10).")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Модель Gemini.")
    parser.add_argument("--output", help="Куда сохранить результат (.json или .md). Иначе — в консоль.")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Формат вывода в консоль.")
    args = parser.parse_args(argv)

    try:
        reels = generate_reels_scripts(args.source, num_reels=args.num, model=args.model)
    except Exception as exc:  # noqa: BLE001
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    if args.output:
        content = reels_to_json(reels) if args.output.endswith(".json") else reels_to_markdown(reels)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"Готово: {len(reels)} сценариев сохранено в {args.output}")
    else:
        print(reels_to_json(reels) if args.format == "json" else reels_to_markdown(reels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
