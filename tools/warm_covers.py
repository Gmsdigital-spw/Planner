import os, sys
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
from playwright.sync_api import sync_playwright

OUT = os.environ.get("COVERS_OUT", os.path.join(os.path.dirname(__file__), "out"))
os.makedirs(OUT, exist_ok=True)

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:2400px;height:1800px;overflow:hidden;font-family:Inter,sans-serif;color:#2b211b}
.wood{position:absolute;inset:0;
 background:
  repeating-linear-gradient(90deg, rgba(0,0,0,.10) 0 3px, transparent 3px 390px),
  repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 2px, transparent 2px 23px),
  repeating-linear-gradient(90deg, rgba(0,0,0,.025) 0 1px, transparent 1px 11px),
  linear-gradient(90deg,#a06b44 0%,#b07a50 18%,#9c6741 33%,#b47e53 50%,#a36d45 66%,#b27c51 82%,#9d6842 100%);}
.vign{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(40,20,5,.35) 100%)}
.paper{position:absolute;background:#f4ede0;border-radius:6px;
 background-image:radial-gradient(rgba(120,90,60,.10) 1.4px, transparent 1.6px);background-size:22px 22px;
 box-shadow:0 30px 60px rgba(40,20,5,.35),0 6px 14px rgba(40,20,5,.25)}
.tape{position:absolute;width:250px;height:70px;background:rgba(232,214,178,.85);top:-28px;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.kicker{font-weight:700;letter-spacing:.32em;font-size:34px;text-transform:uppercase}
.serif{font-family:Lora,serif}
h1{font-family:Lora,serif;font-weight:700;line-height:.98;letter-spacing:-.01em}
.chip{display:inline-block;border:4px solid #d8c4a2;border-radius:60px;padding:16px 40px;font-size:36px;font-weight:500;margin-right:18px;background:#f8f2e6}
.badge{position:absolute;width:330px;height:330px;border-radius:50%;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.badge:before{content:"";position:absolute;inset:16px;border-radius:50%;border:5px dashed rgba(255,255,255,.6)}
.badge .n{font-family:Lora,serif;font-weight:700;font-size:120px;line-height:1}
.badge .l{font-weight:700;letter-spacing:.24em;font-size:30px;margin-top:6px}
.tablet{position:absolute;background:#2b2420;border-radius:56px;padding:34px;box-shadow:0 40px 70px rgba(40,20,5,.45)}
.screen{width:100%;height:100%;background:#faf5ec;border-radius:28px;overflow:hidden;padding:70px 64px}
.mug{position:absolute;width:420px;height:420px;border-radius:50%;background:#e9e1d3;box-shadow:0 30px 50px rgba(40,20,5,.45)}
.mug:before{content:"";position:absolute;inset:45px;border-radius:50%;background:radial-gradient(circle at 45% 40%,#7a4a2c,#5a321c)}
.mug:after{content:"";position:absolute;right:-120px;top:130px;width:150px;height:170px;border:34px solid #e1d8c8;border-left:none;border-radius:0 90px 90px 0}
.lights{position:absolute;left:0;top:0;width:2400px;height:200px}
.pine{position:absolute;width:420px;height:120px}
"""

LIGHTS = """<svg class="lights" viewBox="0 0 2400 200"><path d="M0 70 Q 300 130 600 75 T 1200 80 T 1800 75 T 2400 70" stroke="#4a3426" stroke-width="5" fill="none"/>
""" + "".join(
    f'<circle cx="{x}" cy="{y}" r="15" fill="#ffe7a3"/><circle cx="{x}" cy="{y}" r="38" fill="rgba(255,226,140,.28)"/>'
    for x, y in [(60,78),(180,95),(300,104),(420,100),(540,88),(660,80),(780,94),(900,104),(1020,98),(1140,86),(1260,82),(1380,96),(1500,104),(1620,98),(1740,86),(1860,82),(1980,94),(2100,103),(2220,96),(2340,80)]
) + "</svg>"

def pine(left, top, rot, color="#3f6b46"):
    needles = "".join(
        f'<line x1="{i}" y1="60" x2="{i+28}" y2="{8 if k%2 else 112}" stroke="{color}" stroke-width="7" stroke-linecap="round"/>'
        for k, i in enumerate(range(10, 400, 16)))
    return f'<svg class="pine" style="left:{left}px;top:{top}px;transform:rotate({rot}deg)" viewBox="0 0 420 120"><line x1="0" y1="60" x2="410" y2="60" stroke="#5b3d26" stroke-width="8"/>{needles}</svg>'

def confetti():
    import random
    random.seed(7)
    out = ""
    for _ in range(70):
        x = random.choice([random.randint(20, 220), random.randint(2100, 2380), random.randint(20, 2380)])
        y = random.randint(1450, 1780) if x < 2050 and x > 250 else random.randint(150, 1780)
        c = random.choice(["#e9c46a", "#d4a64a", "#f3dfa2", "#b8873a"])
        out += f'<div style="position:absolute;left:{x}px;top:{y}px;width:{random.randint(14,26)}px;height:{random.randint(14,26)}px;border-radius:50%;background:{c};opacity:.9"></div>'
    return out

def page(cfg):
    a = cfg["accent"]
    deco = cfg.get("deco", "")
    title_html = cfg["title_html"].replace("{A}", a)
    chips = "".join(f'<span class="chip">{c}</span>' for c in cfg["chips"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}</style></head><body>
<div class="wood"></div><div class="vign"></div>
{deco}
<div class="paper" style="left:130px;top:200px;width:1130px;height:1270px;transform:rotate(-1deg);z-index:3">
  <div class="tape" style="left:140px;transform:rotate(-3deg)"></div>
  <div class="tape" style="left:720px;transform:rotate(2deg)"></div>
  <div style="padding:120px 100px 0 100px">
    <div class="kicker" style="color:{a}">{cfg['kicker']}</div>
    <div style="margin-top:60px">{title_html}</div>
    <div class="serif" style="font-style:italic;font-size:54px;line-height:1.3;color:#5a4636;margin-top:56px;max-width:740px">{cfg['sub']}</div>
    <div style="margin-top:60px">{chips}</div>
  </div>
  <div class="badge" style="background:{a};right:-60px;top:{cfg.get('badge_top',470)}px"><div class="n">{cfg['badge_n']}</div><div class="l">{cfg['badge_l']}</div></div>
</div>
<div class="paper" style="left:1240px;top:300px;width:620px;height:780px;transform:rotate(-3deg);padding:80px 50px;z-index:1">
  {cfg['back']}
</div>
<div class="tablet" style="left:1500px;top:510px;width:760px;height:1000px;transform:rotate(3deg);z-index:4">
  <div class="screen">{cfg['screen']}</div>
</div>
{cfg.get('extra','<div class="mug" style="left:1830px;top:1420px;z-index:5"></div>')}
</body></html>"""

def rows(items, a, numbered=True):
    out = ""
    for i, t in enumerate(items, 1):
        num = f'<span class="serif" style="color:{a};font-weight:700;font-size:48px;width:70px;display:inline-block">{i}</span>' if numbered else ""
        out += f'<div style="display:flex;align-items:flex-start;padding:26px 0;border-bottom:4px dotted #d9c9ad;font-size:40px;line-height:1.25">{num}<span>{t}</span></div>'
    return out

def table(head, data, a):
    th = "".join(f'<th style="text-align:left;padding:18px 12px;font-size:28px;letter-spacing:.08em;text-transform:uppercase;color:#fff;background:{a}">{h}</th>' for h in head)
    trs = ""
    for r in data:
        tds = "".join(f'<td style="padding:20px 12px;font-size:32px;border-bottom:3px solid #e7dcc8">{c}</td>' for c in r)
        trs += f"<tr>{tds}</tr>"
    return f'<table style="width:100%;border-collapse:collapse;margin-top:36px">{th and "<tr>"+th+"</tr>"}{trs}</table>'

def scr_title(k, t, a):
    return f'<div class="kicker" style="color:{a};font-size:30px">{k}</div><h1 style="font-size:84px;margin-top:20px">{t}</h1>'

def back_title(k, t, a):
    return f'<div class="kicker" style="color:{a};font-size:26px;text-align:center">{k}</div><h1 style="font-size:64px;text-align:center;margin-top:18px">{t}</h1>'

def grid_cells(words):
    cells = "".join(f'<div style="border:4px solid #d8c4a2;border-radius:16px;height:130px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:28px;padding:8px">{w}</div>' for w in words)
    return f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:40px">{cells}</div>'

RED, GREEN, TERRA, WINE, SAGE = "#a33a2f", "#2f6a4a", "#b5563a", "#8c2f3f", "#5f7f5c"
P = lambda c: f'<span style="color:{c}">'

COVERS = {
 "budget-spreadsheet": dict(
   accent=TERRA, kicker="Google Sheets · Excel",
   title_html=f'<h1 style="font-size:150px">Monthly</h1><h1 style="font-size:150px;color:{{A}};font-weight:500;font-style:italic">Budget</h1><h1 style="font-size:150px">Tracker</h1>',
   sub="Type your numbers in, the math is done for you. 12 months + a year summary.",
   chips=["Auto math","12 months","Easy to use"], badge_n="12", badge_l="MONTHS", badge_top=420,
   back=back_title("Year", "Summary", TERRA) + table("", [["Jan","$412"],["Feb","$385"],["Mar","$460"],["Apr","$298"],["May","$521"]], TERRA),
   screen=scr_title("October", "My Budget", TERRA) + table(["Category","Budget","Actual"], [["Rent","$950","$950"],["Groceries","$400","$362"],["Gas","$160","$171"],["Fun","$120","$88"],["Savings","$200","$200"]], TERRA)
     + f'<div style="margin-top:46px;font-size:38px;display:flex;justify-content:space-between"><span>Left over</span><b class="serif" style="color:{TERRA};font-size:56px">$412</b></div>',
   deco=""),
 "christmas-planner": dict(
   accent=RED, kicker="Printable · 2026 Holiday",
   title_html=f'<h1 style="font-size:150px">Christmas</h1><h1 style="font-size:150px;color:{{A}};font-weight:500;font-style:italic">Planner</h1><h1 style="font-size:96px;margin-top:20px">2026</h1>',
   sub="Gifts, budget, cards, baking and Christmas dinner, all in one place.",
   chips=["Gift tracker","Budget","Meal plan"], badge_n="16", badge_l="PAGES",
   back=back_title("December", "Countdown", GREEN) + grid_cells(["1","2","3","4","5","6","7","8","9"]),
   screen=scr_title("Gift Tracker", "Who's on my list", RED) + table(["Name","Gift","Bought"], [["Mom","Candle set","✓"],["Dad","Knife","✓"],["Sis","Pajamas",""],["Ben","Lego",""],["Nana","Photo book","✓"]], RED),
   deco=LIGHTS + pine(1900, 70, 160) + pine(-60, 1640, -40)),
 "advent-activities": dict(
   accent=GREEN, kicker="Printable · Screen-Free",
   title_html=f'<h1 style="font-size:140px">24 Days of</h1><h1 style="font-size:140px;color:{{A}};font-weight:500;font-style:italic">Christmas</h1><h1 style="font-size:80px;margin-top:16px">Family Activities</h1>',
   sub="One simple activity a day until Christmas, with a fun question on every card.",
   chips=["Ages 4–12","Cut-out cards","Start tonight"], badge_n="24", badge_l="CARDS", badge_top=430,
   back=back_title("Countdown", "Tracker", RED) + grid_cells(["Day 1","Day 2","Day 3","Day 4","Day 5","Day 6","Day 7","Day 8","Day 9"]),
   screen=f'<div style="border:6px solid {GREEN};border-radius:30px;padding:44px 40px;height:100%;text-align:center">'
     + f'<div class="kicker" style="color:{RED};font-size:32px">Day 07</div><h1 style="font-size:78px;margin-top:28px">Blanket Fort Night</h1>'
     + '<div style="font-size:36px;line-height:1.35;margin-top:36px;color:#5a4636">Build a fort with every blanket in the house, then read a story inside.</div>'
     + f'<div style="margin-top:44px;border-top:4px dotted #d9c9ad;padding-top:34px"><div class="kicker" style="color:{GREEN};font-size:26px">Talk about it</div><div class="serif" style="font-style:italic;font-size:40px;margin-top:16px">What would your dream fort have inside?</div></div></div>',
   deco=LIGHTS + pine(1900, 70, 160) + pine(-60, 1640, -40)),
 "secret-santa-kit": dict(
   accent=GREEN, kicker="Printable · Gift Exchange",
   title_html=f'<h1 style="font-size:150px">Secret</h1><h1 style="font-size:150px;color:{RED};font-weight:500;font-style:italic">Santa</h1><h1 style="font-size:110px;margin-top:10px">Exchange Kit</h1>',
   sub="Questionnaire, name slips, rules and gift tags. Everything an organizer needs.",
   chips=["Office","Family","Friends"], badge_n="24", badge_l="NAME SLIPS", badge_top=430,
   back=back_title("Cut & fold", "Name Slips", RED) + grid_cells(["✂","✂","✂","✂","✂","✂","✂","✂","✂"]),
   screen=scr_title("Questionnaire", "All About Me", GREEN) + rows(["Favorite snack: _______","Favorite color: _______","Hobbies: _______","Allergies: _______","Wish list: _______"], RED),
   deco=LIGHTS + pine(1900, 70, 160) + pine(-60, 1640, -40)),
 "nye-games": dict(
   accent=WINE, kicker="Printable · Family Friendly",
   title_html=f'<h1 style="font-size:140px">New Year\'s</h1><h1 style="font-size:140px;color:{{A}};font-weight:500;font-style:italic">Eve Party</h1><h1 style="font-size:140px">Games</h1>',
   sub="Trivia, bingo, 2027 predictions & more. No drinking games, so everyone can play.",
   chips=["All ages","Answer keys","Print at home"], badge_n="8", badge_l="GAMES", badge_top=430,
   back=back_title("Keepsake", "2027 Predictions", "#b8873a") + rows(["I think I'll...","Best new thing:","Biggest change:"], WINE, False),
   screen=scr_title("Game 01", "New Year's Trivia", WINE) + rows(["Where does the big ball drop?","What song is sung at midnight?","Which country rings in the year first?","What's a popular resolution?"], WINE),
   deco=LIGHTS + confetti()),
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(COVERS)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 2400, "height": 1800})
        for n in names:
            pg.set_content(page(COVERS[n]))
            pg.wait_for_timeout(300)
            path = os.path.join(OUT, f"{n}.png")
            pg.screenshot(path=path)
            print(path)
        b.close()
