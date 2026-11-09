"""Build the Christmas Trivia Game PDF (200 questions, 10 rounds). python3 build.py <out.pdf>"""
import sys, datetime
HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, HERE)
import gm_style as gs
from content import ROUNDS, TIEBREAKERS
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else HERE + "/christmas-trivia-game.pdf"
PAL = gs.palette("evergreen")
NAME = "Christmas Trivia Game  ·  200 Questions"
d = gs.Book(OUT, NAME, PAL, cover_style="frame", page_frame="stripe")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
W = R - L
RED, REDT = HexColor("#9E3B33"), HexColor("#F4E1DE")
PAPER = HexColor(PAL["paper"])
FOOT_RULE = M - 1          # stripe frame footer rule (gs.Book.end: MARGIN - 14 + 13)
CLEAR = 18                 # 0.25 in between the lowest element and the footer rule
BOTTOM = FOOT_RULE + CLEAR + 1.5
PAD = 20                   # draw inset; check_boxes proves the 0.25 in (18 pt) bar
HEAD = 40
BOXES = []
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
CONTENT_PAGES = 16          # cover + host + 10 rounds + 2 keys + answer sheet + score sheet (thank-you not counted)


def reg(name, x, yb, w, h, r=8):
    BOXES.append((c.getPageNumber(), name, x, yb, w, h, r))


def para(x, y, text, width, size=10, font=None, color=None, lead=1.42):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawString(x, y - size, ln); y -= size * lead
    return y


def para_c(y, text, width, size=10.5, font=None, color=None, lead=1.45, cx=PW / 2):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawCentredString(cx, y - size, ln); y -= size * lead
    return y


def para_h(text, width, size=10, font=None, lead=1.42):
    return len(gs.wrap(text, font or d.F, size, width)) * size * lead


def card(x, y, w, h, title=None, fill=white, stroke=None):
    c.setStrokeColor(stroke or d.HAIR); c.setLineWidth(0.9); c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    reg(title or "card", x, y - h, w, h, 8)
    if title:
        c.setFillColor(d.T); c.roundRect(x, y - HEAD, w, HEAD, 8, fill=1, stroke=0); c.rect(x, y - HEAD, w, 10, fill=1, stroke=0)
        c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(x + PAD, y - 26, title.upper())
    return y - (HEAD if title else 0) - PAD


def star(x, y, s, fill=None, stroke=None):
    import math
    pts = []
    for i in range(10):
        r = s / 2 if i % 2 == 0 else s / 4.6
        a = math.pi / 2 + i * math.pi / 5
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close()
    c.setFillColor(fill or HexColor("#F3E6C8")); c.setStrokeColor(stroke or d.A); c.setLineWidth(1.2)
    c.drawPath(p, fill=1, stroke=1)


def holly(x, y, s):
    """Two simple leaves and three berries (kit-style drawn motif)."""
    for sgn in (-1, 1):
        p = c.beginPath(); p.moveTo(x, y)
        p.curveTo(x + sgn * s * 0.35, y + s * 0.32, x + sgn * s * 0.75, y + s * 0.28, x + sgn * s, y + s * 0.05)
        p.curveTo(x + sgn * s * 0.7, y - s * 0.12, x + sgn * s * 0.3, y - s * 0.1, x, y); p.close()
        c.setFillColor(d.P); c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(RED)
    for dx, dy in ((-0.1, 0.06), (0.1, 0.06), (0, -0.1)):
        c.circle(x + dx * s, y + dy * s, s * 0.11, fill=1, stroke=0)


# ================================================================== page 1: cover
d.page += 1
c.setFillColor(PAPER); c.rect(0, 0, PW, PH, fill=1, stroke=0)
for inset, w_ in ((36, 1.6), (46, 0.6)):
    c.setStrokeColor(d.P); c.setLineWidth(w_); c.rect(inset, inset, PW - 2 * inset, PH - 2 * inset, fill=0, stroke=1)
d._spaced(PW / 2, PH - 112, "PRINTABLE CHRISTMAS PARTY GAME", 10.5, d.P, d.FM)
holly(PW / 2, PH - 140, 30)
c.setFillColor(d.D); c.setFont(d.S, 58); c.drawCentredString(PW / 2, PH - 222, "Christmas")
c.drawCentredString(PW / 2, PH - 284, "Trivia Game")
# the count: the one thing we beat rivals on
c.setFillColor(d.P); c.roundRect(PW / 2 - 170, PH - 368, 340, 58, 29, fill=1, stroke=0)
c.setFillColor(white); c.setFont(d.S, 30); c.drawCentredString(PW / 2, PH - 349, "200 Questions")
y = para_c(PH - 392, "10 themed rounds with answer keys, a host script, team answer sheets and a score sheet",
           400, 15, font=d.SS, lead=1.4)
# rounds panel
py_top = y - 22
ph_ = 230
c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.9)
c.roundRect(L + 20, py_top - ph_, W - 40, ph_, 10, fill=1, stroke=1)
reg("cover rounds", L + 20, py_top - ph_, W - 40, ph_, 10)
d._spaced(PW / 2, py_top - 38, "THE 10 ROUNDS", 9.5, d.P, d.FM)
d._ornament(PW / 2, py_top - 54)
colx = [L + 20 + 34, PW / 2 + 14]
for i, (t, sub, qs) in enumerate(ROUNDS):
    col, row = i // 5, i % 5
    yy = py_top - 84 - row * 28
    c.setFillColor(d.T); c.circle(colx[col] + 9, yy + 3.5, 10, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 9.5); c.drawCentredString(colx[col] + 9, yy, str(i + 1))
    c.setFillColor(d.INK); c.setFont(d.F, 11); c.drawString(colx[col] + 28, yy, t)
COVER_PANEL_BOTTOM = py_top - ph_
c.setFillColor(d.MUT)
d._spaced(PW / 2, 78, f"{CONTENT_PAGES} PAGES  ·  US LETTER, PRINTS ON A4  ·  INSTANT DOWNLOAD", 8.5, d.MUT, d.FM)
c.setFont(d.F, 8.5); c.setFillColor(d.MUT); c.drawCentredString(PW / 2, 58, "GM's Digital Creations")
c.showPage()

# ================================================================== page 2: how to play + host script
d.start("How to Play", None, kicker="Start here  ·  host page", centered=True)
GAP = 12
cw = (W - GAP) / 2
SZ = 9.6
setup = ["Teams of 2 to 6 players. The score sheet fits up to 10 teams.",
         "Print one Team Answer Sheet (page 15) per team for each round.",
         "Print one Team Score Sheet (page 16) for the host.",
         "Keep the answer keys (pages 13 and 14) with the host."]
play = ["Read each question twice. Teams write one answer.",
        "One point each: 20 a round, 200 in all.",
        "Joker: once per game a team may double one round, if it says so before the round.",
        "Teams swap sheets and mark them as you read the answers."]


def bullet_h(items, width, size=SZ):
    return sum(para_h(t, width - 14, size, lead=1.36) + 4 for t in items) - 4


def bullet_draw(x, y, items, width, size=SZ):
    for t in items:
        c.setFillColor(d.A); c.circle(x + 3, y - size * 0.62, 2.2, fill=1, stroke=0)
        y = para(x + 13, y, t, width - 14, size, lead=1.36) - 4
    return y


top = d.y
ih = max(bullet_h(setup, cw - 2 * PAD), bullet_h(play, cw - 2 * PAD))
h1 = HEAD + PAD + ih + PAD
yy = card(L, top, cw, h1, "Set up")
bullet_draw(L + PAD, yy, setup, cw - 2 * PAD)
yy = card(L + cw + GAP, top, cw, h1, "Play and score")
bullet_draw(L + cw + GAP + PAD, yy, play, cw - 2 * PAD)
y = top - h1 - GAP

script = [("To start", "\u201cWelcome to Christmas Trivia! Ten rounds, twenty questions each. Write your team name on your sheet.\u201d"),
          ("Each round", "\u201cRound [number]: [name]. Jokers, speak now. I'll read every question twice. Ready?\u201d"),
          ("After a round", "\u201cPencils down! Pass your sheet to the team on your left and mark it as I read the answers.\u201d"),
          ("The finale", "\u201cThe scores are in. In third place... in second place... and our champions are...\u201d")]
LW = 88
sh = sum(para_h(t, W - 2 * PAD - LW, SZ, d.SS, lead=1.36) + 6 for _, t in script) - 6
h2 = HEAD + PAD + sh + PAD
yy = card(L, y, W, h2, "Host script: read it out", fill=PAPER)
for lab, t in script:
    c.setFillColor(d.P); c.setFont(d.FM, 8.8); c.drawString(L + PAD, yy - SZ, lab.upper())
    yy = para(L + PAD + LW, yy, t, W - 2 * PAD - LW, SZ, d.SS, lead=1.36) - 6
y = y - h2 - GAP

tips = ["Each round takes about 15 minutes with marking. Short on time? Play any 4 rounds in about an hour.",
        "Round 9 is an easy Kids' Round: use it as a warm-up or as a round for younger players.",
        "A tie at the end? Three closest-number tie-breakers are on the score sheet (page 16)."]

h4 = y - BOTTOM
need = HEAD + PAD + bullet_h(tips, W - 2 * PAD) + PAD
print("host page: h1 %.0f h2 %.0f tips need %.0f have %.0f" % (h1, h2, need, h4))
assert h4 >= need, ("host page overflow", h4, need)
yy = card(L, y, W, h4, "Tips for a smooth game")
yy -= (h4 - need) / 2   # center the tips so the page reaches the footer with no empty band
bullet_draw(L + PAD, yy, tips, W - 2 * PAD)
d.end()

# ================================================================== pages 3-12: the rounds
QS = 10.5
ROUND_PAGES = {}
for ri, (title, sub, qs) in enumerate(ROUNDS, 1):
    d.start(title, sub, kicker=f"Round {ri} of 10  ·  20 questions  ·  1 point each", centered=True)
    ROUND_PAGES[ri] = d.page
    top = d.y
    rowh = (top - BOTTOM) / 20
    assert rowh >= QS * 2.3, ("round rows too tight", ri, rowh)
    for qi, (q, a) in enumerate(qs):
        assert stringWidth(q, d.F, QS) <= W - 46, ("question wraps", q)
        yt = top - qi * rowh
        yb = yt - rowh
        mid = (yt + yb) / 2
        if qi % 2 == 0:
            c.setFillColor(HexColor("#F3F6F4")); c.rect(L, yb, W, rowh, fill=1, stroke=0)
        c.setFillColor(d.P); c.circle(L + 15, mid, 10.5, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(d.FM, 9.5); c.drawCentredString(L + 15, mid - 3.4, str(qi + 1))
        c.setFillColor(d.INK); c.setFont(d.F, QS); c.drawString(L + 36, mid - QS * 0.36, q)
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(L, BOTTOM, R, BOTTOM)
    d.end()

# ================================================================== pages 13-14: answer keys
KS = 9.2
key_colw = W / 4
for half in (0, 1):
    first = half * 5 + 1
    d.start(f"Answer Key: Rounds {first} to {first + 4}", None, kicker="For the host only", centered=True)
    top = d.y
    TB_H = 26 if half else 0          # page 14 also carries the tie-breaker answers (kept off the score sheet photo)
    sec_h = (top - BOTTOM - TB_H) / 5
    need_w = [max(stringWidth(a, d.F, KS) for t_, s_, qs_ in ROUNDS[first - 1:first + 4] for a in [x_[1] for x_ in qs_[cc * 5:cc * 5 + 5]]) + 26 for cc in range(4)]
    extra = (W - sum(need_w)) / 4
    assert extra >= 0, ("key columns overflow", need_w)
    KW = [w_ + extra for w_ in need_w]
    for k in range(5):
        ri = first + k
        title, sub, qs = ROUNDS[ri - 1]
        ys = top - k * sec_h
        c.setFillColor(d.P); c.setFont(d.SB, 12.5); c.drawString(L, ys - 13, f"Round {ri}  ·  {title}")
        c.setStrokeColor(d.A); c.setLineWidth(0.8); c.line(L, ys - 20, R, ys - 20)
        rh = (sec_h - 30 - 8) / 5
        assert rh >= KS * 1.35, ("key rows too tight", rh)
        for qi, (q, a) in enumerate(qs):
            col, row = qi // 5, qi % 5
            x = L + sum(KW[:col])
            yy = ys - 30 - row * rh - KS
            c.setFillColor(d.P); c.setFont(d.FM, KS); c.drawRightString(x + 16, yy, f"{qi + 1}.")
            c.setFillColor(d.INK); c.setFont(d.F, KS); c.drawString(x + 21, yy, a)
            assert stringWidth(a, d.F, KS) <= KW[col] - 26, ("key answer too wide", a)
    if half:
        c.setStrokeColor(d.A); c.setLineWidth(0.8); c.line(L, BOTTOM + 20, R, BOTTOM + 20)
        tb = "Tie-breaker answers (questions on page 16):   " + "     ".join(f"{i + 1}.  {a}" for i, (q, a) in enumerate(TIEBREAKERS))
        c.setFillColor(d.P); c.setFont(d.FM, KS); c.drawString(L, BOTTOM + 4, tb)
        assert stringWidth(tb, d.FM, KS) <= W
    d.end()

# ================================================================== page 15: team answer sheet
d.start("Team Answer Sheet", "Print one per team for each round. Write neatly: another team marks it.",
        kicker="Print as many as you need", centered=True)
top = d.y
hh = 78
yy = card(L, top, W, hh, fill=PAPER)
c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawString(L + PAD, top - hh / 2 - 4, "TEAM NAME")
c.setStrokeColor(d.D); c.setLineWidth(0.8); c.line(L + PAD + 80, top - hh / 2 - 6, L + W - 170, top - hh / 2 - 6)
c.setFillColor(d.D); c.drawString(L + W - 150, top - hh / 2 - 4, "ROUND")
c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1)
c.roundRect(R - PAD - 60, top - hh / 2 - 19, 60, 38, 6, fill=1, stroke=1)
y = top - hh - GAP
sh_ = 70
area = y - (BOTTOM + sh_ + GAP)
lh = area / 10
assert lh >= 30, lh
colw2 = (W - GAP) / 2
for col in range(2):
    x0 = L + col * (colw2 + GAP)
    for r in range(10):
        n = col * 10 + r + 1
        yl = y - (r + 1) * lh + 8
        c.setFillColor(d.T); c.circle(x0 + 11, yl + 8, 10, fill=1, stroke=0)
        c.setFillColor(d.P); c.setFont(d.FM, 9.5); c.drawCentredString(x0 + 11, yl + 4.6, str(n))
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.line(x0 + 28, yl, x0 + colw2, yl)
yb = BOTTOM
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1.2); c.roundRect(L, yb, W, sh_, 10, fill=1, stroke=1)
reg("score strip", L, yb, W, sh_, 10)
c.setFillColor(d.D); c.setFont(d.SB, 14); c.drawString(L + PAD + 4, yb + sh_ / 2 - 5, "Round score")
c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1); c.roundRect(L + PAD + 108, yb + sh_ / 2 - 16, 54, 32, 5, fill=1, stroke=1)
c.setFillColor(d.D); c.setFont(d.SB, 14); c.drawString(L + PAD + 170, yb + sh_ / 2 - 5, "/ 20")
c.setFont(d.FM, 10); c.drawRightString(R - PAD - 30, yb + sh_ / 2 - 4, "Joker played this round?")
c.setFillColor(white); c.roundRect(R - PAD - 20, yb + sh_ / 2 - 10, 20, 20, 3, fill=1, stroke=1)
d.end()

# ================================================================== page 16: team score sheet
d.start("Team Score Sheet", "Write each team's score after every round. Circle the round a team played its Joker and count it twice.",
        kicker="For the host", centered=True)
cols = ["Team"] + [f"R{i}" for i in range(1, 11)] + ["Total"]
widths = [3.4] + [1] * 10 + [1.5]
NT = 10
tb_w = W - 2 * PAD - 60
note = "Still tied at the end? The host reads one of these. Each team writes a number; the closest wins. Answers are on page 14."

th = sum(para_h(q, tb_w - 18, SZ, lead=1.36) + 5 for q, a in TIEBREAKERS) - 5
nh = para_h(note, W - 2 * PAD, SZ, lead=1.36) + 6
h3 = HEAD + PAD + nh + th + PAD
rowh = d.fit_rowh(NT, bottom=BOTTOM + h3 + GAP + 14, max_h=60)
d.table(cols, widths, rows=[], empty=NT, rowh=rowh)
assert d.y >= BOTTOM + h3 + GAP - 0.5, ("score table runs into the tie-breakers", d.y)
y = BOTTOM + h3
yy = card(L, y, W, h3, "Tie-breakers: closest number wins")
yy = para(L + PAD, yy, note, W - 2 * PAD, SZ, color=d.MUT, lead=1.36) - 6
for i, (q, a) in enumerate(TIEBREAKERS):
    c.setFillColor(d.P); c.setFont(d.FM, SZ); c.drawString(L + PAD, yy - SZ, f"{i + 1}.")
    yy = para(L + PAD + 18, yy, q, tb_w - 18, SZ, lead=1.36) - 5
d.end()

# ================================================================== page 17: thank-you
d.page += 1
d._frame()
TYD = 52
star(PW / 2, PH - 236 - TYD, 46)
holly(PW / 2 - 150, PH - 240 - TYD, 30); holly(PW / 2 + 150, PH - 240 - TYD, 30)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 316 - TYD, "You just made my day!")
d._ornament(PW / 2, PH - 340 - TYD)
y = PH - 368 - TYD
y = para_c(y, "Thank you for choosing a small, one-person shop over the big guys.", 420, 13, font=d.SS, lead=1.5) - 16
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 460, 13, font=d.SS, lead=1.5) - 22
bw = 420
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(PW / 2 - bw / 2, y - 60, bw, 60, 12, fill=1, stroke=1)
reg("review box", PW / 2 - bw / 2, y - 60, bw, 60, 12)
parts = "How: Etsy app → You → Purchases → Leave a review".split("→")
widths_ = [stringWidth(p, d.FM, 12.5) for p in parts]; aw = stringWidth("→", "DejaVu", 12.5)
x = PW / 2 - (sum(widths_) + aw * (len(parts) - 1)) / 2
c.setFillColor(d.D)
for i, p in enumerate(parts):
    c.setFont(d.FM, 12.5); c.drawString(x, y - 34, p); x += widths_[i]
    if i < len(parts) - 1:
        c.setFont("DejaVu", 12.5); c.drawString(x, y - 34, "→"); x += aw
y -= 60 + 26
y = para_c(y, "Something not right? Message me first and I'll fix it fast.", 420, 13, font=d.SS, lead=1.5) - 40
c.setFillColor(d.P); c.setFont(d.SB, 14); c.drawCentredString(PW / 2, y - 6, "With thanks,")
c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 30, "GM's Digital Creations")
c.showPage()
d.save()
print("built", OUT)

# ================================================================== verification by code
import re, subprocess, difflib
qs_all = [(ri, q, a) for ri, (t, s, qs) in enumerate(ROUNDS, 1) for q, a in qs]
assert len(ROUNDS) == 10 and all(len(qs) == 20 for t, s, qs in ROUNDS) and len(qs_all) == 200
assert len(set(q for _, q, _ in qs_all)) == 200, "duplicate question"
tf = [a for q, a in ROUNDS[7][2]]
assert tf.count("True") == 10 and tf.count("False") == 10, "true/false balance"
num = {q: a for q, a in ROUNDS[9][2]}
calc = {
    "A team scores 17 points in each of 10 rounds. What is its total score?": str(17 * 10),
    "If Christmas Day falls on a Monday, which day of the week is New Year's Day?": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][(0 + 7) % 7],
    "How many days after Christmas Day is New Year's Day?": str((datetime.date(2027, 1, 1) - datetime.date(2026, 12, 25)).days),
    "How many hours are there in the twelve days of Christmas?": str(12 * 24),
    "How many legs do eight reindeer have altogether?": str(8 * 4),
    "A dozen mince pies plus half a dozen more: how many pies is that?": str(12 + 6),
    "If the winter solstice is on December 21, how many days later is Christmas Day?": str(25 - 21),
    "How many letters are in the word CHRISTMAS?": str(len("CHRISTMAS")),
    "Counting both days, how many days are there from December 1 to December 25?": str((datetime.date(2026, 12, 25) - datetime.date(2026, 12, 1)).days + 1),
    "On which day of the week does Christmas Day 2026 fall?": datetime.date(2026, 12, 25).strftime("%A"),
    "How many minutes are there in Christmas Day?": f"{24 * 60:,}",
    "24 party guests split into teams of 4. How many teams is that?": str(24 // 4),
    "By number, which month of the year is December?": f"{datetime.date(2026, 12, 1).month}th",
}
for q, v in calc.items():
    assert num[q] == v, (q, num[q], v)
assert TIEBREAKERS[2][1] == str((datetime.date(2027, 12, 25) - datetime.date(2027, 1, 1)).days + 1), "tie-breaker 3"
# text in the PDF: every answer appears on its key page, every question on its round page
txt = subprocess.run(["pdftotext", "-layout", OUT, "-"], capture_output=True, text=True).stdout.split("\f")
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'"))
for ri, (t, s, qs) in enumerate(ROUNDS, 1):
    page = norm(txt[ROUND_PAGES[ri] - 1])
    for q, a in qs:
        assert norm(q) in page, ("question missing from page", ri, q)
    keyp = norm(txt[12 + (ri - 1) // 5])
    if ri == 10:
        assert all(a in keyp for q, a in TIEBREAKERS), "tie-breaker answers missing from page 14"
        assert not any(f"  {a}" in txt[15] or txt[15].rstrip().endswith(a) for q, a in TIEBREAKERS[:2]), "tie-breaker answer on the score sheet"
    for qi, (q, a) in enumerate(qs):
        assert norm(a) in keyp, ("answer missing from key", ri, a)
# originality: no trademarked characters/brands/songs; no reuse of the Party Bundle or Office Games trivia
BANNED = ["rudolph", "grinch", "frosty", "kfc", "coca", "disney", "hallmark", "elf on the shelf", "jingle", "lyric",
          "movie", "film", "song", "home alone", "charlie brown", "peanuts", "snoopy", "sears", "macy", "rockefeller"]
blob = " ".join(q + " " + a for _, q, a in qs_all).lower() + " ".join(q + a for q, a in TIEBREAKERS).lower()
hits = [b for b in BANNED if b in blob]
assert not hits, ("banned words", hits)
OLD = []
for f in ["2026-10-27-xmas-bundle-build/build.py", "2026-10-30-office-games-build/content.py"]:
    src = open(HERE + "/../" + f).read()
    import ast
    i0 = src.find("TRIVIA = [") + len("TRIVIA = ")
    OLD += [t_[0] for t_ in ast.literal_eval(src[i0:src.find("\n]", i0) + 2])]
assert len(OLD) == 32, len(OLD)
sim = max((difflib.SequenceMatcher(None, q.lower(), o.lower()).ratio(), q, o) for _, q, _ in qs_all for o in OLD)
assert sim[0] < 0.75, ("too close to an old trivia question", sim)
print(f"verify OK: 200 questions unique, T/F 10/10, {len(calc)} number answers computed, 200 keys found on key pages,"
      f" 0 banned words, closest old question {sim[0]:.2f}")

PAD = 18  # the bar: 0.25 in
exec(open(HERE + "/checks.py").read().replace('if __name__ == "__main__":', "if True:"))
# fill check: every content page reaches within 1.2 in of the footer rule (no empty band over ~15%)
for n, gap_in, has_rule in check_clearance(OUT):
    if has_rule: assert gap_in < 1.2, ("half-empty page", n, gap_in)
assert COVER_PANEL_BOTTOM > 96, COVER_PANEL_BOTTOM
print("fill OK")
