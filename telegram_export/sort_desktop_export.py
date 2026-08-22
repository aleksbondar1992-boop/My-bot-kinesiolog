# -*- coding: utf-8 -*-
"""Раскладка готового экспорта Telegram Desktop по папкам (без видео).

Путь без api-ключей: канал выгружается самим Telegram Desktop
(Настройки → Продвинутые настройки → Экспорт данных, формат JSON),
а этот скрипт разбирает получившуюся папку и раскладывает файлы
по категориям: сертификаты, отзывы, результаты, обычные фото.

  python sort_desktop_export.py --src "D:\\ChatExport_2026-08-22" --out "D:\\Экспорт_канала"

По умолчанию файлы копируются, исходная выгрузка остаётся нетронутой (--move — перенести).
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import common

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = r"D:\Экспорт_канала" if os.name == "nt" else str(Path.home() / "tg_export")

# Как Telegram Desktop помечает видео — такие сообщения пропускаем.
VIDEO_MEDIA_TYPES = {"video_file", "animation", "video_message"}
NOT_DOWNLOADED = "(File not included"


def extract_text(value):
    """Поле text бывает строкой, а бывает списком кусочков со ссылками."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def message_media(msg):
    """Возвращает (относительный путь к файлу, тип) или (None, тип)."""
    media_type = msg.get("media_type", "")
    mime = msg.get("mime_type", "")

    if media_type in VIDEO_MEDIA_TYPES or mime.startswith("video/"):
        return None, "video"
    if media_type == "sticker":
        return msg.get("file"), "sticker"

    if msg.get("photo"):
        return msg["photo"], "photo"

    path = msg.get("file")
    if not path or str(path).startswith(NOT_DOWNLOADED):
        return None, "none"
    if media_type == "voice_message":
        return path, "voice"
    if media_type == "audio_file" or mime.startswith("audio/"):
        return path, "audio"
    if mime.startswith("image/"):
        return path, "photo"
    return path, "document"


def album_texts(messages):
    """У альбома подпись только у одного сообщения — раздаём её всей секунде."""
    texts = {}
    for msg in messages:
        stamp = msg.get("date_unixtime") or msg.get("date")
        text = extract_text(msg.get("text", "")).strip()
        if stamp and text:
            texts.setdefault(str(stamp), text)
    return texts


def build_name(msg, src_file, kind):
    date = str(msg.get("date", ""))[:10] or "0000-00-00"
    stem = common.sanitize(Path(src_file).stem, limit=45) if src_file else kind
    return f"{int(msg.get('id', 0)):06d}_{date}_{stem}{Path(src_file).suffix if src_file else '.txt'}"


def run(args, rules):
    src = Path(args.src)
    result = src / "result.json"
    if not result.exists():
        sys.exit(
            f"Не нашёл {result}.\n"
            "Укажите --src на папку выгрузки Telegram Desktop "
            "(в ней лежит result.json и подпапки photos/, files/…).\n"
            "Важно: при экспорте выберите формат JSON, а не HTML."
        )

    data = json.loads(result.read_text(encoding="utf-8"))
    title = data.get("name") or "Экспорт канала"
    messages = [m for m in data.get("messages", []) if m.get("type") == "message"]
    print(f"Канал: {title}. Сообщений в выгрузке: {len(messages)}")

    out_dir = common.make_dirs(args.out, rules)
    shared = album_texts(messages)

    rows = []
    counters = {"разложено": 0, "видео пропущено": 0, "стикеры": 0,
                "нет файла": 0, "пропало": 0}

    for msg in messages:
        rel, kind = message_media(msg)
        stamp = str(msg.get("date_unixtime") or msg.get("date"))
        text = extract_text(msg.get("text", "")).strip() or shared.get(stamp, "")

        if kind == "video":
            counters["видео пропущено"] += 1
            continue
        if kind == "sticker" and not args.stickers:
            counters["стикеры"] += 1
            continue

        ext = Path(rel).suffix if rel else ""
        category, reason = common.classify(text, kind, ext, rules)
        folder = out_dir / rules[category]["folder"]

        if not rel:
            counters["нет файла"] += 1
            if not text:
                continue
            target = common.unique_path(folder / build_name(msg, "", "текст"))
            target.write_text(text, encoding="utf-8")
            rows.append(row_for(msg, category, target, out_dir, "текст", text, reason, data))
            continue

        source = src / rel
        if not source.exists():
            counters["пропало"] += 1
            continue

        target = common.unique_path(folder / build_name(msg, rel, kind))
        if args.move:
            shutil.move(str(source), str(target))
        else:
            shutil.copy2(str(source), str(target))

        if extract_text(msg.get("text", "")).strip():
            target.with_suffix(target.suffix + ".txt").write_text(text, encoding="utf-8")

        rows.append(row_for(msg, category, target, out_dir, kind, text, reason, data))
        counters["разложено"] += 1
        if counters["разложено"] % 50 == 0:
            print(f"  … {counters['разложено']} файлов")

    csv_path, html_path, md_path = common.write_reports(
        rows, out_dir, rules, title,
        stats_note=f"видео пропущено: {counters['видео пропущено']}",
    )

    print("\nГотово.")
    for name, value in counters.items():
        print(f"  {name}: {value}")
    print("\nПо папкам:")
    for key in common.CATEGORY_ORDER:
        print(f"  {rules[key]['folder']:<32} "
              f"{sum(1 for r in rows if r['category'] == key)}")
    print(f"\nВсё лежит здесь: {out_dir}")
    print(f"  каталог с превью : {html_path}")
    print(f"  таблица для Excel: {csv_path}")
    print(f"  тексты постов    : {md_path}")


def row_for(msg, category, path, out_dir, kind, text, reason, data):
    username = ""
    for key in ("public_username", "username"):
        if data.get(key):
            username = str(data[key]).lstrip("@")
            break
    link = f"https://t.me/{username}/{msg.get('id')}" if username else ""
    return {
        "id": msg.get("id"),
        "date": str(msg.get("date", "")).replace("T", " ")[:16],
        "category": category,
        "file": str(Path(path).relative_to(out_dir)),
        "kind": kind,
        "size_kb": round(Path(path).stat().st_size / 1024),
        "text": text,
        "reason": reason,
        "link": link,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Разложить выгрузку Telegram Desktop по папкам (без видео)."
    )
    parser.add_argument("--src", required=True, help="папка выгрузки с result.json")
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"куда разложить (по умолчанию {DEFAULT_OUT})")
    parser.add_argument("--rules", default=str(HERE / "categories.json"))
    parser.add_argument("--move", action="store_true", help="переносить файлы, а не копировать")
    parser.add_argument("--stickers", action="store_true", help="раскладывать ещё и стикеры")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    run(args, common.load_rules(args.rules))


if __name__ == "__main__":
    main()
