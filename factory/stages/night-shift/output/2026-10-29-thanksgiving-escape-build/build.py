"""Build the Thanksgiving escape room PDF (The Pie Safe). python3 build.py <out.pdf>"""
import sys, math, random
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gm_style as gs
import puzzles as pz
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = sys.argv[1] if len(sys.argv) > 1 else "thanksgiving-escape-room.pdf"
PAL = gs.palette("harvest")
NAME = "The Pie Safe  ·  Thanksgiving Escape Room"
d = gs.Book(OUT, NAME, PAL, cover_style="frame", page_frame="rule")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
GREEN, GTINT = HexColor("#66753A"), HexColor("#EDF0E1")      # olive: Level 2
GOLD, GOLDT = HexColor("#B48A2E"), HexColor("#F7EEDA")
ORANGE, ORANGET = HexColor("#C4682A"), HexColor("#F8E3CF")
RED, REDT = HexColor("#A23B2C"), HexColor("#F5DCD6")
BROWN, BROWNT = HexColor("#7A5232"), HexColor("#EADBC7")
FOOT_RULE = M - 1         # kit footer rule (gs.Book.end: MARGIN - 14 + 13)
CLEAR = 18                # fix round 2: 0.25 in between every page's lowest element and the footer rule
BOTTOM = FOOT_RULE + CLEAR + 1.5   # lowest content line (was M + 16 = 17 pt above the rule)
PAD = 18                  # fix round 3: 0.25 in inside EVERY box border, all four sides (checked by check_boxes)
BOXES = []                # fix round 3: (page, name, x, y_bottom, w, h, corner) of every box/card/answer box


def reg(name, x, yb, w, h, r=8):
    """Register a box so check_boxes() can prove nothing sits within 0.25 in of its border."""
    BOXES.append((c.getPageNumber(), name, x, yb, w, h, r))


# ------------------------------------------------------------------ drawing helpers (original simple shapes)
def poly(pts, fill=None, stroke=None, lw=1.2):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close()
    if fill is not None: c.setFillColor(fill)
    if stroke is not None: c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.drawPath(p, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def pumpkin(x, y, s):
    """x centre, y bottom, s height."""
    w = s * 0.88; h = s * 0.8
    c.setStrokeColor(ORANGE); c.setLineWidth(max(0.8, s * 0.03)); c.setFillColor(ORANGET)
    for dx, ww in ((-0.28, 0.56), (0.28, 0.56), (0, 0.6)):
        c.ellipse(x + dx * w - ww * w / 2, y, x + dx * w + ww * w / 2, y + h, fill=1, stroke=1)
    c.setFillColor(GREEN); c.setStrokeColor(GREEN)
    poly([(x - s * 0.05, y + h - s * 0.04), (x + s * 0.05, y + h - s * 0.04), (x + s * 0.09, y + s * 0.98), (x + s * 0.0, y + s * 0.98)], GREEN, GREEN, 0.6)


def apple(x, y, s):
    """x centre, y bottom, s height."""
    r = s * 0.4
    c.setStrokeColor(RED); c.setLineWidth(max(0.8, s * 0.03)); c.setFillColor(REDT)
    p = c.beginPath()
    p.moveTo(x, y + s * 0.74)
    p.curveTo(x + r * 0.5, y + s * 0.86, x + r * 1.25, y + s * 0.78, x + r * 1.1, y + s * 0.38)
    p.curveTo(x + r * 0.95, y + s * 0.05, x + r * 0.4, y, x, y + s * 0.07)
    p.curveTo(x - r * 0.4, y, x - r * 0.95, y + s * 0.05, x - r * 1.1, y + s * 0.38)
    p.curveTo(x - r * 1.25, y + s * 0.78, x - r * 0.5, y + s * 0.86, x, y + s * 0.74)
    c.drawPath(p, fill=1, stroke=1)
    c.setStrokeColor(BROWN); c.setLineWidth(max(1, s * 0.05)); c.line(x, y + s * 0.72, x + s * 0.05, y + s * 0.95)
    c.setFillColor(GTINT); c.setStrokeColor(GREEN); c.setLineWidth(max(0.6, s * 0.02))
    c.ellipse(x + s * 0.06, y + s * 0.8, x + s * 0.32, y + s * 0.92, fill=1, stroke=1)


def acorn(x, y, s):
    """x centre, y bottom, s height."""
    w = s * 0.62
    c.setStrokeColor(BROWN); c.setLineWidth(max(0.8, s * 0.03)); c.setFillColor(GOLDT)
    p = c.beginPath()
    p.moveTo(x - w * 0.42, y + s * 0.6)
    p.curveTo(x - w * 0.45, y + s * 0.25, x - w * 0.1, y + s * 0.02, x, y)
    p.curveTo(x + w * 0.1, y + s * 0.02, x + w * 0.45, y + s * 0.25, x + w * 0.42, y + s * 0.6)
    p.close(); c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(BROWNT)
    c.roundRect(x - w / 2, y + s * 0.56, w, s * 0.26, s * 0.12, fill=1, stroke=1)
    c.setLineWidth(max(1, s * 0.06)); c.line(x, y + s * 0.82, x + s * 0.06, y + s * 0.97)


def leaf(x, y, s, col=None, fill=None):
    """Simple oak-style leaf. x centre, y bottom, s height."""
    col = col or GOLD; fill = fill if fill is not None else GOLDT
    pts = []
    for i in range(41):
        t = i / 40.0
        yy = y + s * 0.12 + t * s * 0.86
        wob = 1 + 0.18 * math.sin(t * math.pi * 6)
        pts.append((x + s * 0.34 * math.sin(math.pi * t) * wob, yy))
    pts = pts + [(2 * x - px, py) for (px, py) in reversed(pts)]
    poly(pts, fill, col, max(0.7, s * 0.025))
    c.setStrokeColor(col); c.setLineWidth(max(0.7, s * 0.03)); c.line(x, y, x, y + s * 0.9)


def pie(x, y, s, label=None):
    """Pie seen from the side. x centre, y bottom, s width."""
    c.setStrokeColor(BROWN); c.setLineWidth(1.2); c.setFillColor(GOLDT)
    p = c.beginPath(); p.moveTo(x - s / 2, y + s * 0.34)
    p.curveTo(x - s * 0.4, y + s * 0.62, x + s * 0.4, y + s * 0.62, x + s / 2, y + s * 0.34); p.close()
    c.drawPath(p, fill=1, stroke=1)
    for k in (-0.22, 0, 0.22):
        c.line(x + k * s - s * 0.05, y + s * 0.42, x + k * s + s * 0.05, y + s * 0.5)
    poly([(x - s / 2, y + s * 0.34), (x + s / 2, y + s * 0.34), (x + s * 0.4, y), (x - s * 0.4, y)], BROWNT, BROWN, 1.2)
    if label is not None:
        c.setFillColor(d.D); c.setFont(d.S, s * 0.3); c.drawCentredString(x, y + s * 0.07, str(label))


def card_icon(x, y, w, h, fill=white):
    """Recipe card with a folded corner. x,y bottom-left."""
    k = h * 0.22
    poly([(x, y), (x + w - k, y), (x + w, y + k), (x + w, y + h), (x, y + h)], fill, d.P, 1.3)
    poly([(x + w - k, y), (x + w - k, y + k), (x + w, y + k)], d.T, d.P, 1)
    reg("recipe card", x, y, w, h, k)


def padlock(x, y, s):
    c.setStrokeColor(d.D); c.setLineWidth(s * 0.09); c.setFillColor(white)
    c.arc(x - s * 0.28, y + s * 0.35, x + s * 0.28, y + s * 0.98, 0, 180)
    c.line(x - s * 0.28, y + s * 0.66, x - s * 0.28, y + s * 0.5); c.line(x + s * 0.28, y + s * 0.66, x + s * 0.28, y + s * 0.5)
    c.setFillColor(d.T); c.setLineWidth(1.1); c.roundRect(x - s * 0.42, y, s * 0.84, s * 0.56, 3, fill=1, stroke=1)
    c.setFillColor(d.D); c.circle(x, y + s * 0.3, s * 0.06, fill=1, stroke=0)


ICON = {"pumpkin": lambda x, y, s: pumpkin(x, y, s), "apple": lambda x, y, s: apple(x, y, s),
        "acorn": lambda x, y, s: acorn(x, y, s), "leaf": lambda x, y, s: leaf(x, y, s)}
NAMES = {"pumpkin": "Pumpkins", "apple": "Apples", "acorn": "Acorns"}


AB_H = 82                 # fix round 3: answer box tall enough for 0.25 in above and below its 40 pt cells


def answer_box(y, label, cells=1, note=None):
    h = AB_H; w = 300
    x = (PW - w) / 2
    c.setStrokeColor(d.P); c.setLineWidth(1.4); c.setFillColor(d.T)
    c.roundRect(x, y - h, w, h, 10, fill=1, stroke=1)
    reg("answer box: " + label, x, y - h, w, h, 10)
    c.setFillColor(d.D); c.setFont(d.SB, 15); c.drawString(x + 20, y - h / 2 - 5, label)
    bx = x + w - 20 - 44 * cells
    for i in range(cells):
        c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2)
        c.roundRect(bx + i * 44, y - h + PAD + 3, 40, 40, 6, fill=1, stroke=1)
    if note:
        c.setFillColor(d.MUT); c.setFont(d.F, 9); c.drawCentredString(PW / 2, y - h - 14, note)
    return y - h


def para(x, y, text, width, size=10.5, font=None, color=None, lead=1.45):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawString(x, y - size, ln); y -= size * lead
    return y


def para_c(y, text, width, size=10.5, font=None, color=None, lead=1.45):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawCentredString(PW / 2, y - size, ln); y -= size * lead
    return y


HEAD = 36                 # fix round 3: card header band (title 0.25 in from the top border)


def card(x, y, w, h, title=None, fill=white, stroke=None):
    c.setStrokeColor(stroke or d.HAIR); c.setLineWidth(0.9); c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    reg(title or "card", x, y - h, w, h, 8)
    if title:
        c.setFillColor(d.T); c.roundRect(x, y - HEAD, w, HEAD, 8, fill=1, stroke=0); c.rect(x, y - HEAD, w, 10, fill=1, stroke=0)
        c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(x + PAD, y - 28, title.upper())  # fix round 3: 0.25 in from top and left


def level_tab(level):
    txt = "LEVEL 1  ·  AGES 6-9" if level == 1 else "LEVEL 2  ·  AGES 10+"
    w = stringWidth(txt, d.FM, 8) + 20
    c.setFillColor(d.T if level == 1 else GTINT); c.setStrokeColor(d.P if level == 1 else GREEN); c.setLineWidth(0.9)
    c.roundRect(R - w, PH - M - 18, w, 18, 9, fill=1, stroke=1)
    c.setFillColor(d.D); c.setFont(d.FM, 8); c.drawCentredString(R - w / 2, PH - M - 12.5, txt)
    for k in range(level):
        leaf(R - w - 12 - k * 13, PH - M - 18, 16, GOLD if level == 1 else GREEN, GOLDT if level == 1 else GTINT)


def cutline(x0, y0, x1, y1):
    c.setStrokeColor(d.MUT); c.setLineWidth(0.6); c.setDash(4, 3); c.line(x0, y0, x1, y1); c.setDash()


# ================================================================== 1 cover (frame style, drawn here so the lower half carries the harvest row)
def cover(title_lines, subtitle, pages, kicker):
    d.page += 1
    c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    for inset, w in ((36, 1.6), (46, 0.6)):
        c.setStrokeColor(d.P); c.setLineWidth(w); c.rect(inset, inset, PW - 2 * inset, PH - 2 * inset, fill=0, stroke=1)
    d._spaced(PW / 2, PH - 120, kicker, 11, d.P, d.FM)
    d._ornament(PW / 2, PH - 145)
    size = 54
    while max(stringWidth(t, d.S, size) for t in title_lines) > PW - 180: size -= 1
    ty = PH - 215
    for t in title_lines:
        c.setFont(d.S, size); c.setFillColor(d.D); c.drawCentredString(PW / 2, ty, t); ty -= size * 1.08
    y = ty - 14
    c.setFillColor(d.INK); c.setFont(d.SS, 17)
    for ln in gs.wrap(subtitle, d.SS, 17, PW - 220):
        c.drawCentredString(PW / 2, y, ln); y -= 24
    # two level pills
    for i, (txt, f, s_) in enumerate((("LEVEL 1  ·  AGES 6-9", d.T, d.P), ("LEVEL 2  ·  AGES 10+", GTINT, GREEN))):
        w = 170; x = PW / 2 - w - 8 + i * (w + 16)
        c.setFillColor(f); c.setStrokeColor(s_); c.setLineWidth(1.1); c.roundRect(x, y - 22, w, 28, 14, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawCentredString(x + w / 2, y - 12, txt)
    # fix round 2: "inside the kit" strip fills the old empty band with real facts (all on pages 2-16)
    st, sb = y - 38, 282
    c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.9); c.roundRect(96, sb, PW - 192, st - sb, 10, fill=1, stroke=1)
    reg("cover strip", 96, sb, PW - 192, st - sb, 10)
    tiles = [("4 clues", "each in 2 levels"), ("8 hints", "cut-out hint cards"), ("45 min", "1 to 12 players"), ("Host guide", "+ answer key")]
    tw_ = (PW - 192) / 4
    for k, (big, small) in enumerate(tiles):
        tx = 96 + k * tw_ + tw_ / 2
        if k: c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.line(96 + k * tw_, sb + PAD + 5, 96 + k * tw_, st - PAD - 5)
        fs = 20
        while stringWidth(big, d.S, fs) > tw_ - 2 * PAD - 4: fs -= 0.5
        c.setFillColor(d.D); c.setFont(d.S, fs); c.drawCentredString(tx, sb + (st - sb) / 2 + 2, big)
        c.setFillColor(d.MUT); c.setFont(d.F, 9); c.drawCentredString(tx, sb + (st - sb) / 2 - 16, small)
    assert sb - 266 >= 14 and st < y - 30, ("cover strip spacing", sb, st, y)
    # harvest row
    yb = 196
    pumpkin(PW / 2 - 170, yb, 70); apple(PW / 2 - 92, yb, 54); pie(PW / 2, yb, 96); acorn(PW / 2 + 90, yb, 54); pumpkin(PW / 2 + 168, yb, 62)
    leaf(PW / 2 - 222, yb, 46); leaf(PW / 2 + 222, yb, 46, GREEN, GTINT)
    c.setStrokeColor(d.HAIR); c.setLineWidth(1); c.line(110, yb - 2, PW - 110, yb - 2)
    c.setFillColor(d.T); c.rect(46.6, 46.6, PW - 93.2, 120, fill=1, stroke=0)
    d._pill(PW / 2, 118, f"{pages} PAGES")
    d._spaced(PW / 2, 80, "PRINTABLE  ·  INSTANT DOWNLOAD", 9.5, d.MUT, d.FM)
    c.setFont(d.F, 8.5); c.setFillColor(d.MUT); c.drawCentredString(PW / 2, 24, "GM's Digital Creations")
    c.showPage()


cover(["Thanksgiving", "Escape Room"],
      "The Pie Safe: one story, two levels. No phone or internet needed.",
      16, "PRINTABLE ESCAPE GAME")

# ================================================================== 2 game master guide
d.start("Game Master Guide", "Everything you need to run a 45-minute Thanksgiving escape game at home, at Grandma's or in a classroom.", kicker="Read this first")
y = d.y
colw = (R - L - 16) / 2
TOPH = 284                # fix round 3: taller top cards so text keeps 0.25 in on every side
IW = colw - 2 * PAD
card(L, y, colw, TOPH, "How the game works")
yy = para(L + PAD, y - 42, "Grandma Hazel locked the four Thanksgiving pies in the old Pie Safe and mixed up the 4-digit code. Players solve 4 clues. Each clue gives one digit. The 4 digits, in order, open the safe.", IW, 10)
yy = para(L + PAD, yy - 4, "Two levels, one story. Every clue comes in Level 1 (ages 6-9: counting, pictures, simple codes) and Level 2 (ages 10+: shift cipher, picture math, a maze, a logic grid). Both levels of a clue lead to the SAME digit, so brothers, sisters and cousins of different ages play together at the same table and can check each other.", IW, 10)
yy = para(L + PAD, yy - 4, "Players: 1 to 12, in teams of 2 to 4. Time: about 45 minutes.", IW, 10, font=d.FM)
x2 = L + colw + 16
card(x2, y, colw, TOPH, "What you need")
items = ["This PDF, printed (Letter or A4)", "Pencils and a few crayons", "Scissors and tape", "5 envelopes per team (or folded paper)", "A timer or clock", "No phone, app, QR code or internet"]
yy = y - 44
for it in items:
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x2 + PAD + 3, yy - 10, 10, 10, 2, fill=0, stroke=1)
    yy = para(x2 + PAD + 20, yy + 1, it, IW - 20, 9.6) - 3
yy = para(x2 + PAD, yy - 6, "Printing: ink-light pages (white paper, thin lines). Every puzzle works in black and white. On A4, choose \"Fit to page\".", IW, 9, color=d.MUT)
yy = para(x2 + PAD, yy - 6, "Play it again: the other level makes a new game, so a team that played Level 1 this year can try Level 2 next time.", IW, 9, color=d.MUT)
yy = para(x2 + PAD, yy - 6, "Big group? Print one set of clue sheets and lock tags per team and race to the Pie Safe.", IW, 9, color=d.MUT)
assert yy >= y - TOPH + PAD, ("p02 what-you-need overflows", y - TOPH + PAD - yy)
y -= TOPH + 14
card(L, y, R - L, y - BOTTOM, "Set up in 10 minutes")
steps = [
    "Print pages 3 to 14 and 16. Each team gets the clue sheets for its level (Level 1 or Level 2). Mixed-age team? Give it both.",
    "Make one set of 5 envelopes per team. Cut out the lock tags (page 13, one page per team) and tape one on each envelope: Clue 1, Clue 2, Clue 3, Clue 4 and the Pie Safe.",
    "Put each clue's sheets in its envelope, and the Pie Safe sheet (page 12) in the Clue 1 envelope so teams record digits as they go. The certificates (page 16) go in the Pie Safe envelope.",
    "Cut out the hint cards (page 14) and keep them with the Answer Key (page 15). Players never see page 15.",
    "Read the mission letter (page 3) out loud, start the 45-minute timer and hand out the Clue 1 envelope.",
    "When a team finds a digit, they write it on the next envelope's lock tag and show you. Check it on the Answer Key. Right? They open that envelope. Not yet? They keep trying or ask for a hint.",
    "Each team may ask for 3 hint cards. When the 4-digit code is right, read the victory note on page 15 and let the team open the Pie Safe envelope: their certificates are inside.",
]
# fix round 3: numbered steps drawn INSIDE the card (badges 0.25 in+ from the left border, last line
# 0.25 in+ above the bottom border); the font steps down until the list fits.
def steps_in(x, top, w, items, size, gap, draw=True):
    yy = top
    for i, it in enumerate(items):
        if draw:
            c.setFillColor(d.T); c.circle(x + 9, yy - size * 0.62, 9, fill=1, stroke=0)
            c.setFillColor(d.P); c.setFont(d.FM, 8.5); c.drawCentredString(x + 9, yy - size * 0.62 - 3, str(i + 1))
        c.setFillColor(d.INK); c.setFont(d.F, size)
        for ln in gs.wrap(it, d.F, size, w - 28):
            if draw: c.drawString(x + 28, yy - size, ln)
            yy -= size * 1.42
        yy -= gap
    return yy + gap - size * 0.42          # bottom of the last line's descenders


sz = 10.4
while steps_in(L + PAD, y - 50, R - L - 2 * PAD, steps, sz, 6, draw=False) < BOTTOM + PAD + 2 and sz > 8.6: sz -= 0.1
end_y = steps_in(L + PAD, y - 50, R - L - 2 * PAD, steps, sz, 6)
assert end_y >= BOTTOM + PAD, ("p02 set-up list too low", end_y - BOTTOM)
d.end()

# ================================================================== 3 mission letter
d.start("The Pie Safe", "Read this letter out loud to start the game.", kicker="Your mission", centered=True)
y = d.y
h = 252                   # fix round 3: shorter letter so the code tracker card has room below its header
c.setFillColor(GOLDT); c.setStrokeColor(GOLD); c.setLineWidth(1.2)
c.roundRect(L + 10, y - h, R - L - 20, h, 12, fill=1, stroke=1)
reg("mission letter", L + 10, y - h, R - L - 20, h, 12)
for sx, sy in ((L + 42, y - 46), (R - 42, y - 46)): leaf(sx, sy, 24)   # fix round 3: corner leaves 0.25 in+ inside, above the text
letter = [
    "Dear Thanksgiving Helpers,",
    "This morning I baked four pies and locked them in the old Pie Safe so the dog could not reach them... and now I cannot remember the code! No code, no pie after dinner.",
    "I am a careful cook, so I hid 4 clues around the kitchen. Each clue gives one digit of the code. Solve all 4, put the digits in order and the Pie Safe will open.",
    "Please hurry. Dinner is on the table in 45 minutes!",
    "With love, Grandma Hazel (head cook and pie keeper)",
]
yy = y - 52
for i, t in enumerate(letter):
    f = d.SB if i in (0, 4) else d.SS
    yy = para(L + 46, yy, t, R - L - 92, 12, font=f, color=d.D, lead=1.4) - 7
assert yy + 7 + 2 >= y - h + PAD, ("p03 letter text too low", yy + 10 - (y - h + PAD))
y -= h + 14
card(L, y, R - L, 162, "Your team")
rows = [("Team name", None), ("Players", None), ("Level (circle):", "LEVEL 1   or   LEVEL 2   or   BOTH"), ("Start time", "Escape time")]
yy = y - 56
for lab, extra in rows:
    c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawString(L + PAD, yy, lab)
    if lab == "Start time":
        c.setStrokeColor(d.HAIR); c.line(L + 90, yy - 2, L + 230, yy - 2)
        c.drawString(L + 260, yy, "Escape time"); c.line(L + 330, yy - 2, R - PAD, yy - 2)
    elif extra:
        c.setFillColor(d.INK); c.setFont(d.F, 10); c.drawString(L + 120, yy, extra)
    else:
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.line(L + 90, yy - 2, R - PAD, yy - 2)
    yy -= 28
y -= 162 + 10
card(L, y, R - L, y - BOTTOM, "Pie Safe code tracker: write each digit as you find it")
bw = 64; gap = (R - L - 4 * bw) / 5
for i in range(4):
    bx = L + gap + i * (bw + gap); by = BOTTOM + PAD + 14
    assert y - HEAD - 8 >= by + 42, ("p03 tracker card too short", y - BOTTOM)
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(bx, by, bw, 42, 8, fill=1, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.FM, 8); c.drawCentredString(bx + bw / 2, by - 12, f"CLUE {i + 1}")
d.end()

# ================================================================== 4 clue 1 level 1
d.start("The Recipe Card Code", "Grandma wrote the first digit on a recipe card in her secret number code. Each number stands for one letter.", kicker="Clue 1", centered=True)
level_tab(1)
y = d.y
card(L, y, R - L, 128, "The code key: A is 1, B is 2, C is 3...")
cw = (R - L - 2 * PAD - 4) / 13
for row in range(2):
    for i in range(13):
        n = row * 13 + i; x = L + PAD + 2 + i * cw; yy = y - 40 - row * 36
        c.setFillColor(d.T if row == 0 else GTINT); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
        c.rect(x, yy - 32, cw, 32, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.S, 13); c.drawCentredString(x + cw / 2, yy - 16, chr(65 + n))
        c.setFillColor(d.INK); c.setFont(d.F, 8.5); c.drawCentredString(x + cw / 2, yy - 28, str(n + 1))
y -= 142


def tag_row(y, nums, h=108, title=None):
    w = R - L - 40
    card_icon(L + 20, y - h, w, h, fill=white)
    if title:
        c.setFillColor(d.MUT); c.setFont(d.FM, 8.5); c.drawString(L + 70, y - 26, title)
    n = len(nums); bw = 52; gap = 12; tot = n * bw + (n - 1) * gap; x0 = L + 20 + (w - tot) / 2  # centred in the card (fix round 1)
    for i, v in enumerate(nums):
        x = x0 + i * (bw + gap)
        c.setFillColor(d.D); c.setFont(d.S, 20); c.drawCentredString(x + bw / 2, y - 50, str(v))
        c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1); c.roundRect(x, y - h + PAD + 2, bw, 34, 5, fill=1, stroke=1)
    return y - h


c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(L, y - 12, "Warm up: decode this card first")
y = tag_row(y - 22, pz.a1z26(pz.A1_WARMUP), title="WRITE A LETTER IN EACH BOX")
y -= 22
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(L, y - 12, "Grandma's secret card")
y = tag_row(y - 22, pz.a1z26(pz.A1Z26_MSG), h=108, title="THE SECRET WORD IS A NUMBER")
y -= 22
y = answer_box(y, "The first digit is")
y -= 24
print("p04 room under the answer box", round(y - BOTTOM, 1))
if y - BOTTOM >= 64:      # fix round 3: bonus lines only when they fit whole above the footer gap
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(L, y - 10, "Bonus fun: write your own name in Grandma's code")
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.7)
    yy = y - 40
    while yy > BOTTOM + 8:
        c.line(L, yy, R, yy); yy -= 28
d.end()

# ================================================================== 5 clue 1 level 2
d.start("The Scrambled Recipe Note", "Grandma hid the first digit in a shift code: every letter moved the same number of steps along the alphabet.", kicker="Clue 1", centered=True)
level_tab(2)
y = d.y
h = 196
card(L, y, R - L, h, fill=GOLDT, stroke=GOLD)
c.setFillColor(d.MUT); c.setFont(d.FM, 8.5); c.drawString(L + PAD, y - 26, "THE NOTE FOUND UNDER THE ROLLING PIN")
words = pz.C1_CIPHER.split(" ")
lines_ = [words[:2], words[2:]]  # XLI JMVWX / HMKMX MW JMZI
bw, gp = 25, 4
yy = y - 52
for wl in lines_:
    total = sum(len(w) * (bw + gp) for w in wl) + (len(wl) - 1) * 18
    x = (PW - total) / 2
    for w in wl:
        for ch in w:
            c.setFillColor(d.D); c.setFont(d.S, 17); c.drawCentredString(x + bw / 2, yy, ch)
            c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x, yy - 34, bw, 26, 4, fill=1, stroke=1)
            x += bw + gp
        x += 18
    yy -= 62
c.setFillColor(d.D); c.setFont(d.SS, 13)
c.drawRightString(R - 30, y - h + 22, "Signed:  " + " ".join(pz.C1_SIGN))
y -= h + 16
d.y = y
d.heading("How to crack it", 13)
d.text("1.  The note is from Grandma Hazel, so the signature LEDIP must spell HAZEL. Count how many steps H moved to become L.", 10.2)
d.text("2.  Every letter in the note moved by that same number. Move each letter BACK that many steps (after A, go round to Z).", 10.2)
d.text("3.  Use the shift strip below: write the real letter under each code letter, then read the note.", 10.2)
y = d.y - 4
card(L, y, R - L, 106, "Shift strip")
cw = (R - L - 2 * PAD - 4) / 26
for i in range(26):
    x = L + PAD + 2 + i * cw
    c.setFillColor(d.T); c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.rect(x, y - 62, cw, 25, fill=1, stroke=1)
    c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawCentredString(x + cw / 2, y - 53, chr(65 + i))
    c.setFillColor(white); c.rect(x, y - 87, cw, 25, fill=1, stroke=1)
y -= 106 + 18
y = answer_box(y, "The first digit is")
y -= 26
if y - BOTTOM > 60:
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(L, y - 10, "Scratch space")
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.7)
    yy = y - 36
    while yy > BOTTOM + 8:
        c.line(L, yy, R, yy); yy -= 26
d.end()

# ================================================================== 6 clue 2 level 1
d.start("Count the Pantry Shelf", "Grandma says: count everything on my pantry shelf, then do my sum to find the second digit.", kicker="Clue 2", centered=True)
level_tab(1)
y = d.y
gh = 290
card(L, y, R - L, gh, fill=white, stroke=d.P)
cols, rows = pz.SCENE_COLS, pz.SCENE_ROWS
cw = (R - L - 2 * PAD - 16) / cols; ch_ = (gh - 30) / rows
rnd = random.Random(3)
for r in range(rows):
    sy = y - 12 - (r + 1) * ch_ + 8
    c.setFillColor(HexColor("#EADCC8")); c.setStrokeColor(HexColor("#B9A07E")); c.setLineWidth(0.7)
    c.rect(L + PAD + 2, sy - 6, R - L - 2 * PAD - 4, 6, fill=1, stroke=1)
for kind, (cx, cy) in pz.l1_scene():
    x = L + PAD + 8 + cx * cw + cw / 2 + rnd.uniform(-8, 8); yb = y - 12 - (cy + 1) * ch_ + 8
    x = min(max(x, L + PAD + 26), R - PAD - 26)       # fix round 3: icons 0.25 in+ inside the shelf card
    ICON[kind](x, yb, 44)
y -= gh + 16
bw = (R - L - 40) / 3
for i, k in enumerate(("pumpkin", "apple", "acorn")):
    x = L + i * (bw + 20)
    card(x, y, bw, 96)
    ICON[k](x + 44, y - 96 + PAD + 2, 42)
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(x + 76, y - 32, NAMES[k])
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.1); c.roundRect(x + 76, y - 96 + PAD + 2, 44, 34, 6, fill=1, stroke=1)
y -= 96 + 14
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawCentredString(PW / 2, y - 12, "Grandma's sum")
y -= 26
seq = [("box", "pumpkins"), ("op", "+"), ("box", "apples"), ("op", "-"), ("box", "acorns"), ("op", "="), ("ans", "")]
tot = 4 * 70 + 3 * 34
x = (PW - tot) / 2
for kind, t in seq:
    if kind == "op":
        c.setFillColor(d.D); c.setFont(d.S, 26); c.drawCentredString(x + 17, y - 40, t); x += 34
    else:
        c.setFillColor(d.T if kind == "ans" else white); c.setStrokeColor(d.P if kind == "ans" else d.D); c.setLineWidth(1.4 if kind == "ans" else 1.1)
        c.roundRect(x, y - 56, 70, 52, 8, fill=1, stroke=1)
        c.setFillColor(d.MUT); c.setFont(d.F, 8.5); c.drawCentredString(x + 35, y - 70, t if t else "digit 2")
        x += 70
y -= 84
para_c(y, "Tip: put a tiny dot on each picture as you count it so you never count one twice.", R - L, 9.8, color=d.MUT)
d.end()

# ================================================================== 7 clue 2 level 2
d.start("Harvest Picture Sums", "Each picture stands for a different whole number. Work out all three, then solve Grandma's last line.", kicker="Clue 2", centered=True)
level_tab(2)
y = d.y


def eq_row(y, syms, ops, result, h=78, ask=False):
    card(L, y, R - L, h, fill=GOLDT if ask else white, stroke=GOLD if ask else d.HAIR)
    n = len(syms); x = L + 40
    for i, s in enumerate(syms):
        ICON[s](x + 22, y - h + PAD + 3, 37); x += 54
        if i < n - 1:
            c.setFillColor(d.D); c.setFont(d.S, 24); c.drawCentredString(x + 10, y - h / 2 - 8, ops[i]); x += 26
    c.setFillColor(d.D); c.setFont(d.S, 24); c.drawCentredString(x + 14, y - h / 2 - 8, "=")
    if ask:
        c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.4); c.roundRect(x + 38, y - h + PAD + 3, 54, h - 2 * PAD - 6, 8, fill=1, stroke=1)
        c.setFillColor(d.MUT); c.setFont(d.F, 8.5); c.drawString(x + 100, y - h / 2 - 3, "digit 2")
    else:
        c.setFont(d.S, 26); c.drawString(x + 38, y - h / 2 - 9, str(result))
    return y - h


ops_map = {"+": "+", "x": "×"}
for i, (syms, op, tot) in enumerate(pz.L2_EQS):
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L, y - 9, f"LINE {i + 1}")
    y = eq_row(y - 14, syms, [ops_map[op]] * (len(syms) - 1), tot) - 10
c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L, y - 9, "GRANDMA'S LAST LINE")
y = eq_row(y - 14, pz.L2_ASK[0], pz.L2_ASK[1], None, h=84, ask=True) - 12
vh = y - BOTTOM
card(L, y, R - L, vh, "Write what each picture is worth")
bw = (R - L - 60) / 3
cyv = y - HEAD - (vh - HEAD) / 2
for i, k in enumerate(("pumpkin", "apple", "acorn")):
    x = L + 20 + i * (bw + 10)
    ICON[k](x + 26, cyv - 23, 46)
    c.setFillColor(d.D); c.setFont(d.S, 22); c.drawString(x + 62, cyv - 8, "=")
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.1); c.roundRect(x + 84, cyv - 22, 56, 44, 6, fill=1, stroke=1)
d.end()

# ================================================================== 8 clue 3 level 1
d.start("The Tangled Pumpkin Vines", "The garden vines are all tangled up! Follow the vine from the PUMPKIN to find which pie it reaches.", kicker="Clue 3", centered=True)
level_tab(1)
y = d.y
top, bot = y - 70, BOTTOM + 196
xs = [L + 70 + i * (R - L - 140) / 3 for i in range(4)]
for i, p in enumerate(pz.PLUGS):
    x = xs[i]
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x - 26, top + 6, 52, 52, 8, fill=1, stroke=1)
    ICON[p](x, top + 14, 34)
    c.setFillColor(d.D); c.rect(x - 5, top - 4, 10, 10, fill=1, stroke=0)
# strands: each row of waypoints is a permutation of the 4 columns, so strands never share a
# point and every crossing happens mid-curve at a clear angle (verified: rows are permutations)
ROWS = pz.VINE_ROWS
JIT = {"pumpkin": 12, "apple": -10, "acorn": 8, "leaf": -14}
for k in range(3): assert sorted(v[k] for v in ROWS.values()) == [0, 1, 2, 3]
for p, bi in pz.VINES.items():
    x0 = xs[pz.PLUGS.index(p)]; x1 = xs[bi]
    w = ROWS[p]; n = len(w)
    pts = [(x0, top - 4)] + [(xs[w[k]] + JIT[p], top - 4 - (k + 1) * (top - bot) / (n + 1)) for k in range(n)] + [(x1, bot + 8)]
    c.setStrokeColor(GREEN); c.setLineWidth(2.6)
    path = c.beginPath(); path.moveTo(*pts[0])
    for k in range(1, len(pts)):
        (ax, ay), (bx, by) = pts[k - 1], pts[k]
        my = (ay + by) / 2
        path.curveTo(ax, my, bx, my, bx, by)
    c.drawPath(path, fill=0, stroke=1)
for i, v in enumerate(pz.PIES):
    pie(xs[i], bot - 46, 84, v)
y = bot - 76
para_c(y + 8, "Trace it with your finger or a crayon. The number on that pie is the third digit.", R - L, 10, color=d.MUT)
answer_box(y - 14, "The third digit is")
d.end()

# ================================================================== 9 clue 3 level 2
d.start("The Acorn Maze", "Find the only path from the Kitchen Door to the Pie Safe. Count the acorns ON your path; acorns in dead ends do not count.", kicker="Clue 3", centered=True)
level_tab(2)
walls, D, path, on, off = pz.acorns()
y = d.y - 6
cell = min((R - L - 20) / pz.MAZE_W, (y - 14 - 13 - 26 - AB_H - BOTTOM) / pz.MAZE_H)  # fix round 2: maze top 14, finish label, gap, box 58 all above BOTTOM
mw, mh = cell * pz.MAZE_W, cell * pz.MAZE_H
mx = (PW - mw) / 2; my = y - 14
MAZE_GEOM = (mx, my, cell)
c.setFillColor(white); c.setStrokeColor(d.D)
for (cx, cy) in on + off:
    acorn(mx + cx * cell + cell / 2, my - cy * cell - cell * 0.86, cell * 0.7)
c.setStrokeColor(d.D); c.setLineWidth(2); c.setLineCap(1)
for (cx, cy), ws in walls.items():
    x0, y0 = mx + cx * cell, my - cy * cell
    if "N" in ws and not (cx, cy) == (0, 0): c.line(x0, y0, x0 + cell, y0)
    if "W" in ws: c.line(x0, y0, x0, y0 - cell)
    if cy == pz.MAZE_H - 1 and "S" in ws and (cx, cy) != (pz.MAZE_W - 1, pz.MAZE_H - 1): c.line(x0, y0 - cell, x0 + cell, y0 - cell)
    if cx == pz.MAZE_W - 1 and "E" in ws: c.line(x0 + cell, y0, x0 + cell, y0 - cell)
c.setLineCap(0)
c.setFillColor(d.P); c.setFont(d.FM, 8.5)
c.drawString(mx, my + 5, "START: KITCHEN DOOR")
c.drawRightString(mx + mw, my - mh - 13, "FINISH: THE PIE SAFE")
answer_box(my - mh - 26, "The third digit is")
d.end()

# ================================================================== 10 clue 4 level 1
d.start("Leaf Sudoku", "Fill the grid so every row, every column and every thick-lined box has 1, 2, 3 and 4 once each.", kicker="Clue 4", centered=True)
level_tab(1)
y = d.y - 6
HOW = "Start with a row or box that already has 3 numbers: the missing one is easy to spot. Write in pencil so you can rub out. When the grid is full, look at the square with the gold leaf: that number is the fourth digit."
HP_H = HEAD + 8 + len(gs.wrap(HOW, d.F, 9.8, R - L - 2 * PAD)) * 9.8 * 1.45 + PAD   # fix round 3: card sized from its text
gsz = min(372, y - BOTTOM - (20 + HP_H + 18 + AB_H)); cs = gsz / 4; gx = (PW - gsz) / 2  # fix round 2: grid sized so the answer box clears the footer
for r in range(4):
    for col in range(4):
        x, yy = gx + col * cs, y - (r + 1) * cs
        star_cell = (r, col) == pz.SUDOKU_MARK
        c.setFillColor(GOLDT if star_cell else (d.T if pz.SUDOKU_GIVEN[r][col] else white)); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(x, yy, cs, cs, fill=1, stroke=1)
        v = pz.SUDOKU_GIVEN[r][col]
        if v:
            c.setFillColor(d.D); c.setFont(d.S, 40); c.drawCentredString(x + cs / 2, yy + cs / 2 - 14, str(v))
        if star_cell:
            leaf(x + cs - 18, yy + cs - 30, 24)
c.setStrokeColor(d.D); c.setLineWidth(2.6)
c.rect(gx, y - gsz, gsz, gsz, fill=0, stroke=1)
c.line(gx + gsz / 2, y, gx + gsz / 2, y - gsz); c.line(gx, y - gsz / 2, gx + gsz, y - gsz / 2)
y -= gsz + 20
card(L, y, R - L, HP_H, "How to play")
hp_end = para(L + PAD, y - 42, HOW, R - L - 2 * PAD, 9.8)
assert hp_end + 1.5 >= y - HP_H + PAD, ("p10 how-to-play text too low", hp_end)
y -= HP_H + 18
answer_box(y, "The fourth digit is")
d.end()

# ================================================================== 11 clue 4 level 2
d.start("The Kids' Table Puzzle", "Four cousins sit in chairs 1 to 4 at the kids' table. Each brought one dish. Use the clues to find which chair the pie is at.", kicker="Clue 4", centered=True)
level_tab(2)
y = d.y
CLH = HEAD + 10 + 20 * len(pz.LOGIC_CLUES) + PAD
card(L, y, R - L, CLH, "Grandma's clues")
yy = y - HEAD - 14
for i, t in enumerate(pz.LOGIC_CLUES):
    c.setFillColor(d.T); c.circle(L + PAD + 9, yy - 4, 8, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 8.5); c.drawCentredString(L + PAD + 9, yy - 7, str(i + 1))
    para(L + PAD + 26, yy + 6, t, R - L - 2 * PAD - 26, 10.2); yy -= 20
y -= CLH + 12
# logic grid
benches = ["Chair 1", "Chair 2", "Chair 3", "Chair 4"]
toys = ["Corn", "Cranberry", "Pie", "Rolls"]
cs = 26; lab_w = 80; head_h = 62  # fix round 1: answer box clears the footer
gx = (PW - (lab_w + 8 * cs)) / 2 + lab_w
gy = y - head_h
c.setFillColor(d.D); c.setFont(d.FM, 8.5)
for i, t in enumerate(benches + toys):
    c.saveState(); c.translate(gx + i * cs + cs / 2 + 3, gy + 6); c.rotate(60); c.drawString(0, 0, t); c.restoreState()
for i, t in enumerate(pz.COUSINS + toys):
    c.drawRightString(gx - 8, gy - i * cs - cs / 2 - 3, t)
for blk_r in range(2):
    for blk_c in range(2 - blk_r):
        x0, y0 = gx + blk_c * 4 * cs, gy - blk_r * 4 * cs
        for r in range(4):
            for col in range(4):
                c.setFillColor(white if (r + col) % 2 else HexColor("#FBF3F1")); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
                c.rect(x0 + col * cs, y0 - (r + 1) * cs, cs, cs, fill=1, stroke=1)
        c.setStrokeColor(d.D); c.setLineWidth(1.6); c.rect(x0, y0 - 4 * cs, 4 * cs, 4 * cs, fill=0, stroke=1)
c.setFillColor(d.MUT); c.setFont(d.F, 8.5)
para(gx + 4 * cs + 14, gy - 4 * cs - 14, "Mark X for \"no\" and a dot for \"yes\". Each row and column has one yes.", 4 * cs - 14, 8.6, color=d.MUT)
y = gy - 8 * cs - 13
assert y - AB_H >= (M - 1) + 20, ("p11 answer box too low", y - AB_H)
answer_box(y, "The pie is at chair")
d.end()

# ================================================================== 12 the vault
d.start("Open the Pie Safe", "Write the 4 digits in order. Show the Game Master. If the code is right, the Pie Safe swings open!", kicker="The final lock", centered=True)
y = d.y - 4
r = 160; cx, cy = PW / 2, y - r - 6
c.setFillColor(HexColor("#EFEAE3")); c.setStrokeColor(d.D); c.setLineWidth(2.2); c.circle(cx, cy, r, fill=1, stroke=1)
c.setFillColor(white); c.setLineWidth(1.2); c.circle(cx, cy, r - 18, fill=1, stroke=1)
for i in range(12):
    a = i * math.pi / 6
    c.setFillColor(d.D); c.circle(cx + (r - 9) * math.cos(a), cy + (r - 9) * math.sin(a), 3, fill=1, stroke=0)
c.setFillColor(GOLDT); c.setStrokeColor(GOLD); c.circle(cx, cy + 58, 30, fill=1, stroke=1)
pie(cx, cy + 40, 46)
bw = 50; gp = 12; tot = 4 * bw + 3 * gp; bx = cx - tot / 2
for i in range(4):
    x = bx + i * (bw + gp)
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.6); c.roundRect(x, cy - 52, bw, 62, 8, fill=1, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.FM, 7.5); c.drawCentredString(x + bw / 2, cy - 66, f"CLUE {i + 1}")
c.setStrokeColor(d.D); c.setLineWidth(5); c.setLineCap(1)
c.line(cx - 40, cy - 100, cx + 40, cy - 100); c.setLineCap(0)
y = cy - r - 22
card(L, y, R - L, y - BOTTOM, "Wrong code? Check these before you ask for a hint")
checks = ["Are the digits in clue order: Clue 1, Clue 2, Clue 3, Clue 4?",
          "Mixed-age team? Both levels of a clue give the same digit. Compare your answers.",
          "Recount Clue 2 and retrace Clue 3 slowly: those are the easiest to slip on.",
          "Still stuck? Ask the Game Master for a hint card (3 per team).",
          "Code right? Open the Pie Safe envelope together: your Escape Expert certificates are inside. Write your escape time on page 3!"]
yy = y - HEAD - 8; inset = 20; sz = 10.5  # fix round 1: checkboxes 20 pt (0.28 in) inside the card border
for t in checks:
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(L + inset, yy - sz - 1.5, sz, sz, 2.2, fill=0, stroke=1)
    c.setFillColor(d.INK); c.setFont(d.F, sz)
    for ln in gs.wrap(t, d.F, sz, R - L - 2 * inset - sz - 8):
        c.drawString(L + inset + sz + 8, yy - sz, ln); yy -= sz * 1.42
    yy -= 7
assert yy + 7 + 14.9 - 10.5 - 2.5 >= BOTTOM + PAD, ('p12 checks too low', yy)  # last line's descenders
d.end()

# ================================================================== 13 lock tags
d.start("Envelope Lock Tags", "Cut out and tape one tag to each envelope. A team writes its digit on the tag and shows the Game Master to unlock it.", kicker="Game Master: cut out", centered=True)
y = d.y
tw = (R - L - 18) / 2; th = (y - BOTTOM - 24) / 3
tags = [("Clue 1", "Open me first!", 0, "Recipe Card Code / Scrambled Recipe Note"),
        ("Clue 2", "Locked: needs the Clue 1 digit", 1, "Count the Pantry Shelf / Picture Sums"),
        ("Clue 3", "Locked: needs the Clue 2 digit", 1, "Tangled Pumpkin Vines / Acorn Maze"),
        ("Clue 4", "Locked: needs the Clue 3 digit", 1, "Leaf Sudoku / Kids' Table Puzzle"),
        ("The Pie Safe", "Locked: write the 4-digit code", 4, "Inside: Escape Expert certificates (page 16)"),
        ("Game Master", "Hint cards + answer key", 0, "Players: do not open")]
for i, (t, sub, boxes, inside) in enumerate(tags):
    col, row = i % 2, i // 2
    x = L + col * (tw + 18); yy = y - row * (th + 12)
    c.setStrokeColor(d.P if i < 5 else GREEN); c.setLineWidth(1.3); c.setFillColor(white)
    c.setDash(5, 3); c.roundRect(x, yy - th, tw, th, 10, fill=1, stroke=1); c.setDash()
    reg("lock tag " + t, x, yy - th, tw, th, 10)
    padlock(x + PAD + 22, yy - 66, 40)
    c.setFillColor(d.D); c.setFont(d.S, 19); c.drawString(x + 72, yy - 40, t)
    c.setFillColor(d.INK); para(x + 72, yy - 48, sub, tw - 72 - PAD, 9.4)
    if boxes == 1:
        c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x + tw / 2 - 26, yy - th + 38, 52, 50, 8, fill=1, stroke=1)
    elif boxes:
        for k in range(boxes):
            c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x + tw / 2 - 98 + k * 50, yy - th + 38, 44, 48, 7, fill=1, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.F, 8); c.drawCentredString(x + tw / 2, yy - th + PAD + 4, inside)
d.end()

# ================================================================== 14 hint cards
d.start("Hint Cards", "Cut out, fold on the line so Hint 2 stays hidden, and hand over one card at a time (3 per team).", kicker="Game Master only", centered=True)
HINTS = [
    ("Clue 1 · Level 1", "Find 16 in the code key. Which letter is above it?", "The secret word is a number word with 4 letters."),
    ("Clue 1 · Level 2", "H to L is 4 steps forward. So go 4 steps BACK for every letter.", "X goes back to T, L to H, I to E: the first word is THE."),
    ("Clue 2 · Level 1", "Count one kind of picture at a time, and dot each one.", "There are more acorns than apples. Did you take the acorns away last?"),
    ("Clue 2 · Level 2", "Line 1 has three of the same picture. Divide 9 by 3.", "Pumpkin first. Then line 2 gives the apple and line 3 the acorn."),
    ("Clue 3 · Level 1", "Put a crayon on the pumpkin and never lift it off its vine.", "At every crossing, stay on the same vine you came in on."),
    ("Clue 3 · Level 2", "Mazes are easier from the end: try starting at the Pie Safe.", "Shade dead ends as you find them. Only acorns on the open path count."),
    ("Clue 4 · Level 1", "Row 2 already has 1 and 2. Which two numbers are missing?", "The leaf square's row has a 4, and its column has a 2."),
    ("Clue 4 · Level 2", "Clues 1 and 3 together tell you where Ada and Milo sit.", "Rosa has the last chair. Which dishes can sit right next to her?"),
]
y = d.y
cw2 = (R - L - 14) / 2; chh = (y - BOTTOM - 3 * 10) / 4
for i, (t, h1, h2) in enumerate(HINTS):
    col, row = i % 2, i // 2
    x = L + col * (cw2 + 14); yy = y - row * (chh + 10)
    c.setStrokeColor(d.P if "Level 1" in t else GREEN); c.setLineWidth(1.1); c.setFillColor(white)
    c.setDash(5, 3); c.roundRect(x, yy - chh, cw2, chh, 8, fill=1, stroke=1); c.setDash()
    reg("hint card " + t, x, yy - chh, cw2, chh, 8)
    # fix round 3: every word 0.25 in+ inside the card; "HINT 1/2" labels hang left of their text
    c.setFillColor(d.T if "Level 1" in t else GTINT); c.roundRect(x + 1, yy - 31, cw2 - 2, 30, 7, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.FM, 8.5); c.drawString(x + PAD, yy - 26, t.upper())
    mid = yy - 31 - min(45, (chh - 31) * 0.5)        # fold just under Hint 1's 2 lines; Hint 2 gets the rest
    hw = 40; tw_h = cw2 - 2 * PAD - hw
    for lab, txt, top_ in (("HINT 1", h1, yy - 39), ("HINT 2", h2, mid - 9)):
        c.setFillColor(d.P); c.setFont(d.FM, 7.5); c.drawString(x + PAD, top_ - 9, lab)
        e = para(x + PAD + hw, top_, txt, tw_h, 9)
    assert e + 1.5 >= yy - chh + PAD, ("p14 hint 2 too low", t, e - (yy - chh))
    cutline(x + PAD, mid, x + cw2 - PAD, mid)
    c.setFillColor(d.MUT); c.setFont(d.F, 6.5); c.drawRightString(x + cw2 - PAD, mid + 3, "fold here")
d.end()

# ================================================================== 15 answer key
d.start("Answer Key", "Game Master only: keep this page hidden from players.", kicker="Game Master only")
sol_e, sol_t = pz.verify()[1]
rows = [
    ("1", "16 9 5 = PIE; 6 9 22 5 = FIVE", "Signature LEDIP = HAZEL (shift 4). Note reads THE FIRST DIGIT IS FIVE", "5"),
    ("2", "6 pumpkins + 4 apples - 8 acorns = 2", "Pumpkin 3, apple 5, acorn 4, so 3 + 4 - 5 = 2", "2"),
    ("3", "The pumpkin vine ends at pie 8", "The one path from door to Pie Safe passes 8 acorns (see map)", "8"),
    ("4", "The gold leaf square is 3", "Chair 1 Theo corn, 2 Ada rolls, 3 Milo pie, 4 Rosa cranberry", "3"),
]
d.table(["Clue", "Level 1 (ages 6-9)", "Level 2 (ages 10+)", "Digit"], [0.6, 3.4, 4.2, 0.8], rows, size=9.4, rowh=24)
y = d.y
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1.3); c.roundRect(L, y - 60, R - L, 60, 8, fill=1, stroke=1)
reg("safe code box", L, y - 60, R - L, 60, 8)
c.setFillColor(d.D); c.setFont(d.SB, 15); c.drawString(L + PAD + 4, y - 35, "Safe code:")
c.setFont(d.S, 22); c.drawString(L + 116, y - 37, "  ".join(map(str, pz.CODE)))
c.setFillColor(d.INK); c.setFont(d.F, 9.5); c.drawRightString(R - PAD - 4, y - 34, "Both levels give the same 4 digits.")
y -= 72
# sudoku solution + maze solution side by side
c.setFillColor(d.D); c.setFont(d.SB, 11.5); c.drawString(L, y - 10, "Sudoku solution"); c.drawString(L + 190, y - 10, "Maze solution path")
y -= 20
s_cs = 34; sx = L
for r in range(4):
    for col in range(4):
        x, yy = sx + col * s_cs, y - (r + 1) * s_cs
        c.setFillColor(GOLDT if (r, col) == pz.SUDOKU_MARK else white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.rect(x, yy, s_cs, s_cs, fill=1, stroke=1)
        c.setFillColor(d.D if pz.SUDOKU_GIVEN[r][col] else d.P); c.setFont(d.S, 15); c.drawCentredString(x + s_cs / 2, yy + 11, str(pz.SUDOKU_SOL[r][col]))
c.setStrokeColor(d.D); c.setLineWidth(1.6); c.rect(sx, y - 4 * s_cs, 4 * s_cs, 4 * s_cs, fill=0, stroke=1)
c.line(sx + 2 * s_cs, y, sx + 2 * s_cs, y - 4 * s_cs); c.line(sx, y - 2 * s_cs, sx + 4 * s_cs, y - 2 * s_cs)
mc = min((R - L - 190) / pz.MAZE_W, 0)
avail_h = y - BOTTOM - 150
mc = min((R - (L + 190)) / pz.MAZE_W, (y - 4 * s_cs - 120 - (BOTTOM)) / pz.MAZE_H + 999, 22)
mc = 20
mx2, my2 = L + 190, y
c.setStrokeColor(d.D); c.setLineWidth(1)
for (cx_, cy_), ws in walls.items():
    x0, y0 = mx2 + cx_ * mc, my2 - cy_ * mc
    if "N" in ws and (cx_, cy_) != (0, 0): c.line(x0, y0, x0 + mc, y0)
    if "W" in ws: c.line(x0, y0, x0, y0 - mc)
    if cy_ == pz.MAZE_H - 1 and "S" in ws and (cx_, cy_) != (pz.MAZE_W - 1, pz.MAZE_H - 1): c.line(x0, y0 - mc, x0 + mc, y0 - mc)
    if cx_ == pz.MAZE_W - 1 and "E" in ws: c.line(x0 + mc, y0, x0 + mc, y0 - mc)
c.setStrokeColor(d.P); c.setLineWidth(2.2); c.setLineCap(1); c.setLineJoin(1)
pth = c.beginPath()
for k, (cx_, cy_) in enumerate(path):
    px, py = mx2 + cx_ * mc + mc / 2, my2 - cy_ * mc - mc / 2
    pth.moveTo(px, py) if k == 0 else pth.lineTo(px, py)
c.drawPath(pth, fill=0, stroke=1); c.setLineCap(0); c.setLineJoin(0)
for (cx_, cy_) in on:
    c.setFillColor(GOLD); c.circle(mx2 + cx_ * mc + mc / 2, my2 - cy_ * mc - mc / 2, 4.2, fill=1, stroke=0)
c.setFillColor(d.MUT); c.setFont(d.F, 8.5)
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 12, "Gold dots = the 8")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 24, "acorns on the path.")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 36, "Acorns in dead ends")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 48, "do not count.")
yv = y - 4 * s_cs - 22
c.setFillColor(d.D); c.setFont(d.SB, 11.5); c.drawString(L, yv - 10, "Read aloud when")
c.drawString(L, yv - 25, "the safe opens:")
para(L, yv - 34, "\"The Pie Safe door creaks open and there they are: four golden pies, still warm! Grandma Hazel hugs every one of you. Thanks to your team, there is pie after dinner. You are official Thanksgiving Escape Experts!\"", 170, 9.6, font=d.SS, color=d.D)
d.end()

# ================================================================== 16 certificates
d.start("Escape Expert Certificates", None, kicker="Two per page: print one for every player", centered=True)
y = d.y + 6
ch2 = (y - BOTTOM - 14) / 2
for i in range(2):
    yy = y - i * (ch2 + 14)
    c.setFillColor(white); c.setStrokeColor(GOLD); c.setLineWidth(2); c.roundRect(L, yy - ch2, R - L, ch2, 12, fill=1, stroke=1)
    c.setStrokeColor(d.P); c.setLineWidth(0.7); c.roundRect(L + 7, yy - ch2 + 7, R - L - 14, ch2 - 14, 9, fill=0, stroke=1)
    reg("certificate (inner rule)", L + 7, yy - ch2 + 7, R - L - 14, ch2 - 14, 9)
    pumpkin(L + 52, yy - 82, 46); leaf(R - 52, yy - 86, 50)
    d._spaced(PW / 2, yy - 38, "THE PIE SAFE", 9, d.P, d.FM)
    c.setFillColor(d.D); c.setFont(d.S, 26); c.drawCentredString(PW / 2, yy - 72, "Certified Escape Expert")
    c.setFillColor(d.INK); c.setFont(d.SS, 12); c.drawCentredString(PW / 2, yy - 96, "This certifies that")
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.line(L + 90, yy - 128, R - 90, yy - 128)
    c.setFont(d.SS, 11.5); c.setFillColor(d.INK)
    c.drawCentredString(PW / 2, yy - 150, "opened the Pie Safe and saved Thanksgiving dessert.")
    c.setFont(d.FM, 9); c.setFillColor(d.MUT)
    c.drawString(L + 40, yy - ch2 + 56, "LEVEL"); c.line(L + 80, yy - ch2 + 54, L + 170, yy - ch2 + 54)
    c.drawString(L + 190, yy - ch2 + 56, "ESCAPE TIME"); c.line(L + 262, yy - ch2 + 54, L + 330, yy - ch2 + 54)
    c.drawString(L + 350, yy - ch2 + 56, "DATE"); c.line(L + 382, yy - ch2 + 54, R - 40, yy - ch2 + 54)
    c.setFont(d.SS, 10.5); c.setFillColor(d.D); c.drawCentredString(PW / 2, yy - ch2 + 7 + PAD + 4, "Signed: Grandma Hazel, Keeper of the Pies")
d.end()

# ================================================================== 17 thank-you (spec text verbatim)
c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
c.setStrokeColor(d.P); c.setLineWidth(1.3); c.rect(22, 22, PW - 44, PH - 44, fill=0, stroke=1)
c.setStrokeColor(d.A); c.setLineWidth(0.6); c.rect(28, 28, PW - 56, PH - 56, fill=0, stroke=1)
pie(PW / 2, PH - 254, 110)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 302, "You just made my day!")
d._ornament(PW / 2, PH - 326)
y = PH - 356
y = para_c(y, "Thank you for choosing a small, one-person shop over the big guys.", 420, 13, font=d.SS, lead=1.5) - 16
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 460, 13, font=d.SS, lead=1.5) - 22
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(PW / 2 - 200, y - 56, 400, 56, 12, fill=1, stroke=1)
reg("review box", PW / 2 - 200, y - 56, 400, 56, 12)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
parts = "How: Etsy app → You → Purchases → Leave a review".split("→")
widths = [stringWidth(p, d.FM, 12.5) for p in parts]; aw = stringWidth("→", "DejaVu", 12.5)
x = PW / 2 - (sum(widths) + aw * (len(parts) - 1)) / 2
c.setFillColor(d.D)
for i, p in enumerate(parts):
    c.setFont(d.FM, 12.5); c.drawString(x, y - 32, p); x += widths[i]
    if i < len(parts) - 1:
        c.setFont("DejaVu", 12.5); c.drawString(x, y - 32, "→"); x += aw
y -= 56 + 24
y = para_c(y, "Something not right? Message me first and I'll fix it fast.", 420, 13, font=d.SS, lead=1.5) - 40
c.setFillColor(d.P); c.setFont(d.SB, 14); c.drawCentredString(PW / 2, y - 6, "With thanks,")
c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 30, "GM's Digital Creations")
leaf(PW / 2 - 150, PH - 240, 40); leaf(PW / 2 + 150, PH - 240, 40, GREEN, GTINT)
c.showPage()
d.save()
print("built", OUT)


# ------------------------------------------------------------------ fix round 2: EVERY page's lowest element ends 0.25 in+ above the footer rule
def check_clearance(pdf, dpi=100):
    """Render every page and assert no ink sits between the footer rule and 0.25 in above it (x L..R).
    Pages without the kit footer (cover, thank-you) are checked against the same band at the same height."""
    import subprocess, tempfile, glob as _g
    from PIL import Image as _I
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, tmp + "/p"], check=True)
    k = dpi / 72.0
    rule = round((PH - FOOT_RULE) * k)
    x0, x1 = round(L * k) + 2, round(R * k) - 2
    res = []
    for n, f in enumerate(sorted(_g.glob(tmp + "/p-*.png")), 1):
        im = _I.open(f).convert("RGB"); px = im.load()
        bg = px[x0 + 5, rule - 3]
        has_rule = n not in (1, len(_g.glob(tmp + "/p-*.png")))
        top = rule - 2
        while top > 0:
            row_ink = any(sum(abs(a - b) for a, b in zip(px[x, top], bg)) > 40 for x in range(x0, x1))
            if row_ink: break
            top -= 1
        gap_in = (rule - top) / dpi
        res.append((n, round(gap_in, 3), has_rule))
    return res


def check_boxes(pdf, dpi=150):
    """Fix round 3 (root fix): for EVERY registered box on EVERY page, no ink (text, badge, line, icon)
    may sit within 0.25 in of the box border on any side, and every box on a footer page ends 0.25 in+
    above the footer rule. Ink = a pixel that matches neither the box's own fill nor its row's fill (so a
    tinted header band or a writing line counts as fill, text on it does not). Returns the violations."""
    import subprocess, tempfile, numpy as np
    from PIL import Image as _I
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, tmp + "/p"], check=True)
    k = dpi / 72.0
    n_pages = len(__import__("glob").glob(tmp + "/p-*.png"))
    imgs = {}
    bad = []
    for (pg, name, x, yb, w, h, r) in BOXES:
        if pg not in imgs:
            imgs[pg] = np.asarray(_I.open(f"{tmp}/p-{pg:02d}.png").convert("RGB")).astype(int)
        a = imgs[pg]
        if pg not in (1, n_pages) and yb < FOOT_RULE + CLEAR - 0.01:
            bad.append((pg, name, "bottom over footer gap", round((yb - FOOT_RULE) / 72, 3)))
        s = 3.0                                     # border stroke + anti-alias, excluded
        X0, X1 = round((x + s) * k), round((x + w - s) * k)
        Y0, Y1 = round((PH - (yb + h) + s) * k), round((PH - yb - s) * k)
        sub = a[Y0:Y1, X0:X1]
        q = (sub[..., 0] << 16) | (sub[..., 1] << 8) | sub[..., 2]
        def near(col_int, ref):
            return (abs(((col_int >> 16) & 255) - ((ref >> 16) & 255)) + abs(((col_int >> 8) & 255) - ((ref >> 8) & 255)) + abs((col_int & 255) - (ref & 255))) <= 60
        H_, W_ = q.shape
        yy_, xx_ = np.mgrid[0:H_, 0:W_]
        dl, dr = (xx_ + s * k) / k, (W_ - 1 - xx_ + s * k) / k      # distance to border, pt
        dt, db = (yy_ + s * k) / k, (H_ - 1 - yy_ + s * k) / k
        corner = ((np.minimum(dl, dr) < r + 1.5) & (np.minimum(dt, db) < r + 1.5))
        # the box's own fills = the colours along its inner edge (white body, tinted header band)
        edge = (np.minimum(np.minimum(dl, dr), np.minimum(dt, db)) < s + 2.5) & ~corner
        vals, cnt = np.unique(q[edge], return_counts=True)
        fills = [v for v, n_ in zip(vals, cnt) if n_ >= 0.08 * cnt.sum()]
        ink = np.ones_like(q, dtype=bool)
        for f_ in fills: ink &= ~near(q, f_)
        for i in range(q.shape[0]):
            if ink[i].any():
                rv, rc = np.unique(q[i], return_counts=True); ink[i] &= ~near(q[i], rv[rc.argmax()])
        ring = (np.minimum(np.minimum(dl, dr), np.minimum(dt, db)) < PAD) & ~corner
        hit = ink & ring
        if hit.sum() > 2:
            side = {"left": dl[hit].min(), "right": dr[hit].min(), "top": dt[hit].min(), "bottom": db[hit].min()}
            worst = {kk: round(v / 72, 3) for kk, v in side.items() if v < PAD}
            bad.append((pg, name, "ink inside 0.25 in", worst))
    return bad


if __name__ == "__main__":
    box_bad = check_boxes(OUT)
    print(f"boxes checked: {len(BOXES)} on {len(set(b[0] for b in BOXES))} pages; violations: {len(box_bad)}")
    for v in box_bad: print("  BOX", v)
    assert not box_bad, ("boxes with ink inside 0.25 in of the border or over the footer gap", len(box_bad))
    bad = []
    for n, gap_in, has_rule in check_clearance(OUT):
        print(f"p{n:02d} clearance above footer rule {gap_in:.2f} in" + ("" if has_rule else " (no kit footer)"))
        if has_rule and gap_in < 0.25: bad.append((n, gap_in))
    assert not bad, ("pages under 0.25 in above the footer rule", bad)
    print("clearance OK: every footer page >= 0.25 in")
