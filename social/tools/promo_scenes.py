import os, sys
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

S = os.environ.get("WORK") or sys.exit("set WORK=<folder with pdf/hi-NN.png pages>")
P = lambda n: f"file://{S}/pdf/hi-{n:02d}.png"
OUT = os.path.join(S, "frames"); os.makedirs(OUT, exist_ok=True)
W, H = 1215, 2160  # 9:16 with zoom headroom

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:%dpx;height:%dpx;overflow:hidden;position:relative;font-family:Inter,sans-serif}
.wood{position:absolute;inset:0;background:
  repeating-linear-gradient(0deg, rgba(0,0,0,.10) 0 3px, transparent 3px 300px),
  repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 2px, transparent 2px 23px),
  repeating-linear-gradient(0deg, rgba(0,0,0,.025) 0 1px, transparent 1px 11px),
  linear-gradient(0deg,#a06b44 0%%,#b07a50 18%%,#9c6741 33%%,#b47e53 50%%,#a36d45 66%%,#b27c51 82%%,#9d6842 100%%);}
.vign{position:absolute;inset:0;background:radial-gradient(ellipse at 50%% 45%%, transparent 50%%, rgba(40,20,5,.40) 100%%);z-index:20;pointer-events:none}
.light{position:absolute;inset:0;background:linear-gradient(125deg, rgba(255,236,200,.22) 0%%, transparent 45%%);z-index:21}
.sheet{position:absolute;background:#fff;box-shadow:0 26px 50px rgba(40,20,5,.38),0 4px 10px rgba(40,20,5,.25)}
.sheet img{width:100%%;display:block}
.mug{position:absolute;width:360px;height:360px;border-radius:50%%;background:#e9e1d3;box-shadow:0 30px 50px rgba(40,20,5,.45);z-index:10}
.mug:before{content:"";position:absolute;inset:40px;border-radius:50%%;background:radial-gradient(circle at 45%% 40%%,#7a4a2c,#5a321c)}
.pen{position:absolute;width:640px;height:26px;border-radius:13px;background:linear-gradient(#3b2b22,#1f1712);box-shadow:0 12px 18px rgba(40,20,5,.4);z-index:9}
.pen:after{content:"";position:absolute;right:-34px;top:4px;border-left:40px solid #c9b48f;border-top:9px solid transparent;border-bottom:9px solid transparent}
.leaf{position:absolute;width:150px;height:150px;border-radius:0 80%% 0 80%%;z-index:8;box-shadow:0 8px 14px rgba(40,20,5,.3)}
""" % (W, H)

def leaf(x, y, r, c):
    return f'<div class="leaf" style="left:{x}px;top:{y}px;transform:rotate({r}deg);background:{c}"></div>'

DECO = leaf(-40, 1780, 20, "#b5532b") + leaf(1060, 140, -30, "#c98a2e") + leaf(1000, 1960, 70, "#8f3f22")

def sheet(n, x, y, w, rot, z=5):
    return f'<div class="sheet" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg);z-index:{z}"><img src="{P(n)}"></div>'

SCENES = {
 # 1 hook: example timeline printed on the desk, mug and pen
 "s1": sheet(7, 120, 520, 980, -2) + '<div class="mug" style="left:860px;top:1700px"></div>' +
        '<div class="pen" style="left:-120px;top:1650px;transform:rotate(-24deg)"></div>' + DECO,
 # 2 close-up of the timeline rows (big sheet, zoomed)
 "s2": sheet(7, -150, -480, 2050, -1.2) + leaf(1080, 1900, 50, "#b5532b"),
 # 3 quick cuts
 "s3a": sheet(3, 110, 440, 1000, 1.5) + '<div class="pen" style="left:700px;top:1880px;transform:rotate(-8deg)"></div>' + DECO,
 "s3b": sheet(6, 115, 440, 990, -1.5) + '<div class="mug" style="left:-110px;top:1760px"></div>' + DECO,
 "s3c": sheet(9, 105, 440, 1000, 1) + leaf(950, 1820, 40, "#b5532b") + leaf(-30, 160, 10, "#c98a2e"),
 # 4 fanned stack, cover on top
 "s4": sheet(13, 250, 470, 860, 9, 2) + sheet(9, 200, 430, 860, 4, 3) + sheet(7, 140, 410, 860, -2, 4) +
        sheet(1, 150, 380, 860, -6, 6) + '<div class="mug" style="left:900px;top:1780px"></div>' + DECO,
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": W, "height": H})
    for name, body in SCENES.items():
        hp=f"{OUT}/{name}.html"
        open(hp,"w").write(f'<!doctype html><html><head><style>{CSS}</style></head><body><div class="wood"></div>{body}<div class="light"></div><div class="vign"></div></body></html>')
        pg.goto("file://"+hp); pg.wait_for_load_state("load"); pg.wait_for_timeout(300)
        pg.screenshot(path=f"{OUT}/{name}.png")
        print(name)
    b.close()
