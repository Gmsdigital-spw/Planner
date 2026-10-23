import sys, math
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/factory/stages/night-shift/output/2026-10-23-murder-mystery-build")
import gm_style as gs
from gm_style import PW, PH, MARGIN, wrap
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from content import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/build/mystery/christmas-murder-mystery.pdf"
pal = gs.palette("berry")
NAME = "The Stolen Star of Hollyridge Lodge"
d = gs.Book(OUT, NAME, pal, cover_style="frame", page_frame="rule")
c = d.c
registerFont(TTFont("gm-serifI", "/home/claude/planner/tools/fonts/Lora-Italic.ttf"))
registerFont(TTFont("dejavu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
GOLD = HexColor(pal["accent"])
L, R = MARGIN, PW - MARGIN
TW = R - L
BOTTOM = MARGIN + 18

def para(text, x, y, w, font=None, size=10.5, lead=None, color=None, center=False):
    font = font or d.F; lead = lead or size * 1.42
    c.setFillColor(color or d.INK); c.setFont(font, size)
    for ln in wrap(text, font, size, w):
        if center: c.drawCentredString(x + w / 2, y - size, ln)
        else: c.drawString(x, y - size, ln)
        y -= lead
    return y

def para_h(text, w, font=None, size=10.5, lead=None):
    font = font or d.F; lead = lead or size * 1.42
    return len(wrap(text, font, size, w)) * lead

def card(x, y, w, h, title=None, fill=white, tint=None):
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    if title:
        c.setFillColor(tint or d.T); c.roundRect(x, y - 24, w, 24, 8, fill=1, stroke=0); c.rect(x, y - 24, w, 10, fill=1, stroke=0)
        c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(x + 12, y - 16, title.upper())

def star(x, y, r, col):
    c.setFillColor(col); p = c.beginPath()
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.42
        (p.moveTo if i == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    p.close(); c.drawPath(p, fill=1, stroke=0)

def magnifier(x, y, r, col):
    c.setStrokeColor(col); c.setLineWidth(r * 0.22); c.circle(x, y, r, fill=0, stroke=1)
    c.setLineWidth(r * 0.32); c.line(x + r * 0.72, y - r * 0.72, x + r * 1.6, y - r * 1.6)

def stars_row(y):
    for i, dx in enumerate((-40, 0, 40)):
        star(PW / 2 + dx, y, 7 if i == 1 else 4.5, GOLD)

# ---------------- page 1: cover
_sp = c.showPage; c.showPage = lambda: None
d.cover(["Christmas Murder", "Mystery Party"], "The Stolen Star of Hollyridge Lodge: a cozy whodunit for 8 players", pages=16, kicker="PRINTABLE PARTY GAME")
c.showPage = _sp
# what's inside panel in the gap above the pill
inside = ["Host guide and setup", "Timeline and host script", "2 invitations per sheet", "8 character sheets",
          "9 clue cards in 3 rounds", "Detective Notes sheet", "Sealed solution page", "8 name tags and 2 awards"]
px, pw_, ptop = 110, PW - 220, 330
c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.roundRect(px, ptop - 140, pw_, 140, 10, fill=1, stroke=1)
d._spaced(PW / 2, ptop - 24, "WHAT'S INSIDE", 9.5, d.P, d.FM)
for i, t in enumerate(inside):
    x = px + 30 + (i % 2) * (pw_ / 2); yy = ptop - 50 - (i // 2) * 22
    star(x, yy + 3, 4.5, GOLD); c.setFillColor(d.INK); c.setFont(d.F, 10.5); c.drawString(x + 12, yy, t)
c.showPage()

# ---------------- page 2: host guide
d.start("Host Guide", "Everything you need to run the party. Read this page and the next one, then you are ready.", kicker="Start here")
y = d.y
colw = (TW - 18) / 2
card(L, y, colw, 236, "How the game works")
yy = para("Eight guests each play a character at a snowed-in lodge on Christmas Eve. The lodge's famous gold Star "
          "was stolen from the top of the tree during a 12-minute blackout. Over three rounds, guests read their "
          "lines, share alibis, hear 9 clue cards and spill secrets. At the end everyone names the thief.",
          L + 12, y - 34, colw - 24, size=9.8)
yy = para("Only one guest can be the thief, and the clues prove it two separate ways. Every other player has an alibi "
          "a clue card can confirm. Family friendly: nothing is hurt but a mantel clock.", L + 12, yy - 6, colw - 24, size=9.8)
x2 = L + colw + 18
card(x2, y, colw, 236, "What to print")
items = [("Invitations", "page 4, 2 per sheet"), ("8 character sheets", "pages 5 to 12, one each"),
         ("9 clue cards", "page 13, cut apart"), ("Detective Notes", "page 14, one per player"), ("Solution", "page 15, fold and keep sealed"),
         ("Name tags, awards", "page 16, cut apart")]
yy = y - 40
for a, b in items:
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x2 + 12, yy - 9, 9.5, 9.5, 2, fill=0, stroke=1)
    c.setFillColor(d.INK); c.setFont(d.FM, 9.8); c.drawString(x2 + 30, yy - 8, a)
    c.setFillColor(d.MUT); c.setFont(d.F, 9.2); c.drawRightString(x2 + colw - 12, yy - 8, b); yy -= 31
y -= 252
card(L, y, TW, 172, "Before the party: setup checklist")
steps = ["2 to 3 weeks out: send invitations and give each guest a character. Any guest can play any role; costume ideas are on each sheet.",
         "1 week out: send each guest ONLY their own character sheet. One sheet says YOU ARE THE THIEF (the sealed solution says whose): give it to a guest who enjoys a fib.",
         "Party day: cut out the 9 clue cards and stack them by round (R1, R2, R3). Fold the solution page and keep it in an envelope.",
         "Optional props: a gold paper star on a small tree, a stopped clock showing 7:14, a bag of flour, candles for the blackout."]
yy = y - 36
for i, s in enumerate(steps):
    c.setFillColor(d.T); c.circle(L + 22, yy - 6, 9, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawCentredString(L + 22, yy - 9, str(i + 1))
    yy = para(s, L + 40, yy, TW - 56, size=9.8) - 7
y -= 188
h = y - BOTTOM
card(L, y, TW, h, "Host tips")
tips = ["You can play too: take Ivy or Rupert, read the clue cards out yourself, and act surprised at the end.",
        "Fewer than 8 guests? Drop a pair: Noelle and Felix, or Jasper and Dash. Their clue cards still clear them.",
        "Guests may bend the truth about their secrets until Round 3, but never about a clue card.",
        "Keep things moving: about 25 minutes per round is plenty. Dinner fits between Rounds 1 and 2."]
yy = y - 36
for t in tips:
    star(L + 20, yy - 6, 5, GOLD)
    yy = para(t, L + 34, yy, TW - 50, size=9.8) - 6
d.end()

# ---------------- page 3: timeline and host script
d.start("Party Timeline and Host Script", "Read the lines in italics out loud. Times are from when guests arrive.", kicker="Host")
d.table(["Time", "Step", "What to do"], [0.8, 2.0, 5.8], [list(r) for r in TIMELINE], rowh=22, size=9.4)
y = d.y - 4
h = para_h(STORY, TW - 28, "gm-serifI", 10.8, 16) + 44
card(L, y, TW, h, "Opening: read this out at 0:10", tint=d.T)
para(STORY, L + 14, y - 34, TW - 28, "gm-serifI", 10.8, 16, d.D)
y -= h + 14
rounds = [("Round 1", "Read clue cards C1, C3 and C9 aloud. Each guest reads their Round 1 part, then everyone mingles."),
          ("Round 2", "Read clue cards C4, C5 and C6. Alibis come out. Ask: 'Who can prove where they were at 7:14?'"),
          ("Round 3", "Read clue cards C7, C8 and C2. Secrets come out. Then say: 'The Star is still in this lodge. Who took it?'")]
colw = (TW - 24) / 3
hh = max(para_h(s, colw - 24, size=9.8, lead=14.5) for _, s in rounds) + 44
assert y - hh - 12 - BOTTOM >= 62, (y - hh - 12 - BOTTOM)
for i, (t, s) in enumerate(rounds):
    x = L + i * (colw + 12)
    card(x, y, colw, hh, t)
    para(s, x + 12, y - 36, colw - 24, size=9.8, lead=14.5)
yb = y - hh - 12
card(L, yb, TW, yb - BOTTOM, None, fill=d.T)
c.setFillColor(d.D); c.setFont(d.S, 13); c.drawString(L + 14, yb - 20, "Accusations and the reveal")
yy = para("Hand out Detective Notes (page 14) and allow 5 minutes. Then read the sealed solution (page 15) and give out the 2 awards.", L + 14, yb - 27, TW - 28, size=9.8, lead=14.5)
d.end()

# ---------------- page 4: invitations (2 per page)
d.start("Invitations", "Print, cut on the dashed line, and fill in by hand. Two per sheet.", kicker="Send 2 to 3 weeks ahead", centered=True)
top = d.y
ih = (top - BOTTOM - 16) / 2
for k in range(2):
    y0 = top - k * (ih + 16)
    c.setFillColor(HexColor(pal["deep"])); c.roundRect(L, y0 - ih, TW, ih, 10, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(1); c.roundRect(L + 8, y0 - ih + 8, TW - 16, ih - 16, 7, fill=0, stroke=1)
    for sx, sy, r in ((L + 40, y0 - 36, 7), (R - 44, y0 - 50, 5), (L + 30, y0 - ih + 30, 4), (R - 70, y0 - ih + 34, 7), (L + 30, y0 - ih / 2, 3), (R - 30, y0 - ih / 2 + 20, 3)):
        star(sx, sy, r, GOLD)
    cx = PW / 2
    d._spaced(cx, y0 - 38, "YOU ARE INVITED TO A", 9, GOLD, d.FM)
    c.setFillColor(white); c.setFont(d.S, 26); c.drawCentredString(cx, y0 - 70, "Christmas Murder Mystery")
    c.setFont("gm-serifI", 14); c.setFillColor(HexColor("#F6E4E1")); c.drawCentredString(cx, y0 - 92, "The Stolen Star of Hollyridge Lodge")
    para("Christmas Eve. A snowed-in lodge. The lights go out for 12 minutes, and the famous Star vanishes from the tree. Come in character, and find the thief before the buns go cold.",
         L + 60, y0 - 106, TW - 120, "gm-serifI", 10.5, 15, white, center=True)
    fy = y0 - 168
    for lab in ("Your character", "Date and time", "Place", "RSVP to"):
        c.setFillColor(GOLD); c.setFont(d.FM, 8.5); c.drawString(L + 60, fy, lab.upper())
        c.setStrokeColor(HexColor("#C98E95")); c.setLineWidth(0.7); c.line(L + 170, fy - 2, R - 60, fy - 2); fy -= 24
    c.setFillColor(HexColor("#F6E4E1")); c.setFont(d.F, 8.5); c.drawCentredString(cx, y0 - ih + 18, "Dress the part. Costume ideas are on your character sheet.")
    if k == 0:
        c.setDash(4, 4); c.setStrokeColor(d.MUT); c.setLineWidth(0.6); c.line(L, y0 - ih - 8, R, y0 - ih - 8); c.setDash()
d.end()

# ---------------- pages 6-13: character sheets
for idx, ch in enumerate(CHARS):
    d.start(ch["name"], None, kicker=f"Character {idx + 1} of 8  ·  {ch['role']}")
    y = d.y + 4
    # top band: who you are + costume
    colw = TW * 0.63
    h1 = max(para_h(ch["who"], colw - 24, size=10.8, lead=15.4), 96) + 46
    card(L, y, colw, h1, "Who you are")
    para(ch["who"], L + 12, y - 34, colw - 24, size=10.8, lead=15.4)
    x2 = L + colw + 12; w2 = TW - colw - 12
    card(x2, y, w2, h1, "Costume", fill=d.T)
    para(ch["costume"], x2 + 12, y - 34, w2 - 24, size=9.8, lead=14)
    magnifier(x2 + w2 - 34, y - h1 + 34, 12, d.P)
    y -= h1 + 12
    half = (TW - 12) / 2
    hs = max(para_h(ch["secret"], half - 24, size=10.8, lead=15.4), para_h(ch["alibi"], half - 24, size=10.8, lead=15.4)) + 46
    card(L, y, half, hs, "Your secret (keep it until Round 3)")
    para(ch["secret"], L + 12, y - 34, half - 24, size=10.8, lead=15.4)
    card(L + half + 12, y, half, hs, "Your alibi for 7:08 to 7:20")
    para(ch["alibi"], L + half + 24, y - 34, half - 24, size=10.8, lead=15.4)
    y -= hs + 12
    # rounds
    avail = y - BOTTOM
    qh = 30 + 3 * 22 + 12
    rh = (avail - qh - 12 * 3) / 3
    for rn, key in ((1, "r1"), (2, "r2"), (3, "r3")):
        card(L, y, TW, rh, None)
        c.setFillColor(d.P); c.roundRect(L, y - rh, 74, rh, 8, fill=1, stroke=0); c.rect(L + 60, y - rh, 14, rh, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(d.FM, 8); c.drawCentredString(L + 37, y - rh / 2 + 8, "ROUND")
        c.setFont(d.S, 22); c.drawCentredString(L + 37, y - rh / 2 - 16, str(rn))
        th = para_h(ch[key], TW - 110, size=11.2, lead=16)
        para(ch[key], L + 90, y - (rh - th) / 2 + 1, TW - 110, size=11.2, lead=16)
        y -= rh + 12
    card(L, y, TW, y - BOTTOM, "Questions you can ask", fill=d.T)
    yy = y - 36
    for q in ch["ask"]:
        star(L + 18, yy - 4, 4.5, GOLD)
        c.setFillColor(d.INK); c.setFont("gm-serifI", 11); c.drawString(L + 30, yy - 8, q); yy -= 23
    d.end()

# ---------------- page 14: clue cards
d.start("Clue Cards", "Cut apart. The host reads them out by round: R1 = C1, C3, C9; R2 = C4, C5, C6; R3 = C7, C8, C2.", kicker="9 clues", centered=True)
top = d.y; gap = 10
cw = (TW - 2 * gap) / 3; ch_ = (top - BOTTOM - 2 * gap) / 3
for i, (cid, rnd, title, text) in enumerate(CLUES):
    x = L + (i % 3) * (cw + gap); y0 = top - (i // 3) * (ch_ + gap)
    c.setDash(3, 3); c.setStrokeColor(d.MUT); c.setLineWidth(0.5); c.roundRect(x, y0 - ch_, cw, ch_, 6, fill=0, stroke=1); c.setDash()
    c.setFillColor(d.P); c.roundRect(x + 6, y0 - 34, cw - 12, 28, 5, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(d.FM, 8.5); c.drawString(x + 14, y0 - 24, f"{cid}  ·  ROUND {rnd}")
    star(x + cw - 20, y0 - 20, 6, GOLD)
    c.setFillColor(d.D); c.setFont(d.S, 12.5); c.drawString(x + 12, y0 - 54, title)
    fs = 10.6
    while fs > 8.6 and para_h(text, cw - 24, size=fs, lead=fs * 1.4) > ch_ - 80: fs -= 0.2
    assert para_h(text, cw - 24, size=fs, lead=fs * 1.4) <= ch_ - 80, cid
    para(text, x + 12, y0 - 66, cw - 24, size=fs, lead=fs * 1.4)
d.end()

# ---------------- page 15: detective notes / accusation
d.start("Detective Notes", "One per player. Fill it in as the clues come out, then name the thief.", kicker="Accusation sheet")
names = [ch["name"] for ch in CHARS]
y = d.y
cols = ["Suspect", "Where at 7:14?", "Proof (clue card)", "Shoes", "Ruled out?"]
ws = [1.6, 2.0, 1.6, 1.2, 0.9]
tw = TW; wsp = [w * tw / sum(ws) for w in ws]
rowh = 34
c.setFillColor(d.T); c.roundRect(L, y - 24, tw, 24, 4, fill=1, stroke=0)
x = L; c.setFillColor(d.D); c.setFont(d.FM, 8.6)
for col, w in zip(cols, wsp): c.drawString(x + 7, y - 16, col.upper()); x += w
y -= 24
for n in names:
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(L, y - rowh, R, y - rowh)
    c.setFillColor(d.INK); c.setFont(d.FM, 10); c.drawString(L + 7, y - rowh / 2 - 3, n)
    bx = L + sum(wsp[:4]) + wsp[4] / 2 - 6
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(bx, y - rowh / 2 - 6, 12, 12, 2, fill=0, stroke=1)
    y -= rowh
x = L
for w in wsp[:-1]: x += w; c.setStrokeColor(d.HAIR); c.line(x, d.y - 24, x, y)
y -= 16
half = (TW - 12) / 2
bh = y - BOTTOM
card(L, y, half, bh, "Clues I want to remember")
yy = y - 48
while yy > y - bh + 16:
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(L + 12, yy, L + half - 12, yy); yy -= 22
card(L + half + 12, y, half, bh, "My accusation", fill=d.T)
xa = L + half + 24
labels = ["The thief is", "They lied about", "The clue that proves it", "Why they did it", "Detective's name"]
yy = y - 46
step = (bh - 56) / len(labels)
for lab in labels:
    c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawString(xa, yy, lab.upper())
    c.setStrokeColor(d.P); c.setLineWidth(0.7); c.line(xa, yy - 20, xa + half - 24, yy - 20); yy -= step
d.end()

# ---------------- page 16: solution
d.start("The Solution", "Host only. Fold this page and keep it sealed until everyone has made an accusation.", kicker="Do not peek", centered=True)
y = d.y
card(L, y, TW, 30, None, fill=HexColor(pal["deep"]))
c.setFillColor(white); c.setFont(d.S, 14); c.drawCentredString(PW / 2, y - 20, "The thief is Clem Baxter, the head cook.")
y -= 44
h = para_h(SOLUTION_READ, TW - 28, "gm-serifI", 10.6, 15.6) + 44
card(L, y, TW, h, "Read this out")
para(SOLUTION_READ, L + 14, y - 34, TW - 28, "gm-serifI", 10.6, 15.6, d.D)
y -= h + 12
d_rows = [["Ivy", "Office phone call 7:05 to 7:25", "C4"], ["Jasper", "Garage camera 7:06 to 7:30", "C5"],
          ["Dash", "Garage camera 7:06 to 7:30", "C5"], ["Noelle", "Library voice memo 7:09 to 7:19", "C6"],
          ["Felix", "Library voice memo 7:09 to 7:19", "C6"], ["Marigold", "Room 4 lock log 7:02 to 7:31", "C7"],
          ["Rupert", "Right hand in a splint: cannot untwist wire", "C8"], ["Clem", "Oven alibi broken: power off 7:08 to 7:20", "C3 + C2"]]
d.y = y
d.table(["Suspect", "Cleared by", "Card"], [1.4, 5, 1.2], d_rows, rowh=21, size=9.4)
y = d.y
half = (TW - 12) / 2
mh = max(para_h(MOTIVE, half - 24, "gm-serif", 10, 14.4), para_h(ENDING, half - 24, "gm-serif", 10, 14.4)) + 46
mh = max(mh, y - BOTTOM)
card(L, y, half, mh, "Why Clem did it")
para(MOTIVE, L + 12, y - 34, half - 24, "gm-serif", 10, 14.4)
card(L + half + 12, y, half, mh, "How it ends", fill=d.T)
para(ENDING, L + half + 24, y - 34, half - 24, "gm-serif", 10, 14.4)
d.end()

# ---------------- page 17: name tags + awards
d.start("Name Tags and Awards", "Cut out a name tag for each guest. Hand out the 2 awards after the reveal.", kicker="Cut apart", centered=True)
top = d.y; gap = 10
tw2 = (TW - gap) / 2
awards_h = 120
th = (top - BOTTOM - awards_h - 4 * gap) / 4
for i, ch in enumerate(CHARS):
    x = L + (i % 2) * (tw2 + gap); y0 = top - (i // 2) * (th + gap)
    c.setDash(3, 3); c.setStrokeColor(d.MUT); c.setLineWidth(0.5); c.roundRect(x, y0 - th, tw2, th, 8, fill=0, stroke=1); c.setDash()
    c.setFillColor(d.P); c.roundRect(x + 6, y0 - 28, tw2 - 12, 22, 5, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(d.FM, 8.5); d._spaced(x + tw2 / 2, y0 - 21, "HELLO, I AM", 8.5, white, d.FM)
    c.setFillColor(d.D); c.setFont(d.S, 20); c.drawCentredString(x + tw2 / 2, y0 - th / 2 - 10, ch["name"])
    c.setFillColor(d.MUT); c.setFont("gm-serifI", 10); c.drawCentredString(x + tw2 / 2, y0 - th / 2 - 28, ch["role"])
    star(x + 22, y0 - th + 18, 5, GOLD); star(x + tw2 - 22, y0 - th + 18, 5, GOLD)
ya = top - 4 * (th + gap) + gap - gap
for k, (t, s) in enumerate((("Master Detective", "for the sharpest mind at Hollyridge Lodge"), ("Best in Character", "for the performance of the evening"))):
    x = L + k * (tw2 + gap)
    c.setFillColor(HexColor(pal["deep"])); c.roundRect(x, ya - awards_h, tw2, awards_h, 8, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.8); c.roundRect(x + 6, ya - awards_h + 6, tw2 - 12, awards_h - 12, 6, fill=0, stroke=1)
    star(x + tw2 / 2, ya - 26, 10, GOLD)
    c.setFillColor(white); c.setFont(d.S, 17); c.drawCentredString(x + tw2 / 2, ya - 60, t)
    c.setFillColor(HexColor("#F6E4E1")); c.setFont("gm-serifI", 9.5); c.drawCentredString(x + tw2 / 2, ya - 77, s)
    c.setStrokeColor(HexColor("#C98E95")); c.line(x + 40, ya - 100, x + tw2 - 40, ya - 100)
    c.setFont(d.F, 7.5); c.drawCentredString(x + tw2 / 2, ya - 110, "AWARDED TO")
d.end()

# ---------------- thank-you page (spec text verbatim)
d.page += 1; d._frame()
c.setFillColor(d.T); c.roundRect(L, BOTTOM + 40, TW, PH - 2 * MARGIN - 80, 14, fill=1, stroke=0)
y = PH - MARGIN - 110
star(PW / 2, y + 30, 16, GOLD)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, y - 30, "You just made my day!")
y -= 80
for t in ["Thank you for choosing a small, one-person shop over the big guys.",
          "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one."]:
    y = para(t, L + 60, y, TW - 120, "gm-serif", 14, 21, d.INK, center=True) - 16
c.setFillColor(white); c.roundRect(L + 80, y - 40, TW - 160, 40, 20, fill=1, stroke=0)
c.setFillColor(d.P); c.setFont("dejavu", 12.5); c.drawCentredString(PW / 2, y - 25, "How: Etsy app → You → Purchases → Leave a review")
y -= 80
y = para("Something not right? Message me first and I'll fix it fast.", L + 60, y, TW - 120, "gm-serif", 14, 21, d.INK, center=True) - 40
c.setFillColor(d.D); c.setFont("gm-serifI", 16); c.drawCentredString(PW / 2, y, "With thanks,")
c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 26, "GM's Digital Creations")
c.showPage()
d.save()
print("ok", OUT)
