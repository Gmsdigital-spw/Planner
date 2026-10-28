import sys, math
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, ".")
import gm_style as gs
from gm_style import PW, PH, MARGIN
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from content import KIDS, FAMILY, ADULTS
registerFont(TTFont("dv", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

OUT = "christmas-charades-120.pdf"
pal = gs.palette("cranberry")
d = gs.Book(OUT, "Christmas Charades", pal, cover_style="split", page_frame="stripe")
c = d.c
LV = {"K": ("KIDS", HexColor("#3C6454"), HexColor("#E6EEE9")),
      "F": ("FAMILY", HexColor("#8B2E3C"), HexColor("#F5E4E6")),
      "A": ("ADULTS", HexColor("#7A5A24"), HexColor("#F8EFDB"))}
CARDS = [("K", i + 1, p) for i, p in enumerate(KIDS)] + [("F", i + 1, p) for i, p in enumerate(FAMILY)] + [("A", i + 1, p) for i, p in enumerate(ADULTS)]
BOTTOM = MARGIN + 14  # above footer rule

def snowflake(x, y, r, col, w=0.9):
    c.setStrokeColor(col); c.setLineWidth(w)
    for k in range(3):
        a = math.pi / 3 * k
        dx, dy = r * math.cos(a), r * math.sin(a)
        c.line(x - dx, y - dy, x + dx, y + dy)
    for k in range(6):
        a = math.pi / 3 * k; bx, by = x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a)
        for s in (-1, 1):
            b = a + s * math.pi / 4
            c.line(bx, by, bx + r * 0.3 * math.cos(b), by + r * 0.3 * math.sin(b))

def tree(x, y, h, col):
    c.setFillColor(col); p = c.beginPath()
    p.moveTo(x, y + h); p.lineTo(x - h * 0.38, y + h * 0.2); p.lineTo(x + h * 0.38, y + h * 0.2); p.close(); c.drawPath(p, fill=1, stroke=0)
    c.rect(x - h * 0.07, y, h * 0.14, h * 0.2, fill=1, stroke=0)

def star(x, y, r, col):
    c.setFillColor(col); p = c.beginPath()
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        (p.moveTo if k == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    p.close(); c.drawPath(p, fill=1, stroke=0)

ICON = {"K": lambda x, y, col: snowflake(x, y, 7, col), "F": lambda x, y, col: tree(x, y - 7, 15, col), "A": lambda x, y, col: star(x, y, 7.5, col)}

RECTS = []
def card(x, y, w, h, lv, num, text):
    RECTS.append({'page': d.page, 'x': x, 'y': y, 'w': w, 'h': h, 'id': f'{lv}{num:02d}', 'text': text})
    name, col, tint = LV[lv]
    c.setDash(3, 3); c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.rect(x, y, w, h, fill=0, stroke=1); c.setDash()
    ix, iy, iw, ih = x + 6, y + 6, w - 12, h - 12
    c.setFillColor(white); c.setStrokeColor(col); c.setLineWidth(1.4); c.roundRect(ix, iy, iw, ih, 7, fill=1, stroke=1)
    band = 22
    c.setFillColor(col); c.roundRect(ix, iy + ih - band, iw, band, 7, fill=1, stroke=0); c.rect(ix, iy + ih - band, iw, 8, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(d.FM, 8.2); c.drawString(ix + 9, iy + ih - band + 7.5, name)
    c.drawRightString(ix + iw - 9, iy + ih - band + 7.5, f"{lv}{num:02d}")
    if text:
        size = 15
        while True:
            lines = gs.wrap(text, d.SB, size, iw - 22)
            if (len(lines) <= 2 or size <= 12.5) and len(lines) <= 3 and all(stringWidth(l, d.SB, size) <= iw - 22 for l in lines): break
            size -= 0.5
        lh = size * 1.22; mid = iy + (ih - band) / 2 + (12 if len(lines) == 3 else 8)
        ty = mid + (len(lines) - 1) * lh / 2 - size * 0.35
        c.setFillColor(d.INK); c.setFont(d.SB, size)
        for l in lines: c.drawCentredString(ix + iw / 2, ty, l); ty -= lh
    else:
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
        for k in range(3):
            ly = iy + 34 + k * 22; c.line(ix + 14, ly, ix + iw - 14, ly)
    ICON[lv](ix + iw / 2, iy + 22, tint if False else col)
    c.setFillColor(d.MUT); c.setFont(d.F, 6.8)
    c.drawString(ix + 9, iy + 8, "ACT IT"); c.drawRightString(ix + iw - 9, iy + 8, "DRAW IT")

def card_grid(cards, top):
    cols, rows = 3, 4
    w = (PW - 2 * MARGIN) / cols; h = (top - BOTTOM) / rows
    for i, (lv, n, t) in enumerate(cards):
        r, col = divmod(i, cols)
        card(MARGIN + col * w, top - (r + 1) * h, w, h, lv, n, t)
    return w, h

# ---- cover (extra: level chips + count, drawn before the kit's showPage)
_sp = c.showPage
def _cover_extra():
    x0 = PW * 0.34 + 40; y = 300
    c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawString(x0, y + 40, "120 CARDS  ·  40 PER LEVEL")
    for k, lv in enumerate("KFA"):
        name, col, tint = LV[lv]; x = x0 + k * 112
        c.setFillColor(white); c.setStrokeColor(col); c.setLineWidth(1.4); c.roundRect(x, y - 100, 100, 124, 7, fill=1, stroke=1)
        c.setFillColor(col); c.roundRect(x, y + 2, 100, 22, 7, fill=1, stroke=0); c.rect(x, y + 2, 100, 8, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(d.FM, 8.5); c.drawCentredString(x + 50, y + 9, name)
        c.setFillColor(d.INK); c.setFont(d.SB, 30); c.drawCentredString(x + 50, y - 45, "40")
        ICON[lv](x + 50, y - 78, col)
    c.setFillColor(d.MUT); c.setFont(d.F, 10); c.drawString(x0, y - 130, "Plus Draw It mode, timer rules, team score sheet and 12 blank cards.")
    c.showPage = _sp; _sp()
c.showPage = _cover_extra
d.cover(["Christmas", "Charades"], "120 cards in 3 levels: Kids, Family and Adults. Act it or draw it, then keep score.", pages=14, kicker="PRINTABLE PARTY GAME")

# ---- how to play
d.start("How to Play", "Everything you need for a merry, noisy round of charades.", kicker="Start here", centered=True)
d.heading("Get ready")
d.bullets(["Print the card pages on white cardstock (or plain paper) at 100% / Actual size. Letter size; on A4 choose Fit.",
           "Cut along the dashed lines. Each card has its level, its number and a coloured top band.",
           "Split into 2 to 4 teams and print one team score sheet. Grab a phone timer."], numbered=True)
d.heading("Play a round")
d.bullets(["The actor picks a card from their level and reads it silently.",
           "Start the 60-second timer. Act it out with no words, no sounds and no pointing at things in the room.",
           "Your team shouts guesses. A correct guess before time runs out scores 1 point; under 30 seconds scores 2.",
           "Pass the turn to the next team. The team with the most points after the last round wins."], numbered=True)
d.heading("The three levels")
top = d.y - 4; bw = (PW - 2 * MARGIN - 20) / 3; bh = 112
info = [("K", "Kids", "40 cards. Simple actions, animals and things kids know: making a snow angel, a penguin, a snowball fight."),
        ("F", "Family", "40 cards. Funny moments everyone has lived: untangling the lights, stepping on a toy in the dark."),
        ("A", "Adults", "40 cards. Office party and grown-up holiday life: the Secret Santa reveal, hiding the receipt.")]
for k, (lv, nm, tx) in enumerate(info):
    name, col, tint = LV[lv]; x = MARGIN + k * (bw + 10)
    c.setFillColor(tint); c.roundRect(x, top - bh, bw, bh, 6, fill=1, stroke=0)
    c.setFillColor(col); c.roundRect(x, top - 22, bw, 22, 6, fill=1, stroke=0); c.rect(x, top - 22, bw, 8, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(d.FM, 9); c.drawCentredString(x + bw / 2, top - 15, nm.upper())
    c.setFillColor(d.INK); c.setFont(d.F, 9); yy = top - 38
    for l in gs.wrap(tx, d.F, 9, bw - 20): c.drawString(x + 10, yy, l); yy -= 13
d.y = top - bh - 10
d.heading("Mixed ages? Play it this way")
d.bullets(["Each actor picks from their own level, so a 6-year-old and grandpa both get a fair card.",
           "Shuffle all 120 cards together for a wild mixed round where anything can come up.",
           "Little ones who can't read yet: a grown-up whispers the card to them."], size=10.2)
d.heading("Host tips")
tips = ["Keep each level in its own pile or envelope.",
        "Print a second set for two tables at once.",
        "Switch to Draw It mode (page 13) any time.",
        "Blank cards (page 15): add family jokes."]
top = d.y - 2; bh = top - BOTTOM - 8; bw = (PW - 2 * MARGIN - 12) / 2
for k in range(2):
    x = MARGIN + k * (bw + 12)
    c.setFillColor(d.T); c.roundRect(x, top - bh, bw, bh, 6, fill=1, stroke=0)
    yy = top - 18
    for t in tips[k * 2:k * 2 + 2]:
        c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x + 18, yy - 1, 9, 9, 2, fill=0, stroke=1)
        c.setFillColor(d.INK); c.setFont(d.F, 9.6); c.drawString(x + 34, yy, t); yy -= 17
assert bh >= 44, bh

d.end()

# ---- card pages
groups = [CARDS[i:i + 12] for i in range(0, 120, 12)]
for gi, g in enumerate(groups):
    levels = []
    for lv, _, _ in g:
        if LV[lv][0] not in levels: levels.append(LV[lv][0])
    lvtxt = " + ".join(l.title() for l in levels)
    first, last = g[0], g[-1]
    rng = f"{first[0]}{first[1]:02d} to {last[0]}{last[1]:02d}"
    d.start(f"{lvtxt} Cards", f"Cards {rng}  ·  cut on the dashed lines", kicker=f"Card page {gi + 1} of 10", centered=True)
    card_grid(g, d.y)
    d.end()

# ---- draw it + timer
d.start("Draw It Mode", "Same 120 cards, new game: draw the card instead of acting it.", kicker="Bonus mode", centered=True)
d.heading("How Draw It works")
d.bullets(["The artist picks a card and draws it on paper or a whiteboard for the team.",
           "No letters, no numbers and no words in the drawing. Arrows and dashes are fine.",
           "60 seconds per card. 1 point for a correct guess, 2 points under 30 seconds.",
           "Kids can act while grown-ups draw, or swap every round to keep it fresh."], numbered=True)
d.heading("Timer rules (both modes)")
d.bullets(["One timer keeper per round, from the team that is not playing.",
           "Time starts when the actor or artist looks up from the card.",
           "A pass costs nothing but ends the turn. Saying a word of the card ends the turn with 0.",
           "Close calls: the timer keeper decides, and the decision stands."], size=10)
d.heading("Party variations")
d.bullets(["Speed round: one team, 2 minutes, as many cards as you can.",
           "Silent team: the guessers may only write answers, not shout.",
           "Relay: one card, three actors, 20 seconds each.",
           "Act and draw: one player acts while a teammate draws."], size=10, cols=2)
# practice sketch boxes to fill the page
top = d.y - 4; bh = top - BOTTOM - 6; bw = (PW - 2 * MARGIN - 14) / 2
for k in range(2):
    x = MARGIN + k * (bw + 14)
    c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(x, top - bh, bw, bh, 6, fill=0, stroke=1)
    c.setFillColor(d.T); c.roundRect(x, top - 22, bw, 22, 6, fill=1, stroke=0); c.rect(x, top - 22, bw, 8, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawString(x + 10, top - 15, f"SKETCH BOX {k + 1}   ·   CARD #  ______")
d.end()

# ---- team score sheet
d.start("Team Score Sheet", "1 point for a correct guess, 2 points under 30 seconds. Circle A for act or D for draw.", kicker="Keep score", centered=True)
top = d.y; tw = PW - 2 * MARGIN
names_h = 36
c.setFillColor(d.T); c.roundRect(MARGIN, top - names_h, tw, names_h, 5, fill=1, stroke=0)
cw = [0.9, 1, 1, 1, 1]; ws = [w * tw / sum(cw) for w in cw]
x = MARGIN + ws[0]
c.setFillColor(d.D); c.setFont(d.FM, 8.4); c.drawString(MARGIN + 8, top - 22, "TEAM NAMES")
for k in range(4):
    c.setFillColor(LV["KFA"[k % 3]][1] if k < 3 else d.P); c.setFont(d.FM, 8.4); c.drawString(x + 8, top - 13, f"TEAM {k + 1}")
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(x + 8, top - 28, x + ws[k + 1] - 8, top - 28); x += ws[k + 1]
d.y = top - names_h - 8
rows = [[f"Round {i}", "A / D", "A / D", "A / D", "A / D"] for i in range(1, 13)] + [["TOTAL", "", "", "", ""]]
d.table(["Round", "Team 1", "Team 2", "Team 3", "Team 4"], cw, rows=rows, fill=True)
d.end()

# ---- blank cards
d.start("Make Your Own Cards", "12 blank cards, 4 per level: add family jokes, pets and inside stories.", kicker="Blank cards", centered=True)
card_grid([(lv, n, "") for lv, base in (("K", 41), ("F", 41), ("A", 41)) for n in range(base, base + 4)], d.y)
d.end()

# ---- thank-you page (spec text verbatim)
d.page += 1; d._frame()
y = PH - 210
snowflake(PW / 2 - 60, y + 50, 12, d.A); star(PW / 2, y + 52, 13, d.P); snowflake(PW / 2 + 60, y + 50, 12, d.A)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, y - 10, "You just made my day!")
d._ornament(PW / 2, y - 36)
y -= 90; W = PW - 2 * MARGIN - 6
paras = ["Thank you for choosing a small, one-person shop over the big guys.",
         "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one."]
c.setFillColor(d.INK)
for p in paras:
    for l in gs.wrap(p, d.SS, 15, W): c.setFont(d.SS, 15); c.drawCentredString(PW / 2, y, l); y -= 22
    y -= 16
how = "How: Etsy app → You → Purchases → Leave a review"
bw = stringWidth(how, d.FM, 12.5) + 60
c.setFillColor(d.T); c.roundRect(PW / 2 - bw / 2, y - 22, bw, 40, 10, fill=1, stroke=0)
parts = how.split("→"); aw = stringWidth(" → ", "dv", 12.5)
tot = sum(stringWidth(p.strip(), d.FM, 12.5) for p in parts) + aw * (len(parts) - 1)
xx = PW / 2 - tot / 2; c.setFillColor(d.D)
for i, p in enumerate(parts):
    p = p.strip(); c.setFont(d.FM, 12.5); c.drawString(xx, y - 6, p); xx += stringWidth(p, d.FM, 12.5)
    if i < len(parts) - 1: c.setFont("dv", 12.5); c.drawString(xx, y - 6, " → "); xx += aw
y -= 70
c.setFillColor(d.INK); c.setFont(d.SS, 15); c.drawCentredString(PW / 2, y, "Something not right? Message me first and I'll fix it fast.")
y -= 150
c.setFillColor(d.P); c.setFont(d.SB, 16); c.drawCentredString(PW / 2, y, "With thanks,")
c.setFont(d.S, 20); c.drawCentredString(PW / 2, y - 28, "GM's Digital Creations")
for k, xx in enumerate((PW / 2 - 150, PW / 2 + 150)):
    tree(xx, y - 40, 50, d.P if k else HexColor("#3C6454"))
c.showPage()
d.save()
import json; json.dump(RECTS, open("rects.json", "w")); print("ok", d.page)
