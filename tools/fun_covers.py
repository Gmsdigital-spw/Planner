"""Bright, on-theme listing covers (Oct 21, 2026 standard).

Why: Grayson flagged the beige covers as bland ("like it's for college professors").
Rule: every cover shows (1) the real product pages, (2) the THING the product is about drawn big
(cookies on a cookie swap, Santa on Secret Santa), (3) a big count badge, (4) a bold color, not cream.

Usage:  python3 tools/fun_covers.py tools/fun_covers_config.json [slug ...]
Each config entry:
  slug, out, title ("Cookie *Swap* Party Kit" -> *word* gets the accent color/script),
  kicker, badge [number, word], pills [3 short benefits], theme (key of THEMES),
  pages {"src": image path, "crop": [x0,y0,x1,y1] fractions}  (real product pages),
  decor [[art_name, {kwargs}, x, y, size, rotate], ...]  (2000x1500 canvas)
"""
import base64, html, io, json, os, re, sys
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa: E402

W, H = 2000, 1500
# Etsy's app grid shows the CENTRED SQUARE of a 4:3 photo (x 250..1750 on 2000x1500).
# Every word, the badge and the product card must sit inside SAFE_X0..SAFE_X1 or the
# thumbnail clips it (Night Shift failed inspection on this twice, Oct 21-22, 2026).
# Only background pattern, confetti and decor art may use the outer bands.
SAFE_X0, SAFE_X1 = 280, 1720
FONTS = os.path.join(HERE, "fonts")

THEMES = {
    # bg, bg2 (gradient), ink (title), accent (script word + badge), pill bg/text, pattern
    "xmas_red":   dict(bg="#c8102e", bg2="#8f0b20", ink="#ffffff", accent="#ffd34d", pill="#ffffff", pilltx="#a30d24", badge="#1f7a4a", badgetx="#ffffff", pattern="snow"),
    "xmas_green": dict(bg="#1f7a4a", bg2="#0f4d2c", ink="#ffffff", accent="#ffd34d", pill="#ffffff", pilltx="#16603a", badge="#d7192f", badgetx="#ffffff", pattern="snow"),
    "ginger":     dict(bg="#9a5428", bg2="#6b3516", ink="#ffffff", accent="#ffd9a8", pill="#fff6ea", pilltx="#7a3e18", badge="#d7192f", badgetx="#ffffff", pattern="icing"),
    "harvest":    dict(bg="#e8742c", bg2="#b8471a", ink="#ffffff", accent="#ffe08a", pill="#fff7ec", pilltx="#a8461b", badge="#5c8a2e", badgetx="#ffffff", pattern="dots"),
    "midnight":   dict(bg="#1a2a5e", bg2="#0b1433", ink="#ffffff", accent="#ffd34d", pill="#ffd34d", pilltx="#1a2a5e", badge="#ff4f7a", badgetx="#ffffff", pattern="stars"),
    "pink":       dict(bg="#ff8fb6", bg2="#f0628f", ink="#ffffff", accent="#fff1a8", pill="#ffffff", pilltx="#d93b72", badge="#c8102e", badgetx="#ffffff", pattern="hearts"),
    "pink_xmas":  dict(bg="#ff9fc0", bg2="#e25b8c", ink="#ffffff", accent="#fff3b0", pill="#ffffff", pilltx="#c8336b", badge="#c8102e", badgetx="#ffffff", pattern="snow"),
    "money":      dict(bg="#14b37d", bg2="#0a7d56", ink="#ffffff", accent="#ffe066", pill="#ffffff", pilltx="#0a7d56", badge="#ff5a5f", badgetx="#ffffff", pattern="dots"),
    "sunny":      dict(bg="#ffc23d", bg2="#ff9a1f", ink="#2b2140", accent="#e8323c", pill="#2b2140", pilltx="#ffffff", badge="#6c4bd8", badgetx="#ffffff", pattern="dots"),
    "violet":     dict(bg="#7b5cf0", bg2="#4c32b8", ink="#ffffff", accent="#ffe066", pill="#ffffff", pilltx="#4c32b8", badge="#ff5a8a", badgetx="#ffffff", pattern="dots"),
    "sky":        dict(bg="#3fa7f5", bg2="#1f6fd1", ink="#ffffff", accent="#ffe066", pill="#ffffff", pilltx="#1f6fd1", badge="#ff5a5f", badgetx="#ffffff", pattern="dots"),
    "sage":       dict(bg="#7fb27a", bg2="#4f8a4f", ink="#ffffff", accent="#fff1b8", pill="#ffffff", pilltx="#3f7a42", badge="#e8742c", badgetx="#ffffff", pattern="dots"),
    "fall":       dict(bg="#c4452a", bg2="#8a2a17", ink="#ffffff", accent="#ffd36b", pill="#fff4e6", pilltx="#9a3219", badge="#5c8a2e", badgetx="#ffffff", pattern="dots"),
    "berry":      dict(bg="#c2185b", bg2="#7d0f3a", ink="#ffffff", accent="#ffd34d", pill="#ffffff", pilltx="#a3144d", badge="#1f7a4a", badgetx="#ffffff", pattern="snow"),
    "teal":       dict(bg="#12b5a5", bg2="#0a7f74", ink="#ffffff", accent="#ffe066", pill="#ffffff", pilltx="#0a7f74", badge="#ff5a8a", badgetx="#ffffff", pattern="dots"),
    "coral":      dict(bg="#ff6b5b", bg2="#e23d4f", ink="#ffffff", accent="#ffe066", pill="#ffffff", pilltx="#d1334a", badge="#1fb58f", badgetx="#ffffff", pattern="dots"),
}

def _b64(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def pattern_css(kind):
    if kind == "snow":
        s = '<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220"><g fill="#fff" opacity=".14"><circle cx="30" cy="40" r="6"/><circle cx="140" cy="20" r="4"/><circle cx="90" cy="110" r="7"/><circle cx="190" cy="140" r="5"/><circle cx="40" cy="180" r="4"/><circle cx="160" cy="200" r="6"/></g></svg>'
    elif kind == "icing":
        s = '<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><g fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="5" stroke-linecap="round"><path d="M10 40 q15 -18 30 0 q15 18 30 0"/><path d="M90 120 q15 -18 30 0 q15 18 30 0"/></g><g fill="#fff" opacity=".16"><circle cx="120" cy="40" r="6"/><circle cx="40" cy="120" r="6"/></g></svg>'
    elif kind == "stars":
        s = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><g fill="#ffd34d" opacity=".35"><path d="M40 20 l4 10 10 1 -8 6 3 10 -9 -6 -9 6 3 -10 -8 -6 10 -1z"/><circle cx="150" cy="60" r="3"/><circle cx="100" cy="150" r="4"/><path d="M160 140 l3 7 7 1 -5 4 2 7 -7 -4 -7 4 2 -7 -5 -4 7 -1z"/></g><g fill="#fff" opacity=".3"><circle cx="20" cy="120" r="2"/><circle cx="120" cy="20" r="2"/><circle cx="190" cy="190" r="2"/></g></svg>'
    elif kind == "hearts":
        s = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><g fill="#fff" opacity=".2"><path d="M40 60 c-14 -10 -16 -20 -10 -26 c5 -5 10 -2 10 3 c0 -5 5 -8 10 -3 c6 6 4 16 -10 26z"/><path d="M150 160 c-14 -10 -16 -20 -10 -26 c5 -5 10 -2 10 3 c0 -5 5 -8 10 -3 c6 6 4 16 -10 26z"/></g><g fill="#fff" opacity=".2"><circle cx="150" cy="50" r="5"/><circle cx="50" cy="160" r="5"/></g></svg>'
    else:
        s = '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><g fill="#fff" opacity=".13"><circle cx="20" cy="20" r="7"/><circle cx="80" cy="80" r="7"/></g></svg>'
    return f"url('{_b64(s)}')"

def crop_to_data(src, crop, max_w=1400):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    x0, y0, x1, y1 = crop
    im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=92)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.width / im.height

def title_html(t, accent):
    t = html.escape(t)
    return re.sub(r"\*(.+?)\*", r'<span class="acc">\1</span>', t)

def font_faces():
    faces = [("Brico", "BricolageGrotesque-Bold", 700), ("Outfit", "Outfit-Bold", 700), ("Outfit", "Outfit-Regular", 400),
             ("LoraBI", "Lora-BoldItalic", 700), ("Gloock", "Gloock-Regular", 400)]
    return "".join(f"@font-face{{font-family:'{n}';src:url(data:font/ttf;base64,{base64.b64encode(open(os.path.join(FONTS, f + '.ttf'), 'rb').read()).decode()});font-weight:{w}}}" for n, f, w in faces)

def build_html(c):
    th = THEMES[c["theme"]]
    img, ratio = crop_to_data(os.path.join(c.get("root", "."), c["pages"]["src"]), c["pages"]["crop"])
    # product card box: right side, fit image ratio inside 980x1180 area
    safe = c.get("safe", True)
    if safe:  # card fills the right half of the centred square
        box_w, box_h = c.get("card_box", (760, 1120))  # optional bigger hero card (Oct 23: 40%+ of the square)
        centre_x = c.get("card_cx", 1325)
    else:     # legacy full-width layout (old live covers only)
        box_w, box_h = 1000, 1160
        centre_x = 1440
    if ratio >= box_w / box_h:
        cw, ch = box_w, int(box_w / ratio)
    else:
        ch, cw = box_h, int(box_h * ratio)
    cx = centre_x - cw // 2
    cy = 760 - ch // 2
    lx, lw = (SAFE_X0 + 10, c.get("left_w", 640)) if safe else (90, 860)
    badge_d = 270 if safe else 330
    default_bx = (SAFE_X1 - (badge_d + 24) - 30) if safe else cx - 150  # 24 = 12px white border both sides; 30 = room for the -10deg tilt (bug rule fix Oct 23)
    decor = []
    for d in c.get("decor", []):
        name, kw, x, y, size, rot = d[:6]
        if name.startswith("img:"):  # realistic 3D image from tools/img3d (Noto Emoji 3D, Apache-2.0)
            fn = os.path.join(HERE, "img3d", f"emoji_u{name[4:]}.png")
            if not os.path.exists(fn):
                fn = os.path.join(HERE, "img3d", f"emoji_u{name[4:]}_fe0f.png")
            svg = f'<img src="data:image/png;base64,{base64.b64encode(open(fn,"rb").read()).decode()}" style="width:100%;height:100%">'
        else:
            svg = getattr(art, name)(**kw)
        z = 6 if len(d) < 7 else d[6]
        decor.append(f'<div class="dec" style="left:{x}px;top:{y}px;width:{size}px;height:{size}px;transform:rotate({rot}deg);z-index:{z}">{svg}</div>')
    confetti = ""
    if c.get("confetti"):
        confetti = f'<div class="conf">{art.confetti_layer(W, H, n=c["confetti"], seed=len(c["slug"]))}</div>'
    pills = "".join(f'<span class="pill">{html.escape(p)}</span>' for p in c.get("pills", []))
    num, word = c["badge"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:radial-gradient(ellipse at 30% 30%, {th['bg']} 0%, {th['bg']} 45%, {th['bg2']} 100%);font-family:Outfit;position:relative}}
.pat{{position:absolute;inset:0;background:{pattern_css(th['pattern'])};}}
.conf{{position:absolute;inset:0;z-index:1;opacity:.9}}
.left{{position:absolute;left:{lx}px;top:120px;width:{lw}px;z-index:5}}
.kick{{display:inline-block;background:{th['accent']};color:{th['bg2']};font-family:Outfit;font-weight:700;font-size:40px;letter-spacing:4px;padding:14px 30px;border-radius:999px;text-transform:uppercase}}
.title{{margin-top:34px;font-family:Brico;font-weight:700;color:{th['ink']};font-size:{c.get('title_size',130 if safe else 150)}px;line-height:.98;letter-spacing:-2px;text-shadow:0 6px 0 rgba(0,0,0,.18)}}
.acc{{font-family:LoraBI;color:{th['accent']};letter-spacing:0}}
.sub{{margin-top:30px;color:{th['ink']};opacity:.95;font-size:44px;line-height:1.25;font-family:Outfit;font-weight:400}}
.pills{{position:absolute;left:{lx}px;bottom:90px;max-width:{lw}px;display:flex;flex-direction:column;gap:22px;z-index:5;align-items:flex-start}}
.pill{{background:{th['pill']};color:{th['pilltx']};font-weight:700;font-size:{40 if safe else 46}px;padding:{'14px 32px' if safe else '16px 38px'};white-space:nowrap;border-radius:999px;box-shadow:0 8px 0 rgba(0,0,0,.15)}}
.card{{position:absolute;left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px;background:#fff;padding:18px;border-radius:22px;transform:rotate({c.get('card_rot',3)}deg);
  box-shadow:0 30px 60px rgba(0,0,0,.35),0 8px 18px rgba(0,0,0,.25);z-index:4}}
.card img{{width:100%;height:100%;object-fit:cover;object-position:top center;border-radius:10px;display:block}}
.badge{{position:absolute;left:{c.get('badge_x', default_bx)}px;top:{c.get('badge_y', (cy - 90) if safe else (cy - 110))}px;width:{badge_d}px;height:{badge_d}px;border-radius:50%;background:{th['badge']};color:{th['badgetx']};
  display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:8;border:12px solid #fff;box-shadow:0 18px 40px rgba(0,0,0,.35);transform:rotate(-10deg)}}
.badge .n{{font-family:Brico;font-size:{c.get('badge_size',125 if safe else 150)}px;line-height:.9}}
.badge .w{{font-family:Outfit;font-weight:700;font-size:44px;letter-spacing:3px;margin-top:4px}}
.dec{{position:absolute;filter:drop-shadow(0 12px 14px rgba(0,0,0,.28))}}
.dl{{position:absolute;right:{(W-SAFE_X1+10) if safe else 70}px;bottom:46px;color:{th['ink']};font-family:Outfit;font-weight:700;font-size:34px;letter-spacing:3px;z-index:9;opacity:.9}}
</style></head><body>
<div class="pat"></div>{confetti}
<div class="left"><div class="kick" data-fitk="{lw}">{html.escape(c['kicker'])}</div>
<div class="title" data-fit="{lw}" data-fith="{c.get('title_h',640)}">{title_html(c['title'], th['accent'])}</div>
{f'<div class="sub">{html.escape(c["sub"])}</div>' if c.get('sub') else ''}</div>
<div class="pills">{pills}</div>
<div class="card"><img src="{img}"></div>
<div class="badge"><div class="n">{html.escape(str(num))}</div><div class="w" style="font-size:{44 if len(word) <= 7 else 32}px">{html.escape(word)}</div></div>
{''.join(decor)}
<div class="dl">INSTANT DOWNLOAD</div>
<script>
for (const el of document.querySelectorAll('[data-fit]')) {{
  let fs = parseFloat(getComputedStyle(el).fontSize); const mw=+el.dataset.fit, mh=+el.dataset.fith;
  while ((el.scrollWidth > mw || el.scrollHeight > mh) && fs > 40) {{ fs -= 4; el.style.fontSize = fs + 'px'; }}
}}
for (const el of document.querySelectorAll('[data-fitk], .pill')) {{
  const mw = {lw}; let fs = parseFloat(getComputedStyle(el).fontSize);
  while (el.getBoundingClientRect().width > mw && fs > 22) {{ fs -= 2; el.style.fontSize = fs + 'px'; }}
}}
</script></body></html>"""

CHECK_JS = """() => {
  const out = [];
  const box = (sel, label) => document.querySelectorAll(sel).forEach((el, i) => {
    const r = el.getBoundingClientRect();
    out.push({label: label + (i ? ' ' + (i + 1) : ''), x0: r.left, x1: r.right, y0: r.top, y1: r.bottom,
              ow: el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2});
  });
  box('.kick', 'kicker'); box('.title', 'title'); box('.sub', 'subtitle'); box('.pill', 'pill');
  box('.badge', 'badge'); box('.card', 'product card'); box('.dec', 'decor');
  // real text extent of the title (spans/lines can overflow the block)
  const t = document.querySelector('.title');
  if (t) { const rg = document.createRange(); rg.selectNodeContents(t);
    for (const r of rg.getClientRects()) out.push({label: 'title text', x0: r.left, x1: r.right, y0: r.top, y1: r.bottom, ow: false}); }
  return out;
}"""

def check_safe(pg, tol=6):
    """Return a list of problems: any word/badge/card outside the centred square, or decor over words."""
    items = pg.evaluate(CHECK_JS)
    probs = []
    words = [i for i in items if not i["label"].startswith(("decor", "product card"))]
    for i in items:
        if i["label"].startswith("decor"):
            continue
        if i["x0"] < SAFE_X0 - 30 - tol or i["x1"] > SAFE_X1 + 30 + tol:
            probs.append(f"{i['label']} runs outside the Etsy square (x {int(i['x0'])}-{int(i['x1'])}, safe {SAFE_X0}-{SAFE_X1})")
        if i["y0"] < -tol or i["y1"] > H + tol:
            probs.append(f"{i['label']} runs off the top/bottom")
    for d in [i for i in items if i["label"].startswith("decor")]:
        for w in words:
            if not w["label"].startswith(("title text", "kicker", "pill", "subtitle")):
                continue
            ix = min(d["x1"], w["x1"]) - max(d["x0"], w["x0"]); iy = min(d["y1"], w["y1"]) - max(d["y0"], w["y0"])
            if ix > 25 and iy > 25:
                probs.append(f"{d['label']} covers the {w['label']}")
                break
    return sorted(set(probs))

def self_heal(pg, c, rounds=6):
    """Fix a cover that fails the square check instead of stopping (Grayson, Oct 22, 2026:
    "when it runs into these bugs, it fixes it"). Each round: drop decor that covers words,
    pull decor that sits on the card edge outward, shrink the title/kicker/pills a step.
    Prints every fix so the run log shows what happened; only gives up after 6 rounds."""
    import copy
    c = copy.deepcopy(c)
    for n in range(rounds):
        probs = check_safe(pg)
        if not probs:
            if n:
                print(f"self-heal: {c['slug']} fixed in {n} round(s)")
            return c
        print(f"self-heal round {n + 1} ({c['slug']}): " + "; ".join(probs))
        dec = c.get("decor", [])
        bad = {int(p.split()[1]) - 1 if p.split()[1].isdigit() else 0
               for p in probs if p.startswith("decor") and "covers" in p}
        if bad:
            c["decor"] = [d for i, d in enumerate(dec) if i not in bad]
        if any(p.startswith(("title", "kicker", "subtitle")) for p in probs):
            c["title_size"] = int(c.get("title_size", 130) * 0.88)
            c["title_h"] = int(c.get("title_h", 640))
        if any(p.startswith("pill") for p in probs):
            c["pills"] = [p if len(p) <= 22 else p[:22].rsplit(" ", 1)[0] for p in c.get("pills", [])]
        if any(p.startswith("badge") for p in probs):
            c.pop("badge_x", None); c.pop("badge_y", None)
        if any(p.startswith("product card") for p in probs):
            c["card_rot"] = 0
        pg.set_content(build_html(c), wait_until="load")
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
    probs = check_safe(pg)
    if probs:
        raise SystemExit(f"COVER STILL NOT SQUARE-SAFE after {rounds} self-heal rounds ({c['slug']}): "
                         + "; ".join(probs) + " -> fix tools/fun_covers.py itself (bug rule), never switch the check off")
    return c

def render(configs, only=None):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for c in configs:
            if only and c["slug"] not in only:
                continue
            pg.set_content(build_html(c), wait_until="load")
            pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
            if c.get("safe", True):
                c = self_heal(pg, c)
            png = pg.screenshot(type="png")
            out = os.path.join(c.get("root", "."), c["out"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            Image.open(io.BytesIO(png)).convert("RGB").save(out, "JPEG", quality=90)
            print("wrote", out)
        b.close()

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    render(cfg, set(sys.argv[2:]) or None)
