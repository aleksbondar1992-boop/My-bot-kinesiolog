# -*- coding: utf-8 -*-
"""Общие части экспорта: правила категорий, раскладка по папкам, каталог.

Используется двумя скриптами:
  export_channel.py       — качает канал через Telegram API и сразу сортирует;
  sort_desktop_export.py  — сортирует уже готовый экспорт Telegram Desktop.
"""

import csv
import html
import json
import re
from datetime import datetime
from pathlib import Path

# Порядок папок в каталоге и в отчётах.
CATEGORY_ORDER = ["certificates", "reviews", "results", "photos", "other"]

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".tif", ".tiff"}
DOC_EXT = {
    ".pdf", ".doc", ".docx", ".rtf", ".odt", ".txt", ".xls", ".xlsx",
    ".ppt", ".pptx", ".djvu", ".epub", ".fb2", ".csv", ".zip", ".rar",
}

# Типы медиа, которые считаются видео и не скачиваются.
VIDEO_KINDS = {"video", "video_note", "gif"}


# --------------------------------------------------------------------------
# Правила
# --------------------------------------------------------------------------

def load_rules(path):
    """Читает categories.json и убирает служебные ключи (начинаются с '_')."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    rules = {}
    for key, value in raw.items():
        if key.startswith("_") or not isinstance(value, dict):
            continue
        rules[key] = {
            "folder": value.get("folder", key),
            "priority": value.get("priority", 99),
            "keywords": [normalize(k) for k in value.get("keywords", [])],
            "weak_keywords": [normalize(k) for k in value.get("weak_keywords", [])],
        }
    for key in CATEGORY_ORDER:
        rules.setdefault(key, {"folder": key, "priority": 99,
                               "keywords": [], "weak_keywords": []})
    return rules


def normalize(text):
    """Нижний регистр, ё→е, пробелы схлопнуты — чтобы поиск по корням был устойчив."""
    text = (text or "").lower().replace("ё", "е")
    return re.sub(r"\s+", " ", text)


def classify(text, kind, ext, rules):
    """Возвращает (ключ категории, пояснение).

    Сначала считаем совпадения слов в тексте поста. Если ни одного —
    решаем по типу файла: документ → к документам, картинка → к обычным фото,
    остальное (аудио, голосовые, посты без файлов) → в «Прочее».
    """
    norm = normalize(text)
    ext = (ext or "").lower()

    best_key, best_score, best_hits = None, 0, []
    for key in CATEGORY_ORDER:
        rule = rules[key]
        hits, score = [], 0
        for word in rule["keywords"]:
            if word and word in norm:
                score += 2
                hits.append(word)
        for word in rule["weak_keywords"]:
            if word and word in norm:
                score += 1
                hits.append(word)
        better = score > best_score or (
            score == best_score and score > 0
            and rule["priority"] < rules[best_key]["priority"]
        )
        if score > 0 and (best_key is None or better):
            best_key, best_score, best_hits = key, score, hits

    if best_key:
        return best_key, "по словам: " + ", ".join(sorted(set(best_hits))[:5])

    if kind == "document" and ext in DOC_EXT:
        return "certificates", "по типу файла (документ)"
    if kind == "photo" or ext in IMAGE_EXT:
        return "photos", "фото без ключевых слов"
    return "other", "нет ключевых слов и не фото"


# --------------------------------------------------------------------------
# Файловая система
# --------------------------------------------------------------------------

_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize(name, limit=70):
    """Делает из строки безопасное имя файла для Windows."""
    name = _BAD_CHARS.sub("_", name or "").strip(" .")
    name = re.sub(r"_{2,}", "_", name)
    if len(name) > limit:
        name = name[:limit].rstrip(" ._")
    return name or "file"


def unique_path(path):
    """Если файл уже есть — добавляет _2, _3 … вместо перезаписи."""
    path = Path(path)
    if not path.exists():
        return path
    stem, suffix, n = path.stem, path.suffix, 2
    while True:
        candidate = path.with_name(f"{stem}_{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def make_dirs(out_dir, rules):
    """Создаёт корень экспорта и все папки категорий."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key in CATEGORY_ORDER:
        (out_dir / rules[key]["folder"]).mkdir(exist_ok=True)
    return out_dir


def short(text, limit=160):
    text = re.sub(r"\s+", " ", (text or "").strip())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


# --------------------------------------------------------------------------
# Отчёты: CSV, HTML-каталог, все тексты постов
# --------------------------------------------------------------------------

CSV_FIELDS = ["id", "дата", "категория", "папка", "файл", "тип",
              "размер_кб", "почему", "ссылка", "текст"]


def write_csv(rows, out_dir, rules):
    """Таблица всего экспорта — открывается в Excel, годится для ручной пересортировки."""
    path = Path(out_dir) / "КАТАЛОГ.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "id": row.get("id", ""),
                "дата": row.get("date", ""),
                "категория": row.get("category", ""),
                "папка": rules[row.get("category", "other")]["folder"],
                "файл": row.get("file", ""),
                "тип": row.get("kind", ""),
                "размер_кб": row.get("size_kb", ""),
                "почему": row.get("reason", ""),
                "ссылка": row.get("link", ""),
                "текст": short(row.get("text", ""), 500),
            })
    return path


def write_posts_md(rows, out_dir, title):
    """Все тексты постов одним файлом — чтобы не потерять подписи к фото."""
    path = Path(out_dir) / "ВСЕ_ТЕКСТЫ_ПОСТОВ.md"
    by_msg = {}
    for row in rows:
        by_msg.setdefault(row.get("id"), []).append(row)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# Тексты постов: {title}\n\n")
        for msg_id in sorted(by_msg, key=lambda v: (v is None, v)):
            group = by_msg[msg_id]
            first = group[0]
            if not (first.get("text") or "").strip():
                continue
            fh.write(f"## {first.get('date', '')} · пост {msg_id}\n\n")
            if first.get("link"):
                fh.write(f"{first['link']}\n\n")
            fh.write(first["text"].strip() + "\n\n")
            files = [r["file"] for r in group if r.get("file")]
            if files:
                fh.write("Файлы: " + ", ".join(f"`{f}`" for f in files) + "\n\n")
            fh.write("---\n\n")
    return path


_HTML_HEAD = """<meta charset="utf-8">
<title>{title}</title>
<style>
 :root{{color-scheme:light dark}}
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:24px;
      background:#faf9f7;color:#1c1b19}}
 h1{{font-size:22px;margin:0 0 4px}}
 .sub{{color:#6b6862;font-size:14px;margin-bottom:18px}}
 nav a{{display:inline-block;margin:0 10px 10px 0;padding:7px 13px;border-radius:8px;
        background:#fff;border:1px solid #e2ded7;text-decoration:none;color:#1c1b19;font-size:14px}}
 nav a:hover{{background:#f0ece5}}
 #q{{width:100%;max-width:520px;padding:10px 12px;font-size:15px;border-radius:8px;
     border:1px solid #e2ded7;margin:6px 0 22px;background:#fff;color:inherit}}
 h2{{font-size:18px;margin:28px 0 12px;padding-top:10px;border-top:1px solid #e6e2db}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:14px}}
 .card{{background:#fff;border:1px solid #e6e2db;border-radius:10px;overflow:hidden;
        display:flex;flex-direction:column}}
 .card img{{width:100%;height:190px;object-fit:cover;display:block;background:#f0ece5}}
 .doc{{padding:26px 12px;font-size:32px;text-align:center;background:#f4f1ea}}
 .meta{{padding:9px 11px;font-size:12.5px;line-height:1.45;color:#4a4741;flex:1}}
 .meta b{{display:block;font-size:11px;color:#8a867e;font-weight:600;margin-bottom:3px}}
 .meta a{{color:#1c1b19}}
 .empty{{color:#8a867e;font-size:14px}}
 @media (prefers-color-scheme:dark){{
   body{{background:#17161a;color:#eceae6}} nav a,.card,#q{{background:#211f25;border-color:#33303a;color:#eceae6}}
   nav a:hover{{background:#2b2833}} .doc{{background:#2b2833}} .meta{{color:#c3bfb8}} .meta a{{color:#eceae6}}
   h2{{border-color:#33303a}}
 }}
</style>
"""


def write_html(rows, out_dir, rules, title, stats_note=""):
    """Каталог с превью — открывается двойным кликом, работает без интернета."""
    path = Path(out_dir) / "КАТАЛОГ.html"
    by_cat = {key: [] for key in CATEGORY_ORDER}
    for row in rows:
        by_cat.setdefault(row.get("category", "other"), []).append(row)

    total_files = sum(1 for r in rows if r.get("file"))
    parts = [_HTML_HEAD.format(title=html.escape(title))]
    parts.append(f"<h1>{html.escape(title)}</h1>")
    parts.append(
        f'<div class="sub">Файлов: {total_files} · '
        f'постов: {len({r.get("id") for r in rows})} · '
        f'собрано {datetime.now().strftime("%d.%m.%Y %H:%M")}'
        + (f" · {html.escape(stats_note)}" if stats_note else "")
        + "</div>"
    )
    parts.append("<nav>")
    for key in CATEGORY_ORDER:
        folder = rules[key]["folder"]
        parts.append(f'<a href="#{key}">{html.escape(folder)} ({len(by_cat.get(key, []))})</a>')
    parts.append("</nav>")
    parts.append('<input id="q" placeholder="Поиск по тексту постов и именам файлов…">')

    for key in CATEGORY_ORDER:
        folder = rules[key]["folder"]
        items = by_cat.get(key, [])
        parts.append(f'<h2 id="{key}">{html.escape(folder)} — {len(items)}</h2>')
        if not items:
            parts.append('<div class="empty">Пусто.</div>')
            continue
        parts.append('<div class="grid">')
        for row in items:
            rel = (row.get("file") or "").replace("\\", "/")
            text = html.escape(short(row.get("text", ""), 220))
            src = html.escape(rel)
            ext = Path(rel).suffix.lower()
            if rel and ext in IMAGE_EXT:
                media = f'<a href="{src}"><img loading="lazy" src="{src}" alt=""></a>'
            elif rel:
                media = f'<a href="{src}"><div class="doc">📄</div></a>'
            else:
                media = '<div class="doc">📝</div>'
            name = html.escape(Path(rel).name) if rel else "пост без файла"
            link = row.get("link") or ""
            link_html = f' · <a href="{html.escape(link)}">в Telegram</a>' if link else ""
            parts.append(
                f'<div class="card" data-s="{html.escape(normalize(row.get("text", "") + " " + rel))}">'
                f"{media}"
                f'<div class="meta"><b>{html.escape(row.get("date", ""))} · {name}</b>'
                f"{text}{link_html}</div></div>"
            )
        parts.append("</div>")

    parts.append("""
<script>
 const q=document.getElementById('q');
 q.addEventListener('input',()=>{
   const v=q.value.toLowerCase().replace(/ё/g,'е').trim();
   document.querySelectorAll('.card').forEach(c=>{
     c.style.display = !v || c.dataset.s.includes(v) ? '' : 'none';
   });
 });
</script>""")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))
    return path


def write_reports(rows, out_dir, rules, title, stats_note=""):
    """Собирает все три отчёта разом."""
    rows = sorted(rows, key=lambda r: (r.get("date") or "", r.get("id") or 0))
    return (
        write_csv(rows, out_dir, rules),
        write_html(rows, out_dir, rules, title, stats_note),
        write_posts_md(rows, out_dir, title),
    )
