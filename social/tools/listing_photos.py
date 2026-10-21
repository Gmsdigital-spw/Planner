"""Warm listing photos from real product pages. Usage: python3 listing_lib.py spec.json"""
import os, sys, json
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

SPEC = json.load(open(sys.argv[1]))
PD = SPEC["pdf"]
P = lambda n: f"file://{PD}/hi-{n:02d}.png"
OUT = SPEC["out"]; os.makedirs(OUT, exist_ok=True)
A = SPEC.get("accent", "#b0522c")
PROPS = SPEC.get("props", "autumn")
W, H = 2000, 1600

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:%dpx;height:%dpx;overflow:hidden;position:relative;font-family:Inter,sans-serif;color:#2b211b}
.wood{position:absolute;inset:0;background:
  repeating-linear-gradient(90deg, rgba(0,0,0,.10) 0 3px, transparent 3px 330px),
  repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 2px, transparent 2px 23px),
  repeating-linear-gradient(90deg, rgba(0,0,0,.025) 0 1px, transparent 1px 11px),
  linear-gradient(90deg,#a06b44 0%%,#b07a50 18%%,#9c6741 33%%,#b47e53 50%%,#a36d45 66%%,#b27c51 82%%,#9d6842 100%%);}
.vign{position:absolute;inset:0;background:radial-gradient(ellipse at 50%% 45%%, transparent 55%%, rgba(40,20,5,.38) 100%%);z-index:20}
.light{position:absolute;inset:0;background:linear-gradient(125deg, rgba(255,236,200,.20) 0%%, transparent 45%%);z-index:21}
.sheet{position:absolute;background:#fff;box-shadow:0 26px 50px rgba(40,20,5,.38),0 4px 10px rgba(40,20,5,.25)}
.sheet img{width:100%%;display:block}
.crop{position:absolute;overflow:hidden;background:#fff;box-shadow:0 26px 50px rgba(40,20,5,.38),0 4px 10px rgba(40,20,5,.25)}
.crop img{position:absolute;display:block}
.mug{position:absolute;width:380px;height:380px;border-radius:50%%;background:#e9e1d3;box-shadow:0 30px 50px rgba(40,20,5,.45);z-index:10}
.mug:before{content:"";position:absolute;inset:42px;border-radius:50%%;background:radial-gradient(circle at 45%% 40%%,#7a4a2c,#5a321c)}
.pen{position:absolute;width:640px;height:26px;border-radius:13px;background:linear-gradient(#3b2b22,#1f1712);box-shadow:0 12px 18px rgba(40,20,5,.4);z-index:9}
.pen:after{content:"";position:absolute;right:-34px;top:4px;border-left:40px solid #c9b48f;border-top:9px solid transparent;border-bottom:9px solid transparent}
.leaf{position:absolute;width:160px;height:160px;border-radius:0 80%% 0 80%%;z-index:8;box-shadow:0 8px 14px rgba(40,20,5,.3)}
.card{position:absolute;background:#f6efe2;border-radius:10px;box-shadow:0 26px 50px rgba(40,20,5,.35);z-index:12;
  background-image:radial-gradient(rgba(120,90,60,.10) 1.4px, transparent 1.6px);background-size:22px 22px}
.tape{position:absolute;width:220px;height:62px;background:rgba(232,214,178,.88);top:-26px}
.kick{font-weight:700;letter-spacing:.3em;font-size:30px;text-transform:uppercase;color:ACCENT}
h1{font-family:Lora,serif;font-weight:700;font-size:96px;line-height:1.0;color:#2b211b}
h1 i{color:ACCENT}
.sub{font-family:Lora,serif;font-style:italic;font-size:44px;line-height:1.3;color:#5a4636}
.li{font-size:40px;line-height:1.55;color:#3a2c22}
.li b{color:ACCENT}
.chip{display:inline-block;border:4px solid #d8c4a2;border-radius:60px;padding:14px 34px;font-size:34px;font-weight:500;margin:0 14px 14px 0;background:#f8f2e6}
""".replace("ACCENT", A) % (W, H)

def leaf(x, y, r, c): return f'<div class="leaf" style="left:{x}px;top:{y}px;transform:rotate({r}deg);background:{c}"></div>'
def sheet(n, x, y, w, rot, z=5): return f'<div class="sheet" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg);z-index:{z}"><img src="{P(n)}"></div>'
def crop(n, x, y, w, h, iw, ix, iy, rot, z=5):
    return f'<div class="crop" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);z-index:{z}"><img src="{P(n)}" style="width:{iw}px;left:{ix}px;top:{iy}px"></div>'
def card(x, y, w, h, rot, inner):
    return f'<div class="card" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)"><div class="tape" style="left:60px;transform:rotate(-3deg)"></div><div class="tape" style="right:60px;transform:rotate(2deg)"></div><div style="padding:90px 80px">{inner}</div></div>'

def pine(x, y, r):
    needles = "".join(f'<line x1="{i}" y1="60" x2="{i+28}" y2="{8 if k%2 else 112}" stroke="#3f6b46" stroke-width="7" stroke-linecap="round"/>' for k, i in enumerate(range(10, 400, 16)))
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;transform:rotate({r}deg);z-index:8;filter:drop-shadow(0 8px 8px rgba(40,20,5,.35))">'
            f'<svg width="420" height="120" viewBox="0 0 420 120"><line x1="0" y1="60" x2="410" y2="60" stroke="#5b3d26" stroke-width="8"/>{needles}'
            '<circle cx="392" cy="48" r="14" fill="#b3302b"/><circle cx="404" cy="74" r="13" fill="#c43a33"/></svg></div>')

def deco(pos):
    if PROPS == "none": return ""
    if PROPS == "autumn":
        return {"a": leaf(1800, 1380, 40, "#b5532b") + leaf(-30, 40, 10, "#c98a2e"), "b": leaf(1820, 40, -20, "#c98a2e"), "c": leaf(1850, 1400, 60, "#8f3f22")}[pos]
    return {"a": pine(1620, 1460, -25) + pine(-150, 30, 20), "b": pine(1640, 10, 15), "c": pine(1640, 1470, -20)}[pos]

def hero(t):
    return crop(t["page"], 880, 110, 1040, 1380, t.get("iw", 1340), t.get("ix", -40), t.get("iy", -60), 1.5) + \
      card(90, 230, 820, 1100, -2, f'<div class="kick">{t["kick"]}</div><h1 style="margin-top:40px">{t["title"]}</h1>'
           f'<div class="sub" style="margin-top:44px">{t["sub"]}</div><div class="li" style="margin-top:44px">{t["line"]}</div>') + deco("a")
def inside(t):
    rots = [-3, 2, -1.5, 2.5, -2, 1.5, -2.5, 2]
    return "".join(sheet(n, 170 + (i % 4) * 430, 90 + (i // 4) * 520, 370, rots[i], 3 + i) for i, n in enumerate(t["pages"][:8])) + \
      card(640, 1200, 720, 300, 0, f'<div style="margin-top:-30px;text-align:center"><div class="kick">What\'s included</div><h1 style="font-size:84px;margin-top:20px">{t["title"]}</h1></div>')
def trio(t):
    a, b, c = t["pages"]
    return sheet(a, 90, 200, 820, -3, 4) + sheet(b, 640, 260, 820, 2, 5) + sheet(c, 1160, 180, 760, -1.5, 6) + \
      card(500, 1130, 1000, 330, 1, f'<div style="margin-top:-30px;text-align:center"><div class="kick">{t["kick"]}</div><div class="li" style="margin-top:18px">{t["line"]}</div></div>') + deco("b")
def duo(t):
    a, b = t["pages"]
    return sheet(a, 160, 160, 900, -2.5, 4) + sheet(b, 960, 120, 900, 2, 5) + '<div class="mug" style="left:1650px;top:1240px"></div>' + \
      card(140, 1150, 1180, 330, -1, f'<div style="margin-top:-30px"><div class="kick">{t["kick"]}</div><div class="li" style="margin-top:18px">{t["line"]}</div></div>')
def howto(t):
    steps = "<br>".join(f"<b>{i+1}.</b> {x}" for i, x in enumerate(t["steps"]))
    chips = "".join(f'<span class="chip">{c}</span>' for c in t["chips"])
    return sheet(1, 1150, 170, 700, 6, 5) + sheet(t["page"], 1080, 230, 700, 1, 4) + '<div class="pen" style="left:1180px;top:1430px;transform:rotate(-10deg)"></div>' + \
      card(110, 230, 900, 1060, -1.5, f'<div class="kick">How it works</div><h1 style="margin-top:36px;font-size:84px">Instant <i>download</i></h1>'
           f'<div class="li" style="margin-top:50px">{steps}</div><div style="margin-top:56px">{chips}</div>') + deco("c")

def cover(t):  # fanned landscape/portrait pages + title card (for a new main photo)
    pg = t["pages"]; w = t.get("w", 1000)
    out = "".join(sheet(n, 860 + i*60, 200 + i*120, w, [-6, -2, 3, 7][i], 3+i) for i, n in enumerate(pg[:4]))
    chips = "".join(f'<span class="chip">{c}</span>' for c in t.get("chips", []))
    return out + card(110, 260, 860, 1060, -2, f'<div class="kick">{t["kick"]}</div><h1 style="margin-top:40px;font-size:110px">{t["title"]}</h1>'
        f'<div class="sub" style="margin-top:40px">{t["sub"]}</div><div style="margin-top:50px">{chips}</div>') + deco("a")
def screen(t):  # spreadsheet screenshot on a tablet
    img = t["img"]
    return (f'<div style="position:absolute;left:{t.get("x",860)}px;top:{t.get("y",230)}px;width:{t.get("w",1060)}px;background:#2b2420;border-radius:46px;padding:30px;'
            f'box-shadow:0 40px 70px rgba(40,20,5,.45);transform:rotate(1.5deg);z-index:6"><div style="background:#fff;border-radius:18px;overflow:hidden">'
            f'<img src="file://{img}" style="width:100%;display:block"></div></div>') + \
      card(90, 260, 800, 1060, -2, f'<div class="kick">{t["kick"]}</div><h1 style="margin-top:40px">{t["title"]}</h1>'
           f'<div class="sub" style="margin-top:44px">{t["sub"]}</div><div class="li" style="margin-top:44px">{t["line"]}</div>') + \
      '<div class="mug" style="left:1680px;top:1300px"></div>'
def howto2(t):  # how it works without a cover page
    steps = "<br>".join(f"<b>{i+1}.</b> {x}" for i, x in enumerate(t["steps"]))
    chips = "".join(f'<span class="chip">{c}</span>' for c in t["chips"])
    side = (sheet(t["page"], 1080, 300, t.get("w", 760), 4, 4)) if "page" in t else \
      (f'<div style="position:absolute;left:1060px;top:330px;width:820px;background:#2b2420;border-radius:40px;padding:26px;box-shadow:0 40px 70px rgba(40,20,5,.45);transform:rotate(3deg);z-index:6">'
       f'<div style="background:#fff;border-radius:16px;overflow:hidden"><img src="file://{t["img"]}" style="width:100%;display:block"></div></div>')
    return side + '<div class="pen" style="left:1180px;top:1430px;transform:rotate(-10deg)"></div>' + \
      card(110, 230, 900, 1060, -1.5, f'<div class="kick">How it works</div><h1 style="margin-top:36px;font-size:84px">{t.get("title","Instant <i>download</i>")}</h1>'
           f'<div class="li" style="margin-top:50px">{steps}</div><div style="margin-top:56px">{chips}</div>') + deco("c")

def land(t):  # one big landscape page + caption card
    return sheet(t["page"], 260, 110, 1480, -1.5, 4) + \
      card(560, 1170, 880, 320, 1, f'<div style="margin-top:-30px;text-align:center"><div class="kick">{t["kick"]}</div><div class="li" style="margin-top:18px">{t["line"]}</div></div>') + deco("b")
T = {"land": land, "cover": cover, "screen": screen, "howto2": howto2, "hero": hero, "inside": inside, "trio": trio, "duo": duo, "howto": howto}

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
    for sc in SPEC["scenes"]:
        body = T[sc["type"]](sc)
        hp = f"{OUT}/{sc['name']}.html"
        open(hp, "w").write(f'<!doctype html><html><head><style>{CSS}</style></head><body><div class="wood"></div>{body}<div class="light"></div><div class="vign"></div></body></html>')
        pg.goto("file://" + hp); pg.wait_for_load_state("load"); pg.wait_for_timeout(250)
        pg.screenshot(path=f"{OUT}/{sc['name']}.jpg", type="jpeg", quality=88)
        print(sc["name"])
    b.close()
