#!/usr/bin/env python3
"""Сборка PDF «Питание БГБКБС · Веган».

Исходник — pitanie-bgbkbs-vegan.html, где номера страниц записаны токенами
{{pN}} и {{TOTAL}}. Скрипт проставляет реальные номера по порядку секций,
убирает служебный скрипт замера и рендерит PDF через headless Chromium.

    python3 docs/build.py
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pitanie-bgbkbs-vegan.html")
BUILD = os.path.join(HERE, "build", "index.html")
PDF = os.path.join(HERE, "Pitanie_BGBKBS_VEGAN.pdf")

CHROME_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    shutil.which("chromium"),
    shutil.which("chromium-browser"),
    shutil.which("google-chrome"),
]


def render_html(src=SRC, out=BUILD):
    s = open(src, encoding="utf-8").read()
    ids = re.findall(r'<section class="page" id="([^"]+)">', s)
    num = {sid: i + 1 for i, sid in enumerate(ids)}
    num["TOTAL"] = len(ids)

    unresolved = set(re.findall(r"\{\{([^}]+)\}\}", s)) - set(num)
    if unresolved:
        sys.exit("Неизвестные токены: %s" % sorted(unresolved))

    n, n10, n100 = len(ids), len(ids) % 10, len(ids) % 100
    if 11 <= n100 <= 14 or n10 == 0 or n10 >= 5:
        plural = "страниц"
    elif n10 == 1:
        plural = "страница"
    else:
        plural = "страницы"
    s = s.replace("{{TOTAL}} страниц", "{{TOTAL}} " + plural)

    s = re.sub(r"\{\{([^}]+)\}\}", lambda m: str(num[m.group(1)]), s)
    s = re.sub(r'<script id="measure">.*?</script>\s*', "", s, flags=re.S)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(s)
    return len(ids)


def render_pdf(html=BUILD, pdf=PDF):
    chrome = next((c for c in CHROME_CANDIDATES if c and os.path.exists(c)), None)
    if not chrome:
        sys.exit("Chromium не найден — PDF не собран, HTML готов: " + html)
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=9000",
         "--print-to-pdf=" + pdf, "file://" + html],
        check=True, capture_output=True,
    )


if __name__ == "__main__":
    pages = render_html()
    render_pdf()
    print("Готово: %d страниц → %s" % (pages, PDF))
