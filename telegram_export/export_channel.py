# -*- coding: utf-8 -*-
"""Экспорт публичного Telegram-канала на диск: всё, кроме видео.

Что делает:
  1. заходит в Telegram под вашим аккаунтом (нужен один раз код из Telegram);
  2. проходит канал от первого поста до последнего;
  3. качает фото, документы, аудио и голосовые — видео, кружки и GIF пропускает;
  4. раскладывает файлы по папкам: сертификаты, отзывы, результаты, обычные фото;
  5. собирает КАТАЛОГ.html, КАТАЛОГ.csv и ВСЕ_ТЕКСТЫ_ПОСТОВ.md.

Запуск можно прерывать (Ctrl+C) и повторять — уже скачанное не качается заново.

  python export_channel.py --channel @my_channel --out D:\\Экспорт
  python export_channel.py --dry-run          # только посмотреть раскладку
  python export_channel.py --resort           # пересортировать без перекачки
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import common

try:
    from telethon import TelegramClient
    from telethon.errors import FloodWaitError
except ImportError:  # для --resort Telethon не нужен, поэтому не падаем сразу
    TelegramClient = None

    class FloodWaitError(Exception):
        seconds = 30

HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.local.json"
SESSION_PATH = HERE / "tg_export_session"
DEFAULT_OUT = r"D:\Экспорт_канала" if os.name == "nt" else str(Path.home() / "tg_export")

# Что скачиваем. Видео, кружки и GIF (это тоже видео) — мимо.
SKIP_KINDS = set(common.VIDEO_KINDS)


# --------------------------------------------------------------------------
# Доступы
# --------------------------------------------------------------------------

def load_config():
    """api_id / api_hash: из переменных окружения, из файла или спросим один раз."""
    config = {}
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    api_id = os.environ.get("TG_API_ID") or config.get("api_id")
    api_hash = os.environ.get("TG_API_HASH") or config.get("api_hash")

    if not api_id or not api_hash:
        print("\nНужны api_id и api_hash — они бесплатные и берутся один раз:")
        print("  1. откройте https://my.telegram.org  →  API development tools")
        print("  2. войдите по номеру телефона, создайте приложение (любое название)")
        print("  3. скопируйте оттуда App api_id и App api_hash\n")
        api_id = input("api_id: ").strip()
        api_hash = input("api_hash: ").strip()

    try:
        api_id = int(api_id)
    except ValueError:
        sys.exit("api_id должен быть числом.")

    config.update({"api_id": api_id, "api_hash": api_hash})
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return config


def save_config(config):
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# --------------------------------------------------------------------------
# Состояние (чтобы можно было продолжить с места остановки)
# --------------------------------------------------------------------------

def state_path(out_dir):
    return Path(out_dir) / "_состояние_экспорта.json"


def load_state(out_dir):
    path = state_path(out_dir)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("! Файл состояния повреждён, начинаю с нуля.")
    return {"rows": [], "seen": [], "title": "", "channel": ""}


def save_state(out_dir, state):
    tmp = state_path(out_dir).with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(state_path(out_dir))


# --------------------------------------------------------------------------
# Разбор сообщений
# --------------------------------------------------------------------------

def media_kind(msg):
    """Что за вложение в посте. Порядок проверок важен: GIF — тоже видео."""
    if msg.video_note:
        return "video_note"
    if msg.gif:
        return "gif"
    if msg.video:
        return "video"
    if msg.sticker:
        return "sticker"
    if msg.photo:
        return "photo"
    if msg.voice:
        return "voice"
    if msg.audio:
        return "audio"
    if msg.document:
        return "document"
    return "none"


def build_group_texts(messages):
    """У альбома подпись есть только у одного поста — раздаём её всей группе."""
    texts = {}
    for msg in messages:
        gid = getattr(msg, "grouped_id", None)
        if gid and (msg.message or "").strip():
            texts.setdefault(gid, msg.message)
    return texts


def message_text(msg, group_texts):
    if (msg.message or "").strip():
        return msg.message
    gid = getattr(msg, "grouped_id", None)
    return group_texts.get(gid, "") if gid else ""


def build_filename(msg, kind, ext):
    """000123_2024-05-03_исходное-имя.jpg — сортируется по порядку постов."""
    date = msg.date.astimezone().strftime("%Y-%m-%d")
    original = ""
    if getattr(msg, "file", None) and msg.file.name:
        original = common.sanitize(Path(msg.file.name).stem, limit=45)
    base = f"{msg.id:06d}_{date}"
    if original:
        base += f"_{original}"
    else:
        base += f"_{kind}"
    return base + (ext or "")


def post_link(username, msg_id):
    return f"https://t.me/{username}/{msg_id}" if username else ""


# --------------------------------------------------------------------------
# Основной проход
# --------------------------------------------------------------------------

async def run(args, rules):
    if TelegramClient is None:
        sys.exit(
            "Не установлена библиотека Telethon.\n"
            "Установите её командой:  pip install -r requirements.txt\n"
            "(или просто запустите 1_СКАЧАТЬ_КАНАЛ.bat — он сделает это сам)"
        )
    config = load_config()
    out_dir = common.make_dirs(args.out, rules)

    if os.name == "nt" and not Path(args.out).drive.startswith(("D", "d")):
        print(f"! Внимание: путь {args.out} не на диске D.")

    client = TelegramClient(str(SESSION_PATH), config["api_id"], config["api_hash"])
    print("\nПодключаюсь к Telegram…")
    await client.start()

    channel = args.channel or config.get("channel")
    if not channel:
        channel = input("Ссылка или @имя вашего канала: ").strip()
    channel = channel.strip().rstrip("/")
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if channel.startswith(prefix):
            channel = "@" + channel[len(prefix):]
    config["channel"] = channel
    save_config(config)

    entity = await client.get_entity(channel)
    title = getattr(entity, "title", channel)
    username = getattr(entity, "username", None)
    print(f"Канал: {title} ({channel})")

    state = load_state(out_dir)
    state["title"], state["channel"] = title, channel
    seen = set(state["seen"])
    rows = state["rows"]
    if seen:
        print(f"Продолжаю: {len(seen)} постов уже обработано ранее.")

    print("Читаю список постов…")
    messages = []
    async for msg in client.iter_messages(entity, reverse=True, limit=args.limit):
        messages.append(msg)
    group_texts = build_group_texts(messages)
    print(f"Всего постов в канале: {len(messages)}")

    counters = {"скачано": 0, "видео пропущено": 0, "уже было": 0,
                "без файла": 0, "ошибок": 0, "стикеры": 0}
    plan = []
    for msg in messages:
        kind = media_kind(msg)
        text = message_text(msg, group_texts)
        ext = (msg.file.ext if getattr(msg, "file", None) else "") or ""
        category, reason = common.classify(text, kind, ext, rules)
        plan.append((msg, kind, text, ext, category, reason))

    if args.dry_run:
        print("\nПРОБНЫЙ ЗАПУСК — ничего не скачивается.\n")
        preview = {key: 0 for key in common.CATEGORY_ORDER}
        for msg, kind, text, ext, category, reason in plan:
            if kind in SKIP_KINDS:
                counters["видео пропущено"] += 1
                continue
            if kind == "none":
                counters["без файла"] += 1
                if not (text or "").strip():
                    continue  # пустой служебный пост — ничего не сохраняем
            preview[category] += 1
        for key in common.CATEGORY_ORDER:
            print(f"  {rules[key]['folder']:<32} {preview[key]}")
        print(f"\n  видео будет пропущено: {counters['видео пропущено']}")
        print("\nПримеры раскладки:")
        for msg, kind, text, ext, category, reason in plan[:400]:
            if kind in SKIP_KINDS or kind == "none":
                continue
            print(f"  [{rules[category]['folder']}] {msg.id} · {reason} · "
                  f"{common.short(text, 60)}")
        await client.disconnect()
        return

    skip = set(SKIP_KINDS) | {"none"} | (set() if args.stickers else {"sticker"})
    total = sum(1 for _, kind, *_ in plan if kind not in skip)
    print(f"К скачиванию (без видео): {total} файлов\n")
    done = 0

    try:
        for msg, kind, text, ext, category, reason in plan:
            link = post_link(username, msg.id)

            if kind in SKIP_KINDS:
                counters["видео пропущено"] += 1
                seen.add(msg.id)
                continue
            if kind == "sticker" and not args.stickers:
                counters["стикеры"] += 1
                seen.add(msg.id)
                continue

            if kind == "none":
                # Пост без файла: сохраняем текст, если он есть.
                if msg.id not in seen and (text or "").strip():
                    folder = out_dir / rules[category]["folder"]
                    path = common.unique_path(
                        folder / (build_filename(msg, "текст", ".txt"))
                    )
                    path.write_text(text, encoding="utf-8")
                    rows.append(make_row(msg, category, path, out_dir, "текст",
                                         text, reason, link))
                counters["без файла"] += 1
                seen.add(msg.id)
                continue

            if msg.id in seen:
                counters["уже было"] += 1
                done += 1
                continue

            folder = out_dir / rules[category]["folder"]
            target = common.unique_path(folder / build_filename(msg, kind, ext))

            try:
                await download_with_retry(client, msg, target, args.retries)
            except Exception as exc:  # noqa: BLE001 — один плохой файл не должен рушить выгрузку
                counters["ошибок"] += 1
                log_error(out_dir, msg.id, exc)
                print(f"  ! пост {msg.id}: {exc}")
                # В seen не добавляем: следующий запуск попробует этот файл снова.
                continue

            # Подпись рядом с файлом — чтобы контекст не потерялся.
            if (msg.message or "").strip():
                target.with_suffix(target.suffix + ".txt").write_text(
                    msg.message, encoding="utf-8"
                )

            rows.append(make_row(msg, category, target, out_dir, kind,
                                 text, reason, link))
            counters["скачано"] += 1
            done += 1
            seen.add(msg.id)

            print(f"  [{done}/{total}] {rules[category]['folder']} ← {target.name}")

            if counters["скачано"] % 25 == 0:
                state["rows"], state["seen"] = rows, sorted(seen)
                save_state(out_dir, state)

    except KeyboardInterrupt:
        print("\nОстановлено вручную. Прогресс сохранён — запустите скрипт снова, "
              "чтобы продолжить с этого места.")
    finally:
        state["rows"], state["seen"] = rows, sorted(seen)
        save_state(out_dir, state)
        await client.disconnect()

    finish(rows, out_dir, rules, title, counters)


async def download_with_retry(client, msg, target, retries):
    """Сеть у Telegram капризная: повторяем и уважаем FloodWait."""
    for attempt in range(1, retries + 1):
        try:
            await client.download_media(msg, file=str(target))
            return
        except FloodWaitError as exc:
            wait = int(getattr(exc, "seconds", 30)) + 2
            print(f"  … Telegram просит подождать {wait} c")
            time.sleep(wait)
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)


def make_row(msg, category, path, out_dir, kind, text, reason, link):
    rel = str(Path(path).relative_to(out_dir))
    size_kb = round(Path(path).stat().st_size / 1024) if Path(path).exists() else 0
    return {
        "id": msg.id,
        "date": msg.date.astimezone().strftime("%Y-%m-%d %H:%M"),
        "category": category,
        "file": rel,
        "kind": kind,
        "size_kb": size_kb,
        "text": text or "",
        "reason": reason,
        "link": link,
    }


def log_error(out_dir, msg_id, exc):
    with open(Path(out_dir) / "ошибки.log", "a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M')} пост {msg_id}: {exc}\n")


def finish(rows, out_dir, rules, title, counters):
    csv_path, html_path, md_path = common.write_reports(
        rows, out_dir, rules, title,
        stats_note=f"видео пропущено: {counters.get('видео пропущено', 0)}",
    )
    print("\nГотово.")
    for name, value in counters.items():
        print(f"  {name}: {value}")
    print("\nПо папкам:")
    for key in common.CATEGORY_ORDER:
        count = sum(1 for r in rows if r["category"] == key)
        print(f"  {rules[key]['folder']:<32} {count}")
    print(f"\nВсё лежит здесь: {out_dir}")
    print(f"  каталог с превью : {html_path}")
    print(f"  таблица для Excel: {csv_path}")
    print(f"  тексты постов    : {md_path}")


# --------------------------------------------------------------------------
# Пересортировка без перекачки
# --------------------------------------------------------------------------

def resort(out_dir, rules):
    """Поправили categories.json — перекладываем уже скачанное по новым правилам."""
    out_dir = common.make_dirs(out_dir, rules)
    state = load_state(out_dir)
    rows = state.get("rows", [])
    if not rows:
        sys.exit("Нечего пересортировывать: сначала запустите экспорт.")

    moved = 0
    for row in rows:
        old_rel = row.get("file") or ""
        old_path = out_dir / old_rel
        ext = Path(old_rel).suffix
        new_key, reason = common.classify(row.get("text", ""), row.get("kind", ""),
                                          ext, rules)
        if not old_path.exists():
            # Файл унесли руками — не трогаем запись, просто обновляем пояснение.
            row["reason"] = reason
            continue
        if new_key == row["category"]:
            row["reason"] = reason
            continue
        new_path = common.unique_path(
            out_dir / rules[new_key]["folder"] / Path(old_rel).name
        )
        if old_path.exists():
            old_path.replace(new_path)
            sidecar = old_path.with_suffix(old_path.suffix + ".txt")
            if sidecar.exists():
                sidecar.replace(new_path.with_suffix(new_path.suffix + ".txt"))
            moved += 1
        row["category"] = new_key
        row["reason"] = reason
        row["file"] = str(new_path.relative_to(out_dir))

    state["rows"] = rows
    save_state(out_dir, state)
    common.write_reports(rows, out_dir, rules, state.get("title", "Экспорт канала"))
    print(f"Перемещено файлов: {moved}")
    for key in common.CATEGORY_ORDER:
        count = sum(1 for r in rows if r["category"] == key)
        print(f"  {rules[key]['folder']:<32} {count}")


# --------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Экспорт Telegram-канала (всё, кроме видео) с раскладкой по папкам."
    )
    parser.add_argument("--channel", help="@имя канала или ссылка t.me/…")
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"куда сохранять (по умолчанию {DEFAULT_OUT})")
    parser.add_argument("--rules", default=str(HERE / "categories.json"),
                        help="файл с правилами раскладки")
    parser.add_argument("--limit", type=int, default=None, help="взять только N последних постов")
    parser.add_argument("--retries", type=int, default=4, help="попыток на файл при сбое сети")
    parser.add_argument("--dry-run", action="store_true", help="показать раскладку, ничего не качая")
    parser.add_argument("--resort", action="store_true", help="пересортировать уже скачанное")
    parser.add_argument("--stickers", action="store_true", help="качать ещё и стикеры")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    rules = common.load_rules(args.rules)
    if args.resort:
        resort(args.out, rules)
        return
    asyncio.run(run(args, rules))


if __name__ == "__main__":
    main()
