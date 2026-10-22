"""Bold, on-theme Pinterest pins (1000x1500): the portrait twin of tools/fun_covers.py.

Why: cover-styles.md (Oct 21, 2026) makes the bold fun look the standard for every pin, but the
only pin renderer was cover_styles.py with its cream and linen backgrounds. This closes that gap.
Same THEMES, fonts, patterns and 3D art as fun_covers.py, so a pin and its cover match.

Layout (top to bottom): kicker pill, the HOOK (4 to 7 words, top third), the real product pages
on a white card with the count badge on its corner, 2 or 3 benefit pills, "INSTANT DOWNLOAD".

Usage:  python3 tools/fun_pins.py <config.json> [slug ...]
Each config entry (same keys as fun_covers_config.json, portrait coordinates):
  slug, out, hook ("Plan the *Cookie Swap* in 10 Minutes"; *word* gets the accent script),
  kicker, badge [number, word], pills [2-3 short benefits], theme (key of fun_covers.THEMES),
  pages {"src": image path, "crop": [x0,y0,x1,y1] fractions}  (real product pages),
  decor [[art_name | "img:<codepoint>", {kwargs}, x, y, size, rotate(, z)], ...]  (1000x1500 canvas)
  optional: hook_size (default 108), card_rot (default -3), badge_x/badge_y, confetti (count),
            sub (one short line under the hook), title (used when hook is missing)
"""
import base64, html, io, json, os, sys
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import art  # noqa: E402
import fun_covers as fc  # noqa: E402

W, H = 1000, 1500
THEMES = fc.THEMES


def decor_html(items):
    out = []
    for d in items:
        name, kw, x, y, size, rot = d[:6]
        if name.startswith("img:"):
            fn = os.path.join(HERE, "img3d", f"emoji_u{name[4:]}.png")
            if not os.path.exists(fn):
                fn = os.path.join(HERE, "img3d", f"emoji_u{name[4:]}_fe0f.png")
            svg = f'<img src="data:image/png;base64,{base64.b64encode(open(fn, "rb").read()).decode()}" style="width:100%;height:100%">'
        else:
            svg = getattr(art, name)(**kw)
        z = 6 if len(d) < 7 else d[6]
        out.append(f'<div class="dec" style="left:{x}px;top:{y}px;width:{size}px;height:{size}px;transform:rotate({rot}deg);z-index:{z}">{svg}</div>')
    return "".join(out)


def build_html(c):
    th = THEMES[c["theme"]]
    img, ratio = fc.crop_to_data(os.path.join(c.get("root", "."), c["pages"]["src"]), c["pages"]["crop"], max_w=1000)
    # product card: centered, fits inside 820x720 below the hook
    box_w, box_h = 820, 720
    if ratio >= box_w / box_h:
        cw, ch = box_w, int(box_w / ratio)
    else:
        ch, cw = box_h, int(box_h * ratio)
    cx = 500 - cw // 2
    cy = 920 - ch // 2
    confetti = f'<div class="conf">{art.confetti_layer(W, H, n=c["confetti"], seed=len(c["slug"]))}</div>' if c.get("confetti") else ""
    pills = "".join(f'<span class="pill">{html.escape(p)}</span>' for p in c.get("pills", [])[:3])
    num, word = c["badge"]
    hook = c.get("hook") or c["title"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fc.font_faces()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{background:radial-gradient(ellipse at 30% 20%, {th['bg']} 0%, {th['bg']} 45%, {th['bg2']} 100%);font-family:Outfit;position:relative}}
.pat{{position:absolute;inset:0;background:{fc.pattern_css(th['pattern'])};}}
.conf{{position:absolute;inset:0;z-index:1;opacity:.9}}
.top{{position:absolute;left:60px;top:56px;width:880px;z-index:5;text-align:center}}
.kick{{display:inline-block;background:{th['accent']};color:{th['bg2']};font-weight:700;font-size:30px;letter-spacing:4px;padding:12px 26px;border-radius:999px;text-transform:uppercase}}
.hook{{margin-top:26px;font-family:Brico;font-weight:700;color:{th['ink']};font-size:{c.get('hook_size',108)}px;line-height:.98;letter-spacing:-1px;text-shadow:0 5px 0 rgba(0,0,0,.18)}}
.acc{{font-family:LoraBI;color:{th['accent']};letter-spacing:0}}
.sub{{margin-top:18px;color:{th['ink']};opacity:.95;font-size:34px;line-height:1.25}}
.card{{position:absolute;left:{cx}px;top:{cy}px;width:{cw}px;height:{ch}px;background:#fff;padding:14px;border-radius:20px;transform:rotate({c.get('card_rot',-3)}deg);
  box-shadow:0 26px 50px rgba(0,0,0,.35),0 8px 16px rgba(0,0,0,.25);z-index:4}}
.card img{{width:100%;height:100%;object-fit:cover;object-position:top center;border-radius:10px;display:block}}
.badge{{position:absolute;left:{c.get('badge_x', cx+cw-150)}px;top:{c.get('badge_y', cy-120)}px;width:250px;height:250px;border-radius:50%;background:{th['badge']};color:{th['badgetx']};
  display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:8;border:10px solid #fff;box-shadow:0 16px 34px rgba(0,0,0,.35);transform:rotate(10deg)}}
.badge .n{{font-family:Brico;font-size:{c.get('badge_size',112)}px;line-height:.9}}
.badge .w{{font-weight:700;font-size:{34 if len(word) <= 7 else 26}px;letter-spacing:3px;margin-top:4px}}
.pills{{position:absolute;left:40px;right:40px;bottom:112px;display:flex;flex-wrap:wrap;gap:14px;justify-content:center;z-index:5}}
.pill{{background:{th['pill']};color:{th['pilltx']};font-weight:700;font-size:34px;padding:12px 28px;border-radius:999px;box-shadow:0 7px 0 rgba(0,0,0,.15);white-space:nowrap}}
.dec{{position:absolute;filter:drop-shadow(0 10px 12px rgba(0,0,0,.28))}}
.dl{{position:absolute;left:0;right:0;bottom:40px;text-align:center;color:{th['ink']};font-weight:700;font-size:28px;letter-spacing:4px;z-index:9;opacity:.9}}
</style></head><body>
<div class="pat"></div>{confetti}
<div class="top"><div class="kick">{html.escape(c['kicker'])}</div>
<div class="hook" data-fit="880" data-fith="{c.get('hook_h',360)}">{fc.title_html(hook, th['accent'])}</div>
{f'<div class="sub">{html.escape(c["sub"])}</div>' if c.get('sub') else ''}</div>
<div class="card"><img src="{img}"></div>
<div class="badge"><div class="n">{html.escape(str(num))}</div><div class="w">{html.escape(word)}</div></div>
{decor_html(c.get('decor', []))}
<div class="pills">{pills}</div>
<div class="dl">INSTANT DOWNLOAD</div>
<script>
for (const el of document.querySelectorAll('[data-fit]')) {{
  let fs = parseFloat(getComputedStyle(el).fontSize); const mw=+el.dataset.fit, mh=+el.dataset.fith;
  while ((el.scrollWidth > mw || el.scrollHeight > mh) && fs > 40) {{ fs -= 4; el.style.fontSize = fs + 'px'; }}
}}
</script></body></html>"""


def render(configs, only=None):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for c in configs:
            if only and c["slug"] not in only:
                continue
            pg.set_content(build_html(c), wait_until="load")
            pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
            png = pg.screenshot(type="png")
            out = os.path.join(c.get("root", "."), c["out"])
            os.makedirs(os.path.dirname(out), exist_ok=True)
            Image.open(io.BytesIO(png)).convert("RGB").save(out, "JPEG", quality=88)
            print("wrote", out)
        b.close()


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    render(cfg, set(sys.argv[2:]) or None)
