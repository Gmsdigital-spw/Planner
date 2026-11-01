"""Build the Christmas Escape Room for Adults PDF (The Snowbound Lodge). python3 build.py <out.pdf>"""
import sys
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gm_style as gs
import puzzles as pz
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "christmas-escape-room-adults.pdf"
PAL = gs.palette("evergreen")
NAME = "The Snowbound Lodge  ·  Christmas Escape Room"
d = gs.Book(OUT, NAME, PAL, cover_style="split", page_frame="band")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
W = R - L
RED, REDT = HexColor("#9E3B33"), HexColor("#F4E1DE")
FOOT_RULE = M - 9          # band frame footer rule (gs.Book.end: MARGIN - 22 + 13)
CLEAR = 18                 # 0.25 in between the lowest element and the footer rule
BOTTOM = FOOT_RULE + CLEAR + 1.5
PAD = 20                   # draw inset; check_boxes still proves the 0.25 in (18 pt) bar below
HEAD = 36
BOXES = []
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))


def reg(name, x, yb, w, h, r=8):
    BOXES.append((c.getPageNumber(), name, x, yb, w, h, r))


def para(x, y, text, width, size=10.5, font=None, color=None, lead=1.45):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawString(x, y - size, ln); y -= size * lead
    return y


def para_c(y, text, width, size=10.5, font=None, color=None, lead=1.45, cx=PW / 2):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawCentredString(cx, y - size, ln); y -= size * lead
    return y


def para_h(text, width, size=10.5, font=None, lead=1.45):
    return len(gs.wrap(text, font or d.F, size, width)) * size * lead


def card(x, y, w, h, title=None, fill=white, stroke=None):
    c.setStrokeColor(stroke or d.HAIR); c.setLineWidth(0.9); c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    reg(title or "card", x, y - h, w, h, 8)
    if title:
        c.setFillColor(d.T); c.roundRect(x, y - HEAD, w, HEAD, 8, fill=1, stroke=0); c.rect(x, y - HEAD, w, 10, fill=1, stroke=0)
        c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(x + PAD, y - 28, title.upper())
    return y - (HEAD if title else 0) - PAD


def scene(y, text, title="The scene"):
    h = HEAD + PAD + para_h(text, W - 2 * PAD, 10.5, d.SS) + PAD - 4
    yy = card(L, y, W, h, title, fill=HexColor(PAL["paper"]))
    para(L + PAD, yy + 4, text, W - 2 * PAD, 10.5, d.SS)
    return y - h - 14


def answer_strip(label, cells, unlocks):
    h = 80
    c.setStrokeColor(d.P); c.setLineWidth(1.4); c.setFillColor(d.T)
    c.roundRect(L, BOTTOM, W, h, 10, fill=1, stroke=1)
    reg("answer: " + label, L, BOTTOM, W, h, 10)
    c.setFillColor(d.D); c.setFont(d.SB, 15); c.drawString(L + PAD + 2, BOTTOM + h / 2 + 2, label)
    c.setFillColor(d.MUT); c.setFont(d.F, 9); c.drawString(L + PAD + 2, BOTTOM + h / 2 - 14, unlocks)
    cw = 34; gap = 6
    x0 = R - PAD - 2 - cells * cw - (cells - 1) * gap
    for i in range(cells):
        c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.1)
        c.roundRect(x0 + i * (cw + gap), BOTTOM + (h - 36) / 2, cw, 36, 5, fill=1, stroke=1)
    return BOTTOM + h


def padlock(x, y, s, col=None):
    c.setStrokeColor(col or d.D); c.setLineWidth(s * 0.09); c.setFillColor(white)
    c.arc(x - s * 0.28, y + s * 0.35, x + s * 0.28, y + s * 0.98, 0, 180)
    c.line(x - s * 0.28, y + s * 0.66, x - s * 0.28, y + s * 0.5); c.line(x + s * 0.28, y + s * 0.66, x + s * 0.28, y + s * 0.5)
    c.setFillColor(d.T); c.setLineWidth(1.1); c.roundRect(x - s * 0.42, y, s * 0.84, s * 0.56, 3, fill=1, stroke=1)
    c.setFillColor(col or d.D); c.circle(x, y + s * 0.3, s * 0.06, fill=1, stroke=0)


def poly(pts, fill=None, stroke=None, lw=1.2):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close()
    if fill is not None: c.setFillColor(fill)
    if stroke is not None: c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.drawPath(p, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def star(x, y, s):
    import math
    pts = []
    for i in range(10):
        r = s / 2 if i % 2 == 0 else s / 4.6
        a = math.pi / 2 + i * math.pi / 5
        pts.append((x + r * math.cos(a), y + s / 2 + r * math.sin(a) - s * 0.04))
    poly(pts, HexColor("#F3E6C8"), d.A, 1.4)


def bell(x, y, s):
    w = s * 0.8
    p = c.beginPath(); p.moveTo(x - w / 2, y + s * 0.18)
    p.curveTo(x - w * 0.36, y + s * 0.5, x - w * 0.34, y + s * 0.9, x, y + s * 0.92)
    p.curveTo(x + w * 0.34, y + s * 0.9, x + w * 0.36, y + s * 0.5, x + w / 2, y + s * 0.18); p.close()
    c.setFillColor(REDT); c.setStrokeColor(RED); c.setLineWidth(1.4); c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(RED); c.circle(x, y + s * 0.1, s * 0.08, fill=1, stroke=0)
    c.line(x - w / 2, y + s * 0.18, x + w / 2, y + s * 0.18)


def tree(x, y, s):
    c.setFillColor(HexColor("#8A6A48")); c.rect(x - s * 0.06, y, s * 0.12, s * 0.14, fill=1, stroke=0)
    for k, (yb, hw) in enumerate(((0.12, 0.42), (0.38, 0.33), (0.62, 0.24))):
        poly([(x - s * hw, y + s * yb), (x + s * hw, y + s * yb), (x, y + s * (yb + 0.34))], d.T, d.P, 1.4)


def cutline(x0, y0, x1, y1):
    c.setStrokeColor(d.MUT); c.setLineWidth(0.6); c.setDash(4, 3); c.line(x0, y0, x1, y1); c.setDash()


def cells_row(x, y, text, cw, ch, size, fill=white, font=None):
    """One row of letter cells; spaces leave a gap. Returns width."""
    cx = x
    for chh in text:
        if chh == " ":
            cx += cw * 0.6; continue
        c.setFillColor(fill); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(cx, y - ch, cw, ch, fill=1, stroke=1)
        if chh != "_":
            c.setFillColor(d.D); c.setFont(font or d.FM, size); c.drawCentredString(cx + cw / 2, y - ch / 2 - size * 0.35, chh)
        cx += cw
    return cx - x


def text_w(text, cw):
    return sum(cw * 0.6 if ch == " " else cw for ch in text)


# ================================================================== 1 cover (split, drawn here so the lower right carries the 8-lock list)
def cover():
    d.page += 1
    c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(d.P); c.rect(0, 0, PW * 0.34, PH, fill=1, stroke=0)
    c.setFillColor(d.A); c.rect(PW * 0.34, 0, 4, PH, fill=1, stroke=0)
    c.saveState(); c.translate(PW * 0.17 + 5, PH / 2); c.rotate(90)
    d._spaced(0, 0, "PRINTABLE PARTY GAME  ·  8 PUZZLES  ·  TEAMS OF 2 TO 20", 11, white, d.FM); c.restoreState()
    x0, w = PW * 0.34 + 40, PW * 0.66 - 80
    d._spaced(x0 + stringWidth("THE SNOWBOUND LODGE", d.FM, 10) * 0.6, PH - 120, "THE SNOWBOUND LODGE", 10, d.P, d.FM)
    lines = ["Christmas", "Escape Room", "for Adults"]
    size = 46
    while max(stringWidth(t, d.S, size) for t in lines) > w: size -= 1
    ty = PH - 190
    for t in lines:
        c.setFont(d.S, size); c.setFillColor(d.D); c.drawString(x0, ty, t); ty -= size * 1.12
    c.setStrokeColor(d.A); c.setLineWidth(2); c.line(x0, ty + 18, x0 + 70, ty + 18)
    y = ty - 8; c.setFillColor(d.INK); c.setFont(d.SS, 15)
    for ln in gs.wrap("Eight linked puzzles. Each answer opens the next lock. For teens, office parties and game night.", d.SS, 15, w):
        c.drawString(x0, y, ln); y -= 21
    y -= 16
    h = 8 * 21 + 2 * PAD + 6
    c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.9); c.roundRect(x0 - 4, y - h, w + 8, h, 8, fill=1, stroke=1)
    reg("cover lock list", x0 - 4, y - h, w + 8, h, 8)
    names = ["The Keeper's Letter", "The Frosted Window", "The Card Box", "The Grandfather Clock",
             "The Guest Register", "The Ornament Scale", "The Storm Telegram", "The Gift Vault"]
    yy = y - PAD - 14
    for i, n in enumerate(names):
        padlock(x0 + PAD + 4, yy - 2, 13)
        c.setFillColor(d.P); c.setFont(d.FM, 10); c.drawString(x0 + PAD + 18, yy + 1, f"{i + 1}")
        c.setFillColor(d.INK); c.setFont(d.F, 11); c.drawString(x0 + PAD + 34, yy + 1, n)
        yy -= 21
    c.setFont(d.FM, 9.5); c.setFillColor(d.MUT); c.drawString(x0, 74, "US LETTER + A4  ·  PRINT AT HOME  ·  45 TO 60 MIN")
    c.setFont(d.F, 8.5); c.drawString(x0, 54, "GM's Digital Creations")
    c.showPage()


cover()

# ================================================================== 2 host guide
d.start("Host Guide", "Read this page alone. It explains the game without giving away any answers.", kicker="Host only")
y = d.y
y = scene(y, "Read aloud: \"The storm closed the mountain road at noon. The keeper of the Snowbound Lodge left before it hit, "
          "but every present for tonight's party is locked in the gift vault. The keeper left a trail: eight locks, each opened "
          "by the answer to the one before. You have sixty minutes before the fire burns out. Find the vault code.\"", "Story to read aloud")
colw = (W - 14) / 2
h1 = 300
yy = card(L, y, colw, h1, "How to run it")
steps = ["Print one full set per team (pages 3 to 13).", "Cut the hint cards apart; keep them face down.",
         "Give each team Puzzle 1, the Lock Sheet and a pencil.", "Hand out the next puzzle only when a team shows you the right answer.",
         "A team may ask for a hint card; each hint adds 2 minutes.", "First team to the vault code with the best time wins."]
for i, s in enumerate(steps):
    c.setFillColor(d.P); c.setFont(d.FM, 10.5); c.drawString(L + PAD, yy - 10.5, f"{i + 1}.")
    yy = para(L + PAD + 16, yy, s, colw - 2 * PAD - 16, 10, d.F, lead=1.4) - 7
x2 = L + colw + 14
yy = card(x2, y, colw, h1, "Before guests arrive")
for s in ["Print on plain paper, US Letter or A4", "Put each puzzle in a numbered envelope", "Set a 60-minute timer you can show",
          "Keep the answer key (page 14) out of sight", "Pencils and scrap paper for every team", "Optional: a small prize in a box for the vault"]:
    c.setStrokeColor(d.P); c.setLineWidth(1); c.rect(x2 + PAD, yy - 11, 9, 9, fill=0, stroke=1)
    yy = para(x2 + PAD + 16, yy, s, colw - 2 * PAD - 16, 10, d.F, lead=1.4) - 9
y -= h1 + 14
hb = y - BOTTOM
facts = [("PLAYERS", "2 to 20"), ("TEAMS", "2 to 5 each"), ("TIME", "45 to 60 min"), ("LEVEL", "Teens + adults")]
fw = (W - 3 * 10) / 4
for i, (k, v) in enumerate(facts):
    fx = L + i * (fw + 10)
    c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(fx, BOTTOM, fw, hb, 8, fill=1, stroke=1)
    reg("fact " + k, fx, BOTTOM, fw, hb, 8)
    c.setFillColor(d.P); c.setFont(d.FM, 8.5); c.drawCentredString(fx + fw / 2, BOTTOM + hb / 2 + 8, k)
    fs = 15
    while stringWidth(v, d.S, fs) > fw - 2 * PAD - 6: fs -= 0.5
    c.setFillColor(d.D); c.setFont(d.S, fs); c.drawCentredString(fx + fw / 2, BOTTOM + hb / 2 - 14, v)
d.end()

# ================================================================== 3 puzzle 1: the keeper's letter
d.start("1  ·  The Keeper's Letter", "A note waits on the kitchen table, under a mug of cold cider.", kicker="Puzzle 1 of 8")
y = d.y
top = answer_strip("What number does the letter give you?", 1, "Unlocks Puzzle 2: The Frosted Window")
h = y - top - 16
yy = card(L, y, W, h, "On the kitchen table", fill=HexColor(PAL["paper"]))
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(L + PAD + 8, yy - 13, "Dear guests,")
yy -= 34
for ln in pz.LETTER:
    yy = para(L + PAD + 8, yy, ln, W - 2 * PAD - 16, 12, d.SS, lead=1.42) - 13
c.setFillColor(d.D); c.setFont(d.SB, 12.5); c.drawRightString(R - PAD - 8, yy - 18, "The Keeper")
d.end()

# ================================================================== 4 puzzle 2: the frosted window
d.start("2  ·  The Frosted Window", "Letters are scratched into the frost on the glass.", kicker="Puzzle 2 of 8")
y = d.y
y = scene(y, "Someone wrote a message in the frost, but every letter has slipped forward along the alphabet by the same "
          "number of places. Your answer to Puzzle 1 tells you how far. Slide each letter back to read it. The alphabet wraps: one back from A is Z.")
words = pz.P2_CIPHER.split(" ")
cw = 25
h = 2 * HEAD + 2 * cw * 2 + 30 + 2 * PAD
yy = card(L, y, W, 206, "The glass")
lines_ = [" ".join(words[:3]), " ".join(words[3:])]
for ln in lines_:
    x = L + (W - text_w(ln, cw)) / 2
    cells_row(x, yy, ln, cw, cw, 13, fill=d.T)
    cells_row(x, yy - cw - 4, "".join("_" if ch != " " else " " for ch in ln), cw, cw, 13)
    yy -= 2 * cw + 20
y -= 206 + 14
top = answer_strip("What is the keyword?", 4, "Unlocks Puzzle 3: The Card Box")
h = y - top - 16
yy = card(L, y, W, h, "Alphabet strip: count back along it")
cw2 = (W - 2 * PAD) / 13
for row in range(2):
    seg = pz.A[row * 13:(row + 1) * 13]
    for i, ch in enumerate(seg):
        x = L + PAD + i * cw2
        c.setFillColor(d.T if row == 0 else HexColor("#EFE7D2")); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(x, yy - 24, cw2, 24, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.FM, 12); c.drawCentredString(x + cw2 / 2, yy - 16, ch)
        c.setFillColor(d.MUT); c.setFont(d.F, 7.5); c.drawCentredString(x + cw2 / 2, yy - 35, str(row * 13 + i + 1))
    yy -= 46
d.end()

# ================================================================== 5 puzzle 3: the card box
d.start("3  ·  The Card Box", "A wooden recipe box with a brass letter grid glued inside the lid.", kicker="Puzzle 3 of 8")
y = d.y
y = scene(y, "The top card is in a keyword cipher. Write your Puzzle 2 keyword under it, over and over. For each pair: find "
          "the keyword letter's row in the grid, run along to the card's letter, then look up. The column's top letter is the real one.")
cw = 22
words = pz.P3_CIPHER.split(" ")
hcard = 3 * (3 * cw + 16) - 16 + HEAD + 2 * PAD - 4
cw = 19
lines_ = [pz.P3_CIPHER]
hcard = 3 * cw + 2 * PAD + 4
yy = card(L, y, W, hcard, None) - 2
for ln in lines_:
    x = R - PAD - text_w(ln, cw)
    for k, lab in enumerate(("CARD", "KEY", "REAL")):
        c.setFillColor(d.P); c.setFont(d.FM, 8); c.drawString(L + PAD, yy - k * cw - cw / 2 - 3, lab)
    cells_row(x, yy, ln, cw, cw, 11.5, fill=d.T)
    blank = "".join("_" if ch != " " else " " for ch in ln)
    cells_row(x, yy - cw, blank, cw, cw, 11.5, fill=HexColor("#EFE7D2"))
    cells_row(x, yy - 2 * cw, blank, cw, cw, 11.5)
    yy -= 3 * cw + 18
y -= hcard + 14
top = answer_strip("Which row of the clock should you read?", 1, "Unlocks Puzzle 4: The Grandfather Clock")
hg = y - top - 14
yy = card(L, y, W, hg, None) - 2
sh = (yy - (y - hg) - PAD - 2) / 27
sw = (W - 2 * PAD) / 27
print("brass grid cell", round(sw, 1), "x", round(sh, 1), "pt")
gx = L + PAD
gy = yy
fs = min(sh * 0.74, 9)
for r in range(27):
    for col in range(27):
        x = gx + col * sw; ty = gy - (r + 1) * sh
        if r == 0 and col == 0: continue
        if r == 0 or col == 0:
            c.setFillColor(d.P); c.rect(x, ty, sw, sh, fill=1, stroke=0); ch = pz.A[(col or r) - 1]
            c.setFillColor(white); c.setFont(d.FM, fs); c.drawCentredString(x + sw / 2, ty + sh * 0.26, ch)
        else:
            if r % 2 == 0:
                c.setFillColor(HexColor("#EEF3F0")); c.rect(x, ty, sw, sh, fill=1, stroke=0)
            c.setFillColor(d.INK); c.setFont(d.F, fs); c.drawCentredString(x + sw / 2, ty + sh * 0.26, pz.A[(r - 1 + col - 1) % 26])
d.end()

# ================================================================== 6 puzzle 4: grandfather clock (sudoku)
d.start("4  ·  The Grandfather Clock", "The clock face has been swapped for a grid of numbered tiles.", kicker="Puzzle 4 of 8")
y = d.y
y = scene(y, "Fill the grid so every row, every column and every bold 2 x 3 block holds the numbers 1 to 6 once each. "
          "Each row has three shaded tiles. Read the shaded tiles in the row your Puzzle 3 answer names, left to right: "
          "that three-digit number is a guest room.")
top = answer_strip("Which room number did the clock give?", 3, "Unlocks Puzzle 5: The Guest Register")
hg = y - top - 14
yy = card(L, y, W, hg, "The clock face")
gs_ = min(yy - (y - hg) - PAD - 6, W - 2 * PAD - 80)
cs = gs_ / 6
gx = L + (W - gs_) / 2 + 12
gy = yy - 2
for r in range(6):
    c.setFillColor(d.P); c.setFont(d.FM, 11); c.drawRightString(gx - 12, gy - (r + 0.5) * cs - 4, f"Row {r + 1}")
    for col in range(6):
        x = gx + col * cs; ty = gy - (r + 1) * cs
        c.setFillColor(d.T if col in pz.SHADE[r] else white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(x, ty, cs, cs, fill=1, stroke=1)
        v = pz.SUD_PUZ[r][col]
        if v:
            c.setFillColor(d.D); c.setFont(d.S, cs * 0.5); c.drawCentredString(x + cs / 2, ty + cs * 0.32, str(v))
c.setStrokeColor(d.D); c.setLineWidth(2.2)
c.rect(gx, gy - gs_, gs_, gs_, fill=0, stroke=1)
for r in (2, 4): c.line(gx, gy - r * cs, gx + gs_, gy - r * cs)
c.line(gx + 3 * cs, gy, gx + 3 * cs, gy - gs_)
d.end()

# ================================================================== 7 puzzle 5: guest register (logic grid)
d.start("5  ·  The Guest Register", "Four guests signed the book, and each wrapped one present.", kicker="Puzzle 5 of 8")
y = d.y
colw = 230
hc = 290
yy = card(L, y, colw, hc, "The register notes")
for i, cl in enumerate(pz.CLUES):
    c.setFillColor(d.P); c.setFont(d.FM, 10); c.drawString(L + PAD, yy - 10, f"{i + 1}.")
    yy = para(L + PAD + 15, yy, cl, colw - 2 * PAD - 15, 10, d.F, lead=1.38) - 6
x2 = L + colw + 14; w2 = W - colw - 14
yy = card(x2, y, w2, hc, "Guests and rooms")
yq = para(x2 + PAD, yy, "Margo, Felix, Iris and Dexter. Rooms: 204, "
     f"{pz.ROOM}, 421 and 536. Presents: a scarf, a candle, a snow globe and mittens. Each guest has one room and wrapped one present.",
     w2 - 2 * PAD, 10.5, d.SS, lead=1.45)
yy2 = yq - 22
c.setFillColor(d.D); c.setFont(d.SB, 12)
for ln in gs.wrap("Who is staying in the room the clock gave you?", d.SB, 12, w2 - 2 * PAD):
    c.drawString(x2 + PAD, yy2, ln); yy2 -= 17
y -= hc + 14
top = answer_strip("Name of the guest in that room", 6, "Unlocks Puzzle 6: The Ornament Scale")
hg = y - top - 14
yy = card(L, y, W, hg, "Working grid: mark X for no, O for yes")
heads = [str(r) for r in pz.ROOMS] + ["Scarf", "Candle", "Globe", "Mittens"]
lab = 80
cw = (W - 2 * PAD - lab) / 8
rh = min(34, (yy - (y - hg) - PAD - 30) / 4)
for i, hd in enumerate(heads):
    c.setFillColor(d.P if i < 4 else d.D); c.setFont(d.FM, 9.5); c.drawCentredString(L + PAD + lab + (i + 0.5) * cw, yy - 14, hd)
yy -= 24
for r, g in enumerate(pz.GUESTS):
    c.setFillColor(d.D); c.setFont(d.SB, 11); c.drawString(L + PAD, yy - (r + 0.5) * rh - 4, g)
    for i in range(8):
        c.setFillColor(white if i < 4 else HexColor(PAL["paper"])); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(L + PAD + lab + i * cw, yy - (r + 1) * rh, cw, rh, fill=1, stroke=1)
c.setStrokeColor(d.D); c.setLineWidth(1.6); c.line(L + PAD + lab + 4 * cw, yy, L + PAD + lab + 4 * cw, yy - 4 * rh)
d.end()

# ================================================================== 8 puzzle 6: ornament scale
d.start("6  ·  The Ornament Scale", "A brass scale on the mantel, with ornaments in place of weights.", kicker="Puzzle 6 of 8")
y = d.y
y = scene(y, "Each kind of ornament always weighs the same whole number. On its own the scale has too many answers. "
          "The keeper's tag says: the star weighs as much as the number of letters in the name you found in Puzzle 5.")
top = answer_strip("Tree + star = ?", 1, "Unlocks Puzzle 7: The Storm Telegram")
rows = [[("star",), "+", ("bell",), "+", ("bell",), "=", "14"],
        [("tree",), "+", ("bell",), "=", ("star",), "+", "4"],
        [("tree",), "+", ("star",), "=", "?"]]
gap = 12
rh = (y - top - 14 - 2 * gap) / 3
draw = {"star": star, "bell": bell, "tree": tree}
for k, row in enumerate(rows):
    ytop = y - k * (rh + gap)
    c.setFillColor(white if k < 2 else d.T); c.setStrokeColor(d.HAIR if k < 2 else d.P); c.setLineWidth(0.9 if k < 2 else 1.3)
    c.roundRect(L, ytop - rh, W, rh, 8, fill=1, stroke=1); reg(f"scale row {k + 1}", L, ytop - rh, W, rh, 8)
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L + PAD, ytop - PAD - 9, f"PAN {k + 1}" if k < 2 else "YOUR TURN")
    s = min(rh - 2 * PAD - 18, 84)
    item_w = [s if isinstance(t, tuple) else 36 for t in row]
    tot = sum(item_w) + 10 * (len(row) - 1)
    x = L + (W - tot) / 2
    by = ytop - rh + PAD + 2
    for t, iw in zip(row, item_w):
        if isinstance(t, tuple):
            draw[t[0]](x + iw / 2, by, s)
        else:
            c.setFillColor(d.D); c.setFont(d.S, 30); c.drawCentredString(x + iw / 2, by + s / 2 - 10, t)
        x += iw + 10
d.end()

# ================================================================== 9 puzzle 7: storm telegram (skip cipher)
d.start("7  ·  The Storm Telegram", "A telegram slip came through before the line went dead. It looks like noise.", kicker="Puzzle 7 of 8")
y = d.y
y = scene(y, "Your Puzzle 6 answer is the step. Start on the very first letter, then count forward that many letters each time, "
          "reading across each row and on to the next. Write each letter you land on below. The message tells you how to open the vault.")
top = answer_strip("Write the instruction in the cells above", 0, "Unlocks Puzzle 8: The Gift Vault")
hm = 2 * 30 + 4 + HEAD + 2 * PAD + 4
yy = card(L, top + 14 + hm, W, hm, "The hidden message")
cw = (W - 2 * PAD) / 10
for r in range(2):
    for i in range(10 if r == 0 else 9):
        c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(L + PAD + i * cw, yy - (r + 1) * 30 - r * 4, cw, 30, fill=1, stroke=1)
hg = y - (top + 14 + hm) - 14
yy = card(L, y, W, hg, "The telegram")
n = len(pz.TELEGRAM) // pz.COLS
cs = min((W - 2 * PAD - 30) / pz.COLS, (yy - (y - hg) - PAD) / n)
gx = L + (W - cs * pz.COLS) / 2 + 10
for r in range(n):
    c.setFillColor(d.MUT); c.setFont(d.F, 8); c.drawRightString(gx - 8, yy - (r + 0.5) * cs - 3, str(r + 1))
    for col in range(pz.COLS):
        x = gx + col * cs; ty = yy - (r + 1) * cs
        c.setFillColor(d.T if (r + col) % 2 == 0 else white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
        c.rect(x, ty, cs, cs, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.FM, cs * 0.5); c.drawCentredString(x + cs / 2, ty + cs * 0.32, pz.TELEGRAM[r * pz.COLS + col])
d.end()

# ================================================================== 10 puzzle 8: gift vault
d.start("8  ·  The Gift Vault", "A heavy green door behind the tree, with four brass number wheels.", kicker="Puzzle 8 of 8")
y = d.y
y = scene(y, "Follow the telegram's instruction using the answers on your Lock Sheet. The result is a four-digit number. "
          "Set it on the wheels below and show your host. A brass plate under the dial reads: the four digits add up to 18.")
top = answer_strip("The vault code", 4, "Opens the vault: stop the clock!")
hv = y - top - 14
yy = card(L, y, W, hv, "The vault door", fill=HexColor(PAL["paper"]))
cx, cy = PW / 2, (yy + (y - hv) + PAD) / 2
rad = min((yy - (y - hv) - PAD) / 2 - 4, 150)
c.setFillColor(d.P); c.setStrokeColor(d.D); c.setLineWidth(3); c.circle(cx, cy, rad, fill=1, stroke=1)
c.setFillColor(d.D); c.circle(cx, cy, rad * 0.86, fill=1, stroke=0)
c.setStrokeColor(d.A); c.setLineWidth(1.4); c.circle(cx, cy, rad * 0.8, fill=0, stroke=1)
import math
for i in range(40):
    a = i * math.pi / 20
    r1 = rad * 0.8 - (8 if i % 5 == 0 else 4)
    c.line(cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + rad * 0.8 * math.cos(a), cy + rad * 0.8 * math.sin(a))
ww, wh = rad * 0.3, rad * 0.46
for i in range(4):
    x = cx - 2 * ww - 6 + i * (ww + 4)
    c.setFillColor(white); c.setStrokeColor(d.A); c.setLineWidth(1.4); c.roundRect(x, cy - wh / 2, ww, wh, 4, fill=1, stroke=1)
padlock(cx, cy + wh / 2 + 10, 24, d.A)
c.setFillColor(d.A); c.setFont(d.FM, 9); c.drawCentredString(cx, cy - wh / 2 - 18, "SET THE WHEELS")
d.end()

# ================================================================== 11 lock sheet
d.start("Lock Sheet", "One per team. Write each answer as you solve it; your host checks it before the next envelope.", kicker="Team record")
y = d.y
c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(L, y - 12, "Team name"); c.setStrokeColor(d.HAIR); c.line(L + 80, y - 14, R, y - 14)
y -= 32
names = ["The Keeper's Letter", "The Frosted Window", "The Card Box", "The Grandfather Clock",
         "The Guest Register", "The Ornament Scale", "The Storm Telegram", "The Gift Vault"]
rh = (y - BOTTOM - 7 * 6) / 8
for i, nme in enumerate(names):
    ty = y - i * (rh + 6)
    c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.9); c.roundRect(L, ty - rh, W, rh, 8, fill=1, stroke=1)
    reg("lock row %d" % (i + 1), L, ty - rh, W, rh, 8)
    padlock(L + PAD + 10, ty - rh / 2 - 11, 22)
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L + PAD + 32, ty - rh / 2 + 4, f"LOCK {i + 1}")
    c.setFillColor(d.D); c.setFont(d.SB, 12.5); c.drawString(L + PAD + 32, ty - rh / 2 - 12, nme)
    c.setFillColor(d.MUT); c.setFont(d.F, 8.5); c.drawString(L + 260, ty - PAD - 8, "ANSWER")
    c.setStrokeColor(d.HAIR); c.line(L + 260, ty - rh + PAD + 2, L + 430, ty - rh + PAD + 2)
    c.setFillColor(d.MUT); c.drawString(L + 444, ty - PAD - 8, "TIME")
    c.line(L + 444, ty - rh + PAD + 2, R - PAD, ty - rh + PAD + 2)
d.end()

# ================================================================== 12 hint cards
d.start("Hint Cards", "Cut along the dashed lines. Fold each card so Hint 2 stays hidden until a team needs it.", kicker="Host: cut out")
y = d.y
HINTS = [
    ("The Keeper's Letter", "The message is not in what the letter says.", "Read the first letter of every line, top to bottom."),
    ("The Frosted Window", "Each glass letter moved forward the same number of places.", "Slide every letter back by your Puzzle 1 number. C becomes T."),
    ("The Card Box", "Line up the keyword under the card: P I N E P I N E ...", "First pair: row P, find H in that row, look up to the top letter."),
    ("The Grandfather Clock", "Start with the blocks that already hold four numbers.", "Your Puzzle 3 answer is a row number. Read only that row's shaded tiles."),
    ("The Guest Register", "Margo's room is fixed by note 1. Note 2 then gives her present.", "Felix cannot be in 421, and Dexter must be lower than Felix."),
    ("The Ornament Scale", "Count the letters in the Puzzle 5 name to weigh the star.", "Pan 1 then gives the bell. Pan 2 gives the tree."),
    ("The Storm Telegram", "The step is your Puzzle 6 answer. The first letter counts.", "Letters 1, 8, 15, 22 and so on. The message starts with R."),
    ("The Gift Vault", "The telegram names two answers from your Lock Sheet.", "Multiply them. Check: the four digits add up to 18."),
]
colw = W / 2
rh = (y - BOTTOM) / 4
for i, (nme, h1, h2) in enumerate(HINTS):
    col, row = i % 2, i // 2
    x = L + col * colw + (6 if col else 0); ty = y - row * rh
    w = colw - 6; hh = rh - 10
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(x, ty - hh, w, hh, 8, fill=1, stroke=1)
    reg("hint " + nme, x, ty - hh, w, hh, 8)
    c.setFillColor(d.P); c.setFont(d.FM, 8.5); c.drawString(x + PAD, ty - PAD - 8, f"HINT  ·  PUZZLE {i + 1}")
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(x + PAD, ty - PAD - 24, nme)
    yy = para(x + PAD, ty - PAD - 32, "1. " + h1, w - 2 * PAD, 9.4, d.F, lead=1.35)
    mid = ty - hh / 2 - 12
    cutline(x + PAD, mid + 4, x + w - PAD, mid + 4)
    c.setFillColor(d.MUT); c.setFont(d.F, 7.5); c.drawRightString(x + w - PAD, mid + 8, "fold here")
    para(x + PAD, mid - 4, "2. " + h2, w - 2 * PAD, 9.4, d.F, lead=1.35)
    if row < 3: cutline(L, ty - rh + 4, R, ty - rh + 4)
cutline(PW / 2, y, PW / 2, BOTTOM)
d.end()

# ================================================================== 13 timer and scores
d.start("Team Timer & Scores", "Write the clock time when each team opens a lock. Each hint card adds 2 minutes.", kicker="Host sheet")
y = d.y
txt = ("Final time = minutes from start to vault + 2 minutes for each hint card used. The lowest final time wins. "
       "If no team opens the vault in 60 minutes, the team with the most locks open wins; ties go to fewer hints.")
h = HEAD + PAD + para_h(txt, W - 2 * PAD, 10.2) + 40 + PAD
yy = card(L, y, W, h, "How the final time works")
yy = para(L + PAD, yy, txt, W - 2 * PAD, 10.2, d.F) - 6
c.setFillColor(d.T); c.roundRect(L + PAD, yy - 30, W - 2 * PAD, 28, 6, fill=1, stroke=0)
c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(L + PAD + 12, yy - 20, "Example:  vault opened at 41 min, 3 hint cards used  =  41 + 6  =  47 min final time")
d.y = y - h - 16
cols = ["Team", "Start", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "Vault", "Hints", "Final", "Place"]
widths = [100, 36, 32, 32, 32, 32, 32, 32, 32, 38, 36, 40, 37.2]
assert abs(sum(widths) - W) < 1, sum(widths)
d.table(cols, widths, empty=10, rowh=40, fill=True)
d.end()

# ================================================================== 14 answer key
d.start("Answer Key", "Host only. Fold this page away before the game starts.", kicker="Host only")
y = d.y
ans = [
    ("1  The Keeper's Letter", "First letters spell SHIFT BY NINE.", "9"),
    ("2  The Frosted Window", f"{pz.P2_CIPHER} back 9 = {pz.P2_PLAIN}.", pz.P2_ANS),
    ("3  The Card Box", f"{pz.P3_CIPHER} with key PINE = {pz.P3_PLAIN}.", "6"),
    ("4  The Grandfather Clock", f"Row 6 of the solved grid: {' '.join(map(str, pz.SUD_SOL[5]))}. Shaded tiles read {pz.ROOM}.", str(pz.ROOM)),
    ("5  The Guest Register", f"Margo 204 candle, Iris {pz.ROOM} snow globe, Dexter 421 scarf, Felix 536 mittens.", pz.P5_ANS),
    ("6  The Ornament Scale", "Star 4 (I-R-I-S), bell 5, tree 3. Tree + star = 7.", "7"),
    ("7  The Storm Telegram", "Every 7th letter from the first: ROOM NUMBER TIMES NINE.", "Room x 9"),
    ("8  The Gift Vault", f"{pz.ROOM} x 9 = {pz.CODE}. Digits add to 18.", str(pz.CODE)),
]
hk = 330
yy = card(L, y, W, hk, "The full clue chain")
rowh = (hk - HEAD - 2 * PAD + 4) / 8
for i, (a, b, cc) in enumerate(ans):
    ty = yy - i * rowh
    c.setFillColor(d.D); c.setFont(d.SB, 10.5); c.drawString(L + PAD, ty - 11, a)
    c.setFillColor(d.INK); c.setFont(d.F, 9); c.drawString(L + PAD, ty - 25, b)
    c.setFillColor(d.P); c.setFont(d.S, 13); c.drawRightString(R - PAD, ty - 15, cc)
y -= hk + 14
hs = y - BOTTOM
yy = card(L, y, W, hs, "Solved clock grid (Puzzle 4)")
cs = min((hs - HEAD - 2 * PAD) / 6, 30)
gx = L + PAD
for r in range(6):
    for col in range(6):
        x = gx + col * cs; ty = yy - (r + 1) * cs
        c.setFillColor(d.T if col in pz.SHADE[r] else white); c.setStrokeColor(d.HAIR); c.rect(x, ty, cs, cs, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.F, cs * 0.5); c.drawCentredString(x + cs / 2, ty + cs * 0.3, str(pz.SUD_SOL[r][col]))
tx = gx + 6 * cs + 24
para(tx, yy, "Every answer in the chain was checked by a script before printing: the grid has one solution, the "
     "register has one solution, and the scale has one solution once the star is known.", R - PAD - tx, 10, d.F, lead=1.45)
d.end()

# ================================================================== 15 certificate
d.start("Certificate of Escape", None, kicker="Print one per team")
y = d.y - 6
h = y - BOTTOM
c.setFillColor(HexColor(PAL["paper"])); c.setStrokeColor(d.P); c.setLineWidth(2); c.roundRect(L, BOTTOM, W, h, 10, fill=1, stroke=1)
c.setStrokeColor(d.A); c.setLineWidth(0.8); c.roundRect(L + 10, BOTTOM + 10, W - 20, h - 20, 6, fill=0, stroke=1)
reg("certificate", L + 10, BOTTOM + 10, W - 20, h - 20, 6)
cy = y - 70
padlock(PW / 2, cy - 30, 54, d.P)
d._spaced(PW / 2, cy - 60, "THIS CERTIFIES THAT TEAM", 10, d.P, d.FM)
c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.line(L + 90, cy - 110, R - 90, cy - 110)
c.setFillColor(d.D); c.setFont(d.S, 30); c.drawCentredString(PW / 2, cy - 160, "escaped the")
c.setFont(d.S, 38); c.drawCentredString(PW / 2, cy - 204, "Snowbound Lodge")
d._ornament(PW / 2, cy - 228)
c.setFillColor(d.INK); c.setFont(d.SS, 13); c.drawCentredString(PW / 2, cy - 262, "and opened the gift vault before the fire burned out.")
fy = BOTTOM + 110
for i, lab in enumerate(["Final time", "Hints used", "Date"]):
    fx = L + 50 + i * ((W - 100) / 3)
    fw = (W - 100) / 3 - 20
    c.setStrokeColor(d.HAIR); c.line(fx, fy, fx + fw, fy)
    c.setFillColor(d.MUT); c.setFont(d.FM, 9); c.drawCentredString(fx + fw / 2, fy - 16, lab.upper())
c.line(PW / 2 - 110, BOTTOM + 56, PW / 2 + 110, BOTTOM + 56)
c.drawCentredString(PW / 2, BOTTOM + 40, "SIGNED BY THE HOST")
star(L + 60, cy - 64, 40); star(R - 60, cy - 64, 40)
d.end()

# ================================================================== 16 thank-you (spec text verbatim)
c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
c.setFillColor(d.P); c.rect(0, PH - 64, PW, 64, fill=1, stroke=0)
c.setFillColor(d.A); c.rect(0, PH - 68, PW, 4, fill=1, stroke=0)
star(PW / 2, PH - 250, 110)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 300, "You just made my day!")
d._ornament(PW / 2, PH - 324)
y = PH - 352
y = para_c(y, "Thank you for choosing a small, one-person shop over the big guys.", 420, 13, font=d.SS, lead=1.5) - 16
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 460, 13, font=d.SS, lead=1.5) - 22
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(PW / 2 - 200, y - 56, 400, 56, 12, fill=1, stroke=1)
reg("review box", PW / 2 - 200, y - 56, 400, 56, 12)
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
bell(PW / 2 - 160, PH - 250, 60); tree(PW / 2 + 160, PH - 254, 70)
c.showPage()
d.save()
print("built", OUT)

PAD = 18  # the bar: 0.25 in
exec(open(__file__.rsplit("/", 1)[0] + "/checks.py").read())
