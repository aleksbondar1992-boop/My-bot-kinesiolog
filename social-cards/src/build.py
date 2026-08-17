# -*- coding: utf-8 -*-
"""Рендер карточек карусели 1080x1350 через headless Chromium."""
import base64, html, json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from content import CARDS, HANDLE, TOTAL

S = Path(__file__).parent
OUT = S.parent / "png"
OUT.mkdir(exist_ok=True)
TMP = S / ".build"
TMP.mkdir(exist_ok=True)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W, H = 1080, 1350


def font_face_css():
    idx = json.loads((S / "fonts/index.json").read_text(encoding="utf-8"))
    out = []
    for fam, items in idx.items():
        for it in items:
            data = (S / "fonts/woff" / it["file"]).read_bytes()
            b64 = base64.b64encode(data).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-style:{it['s']};"
                f"font-weight:{it['w']};font-display:block;"
                f"src:url(data:font/woff;base64,{b64}) format('woff');}}"
            )
    return "\n".join(out)


FONTS = font_face_css()

# Вертикальный мотив: позвоночник = цепочка центров
def spine_svg(active=None, opacity=0.5):
    nodes = ""
    for i in range(7):
        cy = 90 + i * 118
        is_on = active is not None and i == active
        r = 15 if is_on else 8
        fill = "#E5B45F" if is_on else "none"
        stroke = "#E5B45F" if is_on else "rgba(229,180,95,.45)"
        sw = 0 if is_on else 2
        nodes += f'<circle cx="60" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        if is_on:
            nodes += (f'<circle cx="60" cy="{cy}" r="32" fill="none" '
                      f'stroke="rgba(229,180,95,.35)" stroke-width="1.5"/>'
                      f'<circle cx="60" cy="{cy}" r="50" fill="none" '
                      f'stroke="rgba(229,180,95,.15)" stroke-width="1"/>')
    return f'''<svg class="spine" style="opacity:{opacity}" width="120" height="900" viewBox="0 0 120 900" fill="none">
      <line x1="60" y1="60" x2="60" y2="840" stroke="rgba(229,180,95,.28)" stroke-width="1.5"/>
      {nodes}
    </svg>'''


BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
body{
  font-family:'Manrope',sans-serif;
  background:#0A0B14;
  color:#F2EFE9;
  overflow:hidden;
  -webkit-font-smoothing:antialiased;
}
.card{
  position:relative;width:1080px;height:1350px;overflow:hidden;
  background:
    radial-gradient(900px 620px at 88% 8%, rgba(229,180,95,.13), transparent 62%),
    radial-gradient(760px 700px at 6% 96%, rgba(97,136,178,.14), transparent 64%),
    linear-gradient(163deg,#0F1122 0%,#16122A 46%,#0A0B13 100%);
}
.grain{position:absolute;inset:0;opacity:.22;mix-blend-mode:overlay;pointer-events:none}
.vign{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(120% 90% at 50% 45%,transparent 52%,rgba(0,0,0,.55) 100%)}
.spine{position:absolute;right:74px;top:225px}
.inner{position:absolute;inset:0;padding:92px 96px 84px;display:flex;flex-direction:column}

.eyebrow{
  font-size:22px;font-weight:700;letter-spacing:.30em;color:#E5B45F;
  text-transform:uppercase;
}
.counter{
  position:absolute;top:92px;right:96px;font-size:22px;font-weight:600;
  letter-spacing:.16em;color:rgba(242,239,233,.42);font-variant-numeric:tabular-nums;
}
.rule{height:1px;background:linear-gradient(90deg,rgba(229,180,95,.75),rgba(229,180,95,0));}

h1{font-family:'Playfair Display',serif;font-weight:700;line-height:1.06;
   letter-spacing:-.015em;white-space:pre-line}
h2{font-family:'Playfair Display',serif;font-weight:700;line-height:1.08;
   letter-spacing:-.01em;white-space:pre-line}

.foot{
  margin-top:auto;display:flex;align-items:center;justify-content:space-between;
  padding-top:30px;border-top:1px solid rgba(242,239,233,.13);
  font-size:22px;letter-spacing:.06em;color:rgba(242,239,233,.5);font-weight:500;
}
.foot b{color:rgba(242,239,233,.82);font-weight:600}
"""

GRAIN = ('<svg class="grain" xmlns="http://www.w3.org/2000/svg">'
         '<filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".85" '
         'numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/>'
         '</filter><rect width="100%" height="100%" filter="url(#n)"/></svg>')


def page(body, extra_css=""):
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>{FONTS}{BASE_CSS}{extra_css}</style></head><body>{body}</body></html>"""


def esc(t):
    return html.escape(t)


def render_cover(c, n):
    css = """
    .cv-title{font-size:82px;margin-top:44px;max-width:850px}
    .cv-title em{font-style:italic;color:#E5B45F;font-weight:500}
    .cv-sub{font-size:29px;line-height:1.55;color:rgba(242,239,233,.68);
            margin-top:40px;max-width:720px;white-space:pre-line;font-weight:400}
    .cv-rule{width:190px;margin-top:56px}
    .badge{align-self:flex-start;display:inline-flex;align-items:center;gap:14px;
      margin-top:62px;padding:19px 36px;border:1px solid rgba(229,180,95,.42);
      border-radius:999px;font-size:21px;letter-spacing:.22em;font-weight:700;color:#E5B45F}
    .spacer{flex:1}
    .halo{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
      width:1180px;height:1180px;opacity:.5}
    """
    title = esc(c["title"]).replace("«блок»", "<em>«блок»</em>").replace("«спазм»", "<em>«спазм»</em>")
    halo = ('<svg class="halo" viewBox="0 0 600 600" fill="none">'
            '<circle cx="300" cy="300" r="150" stroke="rgba(229,180,95,.16)"/>'
            '<circle cx="300" cy="300" r="215" stroke="rgba(229,180,95,.11)"/>'
            '<circle cx="300" cy="300" r="280" stroke="rgba(97,136,178,.13)"/>'
            '<circle cx="300" cy="220" r="150" stroke="rgba(229,180,95,.10)"/>'
            '<circle cx="300" cy="380" r="150" stroke="rgba(97,136,178,.10)"/></svg>')
    body = f"""<div class="card">{halo}{GRAIN}{spine_svg(active=3, opacity=.85)}<div class="vign"></div>
      <div class="inner">
        <div class="eyebrow">{esc(c['eyebrow'])}</div>
        <div class="rule cv-rule"></div>
        <h1 class="cv-title">{title}</h1>
        <div class="cv-sub">{esc(c['sub'])}</div>
        <div class="badge">{esc(c['hint'])} &nbsp;→</div>
        <div class="spacer"></div>
        <div class="foot"><span>Кинезиолог Александр Бондарь</span><span><b>{HANDLE}</b></span></div>
      </div></div>"""
    return page(body, css)


def render_parallel(c, n):
    css = """
    .topic{font-size:22px;font-weight:800;letter-spacing:.34em;color:#E5B45F}
    .p-title{font-size:66px;margin-top:26px;max-width:640px}
    .rows{margin-top:66px;max-width:700px}
    .row{position:relative;padding:32px 34px;border-radius:20px;
         border:1px solid rgba(242,239,233,.10);background:rgba(255,255,255,.028)}
    .row.eso{border-color:rgba(229,180,95,.30);background:rgba(229,180,95,.055)}
    .row.som{border-color:rgba(126,166,209,.30);background:rgba(126,166,209,.055)}
    .lab{font-size:19px;font-weight:800;letter-spacing:.22em;text-transform:uppercase}
    .row.eso .lab{color:#E5B45F}
    .row.som .lab{color:#9CC0E4}
    .val{font-family:'Playfair Display',serif;font-size:38px;line-height:1.25;
         margin-top:14px;white-space:pre-line;color:#F5F2EC}
    .row.eso .val{font-style:italic}
    .arrow{display:flex;align-items:center;gap:18px;padding:20px 34px;color:rgba(242,239,233,.35)}
    .arrow .ln{height:1px;flex:1;background:linear-gradient(90deg,rgba(229,180,95,.4),rgba(126,166,209,.4))}
    .arrow .tx{font-size:18px;letter-spacing:.24em;font-weight:700;color:rgba(242,239,233,.42)}
    .text{margin-top:52px;font-size:28px;line-height:1.62;color:rgba(242,239,233,.76);
          max-width:740px;white-space:pre-line;font-weight:400}
    """
    body = f"""<div class="card">{GRAIN}{spine_svg(active=n - 2, opacity=.7)}<div class="vign"></div>
      <div class="counter">{n:02d} / {TOTAL:02d}</div>
      <div class="inner">
        <div class="topic">{esc(c['topic'])}</div>
        <h2 class="p-title">{esc(c['title'])}</h2>
        <div class="rows">
          <div class="row eso"><div class="lab">Эзотерика говорит</div>
            <div class="val">{esc(c['eso'])}</div></div>
          <div class="arrow"><div class="ln"></div><div class="tx">ЭТО ПРО</div><div class="ln"></div></div>
          <div class="row som"><div class="lab">Тело говорит</div>
            <div class="val">{esc(c['body_label'])}</div></div>
        </div>
        <div class="text">{esc(c['text'])}</div>
        <div class="foot"><span>Кинезиолог Александр Бондарь</span><span><b>{HANDLE}</b></span></div>
      </div></div>"""
    return page(body, css)


def render_cta(c, n):
    css = """
    .c-title{font-size:74px;margin-top:40px;max-width:800px}
    .c-title em{font-style:italic;color:#E5B45F;font-weight:500}
    .c-text{margin-top:44px;font-size:29px;line-height:1.6;
            color:rgba(242,239,233,.74);max-width:720px;font-weight:400}
    .usp{margin-top:62px;padding:44px 46px;border-radius:24px;
         border:1px solid rgba(229,180,95,.45);
         background:linear-gradient(135deg,rgba(229,180,95,.14),rgba(229,180,95,.03));
         max-width:760px}
    .usp .k{font-size:19px;font-weight:800;letter-spacing:.26em;color:#E5B45F}
    .usp .v{font-family:'Playfair Display',serif;font-size:47px;line-height:1.22;
            margin-top:16px;white-space:pre-line}
    .cta{margin-top:52px;display:flex;align-items:center;gap:26px}
    .cta .k{font-size:19px;font-weight:800;letter-spacing:.26em;color:rgba(242,239,233,.45)}
    .cta .v{font-size:44px;font-weight:800;color:#F5F2EC;letter-spacing:-.01em}
    .halo{position:absolute;right:-190px;bottom:-230px;width:840px;height:840px;opacity:.5}
    """
    title = esc(c["title"]).replace("верить.", "<em>верить.</em>")
    halo = ('<svg class="halo" viewBox="0 0 600 600" fill="none">'
            '<circle cx="300" cy="300" r="120" stroke="rgba(229,180,95,.18)"/>'
            '<circle cx="300" cy="300" r="190" stroke="rgba(229,180,95,.13)"/>'
            '<circle cx="300" cy="300" r="262" stroke="rgba(229,180,95,.08)"/></svg>')
    body = f"""<div class="card">{halo}{GRAIN}<div class="vign"></div>
      <div class="counter">{n:02d} / {TOTAL:02d}</div>
      <div class="inner">
        <div class="eyebrow">{esc(c['eyebrow'])}</div>
        <h1 class="c-title">{title}</h1>
        <div class="c-text">{esc(c['text'])}</div>
        <div class="usp"><div class="k">МОЁ УСЛОВИЕ</div>
          <div class="v">{esc(c['usp'])}</div></div>
        <div class="cta"><span class="k">{esc(c['cta_label'])}</span>
          <span class="v">{esc(c['cta_value'])}</span></div>
        <div class="foot"><span>Кинезиолог Александр Бондарь</span><span><b>Пиши в директ</b></span></div>
      </div></div>"""
    return page(body, css)


RENDERERS = {"cover": render_cover, "parallel": render_parallel, "cta": render_cta}

for i, card in enumerate(CARDS, start=1):
    html_path = TMP / f"card-{i:02d}.html"
    png_path = OUT / f"card-{i:02d}.png"
    html_path.write_text(RENDERERS[card["kind"]](card, i), encoding="utf-8")
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--force-device-scale-factor=1", f"--window-size={W},{H}",
        "--default-background-color=00000000", "--virtual-time-budget=4000",
        f"--screenshot={png_path}", f"file://{html_path}",
    ], check=True, capture_output=True)
    print(f"✓ card-{i:02d}.png  {png_path.stat().st_size // 1024} KB")
