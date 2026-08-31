# -*- coding: utf-8 -*-
"""
Генератор схем "Параллельные линии тела" (вид со спины).

Строит три SVG-рисунка:
  1. Базовая последовательность линий.
  2. Тот же набор линий с другой последовательностью работы.
  3. Протокол мобилизации шеи (+ линия грудины Th2-Th3).

Фигура рисуется линиями (контуры + анатомические ориентиры),
поверх неё накладываются горизонтальные параллельные линии.
"""

import os

W, H = 1000, 1460
CX = 400                      # средняя линия тела
LINE_X0, LINE_X1 = 112, 692   # горизонтальная протяжённость линий
BADGE_X = 72                  # центр номерного кружка
LABEL_X = 708                 # левый край подписи

# ---------------------------------------------------------------- палитра
PAPER   = "#FFFFFF"
INK     = "#33454F"           # контур тела
INK_SOFT= "#8AA0AC"           # анатомические детали
GRID    = "#DCE4E8"

C_KEY   = "#D92B3A"           # жирные (опорные) линии
C_SEC   = "#1E7FC2"           # тонкие (вспомогательные) линии
C_WORK  = "#0E7C86"           # рабочие линии (протокол)
C_TARGET= "#7A3FF2"           # линия-цель

TXT     = "#22323B"
TXT_DIM = "#7A8A94"

FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"

# ------------------------------------------------- уровни (координата Y)
Y = {
    "eyes":      190,
    "jaw":       250,
    "neck":      300,
    "aperture":  352,
    "sternum":   424,
    "diaphragm": 600,
    "pelvis":    780,
    "knees":    1058,
    "feet":     1330,
}

# ключ -> (подпись [строки], анатомический ориентир, короткое имя)
META = {
    "eyes":      (["Линия глаз"],                          "уровень зрачков / верх ушных раковин", "глаза"),
    "jaw":       (["Линия челюсти"],                       "угол нижней челюсти",                  "челюсть"),
    "neck":      (["Линия шеи"],                           "средний шейный отдел, C3–C4",          "шея"),
    "aperture":  (["Линия апертуры", "грудной клетки"],    "верхняя апертура: Th1–Th2, I ребро",   "апертура"),
    "sternum":   (["Линия грудины", "(уровень Th2–Th3)"],  "верхнегрудной отдел, Th2–Th3"  ,"грудина Th3"),
    "diaphragm": (["Линия грудобрюшной", "диафрагмы"],     "Th12–L1, рёберная дуга",               "диафрагма"),
    "pelvis":    (["Линия тазобедренных", "суставов"],     "большие вертелы бедренных костей",     "таз"),
    "knees":     (["Линия колен"],                         "щели коленных суставов"      , "колени"),
    "feet":      (["Линия стоп"],                          "опора: подошвы, пяточные бугры",       "стопы"),
}



# ------------------------------------------------- метрики шрифта
_FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_ADV, _UPM = {}, 2048
try:
    from fontTools.ttLib import TTFont as _TTF
    _f = _TTF(_FONT_FILE, fontNumber=0)
    _UPM = _f["head"].unitsPerEm
    _cmap, _hmtx = _f.getBestCmap(), _f["hmtx"]
    for _cp, _gn in _cmap.items():
        _ADV[_cp] = _hmtx[_gn][0]
    _f.close()
except Exception:
    pass


def text_w(s, size, bold=False):
    """Ширина строки в пикселях (DejaVu Sans; жирное начертание чуть шире)."""
    if not _ADV:
        return len(s) * size * 0.58
    total = sum(_ADV.get(ord(ch), _ADV.get(32, _UPM // 2)) for ch in s)
    w = total * size / _UPM
    return w * 1.06 if bold else w


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ==========================================================  ФИГУРА
def figure():
    """Контурный рисунок человека со спины."""
    p = []
    a = p.append

    # --- силуэт: трапеция -> корпус -> таз -> ноги -> стопы (один контур)
    body = (
        "M 352 320 "
        "C 316 328, 286 344, 268 376 "          # левая трапеция -> акромион
        "C 280 420, 292 446, 296 470 "          # боковая стенка груди
        "C 300 530, 306 568, 308 610 "          # талия
        "C 310 660, 292 702, 288 748 "          # гребень подвздошной кости
        "C 284 812, 290 880, 296 940 "          # наружное бедро
        "C 300 998, 302 1030, 304 1062 "        # колено снаружи
        "C 302 1104, 296 1134, 300 1166 "       # икра
        "C 306 1210, 316 1250, 322 1288 "       # голень -> лодыжка
        "C 316 1308, 316 1324, 322 1330 "       # пятка
        "L 368 1330 "
        "C 374 1324, 374 1308, 370 1288 "
        "C 372 1246, 380 1200, 384 1160 "       # внутренняя икра
        "C 387 1126, 386 1096, 386 1062 "       # колено изнутри
        "C 388 1000, 393 944, 398 892 "         # внутреннее бедро
        "L 400 878 "                            # промежность
        "L 402 892 "
        "C 407 944, 412 1000, 414 1062 "
        "C 414 1096, 413 1126, 416 1160 "
        "C 420 1200, 428 1246, 430 1288 "
        "C 426 1308, 426 1324, 432 1330 "
        "L 478 1330 "
        "C 484 1324, 484 1308, 478 1288 "
        "C 484 1250, 494 1210, 500 1166 "
        "C 504 1134, 498 1104, 496 1062 "
        "C 498 1030, 500 998, 504 940 "
        "C 510 880, 516 812, 512 748 "
        "C 508 702, 490 660, 492 610 "
        "C 494 568, 500 530, 504 470 "
        "C 508 446, 520 420, 532 376 "
        "C 514 344, 484 328, 448 320 Z"
    )
    a(f'<path d="{body}" fill="#F3F7F9" stroke="{INK}" stroke-width="2.6" '
      f'stroke-linejoin="round"/>')

    # --- руки (поверх корпуса)
    arm_l = (
        "M 274 356 "
        "C 248 378, 238 418, 236 462 "
        "C 232 520, 228 566, 226 610 "
        "C 224 652, 226 682, 230 706 "
        "C 232 744, 234 776, 236 804 "
        "C 234 834, 238 858, 242 878 "
        "C 250 902, 268 906, 278 890 "
        "C 284 868, 286 844, 286 818 "
        "C 288 788, 290 758, 290 718 "
        "C 292 684, 294 654, 294 618 "
        "C 296 566, 300 512, 304 470 "
        "C 306 442, 304 416, 298 396 Z"
    )
    arm_r = mirror_path(arm_l)
    for d in (arm_l, arm_r):
        a(f'<path d="{d}" fill="#F3F7F9" stroke="{INK}" stroke-width="2.6" '
          f'stroke-linejoin="round"/>')

    # --- шея
    neck = ("M 366 236 C 364 272, 360 296, 350 322 "
            "C 380 332, 420 332, 450 322 "
            "C 440 296, 436 272, 434 236 Z")
    a(f'<path d="{neck}" fill="#F3F7F9" stroke="{INK}" stroke-width="2.6"/>')

    # --- голова (затылок) + уши
    a(f'<ellipse cx="400" cy="185" rx="62" ry="78" fill="#F3F7F9" '
      f'stroke="{INK}" stroke-width="2.6"/>')
    for x, sw in ((338, 1), (462, -1)):
        a(f'<path d="M {x} 180 C {x-9*sw} 184, {x-10*sw} 202, {x-2*sw} 212" '
          f'fill="none" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')

    # ---------- анатомические ориентиры (тонкая графика) ----------
    g = [f'<g fill="none" stroke="{INK_SOFT}" stroke-width="1.8" '
         f'stroke-linecap="round" stroke-linejoin="round">']

    # линия роста волос / затылок
    g.append('<path d="M 340 208 C 356 236, 374 248, 400 254 C 426 248, 444 236, 460 208"/>')

    # позвоночник
    g.append('<path d="M 400 330 C 396 420, 404 520, 400 600 '
             'C 396 682, 404 742, 400 800" stroke-width="2"/>')
    # остистые отростки
    for yy in range(346, 800, 26):
        g.append(f'<path d="M 392 {yy} H 408" stroke-width="1.2" opacity="0.8"/>')
    # C7
    g.append(f'</g><circle cx="400" cy="332" r="5.5" fill="none" '
             f'stroke="{INK_SOFT}" stroke-width="2.2"/>'
             f'<g fill="none" stroke="{INK_SOFT}" stroke-width="1.8" '
             f'stroke-linecap="round" stroke-linejoin="round">')

    # лопатки
    scap_l = ("M 378 392 C 356 382, 332 380, 316 388 "
              "C 328 422, 346 454, 368 474 "
              "C 375 444, 378 414, 378 392 Z")
    g.append(f'<path d="{scap_l}"/>')
    g.append(f'<path d="{mirror_path(scap_l)}"/>')

    # рёберная дуга (уровень диафрагмы)
    g.append('<path d="M 320 552 C 348 588, 374 604, 398 610"/>')
    g.append('<path d="M 480 552 C 452 588, 426 604, 402 610"/>')

    # таз: крестец + ягодичные складки
    g.append('<path d="M 372 726 L 400 800 L 428 726"/>')
    g.append('<path d="M 400 800 L 400 872"/>')
    g.append('<path d="M 312 856 C 340 878, 372 882, 396 874"/>')
    g.append('<path d="M 488 856 C 460 878, 428 882, 404 874"/>')

    # подколенные ямки
    g.append('<path d="M 314 1050 C 334 1062, 358 1062, 380 1050"/>')
    g.append('<path d="M 486 1050 C 466 1062, 442 1062, 420 1050"/>')

    # ахилловы сухожилия
    g.append('<path d="M 336 1246 C 338 1276, 340 1298, 342 1312"/>')
    g.append('<path d="M 464 1246 C 462 1276, 460 1298, 458 1312"/>')

    g.append("</g>")
    p.extend(g)
    return "\n".join(p)


def mirror_path(d):
    """Отражение пути относительно вертикали x = CX."""
    out, num, i = [], "", 0
    tokens = []
    for ch in d:
        if ch.isdigit() or ch == "." or (ch == "-" and not num):
            num += ch
        else:
            if num:
                tokens.append(("n", num)); num = ""
            if not ch.isspace():
                tokens.append(("c", ch))
            else:
                tokens.append(("s", " "))
    if num:
        tokens.append(("n", num))

    coord = 0  # 0 = x, 1 = y
    for kind, val in tokens:
        if kind == "n":
            v = float(val)
            if coord == 0:
                v = 2 * CX - v
            out.append(f"{v:g}")
            coord = 1 - coord
        elif kind == "c":
            if val.upper() in "MCLQTSAHVZ":
                coord = 0
            out.append(val)
        else:
            out.append(" ")
    return "".join(out)


# ==========================================================  ЭЛЕМЕНТЫ
# точки-ориентиры: где линия пересекает костный ориентир на теле
MARKS = {
    "eyes":      [338, 462],
    "jaw":       [352, 448],
    "neck":      [362, 438],
    "aperture":  [286, 514],
    "sternum":   [356, 400, 444],
    "diaphragm": [350, 450],
    "pelvis":    [290, 510],
    "knees":     [332, 468],
    "feet":      [345, 455],
}

TITLE_LH = 22      # межстрочный интервал заголовка подписи
HINT_H   = 18      # высота строки-подсказки
NOTE_LH  = 18      # межстрочный интервал пояснения
BLOCK_GAP = 14     # минимальный зазор между блоками подписей


def block_height(key, note_lines):
    h = len(META[key][0]) * TITLE_LH + HINT_H
    if note_lines:
        h += 10 + len(note_lines) * NOTE_LH + 6
    return h


def layout(specs):
    """Развести подписи по вертикали так, чтобы они не наезжали друг на друга."""
    n = len(specs)
    c = [Y[s["key"]] for s in specs]
    h = [block_height(s["key"], s.get("note")) for s in specs]
    top_limit, bot_limit = 126, H - 118

    for i in range(1, n):                                   # вниз
        need = c[i - 1] + h[i - 1] / 2 + BLOCK_GAP + h[i] / 2
        if c[i] < need:
            c[i] = need
    if c[0] - h[0] / 2 < top_limit:
        c[0] = top_limit + h[0] / 2
    for i in range(n - 1, -1, -1):                          # вверх
        if c[i] + h[i] / 2 > bot_limit:
            c[i] = bot_limit - h[i] / 2
        if i > 0:
            room = c[i] - h[i] / 2 - BLOCK_GAP - h[i - 1] / 2
            if c[i - 1] > room:
                c[i - 1] = room
    return c, h


def ref_line(spec, cy, bh):
    """Горизонтальная параллельная линия + номер + подпись (центр подписи = cy)."""
    key, num, color = spec["key"], spec["num"], spec["color"]
    weight = spec["weight"]
    y = Y[key]
    label, hint, _ = META[key]
    s = []

    if spec.get("halo"):
        s.append(f'<line x1="{LINE_X0}" y1="{y}" x2="{LINE_X1}" y2="{y}" '
                 f'stroke="{color}" stroke-width="{weight + 14}" opacity="0.16" '
                 f'stroke-linecap="round"/>')

    dash = ' stroke-dasharray="11 7"' if spec.get("dashed") else ""
    s.append(f'<line x1="{LINE_X0}" y1="{y}" x2="{LINE_X1}" y2="{y}" '
             f'stroke="{color}" stroke-width="{weight}" stroke-linecap="round"{dash}/>')

    # точки-ориентиры на теле
    for mx in MARKS.get(key, []):
        s.append(f'<circle cx="{mx}" cy="{y}" r="5.6" fill="{PAPER}" '
                 f'stroke="{color}" stroke-width="2.6"/>')

    # выноска от конца линии к подписи
    s.append(f'<path d="M {LINE_X1} {y} H {LABEL_X - 26} L {LABEL_X - 8} {cy}" '
             f'fill="none" stroke="{color}" stroke-width="1.5" opacity="0.55"/>')

    # номер линии
    s.append(f'<circle cx="{BADGE_X}" cy="{y}" r="21" fill="{color}"/>')
    s.append(f'<text x="{BADGE_X}" y="{y}" fill="#fff" font-family="{FONT}" '
             f'font-size="21" font-weight="bold" text-anchor="middle" '
             f'dominant-baseline="central">{num}</text>')

    # подпись
    top = cy - bh / 2
    for i, ln in enumerate(label):
        s.append(f'<text x="{LABEL_X}" y="{top + 11 + i * TITLE_LH}" fill="{TXT}" '
                 f'font-family="{FONT}" font-size="18" font-weight="bold" '
                 f'dominant-baseline="central">{esc(ln)}</text>')
    hy = top + len(label) * TITLE_LH + 9
    s.append(f'<text x="{LABEL_X}" y="{hy}" fill="{TXT_DIM}" font-family="{FONT}" '
             f'font-size="12.5" dominant-baseline="central">{esc(hint)}</text>')

    # пояснение-задание
    nt = spec.get("note")
    if nt:
        ny = hy + 9 + 10
        s.append(f'<rect x="{LABEL_X - 5}" y="{ny - 12}" width="274" '
                 f'height="{len(nt) * NOTE_LH + 8}" rx="7" fill="{color}" opacity="0.11"/>')
        for i, ln in enumerate(nt):
            s.append(f'<text x="{LABEL_X + 4}" y="{ny + i * NOTE_LH}" fill="{color}" '
                     f'font-family="{FONT}" font-size="13" font-weight="bold" '
                     f'dominant-baseline="central">{esc(ln)}</text>')
    return "\n".join(s)


def sequence_strip(order, colors, y0):
    """Нижняя лента: последовательность работы. Кегль подбирается так,
    чтобы вся цепочка уложилась в одну строку."""
    avail = W - 56
    # (кегль подписи, зазор до "›", радиус кружка, кегль номера, отступ до текста)
    for fs, sep, R, ns, PAD in ((14, 15, 11.5, 12.5, 15), (13, 13, 11, 12, 14),
                                (12.2, 11, 10.5, 11.5, 13), (11.4, 9, 10, 11, 12)):
        widths = {k: text_w(META[k][2], fs) for k in order}
        total = sum(R + PAD + widths[k] for k in order) + (len(order) - 1) * sep * 2
        if total <= avail:
            break

    out, x = [], (W - total) / 2
    for j, key in enumerate(order):
        i = j + 1
        cxx, tx = x + R, x + R + PAD
        out.append(f'<circle cx="{cxx:.1f}" cy="{y0}" r="{R}" fill="{colors[key]}"/>')
        out.append(f'<text x="{cxx:.1f}" y="{y0}" fill="#fff" font-family="{FONT}" '
                   f'font-size="{ns}" font-weight="bold" text-anchor="middle" '
                   f'dominant-baseline="central">{i}</text>')
        out.append(f'<text x="{tx:.1f}" y="{y0}" fill="{TXT}" font-family="{FONT}" '
                   f'font-size="{fs}" dominant-baseline="central">{esc(META[key][2])}</text>')
        x = tx + widths[key]
        if j < len(order) - 1:
            out.append(f'<text x="{x + sep:.1f}" y="{y0}" fill="{TXT_DIM}" '
                       f'font-family="{FONT}" font-size="{fs + 3:.0f}" text-anchor="middle" '
                       f'dominant-baseline="central">&#8250;</text>')
            x += sep * 2
    return "\n".join(out)


def legend(items, y):
    out, x = [], 40
    for color, weight, dashed, text in items:
        dash = ' stroke-dasharray="9 6"' if dashed else ""
        out.append(f'<line x1="{x}" y1="{y}" x2="{x + 40}" y2="{y}" stroke="{color}" '
                   f'stroke-width="{weight}" stroke-linecap="round"{dash}/>')
        out.append(f'<text x="{x + 50}" y="{y}" fill="{TXT_DIM}" font-family="{FONT}" '
                   f'font-size="13.5" dominant-baseline="central">{esc(text)}</text>')
        x += 50 + text_w(text, 13.5) + 30
    return "\n".join(out)


def header(title, subtitle):
    return (f'<text x="40" y="54" fill="{TXT}" font-family="{FONT}" font-size="29" '
            f'font-weight="bold" dominant-baseline="central">{esc(title)}</text>'
            f'<text x="40" y="86" fill="{TXT_DIM}" font-family="{FONT}" font-size="16.5" '
            f'dominant-baseline="central">{esc(subtitle)}</text>'
            f'<line x1="40" y1="106" x2="{W - 40}" y2="106" stroke="{GRID}" stroke-width="2"/>')


def plumb():
    """Отвесная средняя линия — поверх фигуры, чтобы видеть симметрию."""
    return (f'<line x1="{CX}" y1="118" x2="{CX}" y2="{Y["feet"] + 24}" stroke="#B9C6CD" '
            f'stroke-width="1.8" stroke-dasharray="5 9" opacity="0.9"/>'
            f'<text x="{CX + 8}" y="{Y["feet"] + 36}" fill="{TXT_DIM}" '
            f'font-family="{FONT}" font-size="12.5">средняя линия (отвес)</text>')


def svg_wrap(inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>\n{inner}\n</svg>\n')


def render(title, subtitle, specs, legend_items, strip_y, legend_y):
    colors = {s["key"]: s["color"] for s in specs}
    order = [s["key"] for s in specs]
    order_by_y = sorted(specs, key=lambda s: Y[s["key"]])
    centers, heights = layout(order_by_y)

    out = [header(title, subtitle), figure(), plumb()]
    for s, cy, bh in zip(order_by_y, centers, heights):
        out.append(ref_line(s, cy, bh))
    out.append(sequence_strip(order, colors, strip_y))
    out.append(legend(legend_items, legend_y))
    return svg_wrap("\n".join(out))


# ==========================================================  СХЕМЫ
BOLD = {"eyes", "jaw", "aperture", "pelvis", "feet"}
LEG_BASE = [(C_KEY, 8, False, "опорные (жирные) линии"),
            (C_SEC, 3.2, True, "вспомогательные линии")]


def spec(key, num, color, weight, dashed=False, halo=False, note=None):
    return {"key": key, "num": num, "color": color, "weight": weight,
            "dashed": dashed, "halo": halo, "note": note}


def plain(order):
    out = []
    for i, k in enumerate(order, 1):
        b = k in BOLD
        out.append(spec(k, i, C_KEY if b else C_SEC, 8 if b else 3.2, dashed=not b))
    return out


def build_1():
    order = ["eyes", "jaw", "neck", "aperture", "diaphragm", "pelvis", "knees", "feet"]
    return render(
        "Схема 1 — Параллельные линии тела, вид со спины",
        "Базовая последовательность. Жирные линии — опорные, тонкие — вспомогательные.",
        plain(order), LEG_BASE, 1392, 1434)


def build_2():
    order = ["eyes", "jaw", "aperture", "neck", "pelvis", "diaphragm", "feet", "knees"]
    return render(
        "Схема 2 — Те же линии, другая последовательность",
        "За каждой опорной линией сразу её вспомогательная: апертура→шея, таз→диафрагма, стопы→колени.",
        plain(order), LEG_BASE, 1392, 1434)


def build_3():
    specs = [
        spec("eyes",     1, C_KEY, 8),
        spec("jaw",      2, C_KEY, 8),
        spec("aperture", 3, C_KEY, 8),
        spec("pelvis",   4, C_KEY, 8),
        spec("diaphragm",5, C_WORK, 6,
             note=["Растянуть, подышать,", "подвигать во всех плоскостях"]),
        spec("sternum",  6, C_WORK, 6,
             note=["Лечь на ролик, разогнуть", "этот отдел, поработать"]),
        spec("neck",     7, C_TARGET, 9, halo=True, note=["ЦЕЛЬ — мобилизация шеи"]),
        spec("feet",     8, C_KEY, 8),
        spec("knees",    9, C_SEC, 3.2, dashed=True),
    ]
    return render(
        "Схема 3 — Протокол мобилизации шеи",
        "Шея (7) — цель. Идём к ней снизу: сначала опора и дыхание, затем верхнегрудной отдел.",
        specs,
        [(C_KEY, 8, False, "опорные"), (C_WORK, 6, False, "рабочие"),
         (C_TARGET, 9, False, "цель"), (C_SEC, 3.2, True, "вспомогательные")],
        1386, 1436)


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    out = os.path.join(root, "assets", "anatomy")
    os.makedirs(out, exist_ok=True)
    files = {
        "body-lines-1-base.svg": build_1(),
        "body-lines-2-alt-order.svg": build_2(),
        "body-lines-3-neck-mobilization.svg": build_3(),
    }
    for name, data in files.items():
        path = os.path.join(out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        print("written:", os.path.relpath(path, root))


if __name__ == "__main__":
    main()
