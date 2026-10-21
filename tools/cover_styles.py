"""Cover & pin renderer for the 6 styles in factory/specs/cover-styles.md.

Usage:
  python3 tools/cover_styles.py config.json            # one config or a list of configs
Config keys:
  style      1..6 (see spec)            size     "cover" (2000x1500 JPG) | "pin" (1000x1500 JPG)
  title      main title                  script   optional script word for style 2 (defaults to first word)
  subtitle   format line ("Printable | US Letter + A4 | Instant Download")
  badge      count badge text, style 1 ("36 GAMES", "85+ PAGES") - first token is the big number
  pills      list of short benefits      hook     pin hook text (big, top third). Pins only.
  year       big year for style 5 (optional)
  theme      christmas | blush | sage | linen | bright | harvest | berry
  pages      list of local image paths of REAL product pages (first = hero)
  variant    style 6 only: "desk" (default) or "frame" (framed prints on a wall)
  out        output .jpg path
Renders with headless Chromium (PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers) and bundled OFL fonts in tools/fonts.
"""
import base64, html, json, os, random, sys, tempfile
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

THEMES = {
  # bg = background, bg2 = second background tone, a = accent, a2 = second accent, ink = text, soft = pale accent
  "christmas": dict(bg="#f4ece0", bg2="#e9dccb", a="#a3262e", a2="#2f5d43", gold="#c9a24a", ink="#3b1f1a", soft="#f3d9d3", motif="star"),
  "berry":     dict(bg="#f6ece9", bg2="#ecd8d3", a="#9b2c3c", a2="#3f6b4f", gold="#c9a24a", ink="#3d1d22", soft="#f4dcdf", motif="star"),
  "blush":     dict(bg="#f8e4e4", bg2="#f1cfd2", a="#c45b72", a2="#e9a7b3", gold="#c99a6a", ink="#5a2a35", soft="#fdf1f1", motif="heart"),
  "sage":      dict(bg="#e6ebdf", bg2="#d5ddca", a="#5f7b5a", a2="#b88a5a", gold="#c3a46a", ink="#2c3629", soft="#f1f4ec", motif="leaf"),
  "linen":     dict(bg="#efe7db", bg2="#e2d6c4", a="#8a6447", a2="#5f7b5a", gold="#c3a46a", ink="#3a2c22", soft="#f7f1e8", motif="dot"),
  "harvest":   dict(bg="#f5e9db", bg2="#ebd5bd", a="#b0532f", a2="#6b7a3a", gold="#d39b3a", ink="#3d2418", soft="#f8e3d3", motif="leaf"),
  "evergreen": dict(bg="#eef1ea", bg2="#dde5d8", a="#2f5d43", a2="#a3262e", gold="#c9a24a", ink="#1f2e24", soft="#f4f7f1", motif="star"),
  "champagne": dict(bg="#f6efe2", bg2="#ebdfc8", a="#9a6b22", a2="#7a2e3a", gold="#d4af5a", ink="#3a2a17", soft="#fbf6ec", motif="star"),
  "bright":    dict(bg="#fff8ec", bg2="#ffeccf", a="#ff5a5f", a2="#1fb58f", gold="#ffc23d", ink="#2b2b2b", soft="#fff1d6", motif="confetti",
                    multi=["#ff5a5f", "#ffb627", "#1fb58f", "#3fa7f5", "#b06ee8", "#ff8fb1"]),
}

def font_css():
    faces = [("Gloock", "Gloock-Regular", 400, "normal"), ("Young", "YoungSerif-Regular", 400, "normal"),
             ("Lora", "Lora-Regular", 400, "normal"), ("Lora", "Lora-Bold", 700, "normal"),
             ("Lora", "Lora-Italic", 400, "italic"), ("Lora", "Lora-BoldItalic", 700, "italic"),
             ("Work", "WorkSans-Regular", 400, "normal"), ("Work", "WorkSans-Bold", 700, "normal"),
             ("Brico", "BricolageGrotesque-Regular", 400, "normal"), ("Brico", "BricolageGrotesque-Bold", 700, "normal"),
             ("Outfit", "Outfit-Regular", 400, "normal"), ("Outfit", "Outfit-Bold", 700, "normal"),
             ("Hand", "NothingYouCouldDo-Regular", 400, "normal")]
    return "".join(f"@font-face{{font-family:'{n}';src:url('file://{FONTS}/{f}.ttf');font-weight:{w};font-style:{s}}}" for n, f, w, s in faces)

NOISE = "url(\"data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.35  0 0 0 0 0.28  0 0 0 0 0.2  0 0 0 .09 0'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>""").decode() + "\")"
LINEN = "url(\"data:image/svg+xml;base64," + base64.b64encode(b"""<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'><filter id='l'><feTurbulence type='fractalNoise' baseFrequency='.012 .9' numOctaves='2' seed='3'/><feColorMatrix values='0 0 0 0 0.4  0 0 0 0 0.34  0 0 0 0 0.27  0 0 0 .16 0'/></filter><filter id='m'><feTurbulence type='fractalNoise' baseFrequency='.9 .012' numOctaves='2' seed='5'/><feColorMatrix values='0 0 0 0 0.4  0 0 0 0 0.34  0 0 0 0 0.27  0 0 0 .12 0'/></filter><rect width='100%' height='100%' filter='url(#l)'/><rect width='100%' height='100%' filter='url(#m)'/></svg>""").decode() + "\")"

BASE = """*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden}
body{position:relative;font-family:Work,sans-serif;color:var(--ink);background:var(--bg)}
.abs{position:absolute}
.pg{position:absolute;background:#fff;overflow:hidden;box-shadow:0 2px 3px rgba(40,25,15,.18),0 14px 30px rgba(40,25,15,.22),0 40px 80px rgba(40,25,15,.18)}
.pg img{width:100%%;height:100%%;object-fit:cover;object-position:top center;display:block}
.pg:after{content:"";position:absolute;inset:0;background:%(NOISE)s;mix-blend-mode:multiply;opacity:.55;pointer-events:none}
.fit{white-space:nowrap}
.pill{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;font-family:Outfit;font-weight:700;white-space:nowrap}
.noise{position:absolute;inset:0;background:%(NOISE)s;pointer-events:none}
"""

FIT_JS = """
for (const el of document.querySelectorAll('[data-fit]')) {
  const maxW = parseFloat(el.dataset.fit); let fs = parseFloat(getComputedStyle(el).fontSize);
  const maxH = el.dataset.fith ? parseFloat(el.dataset.fith) : 1e9;
  el.style.display = 'inline-block'; el.style.maxWidth = 'none';
  if (getComputedStyle(el).whiteSpace !== 'nowrap') el.style.width = maxW + 'px';
  while ((el.scrollWidth > maxW || el.scrollHeight > maxH) && fs > 10) { fs -= 2; el.style.fontSize = fs + 'px'; }
}
"""

def esc(s):
    import re
    out = html.escape(str(s or ""))
    # keep hyphenated words (Debt-Free, Grown-Ups) on one line
    return re.sub(r"(\S+-\S+)", r'<span style="white-space:nowrap">\1</span>', out)

def img_url(p): return "file://" + os.path.abspath(p)

def page(p, x, y, w, h, rot=0, z=1, extra=""):
    return f'<div class="pg" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);z-index:{z};{extra}"><img src="{img_url(p)}"></div>'

def cyc(pages, n):
    return [pages[i % len(pages)] for i in range(n)]

def motif_svg(t, W, H, n=26, seed=4, area=None, size=(26, 60)):
    random.seed(seed)
    out = []
    x0, y0, x1, y1 = area or (0, 0, W, H)
    for _ in range(n):
        x, y = random.uniform(x0, x1), random.uniform(y0, y1)
        s = random.uniform(*size); r = random.uniform(-30, 30)
        kind = t["motif"]
        col = random.choice([t["a"], t["a2"], t["gold"]]) if kind != "confetti" else random.choice(t["multi"])
        op = random.uniform(.55, .9)
        if kind == "star":
            path = "M0,-10 L2.9,-3.1 10,-3.1 4.3,1.2 6.5,8.1 0,4 -6.5,8.1 -4.3,1.2 -10,-3.1 -2.9,-3.1Z"
        elif kind == "heart":
            path = "M0,8 C-12,-1 -8,-11 0,-5 C8,-11 12,-1 0,8Z"
        elif kind == "leaf":
            path = "M0,-10 C7,-4 7,4 0,10 C-7,4 -7,-4 0,-10Z M0,-10 L0,10"
        elif kind == "confetti":
            path = random.choice(["M-6,-2 h12 v4 h-12Z", "M0,-6 A6,6 0 1,1 -0.1,-6Z", "M0,-7 L6,5 -6,5Z"])
        else:
            path = "M0,-5 A5,5 0 1,1 -0.1,-5Z"
        out.append(f'<path d="{path}" fill="{col}" opacity="{op:.2f}" transform="translate({x:.0f},{y:.0f}) rotate({r:.0f}) scale({s/20:.2f})"/>')
    return f'<svg class="abs" style="left:0;top:0;z-index:0" width="{W}" height="{H}">{"".join(out)}</svg>'

def pills_html(pills, t, fs, pad, bg=None, fg=None, gap=None, border=None):
    gap = gap or fs * .6
    items = "".join(f'<span class="pill" style="font-size:{fs}px;padding:{pad*.55:.0f}px {pad:.0f}px;background:{bg or "#fff"};color:{fg or t["ink"]};{("border:" + border) if border else ""};box-shadow:0 6px 14px rgba(0,0,0,.10)">{esc(p)}</span>' for p in pills)
    return f'<div style="display:flex;gap:{gap:.0f}px;justify-content:center;flex-wrap:nowrap">{items}</div>'

def split_badge(b):
    parts = str(b or "").split(None, 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")

# ---------------------------------------------------------------- style 1: contents collage + count badge
def style1(c, t, W, H, pin):
    pages = c["pages"]
    # tiled wall of real pages, edge to edge, slightly overlapping and tilted
    cols = 3 if pin else 5
    tw = W / cols * 1.04; th = tw * 1.294
    rows = int(H / (th * .92)) + 2
    tiles = []
    random.seed(11)
    idx = 0
    for r in range(rows):
        for k in range(cols + 1):
            x = k * tw * .97 - tw * .28 + (tw * .22 if r % 2 else 0)
            y = r * th * .9 - th * .18 + (H * .2 if pin else H * .16)
            rot = random.uniform(-3.5, 3.5)
            tiles.append(page(pages[idx % len(pages)], x, y, tw * .94, th * .94, rot, 1 + (idx % 3)))
            idx += 1
    banner_h = H * (.34 if pin else .30)
    title = esc(c.get("hook") if pin and c.get("hook") else c["title"])
    tfs = W * (.095 if pin else .062)
    sub = esc(c.get("subtitle", ""))
    n, lab = split_badge(c.get("badge"))
    bd = W * (.30 if pin else .19)
    badge = ""
    if n:
        badge = f'''<div class="abs" style="z-index:30;width:{bd}px;height:{bd}px;right:{W*.04}px;top:{(H*.70) if pin else (banner_h - bd*.32)}px;border-radius:50%;background:{t["a2"]};color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 18px 40px rgba(0,0,0,.35);transform:rotate(-8deg)">
          <div class="abs" style="inset:{bd*.05}px;border-radius:50%;border:{bd*.014}px dashed rgba(255,255,255,.7)"></div>
          <div style="font-family:Gloock;font-size:{bd*.44}px;line-height:.9">{esc(n)}</div>
          <div style="font-family:Outfit;font-weight:700;letter-spacing:.12em;font-size:{bd*.12}px;margin-top:{bd*.03}px">{esc(lab)}</div></div>'''
    pills = c.get("pills") or []
    strip = ""
    if pills:
        strip = f'<div class="abs" style="z-index:25;left:0;right:0;bottom:{H*.035}px">{pills_html(pills[:3], t, W*(.034 if pin else .021), W*(.04 if pin else .026), bg=t["bg"], fg=t["ink"], border=f"{W*.002}px solid {t["a"]}")}</div>'
    return f'''<div class="abs" style="inset:0;background:{t["bg2"]}"></div>{"".join(tiles)}
    <div class="abs" style="inset:0;z-index:5;background:linear-gradient(180deg,rgba(0,0,0,0) 60%,rgba(0,0,0,.18))"></div>
    <div class="abs" style="z-index:20;left:0;top:0;width:{W}px;height:{banner_h}px;background:{t["a"]};box-shadow:0 14px 40px rgba(0,0,0,.35);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 {W*.05}px">
      <div class="noise" style="opacity:.6"></div>
      <div class="abs" style="left:{W*.02}px;right:{W*.02}px;top:{W*.012}px;bottom:{W*.012}px;border:{W*.0025}px solid rgba(255,255,255,.45)"></div>
      <div data-fit="{W*(.86 if pin else .70)}" data-fith="{banner_h*.62}" style="font-family:Gloock;color:#fff;font-size:{tfs}px;line-height:1.02;text-align:center;{'white-space:normal;max-width:%dpx' % (W*.86) if pin else 'white-space:nowrap'};margin-right:{0 if pin else W*.08}px">{title}</div>
      <div data-fit="{W*.80}" style="white-space:nowrap;font-family:Outfit;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:{t["soft"]};font-size:{W*(.03 if pin else .017)}px;margin-top:{H*.018}px;margin-right:{0 if pin else W*.08}px">{sub}</div>
    </div>{badge}{strip}'''

# ---------------------------------------------------------------- style 2: headline + device dashboard
def style2(c, t, W, H, pin):
    pages = cyc(c["pages"], 3)
    words = (c.get("hook") if pin and c.get("hook") else c["title"]).split()
    script = c.get("script") or words[0]
    rest = " ".join(w for w in words if w != script) if c.get("script") else " ".join(words[1:])
    if pin and c.get("hook"):
        script, rest = words[0], " ".join(words[1:])
    benefits = c.get("benefits") or (c.get("pills") or [])[:3]
    pills = c.get("pills") or []
    hs = W * (.12 if pin else .085)
    head = f'''<div class="abs" style="z-index:10;left:0;right:0;top:{H*(.035 if pin else .04)}px;text-align:center">
      <div style="font-family:Hand;color:{t["a"]};font-size:{hs*.95}px;line-height:1;transform:rotate(-3deg)">{esc(script)}</div>
      <div data-fit="{W*.9}" data-fith="{hs*2.3}" style="font-family:Gloock;color:{t["ink"]};font-size:{hs}px;line-height:1.0;margin-top:{-hs*.08}px;{'white-space:normal;padding:0 5%' if pin else 'white-space:nowrap'}">{esc(rest)}</div>
      <div data-fit="{W*.9}" style="white-space:nowrap;font-family:Outfit;font-weight:700;letter-spacing:.06em;color:{t["a2"]};font-size:{W*(.032 if pin else .021)}px;margin-top:{H*.015}px">{" &nbsp;•&nbsp; ".join(esc(b) for b in benefits)}</div></div>'''
    if pin:
        lx, ly, lw = W * .02, H * .47, W * .96
    else:
        lx, ly, lw = W * .21, H * .31, W * .58
    lh = lw * .62
    bez = lw * .025
    laptop = f'''<div class="abs" style="z-index:3;left:{lx}px;top:{ly}px;width:{lw}px;height:{lh}px;background:#2d2b2a;border-radius:{lw*.025}px {lw*.025}px 0 0;padding:{bez}px;box-shadow:0 30px 60px rgba(0,0,0,.25)">
       <div style="width:100%;height:100%;background:#eeebe6;overflow:hidden;display:flex;gap:{lw*.015}px;padding:{lw*.015}px {lw*.015}px 0;align-items:flex-start;justify-content:center">
         <img src="{img_url(pages[0])}" style="width:{(lw-2*bez-lw*.045)/2}px;box-shadow:0 2px 8px rgba(0,0,0,.15)">
         <img src="{img_url(pages[1])}" style="width:{(lw-2*bez-lw*.045)/2}px;box-shadow:0 2px 8px rgba(0,0,0,.15)"></div></div>
       <div class="abs" style="z-index:3;left:{lx-lw*.07}px;top:{ly+lh}px;width:{lw*1.14}px;height:{lw*.035}px;background:linear-gradient(#d9d6d2,#a9a5a0);border-radius:0 0 {lw*.04}px {lw*.04}px;box-shadow:0 24px 40px rgba(0,0,0,.28)"></div>'''
    tw = W * (.30 if pin else .17); th = tw * 1.36
    tx = lx - tw * (.18 if pin else .55); ty = ly + lh - th * (.55 if pin else .62)
    tablet = f'''<div class="abs" style="z-index:5;left:{tx}px;top:{ty}px;width:{tw}px;height:{th}px;background:#232221;border-radius:{tw*.07}px;padding:{tw*.045}px;box-shadow:0 30px 60px rgba(0,0,0,.33);transform:rotate(-4deg)">
       <div style="width:100%;height:100%;border-radius:{tw*.025}px;overflow:hidden;background:#fff"><img src="{img_url(pages[2])}" style="width:100%;height:100%;object-fit:cover;object-position:top"></div></div>'''
    pw = W * (.17 if pin else .09); ph = pw * 2.05
    px = lx + lw - pw * (.6 if pin else .2); py = ly + lh - ph * (.6 if pin else .72)
    phone = f'''<div class="abs" style="z-index:6;left:{px}px;top:{py}px;width:{pw}px;height:{ph}px;background:#232221;border-radius:{pw*.16}px;padding:{pw*.06}px;box-shadow:0 26px 50px rgba(0,0,0,.35);transform:rotate(5deg)">
       <div style="width:100%;height:100%;border-radius:{pw*.11}px;overflow:hidden;background:#fff"><img src="{img_url(pages[0])}" style="width:250%;margin-left:-6%;object-fit:cover"></div></div>'''
    strip = ""
    if pills:
        strip = f'<div class="abs" style="z-index:9;left:0;right:0;bottom:{H*.04}px">{pills_html(pills[:3], t, W*(.03 if pin else .021), W*(.035 if pin else .024), bg=t["a"], fg="#fff")}</div>'
    bg = f'''<div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 70%, {t["soft"]} 0%, {t["bg"]} 55%, {t["bg2"]} 100%)"></div><div class="noise" style="opacity:.5"></div>
    <div class="abs" style="left:{-W*.1}px;right:{-W*.1}px;bottom:0;height:{H*.24}px;background:{t["bg2"]};border-radius:50% 50% 0 0/30% 30% 0 0"></div>'''
    return bg + head + laptop + tablet + phone + strip

# ---------------------------------------------------------------- style 3: clean tablet on linen
def style3(c, t, W, H, pin):
    pages = cyc(c["pages"], 2)
    linen = f'<div class="abs" style="inset:0;background:{LINEN},linear-gradient(135deg,{t["bg"]},{t["bg2"]})"></div><div class="abs" style="inset:0;background:radial-gradient(ellipse at 40% 40%,rgba(255,255,255,.35),rgba(0,0,0,.10) 100%)"></div>'
    title = esc(c.get("hook") if pin and c.get("hook") else c["title"])
    if pin:
        tw, th = W * .74, W * .74 * 1.36
        tx, ty, rot = W * .13, H * .315, -2.5
    else:
        tw, th = W * .80, W * .80 * .72
        tx, ty, rot = W * .03, H * .265, -2
    bez = tw * .035
    sh = th - 2 * bez
    tab = f'''<div class="abs" style="z-index:3;left:{tx}px;top:{ty}px;width:{tw}px;height:{th}px;background:linear-gradient(145deg,#3a3836,#1f1e1d);border-radius:{tw*.045}px;padding:{bez}px;transform:rotate({rot}deg);box-shadow:0 3px 4px rgba(0,0,0,.25),{tw*.02}px {tw*.04}px {tw*.07}px rgba(50,35,20,.35)">
      <div style="width:100%;height:100%;border-radius:{tw*.015}px;overflow:hidden;background:#ece8e2;display:flex;gap:{tw*.012}px;align-items:center;justify-content:center">
        <img src="{img_url(pages[0])}" style="{('width:100%;height:100%;object-fit:cover;object-position:top') if pin else ('height:%dpx;box-shadow:0 2px 10px rgba(0,0,0,.18)' % (sh*.96))}">
        {'' if pin else f'<img src="{img_url(pages[1])}" style="height:{sh*.96}px;box-shadow:0 2px 10px rgba(0,0,0,.18)">'}</div>
      <div class="abs" style="inset:{bez}px;border-radius:{tw*.015}px;background:linear-gradient(115deg,rgba(255,255,255,.16) 0%,rgba(255,255,255,0) 35%)"></div></div>'''
    sl = W * (.62 if pin else .40)
    sx = tx + tw * (.98 if pin else .82); sy = ty + th * (.35 if pin else .55)
    stylus = f'''<div class="abs" style="z-index:4;left:{sx}px;top:{sy}px;width:{sl}px;height:{sl*.045}px;transform:rotate({100 if pin else 62}deg);transform-origin:0 50%;border-radius:{sl*.03}px;background:linear-gradient(180deg,#fbfaf8,#d9d6d1);box-shadow:{sl*.02}px {sl*.03}px {sl*.04}px rgba(50,35,20,.35)">
       <div class="abs" style="right:-{sl*.06}px;top:0;width:{sl*.07}px;height:100%;background:linear-gradient(180deg,#e9e7e3,#bdb9b3);clip-path:polygon(0 0,100% 40%,100% 60%,0 100%)"></div></div>'''
    leaf = ""
    if not pin:
        leaf = f'<svg class="abs" style="z-index:2;right:{-W*.03}px;bottom:{-H*.04}px;opacity:.85" width="{W*.22}" height="{W*.22}" viewBox="0 0 100 100"><path d="M10 95 C40 70 60 40 92 8" stroke="{t["a"]}" stroke-width="1.6" fill="none"/>' + "".join(f'<path d="M0 0 C6 -6 16 -6 22 0 C16 6 6 6 0 0Z" fill="{t["a"]}" opacity=".75" transform="translate({10+i*9},{95-i*9.5}) rotate({-40 + (50 if i%2 else -40)})"/>' for i in range(9)) + "</svg>"
    if pin:
        txt = f'''<div class="abs" style="z-index:6;left:{W*.06}px;right:{W*.06}px;top:{H*.05}px;text-align:center">
          <div style="font-family:Outfit;font-weight:700;letter-spacing:.3em;font-size:{W*.03}px;color:{t["a"]};text-transform:uppercase">{esc(c.get("kicker","Digital Planner"))}</div>
          <div data-fit="{W*.88}" data-fith="{H*.24}" style="font-family:Gloock;font-size:{W*.105}px;line-height:1.04;color:{t["ink"]};margin-top:{H*.02}px">{title}</div></div>'''
    else:
        txt = f'''<div class="abs" style="z-index:6;left:{W*.04}px;top:{H*.045}px;width:{W*.92}px">
          <div style="font-family:Outfit;font-weight:700;letter-spacing:.3em;font-size:{W*.014}px;color:{t["a"]};text-transform:uppercase">{esc(c.get("kicker","Digital Planner"))}</div>
          <div data-fit="{W*.92}" data-fith="{H*.14}" style="font-family:Gloock;font-size:{W*.06}px;line-height:1.04;color:{t["ink"]};margin-top:{H*.01}px;white-space:nowrap">{title}</div></div>
          <div class="abs" style="z-index:6;left:{W*.04}px;top:{H*.205}px;font-family:Lora;font-style:italic;font-size:{W*.022}px;color:{t["ink"]};opacity:.85;white-space:nowrap">{esc(c.get("subtitle",""))}</div>'''
    return linen + leaf + tab + stylus + txt

# ---------------------------------------------------------------- style 4: hero page close-up
def style4(c, t, W, H, pin):
    pages = c["pages"]
    bg = f'<div class="abs" style="inset:0;background:radial-gradient(ellipse at 35% 55%,{t["soft"]} 0%,{t["bg2"]} 75%)"></div><div class="noise" style="opacity:.45"></div>'
    title = esc(c.get("hook") if pin and c.get("hook") else c["title"])
    if pin:
        ph = H * .70; pw = ph / 1.294
        x, y = (W - pw) / 2 + W * .04, H * .345
        hero = page(pages[0], x, y, pw, ph, 2.5, 4)
        back = page(pages[1 % len(pages)], x - W * .2, y + H * .03, pw * .9, ph * .9, -7, 2)
        mot = motif_svg(t, W, H, 22, 5, (0, H * .28, W, H), (24, 52))
        txt = f'''<div class="abs" style="z-index:6;left:{W*.05}px;right:{W*.05}px;top:{H*.04}px;text-align:center">
          <div data-fit="{W*.9}" data-fith="{H*.22}" style="font-family:Young;font-size:{W*.1}px;line-height:1.06;color:{t["a"]};white-space:normal">{title}</div>
          <div data-fit="{W*.8}" style="white-space:nowrap;display:inline-block;margin-top:{H*.015}px;background:{t["a2"]};color:#fff;font-family:Outfit;font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:{W*.03}px;padding:{W*.012}px {W*.035}px;border-radius:999px">{esc(c.get("subtitle","Printable"))}</div></div>'''
        return bg + mot + back + hero + txt
    ph = H * 1.08; pw = ph / 1.294
    x, y = W * .06, H * .03
    hero = page(pages[0], x, y, pw, ph, -3, 4)
    back = page(pages[1 % len(pages)], x + pw * .62, y + H * .1, pw * .85, ph * .85, 5, 2)
    mot = motif_svg(t, W, H, 26, 6, (W * .5, 0, W, H), (30, 70))
    pills = c.get("pills") or []
    pl = "".join(f'<div style="display:flex;align-items:center;gap:{W*.01}px;font-family:Outfit;font-weight:700;font-size:{W*.022}px;color:{t["ink"]};margin-top:{H*.022}px"><span style="width:{W*.016}px;height:{W*.016}px;border-radius:50%;background:{t["a2"]};display:inline-block"></span>{esc(p)}</div>' for p in pills[:3])
    panel = f'''<div class="abs" style="z-index:6;right:{W*.04}px;top:{H*.1}px;width:{W*.42}px;padding:{W*.035}px {W*.035}px;background:#fffdfb;border-radius:{W*.012}px;box-shadow:0 20px 50px rgba(0,0,0,.15);border-top:{W*.008}px solid {t["a"]}">
        <div style="font-family:Outfit;font-weight:700;letter-spacing:.28em;font-size:{W*.015}px;color:{t["a2"]};text-transform:uppercase">{esc(c.get("subtitle","Printable"))}</div>
        <div data-fit="{W*.35}" data-fith="{H*.42}" style="font-family:Young;font-size:{W*.058}px;line-height:1.05;color:{t["a"]};margin-top:{H*.015}px;white-space:normal">{title}</div>
        {pl}</div>'''
    return bg + mot + back + hero + panel

# ---------------------------------------------------------------- style 5: bright month grid
def style5(c, t, W, H, pin):
    multi = t.get("multi") or [t["a"], t["a2"], t["gold"], t["a"], t["a2"], t["gold"]]
    cols, rows = (2, 3) if pin else (4, 2)
    n = cols * rows
    pages = cyc(c["pages"], n)
    top = H * (.30 if pin else .27)
    gx, gy = W * .035, H * .025
    cw = (W - gx * (cols + 1)) / cols
    chh = (H - top - gy * (rows + .4)) / rows
    cells = []
    for i, p in enumerate(pages):
        r, k = divmod(i, cols)
        x = gx + k * (cw + gx); y = top + gy * .6 + r * (chh + gy)
        col = multi[i % len(multi)]
        rot = [-1.5, 1, -0.5, 1.5, 0.8, -1.2, 1.2, -0.8][i % 8]
        cells.append(f'''<div class="abs" style="z-index:3;left:{x}px;top:{y}px;width:{cw}px;height:{chh}px;transform:rotate({rot}deg);background:#fff;border-radius:{W*.008}px;overflow:hidden;box-shadow:0 10px 26px rgba(0,0,0,.16),0 2px 4px rgba(0,0,0,.12)">
          <div style="height:{W*.012}px;background:{col}"></div>
          <img src="{img_url(p)}" style="width:100%;height:calc(100% - {W*.012}px);object-fit:cover;object-position:top"></div>''')
    title = esc(c.get("hook") if pin and c.get("hook") else c["title"])
    year = esc(c.get("year", ""))
    dots = "".join(f'<span style="display:inline-block;width:{W*.018}px;height:{W*.018}px;border-radius:50%;background:{m};margin:0 {W*.005}px"></span>' for m in multi[:6])
    yfs = W * (.2 if pin else .13)
    head = f'''<div class="abs" style="z-index:5;left:0;top:0;width:{W}px;height:{top}px;display:flex;align-items:center;justify-content:center;gap:{W*.03}px;padding:0 {W*.04}px">
       {f'<div style="font-family:Brico;font-weight:700;font-size:{yfs}px;line-height:.85;color:{multi[0]};letter-spacing:-.03em">{year}</div>' if year and not pin else ''}
       <div style="text-align:{'center' if pin else 'left'}">
         {f'<div style="font-family:Brico;font-weight:700;font-size:{W*.12}px;line-height:.9;color:{multi[0]};letter-spacing:-.03em">{year}</div>' if year and pin else ''}
         <div data-fit="{W*(.9 if pin else .62)}" data-fith="{top*(.42 if pin and year else .62)}" style="font-family:Brico;font-weight:700;font-size:{W*(.085 if pin else .056)}px;line-height:1.0;color:{t["ink"]};white-space:normal;max-width:{W*(.9 if pin else .62)}px">{title}</div>
         <div style="margin-top:{H*.014}px;display:flex;align-items:center;gap:{W*.012}px;justify-content:{'center' if pin else 'flex-start'}">{dots}<span style="white-space:nowrap;font-family:Outfit;font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:{W*(.026 if pin else .016)}px;color:{t["ink"]};opacity:.75;margin-left:{W*.01}px">{esc(c.get("subtitle",""))}</span></div>
       </div></div>'''
    bg = f'<div class="abs" style="inset:0;background:{t["bg"]}"></div><div class="abs" style="left:0;right:0;top:{top}px;bottom:0;background:{t["bg2"]}"></div>' + motif_svg(t, W, top, 30, 9, None, (16, 34)).replace("z-index:0", "z-index:1;opacity:.6")
    return bg + head + "".join(cells)

# ---------------------------------------------------------------- style 6: warm desk flat-lay / framed prints
WOOD = """repeating-linear-gradient(90deg, rgba(0,0,0,.09) 0 3px, transparent 3px 390px),
  repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 2px, transparent 2px 23px),
  repeating-linear-gradient(90deg, rgba(0,0,0,.025) 0 1px, transparent 1px 11px),
  linear-gradient(90deg,#a06b44 0%,#b07a50 18%,#9c6741 33%,#b47e53 50%,#a36d45 66%,#b27c51 82%,#9d6842 100%)"""

def sprig(x, y, s, rot, col="#4f6b45"):
    leaves = "".join(f'<path d="M0 0 C6 -7 16 -7 24 0 C16 7 6 7 0 0Z" fill="{col}" transform="translate({8+i*10},{50 - (6 if i%2 else -6)}) rotate({-35 if i%2 else 35})"/>' for i in range(9))
    return f'<svg class="abs" style="z-index:7;left:{x}px;top:{y}px;transform:rotate({rot}deg);filter:drop-shadow(6px 10px 8px rgba(40,20,5,.35))" width="{s}" height="{s*.4}" viewBox="0 0 110 100"><path d="M0 50 L108 50" stroke="#6b4a2c" stroke-width="2.4"/>{leaves}</svg>'

def pencil(x, y, L, rot):
    return f'''<div class="abs" style="z-index:7;left:{x}px;top:{y}px;width:{L}px;height:{L*.05}px;transform:rotate({rot}deg);transform-origin:0 50%;filter:drop-shadow({L*.015}px {L*.025}px {L*.02}px rgba(40,20,5,.4))">
      <div class="abs" style="left:0;top:0;width:{L*.08}px;height:100%;background:#d9a3a3;border-radius:{L*.02}px 0 0 {L*.02}px"></div>
      <div class="abs" style="left:{L*.08}px;top:0;width:{L*.05}px;height:100%;background:linear-gradient(#e2e2e2,#9c9c9c)"></div>
      <div class="abs" style="left:{L*.13}px;top:0;width:{L*.75}px;height:100%;background:linear-gradient(#f2c94c,#d9a92e 55%,#c48f1f)"></div>
      <div class="abs" style="left:{L*.88}px;top:0;width:{L*.12}px;height:100%;background:linear-gradient(90deg,#efd6b0,#e5c49a 70%,#333 70%);clip-path:polygon(0 0,100% 45%,100% 55%,0 100%)"></div></div>'''

def style6(c, t, W, H, pin):
    pages = c["pages"]
    title = esc(c.get("hook") if pin and c.get("hook") else c["title"])
    if c.get("variant") == "frame":
        wall = f'<div class="abs" style="inset:0;background:linear-gradient(180deg,{t["soft"]},{t["bg"]})"></div><div class="noise" style="opacity:.5"></div>'
        def frame(p, x, y, w, rot=0, z=3):
            h = w * 1.25; fr = w * .045; mat = w * .09
            return f'''<div class="abs" style="z-index:{z};left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);padding:{fr}px;background:linear-gradient(135deg,#e8d3b3,#c9a97f 50%,#b8966c);box-shadow:0 4px 6px rgba(0,0,0,.18),{w*.03}px {w*.06}px {w*.1}px rgba(60,35,25,.3)">
              <div style="width:100%;height:100%;background:#fdfbf8;padding:{mat}px;box-shadow:inset 0 2px 6px rgba(0,0,0,.18)">
                <div style="width:100%;height:100%;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(0,0,0,.06)"><img src="{img_url(p)}" style="width:100%;height:100%;object-fit:cover"></div></div></div>'''
        ps = cyc(pages, 3)
        if pin:
            out = wall + frame(ps[0], W * .2, H * .36, W * .6, 0, 4) + frame(ps[1], W * .03, H * .52, W * .36, 0, 3) + frame(ps[2], W * .61, H * .52, W * .36, 0, 3)
            out += f'<div class="abs" style="z-index:2;left:0;right:0;bottom:0;height:{H*.12}px;background:linear-gradient(180deg,#e9dccb,#d8c6ae);box-shadow:0 -8px 20px rgba(0,0,0,.08)"></div>'
            out += sprig(W * .62, H * .87, W * .4, -12, t["a2"] if t["motif"] == "leaf" else "#5d7a55")
            out += f'''<div class="abs" style="z-index:6;left:{W*.05}px;right:{W*.05}px;top:{H*.045}px;text-align:center">
              <div data-fit="{W*.9}" data-fith="{H*.21}" style="font-family:Lora;font-style:italic;font-weight:700;font-size:{W*.1}px;line-height:1.08;color:{t["a"]};white-space:normal">{title}</div>
              <div style="font-family:Outfit;font-weight:700;letter-spacing:.2em;text-transform:uppercase;font-size:{W*.028}px;color:{t["ink"]};margin-top:{H*.015}px">{esc(c.get("subtitle",""))}</div></div>'''
            return out
        fw = W * .26
        out = wall + frame(ps[0], W * .37, H * .26, fw * 1.05, 0, 4) + frame(ps[1], W * .07, H * .36, fw * .8, 0, 3) + frame(ps[2], W * .72, H * .36, fw * .8, 0, 3)
        out += f'<div class="abs" style="z-index:2;left:0;right:0;bottom:0;height:{H*.12}px;background:linear-gradient(180deg,#e9dccb,#d8c6ae)"></div>'
        out += sprig(W * .02, H * .86, W * .2, -8, "#5d7a55") + sprig(W * .8, H * .87, W * .19, 10, "#5d7a55")
        out += f'''<div class="abs" style="z-index:6;left:0;right:0;top:{H*.04}px;text-align:center">
          <div data-fit="{W*.9}" style="font-family:Lora;font-style:italic;font-weight:700;font-size:{W*.055}px;line-height:1.05;color:{t["a"]};white-space:nowrap">{title}</div>
          <div style="font-family:Outfit;font-weight:700;letter-spacing:.2em;text-transform:uppercase;font-size:{W*.017}px;color:{t["ink"]};margin-top:{H*.012}px">{esc(c.get("subtitle",""))}</div></div>'''
        return out
    wood = f'<div class="abs" style="inset:0;background:{WOOD}"></div><div class="abs" style="inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 55%,rgba(40,20,5,.35) 100%)"></div>'
    ps = cyc(pages, 3)
    if pin:
        ph = H * .56; pw = ph / 1.294
        out = wood + page(ps[1], W * .02, H * .40, pw * .92, ph * .92, -8, 2) + page(ps[2], W * .38, H * .43, pw * .92, ph * .92, 7, 2) + page(ps[0], (W - pw) / 2, H * .37, pw, ph, -1.5, 4)
        out += pencil(W * .12, H * .96, W * .7, -6) + sprig(W * .62, H * .3, W * .42, 30)
        out += f'''<div class="abs" style="z-index:8;left:{W*.06}px;right:{W*.06}px;top:{H*.04}px;padding:{H*.03}px {W*.05}px;background:{t["bg"]};box-shadow:0 18px 40px rgba(40,20,5,.35);transform:rotate(-1deg);text-align:center">
          <div class="noise" style="opacity:.7"></div>
          <div data-fit="{W*.78}" data-fith="{H*.2}" style="position:relative;font-family:Gloock;font-size:{W*.095}px;line-height:1.05;color:{t["a"]};white-space:normal">{title}</div>
          <div style="position:relative;font-family:Outfit;font-weight:700;letter-spacing:.16em;text-transform:uppercase;font-size:{W*.027}px;color:{t["ink"]};margin-top:{H*.012}px">{esc(c.get("subtitle",""))}</div></div>'''
        return out
    ph = H * .86; pw = ph / 1.294
    out = wood + page(ps[1], W * .05, H * .12, pw * .9, ph * .9, -6, 2) + page(ps[2], W * .54, H * .1, pw * .9, ph * .9, 5, 2) + page(ps[0], W * .29, H * .07, pw, ph, -1, 4)
    out += pencil(W * .6, H * .93, W * .3, -10) + sprig(W * .76, H * .02, W * .25, 25) + sprig(-W * .02, H * .8, W * .22, -20)
    out += f'''<div class="abs" style="z-index:8;left:{W*.6}px;top:{H*.32}px;width:{W*.36}px;padding:{H*.04}px {W*.025}px;background:{t["bg"]};box-shadow:0 18px 40px rgba(40,20,5,.35);transform:rotate(2deg);text-align:center">
       <div class="noise" style="opacity:.7"></div>
       <div data-fit="{W*.31}" data-fith="{H*.3}" style="position:relative;font-family:Gloock;font-size:{W*.05}px;line-height:1.05;color:{t["a"]};white-space:normal">{title}</div>
       <div style="position:relative;font-family:Outfit;font-weight:700;letter-spacing:.16em;text-transform:uppercase;font-size:{W*.014}px;color:{t["ink"]};margin-top:{H*.015}px">{esc(c.get("subtitle",""))}</div></div>'''
    return out

STYLES = {1: style1, 2: style2, 3: style3, 4: style4, 5: style5, 6: style6}

def build_html(c):
    pin = c.get("size") == "pin"
    W, H = (1000, 1500) if pin else (2400, 1800)
    t = dict(THEMES[c.get("theme", "linen")])
    body = STYLES[int(c["style"])](c, t, W, H, pin)
    css = font_css() + BASE % dict(W=W, H=H, NOISE=NOISE) + f":root{{--ink:{t['ink']};--bg:{t['bg']}}}"
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{body}<script>document.fonts.ready.then(()=>{{{FIT_JS};document.body.dataset.ready=1}})</script></body></html>', W, H, pin

def render(configs):
    outs = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        for c in configs:
            doc, W, H, pin = build_html(c)
            ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=(1.5 if pin else 1))
            pg = ctx.new_page()
            fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(os.path.abspath(c["out"])) if os.environ.get("CS_KEEP") else None)
            with os.fdopen(fd, "w") as f: f.write(doc)
            pg.goto("file://" + tmp); pg.wait_for_selector("body[data-ready]", timeout=15000); pg.wait_for_timeout(250)
            png = tmp[:-5] + ".png"; pg.screenshot(path=png); ctx.close()
            im = Image.open(png).convert("RGB")
            size, q = ((1000, 1500), 88) if pin else ((2000, 1500), 86)
            im = im.resize(size, Image.LANCZOS)
            os.makedirs(os.path.dirname(os.path.abspath(c["out"])), exist_ok=True)
            im.save(c["out"], "JPEG", quality=q, optimize=True, progressive=True)
            os.remove(png); os.remove(tmp)
            outs.append(c["out"]); print(c["out"])
        b.close()
    return outs

if __name__ == "__main__":
    data = json.load(open(sys.argv[1]))
    render(data if isinstance(data, list) else [data])
