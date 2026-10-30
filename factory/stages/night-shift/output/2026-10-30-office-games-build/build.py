"""Build Office Christmas Party Games PDF. python3 build.py <out.pdf>"""
import sys, math
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gm_style as gs
import content as K
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = sys.argv[1] if len(sys.argv) > 1 else "office-christmas-party-games.pdf"
PAL = gs.palette("honey")
NAME = "Office Christmas Party Games"
d = gs.Book(OUT, NAME, PAL, cover_style="band", page_frame="stripe")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
W = R - L
BERRY, BERRYT = HexColor("#9C3A41"), HexColor("#F6E4E1")
PINE, PINET = HexColor("#5E6F4E"), HexColor("#E9EDE2")
FOOT_RULE = M - 1
CLEAR = 18
BOTTOM = FOOT_RULE + CLEAR + 1.5
PAD = 18
BOXES = []
TYPE_COL = {"Mingle": (BERRY, BERRYT), "Team": (d.D, d.T), "Icebreaker": (PINE, PINET),
            "Active": (BERRY, BERRYT), "Seated": (PINE, PINET)}


def reg(name, x, yb, w, h, r=8):
    BOXES.append((c.getPageNumber(), name, x, yb, w, h, r))


def para(x, y, text, width, size=10, font=None, color=None, lead=1.42):
    font = font or d.F; c.setFont(font, size); c.setFillColor(color or d.INK)
    for ln in gs.wrap(text, font, size, width):
        c.drawString(x, y - size, ln); y -= size * lead
    return y


def para_c(y, text, width, size=10.5, font=None, color=None, lead=1.45):
    font = font or d.F; c.setFont(font, size); c.setFillColor(color or d.INK)
    for ln in gs.wrap(text, font, size, width):
        c.drawCentredString(PW / 2, y - size, ln); y -= size * lead
    return y


def nlines(text, width, size, font=None):
    return len(gs.wrap(text, font or d.F, size, width))


def card(x, ytop, w, h, name, fill=white, stroke=None, r=8, lw=1.1):
    c.setFillColor(fill); c.setStrokeColor(stroke or d.P); c.setLineWidth(lw)
    c.roundRect(x, ytop - h, w, h, r, fill=1, stroke=1)
    reg(name, x, ytop - h, w, h, r)


def star(x, y, s, col):
    p = c.beginPath()
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = s if i % 2 == 0 else s * 0.42
        (p.moveTo if i == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    p.close(); c.setFillColor(col); c.drawPath(p, fill=1, stroke=0)


def snowflake(x, y, s, col):
    c.setStrokeColor(col); c.setLineWidth(max(0.8, s * 0.09))
    for k in range(6):
        a = k * math.pi / 3; ex, ey = x + s * math.cos(a), y + s * math.sin(a)
        c.line(x, y, ex, ey)
        for sgn in (-1, 1):
            b = a + sgn * 0.6; mx, my = x + s * 0.6 * math.cos(a), y + s * 0.6 * math.sin(a)
            c.line(mx, my, mx + s * 0.3 * math.cos(b), my + s * 0.3 * math.sin(b))


def chip(x, y, text, col, tint, size=7.6):
    w = stringWidth(text, d.FM, size) + 14
    c.setFillColor(tint); c.roundRect(x, y - 4, w, 15, 7.5, fill=1, stroke=0)
    c.setFillColor(col); c.setFont(d.FM, size); c.drawString(x + 7, y + 0.5, text)
    return w


# ================================================================== 1 cover (PDF)
CONTENT_PAGES = 15
d.cover(["Office Christmas", "Party Games"], "24 no-prep games for coworkers, a 45-minute run sheet, score sheet and answer keys",
        pages=CONTENT_PAGES, kicker="PRINTABLE PARTY GAMES")

# ================================================================== 2 host plan + run sheet
d.start("Your 45-Minute Party Plan", "Got handed the staff party? Print this page and you are the host. Every game here works for "
        "any coworker: no props to buy, no drinking, no movie or song knowledge.", kicker="Start here")
y = d.y
# what to print box
bh = 112
card(L, y, W, bh, "print box", fill=d.T, stroke=d.P)
c.setFillColor(d.D); c.setFont(d.SB, 12.5); c.drawString(L + PAD, y - PAD - 12, "What to print (US Letter, black and white is fine)")
items = ["Bingo card: 1 per person (page 10)", "Fact card: 1 per person, cut out (page 14)",
         "Scramble + trivia: 1 per team (11, 12)", "Letter Lists: 1 per team (page 13)",
         "Score sheet: 1 for the host (page 15)", "Answer keys: host only (page 16)"]
colw = (W - 2 * PAD) / 2
for i, it in enumerate(items):
    xx = L + PAD + 2 + (i % 2) * colw; yy = y - PAD - 36 - (i // 2) * 17
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.setFillColor(white); c.roundRect(xx, yy - 2, 9, 9, 2, fill=1, stroke=1)
    c.setFillColor(d.INK); c.setFont(d.F, 9.4); c.drawString(xx + 15, yy, it)
y -= bh + 16
c.setFillColor(d.P); c.setFont(d.SB, 13); c.drawString(L, y - 13, "The run sheet"); y -= 24
# run sheet rows
rows = K.RUN_SHEET
avail_tbl = y - (BOTTOM + 98)
rh = avail_tbl / len(rows)
for i, (t, mins, game, why) in enumerate(rows):
    yt = y - i * rh
    c.setFillColor(d.T if i % 2 == 0 else white); c.rect(L, yt - rh, W, rh, fill=1, stroke=0)
    c.setFillColor(BERRY); c.setFont(d.S, 15); c.drawString(L + 10, yt - rh / 2 - 5, t)
    c.setFillColor(d.MUT); c.setFont(d.FM, 8); c.drawString(L + 62, yt - rh / 2 - 3, mins.upper())
    c.setFillColor(d.D); c.setFont(d.SB, 11.5); c.drawString(L + 120, yt - rh / 2 + 3, game)
    c.setFillColor(d.INK); c.setFont(d.F, 8.8); c.drawString(L + 120, yt - rh / 2 - 10, why)
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.line(L, yt - rh, R, yt - rh)
y -= len(rows) * rh + 12
bw = (W - 12) / 2; bh2 = y - BOTTOM
for j, (ttl, txt) in enumerate([("Only 20 minutes?", "Play Silent Line-Up, Bingo and Last One Standing. Skip the score sheet."),
                                ("More than 30 people?", "Make teams of 6. Swap Trivia for Sixty-Second Sprints so every table plays at once.")]):
    xx = L + j * (bw + 12)
    card(xx, y, bw, bh2, "tip " + ttl, fill=white, stroke=BERRY if j == 0 else PINE)
    c.setFillColor(BERRY if j == 0 else PINE); c.setFont(d.SB, 11); c.drawString(xx + PAD, y - PAD - 10, ttl)
    para(xx + PAD, y - PAD - 16, txt, bw - 2 * PAD, 8.8)
d.end()

# ================================================================== 3 game finder
d.start("Game Finder: All 24 Games", "Pick by group size, time and mood. Games 1 to 5 have a printable sheet; the other 19 "
        "need nothing but people (and a pen or scrap paper for a few).", kicker="Pick your games")
rows = []
for i, g in enumerate(K.GAMES):
    rows.append([str(i + 1), g[0], g[1], g[2], g[3], f"p. {g[6]:02d}" if g[6] else "none"])
d.table(["#", "Game", "Players", "Time", "Type", "Sheet"], [4, 30, 16, 9, 12, 9], rows, fill=False,
        rowh=(d.y - BOTTOM) / 25 - 0.01, size=9.2)
d.end()

# ================================================================== 4-9 game cards (4 per page)
GPAGE = [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 24)]
TITLES = ["Games 1 to 4", "Games 5 to 8", "Games 9 to 12", "Games 13 to 16", "Games 17 to 20", "Games 21 to 24"]
BS = 10.6; TS = 9.8
for pi, (a, b) in enumerate(GPAGE):
    d.start(TITLES[pi], None, kicker="How to play")
    top = d.y + 2
    iw = W - 2 * PAD
    hs = []
    for g in K.GAMES[a:b]:
        h = PAD + 24 + 10 + nlines(g[4], iw, BS) * BS * 1.42 + 6 + nlines(g[5], iw, TS, d.FM) * TS * 1.42 + PAD - 4
        hs.append(h)
    avail = top - BOTTOM
    extra = avail - sum(hs)
    gap = min(16, extra / 3)
    add = (extra - 3 * gap) / 4
    assert extra >= 3 * 8, ("cards too tall", pi, extra)
    y = top
    for k, g in enumerate(K.GAMES[a:b]):
        n = a + k + 1
        h = hs[k] + add
        col, tint = TYPE_COL[g[3]]
        card(L, y, W, h, f"game {n}", fill=white, stroke=d.P)
        # number disc
        cy = y - PAD - 13
        c.setFillColor(col); c.circle(L + PAD + 12, cy, 10, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(d.FB, 9.5); c.drawCentredString(L + PAD + 12, cy - 3.4, str(n))
        c.setFillColor(d.D); c.setFont(d.S, 13.5); c.drawString(L + PAD + 30, cy - 5, g[0])
        # chips right aligned
        chips = [(g[1].upper(), d.D, d.T), (g[2].upper(), d.D, d.T), (g[3].upper(), col, tint)]
        if g[6]: chips.insert(0, (f"SHEET P. {g[6]:02d}", BERRY, BERRYT))
        ws = [stringWidth(t, d.FM, 7.6) + 14 for t, _, _ in chips]
        xx = R - PAD - sum(ws) - 5 * (len(ws) - 1)
        assert xx > L + PAD + 28 + stringWidth(g[0], d.S, 13.5) + 8, ("chips overlap name", n)
        for (t, cc, tt), w_ in zip(chips, ws):
            chip(xx, cy - 4, t, cc, tt); xx += w_ + 5
        yy = y - PAD - 24 - 10 - add / 2
        yy = para(L + PAD, yy, g[4], iw, BS)
        para(L + PAD, yy - 6, g[5], iw, TS, font=d.FM, color=BERRY if g[5].startswith("Win") else PINE)
        y -= h + gap
    d.end()

# ================================================================== 10 bingo
d.start("Coworker Holiday Bingo", "Find a different coworker for each square and write their first name in it. "
        "Nobody signs their own card. First full row, column or diagonal wins.", kicker="Game 1  ·  1 per person", centered=True)
top = d.y - 2
gs_ = W / 5
gh = (top - BOTTOM - 26) / 5
c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(L, top - 10, "My name: ______________________________")
top -= 24
cells = K.BINGO[:12] + ["FREE"] + K.BINGO[12:]
for i, txt in enumerate(cells):
    r_, k = divmod(i, 5)
    x = L + k * gs_; yt = top - r_ * gh
    free = txt == "FREE"
    c.setFillColor(d.T if free else white); c.setStrokeColor(d.P); c.setLineWidth(1.1)
    c.rect(x, yt - gh, gs_, gh, fill=1, stroke=1)
    if free:
        star(x + gs_ / 2, yt - gh / 2 + 12, 13, BERRY)
        c.setFillColor(d.D); c.setFont(d.FB, 9); c.drawCentredString(x + gs_ / 2, yt - gh / 2 - 14, "FREE SPACE")
        c.setFont(d.F, 7.6); c.setFillColor(d.MUT); c.drawCentredString(x + gs_ / 2, yt - gh / 2 - 25, "you came to the party")
        continue
    ls = gs.wrap(txt, d.FM, 8.6, gs_ - 14)
    ty = yt - 14
    for ln in ls:
        c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawCentredString(x + gs_ / 2, ty - 8.6, ln); ty -= 11.5
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(x + 9, yt - gh + 16, x + gs_ - 9, yt - gh + 16)
    c.setFillColor(d.MUT); c.setFont(d.F, 6.4); c.drawString(x + 9, yt - gh + 7, "name")
d.end()

# ================================================================== 11 word scramble
d.start("Holiday Word Scramble", "Unscramble each holiday word. The hint helps. 6 minutes on the clock!",
        kicker="Game 2  ·  1 per team", centered=True)
c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(L, d.y - 10, "Team name: ______________________________")
c.drawRightString(R, d.y - 10, "Score: ______ / 20"); d.y -= 26
SCR = [(K.scramble(w, i), w, h) for i, (w, h) in enumerate(K.SCRAMBLE)]
top = d.y; colw = (W - 14) / 2; rh = (top - BOTTOM) / 10
for i, (s, w, h) in enumerate(SCR):
    col_, r_ = divmod(i, 10)
    x = L + col_ * (colw + 14); yt = top - r_ * rh
    c.setFillColor(d.T if r_ % 2 == 0 else white); c.rect(x, yt - rh, colw, rh, fill=1, stroke=0)
    c.setFillColor(BERRY); c.setFont(d.FB, 9); c.drawString(x + 8, yt - 17, f"{i + 1}.")
    c.setFillColor(d.D); c.setFont(d.FM, 12); c.drawString(x + 28, yt - 18, " ".join(s))
    c.setFillColor(d.MUT); c.setFont(d.F, 7.8); c.drawString(x + 28, yt - 30, "hint: " + h)
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.line(x + 28, yt - rh + 9, x + colw - 10, yt - rh + 9)
d.end()

# ================================================================== 12 trivia
d.start("Holiday Trivia Showdown", "The host reads each question out loud. Talk it over quietly and write one answer.",
        kicker="Game 3  ·  1 per team", centered=True)
c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(L, d.y - 10, "Team name: ______________________________")
c.drawRightString(R, d.y - 10, "Score: ______ / 20"); d.y -= 22
_ws = [w * W / 90 for w in (4, 62, 24)]
_n2 = sum(1 for q, a in K.TRIVIA if len(gs.wrap(q, d.F, 8.9, _ws[1] - 14)) > 1)
_rh = (d.y - BOTTOM - 14 - 0.5) / 21
if _rh < 2 * 8.9 * 1.32 + 10:
    _rh = (d.y - BOTTOM - 14 - 0.5 - _n2 * (2 * 8.9 * 1.32 + 10)) / (21 - _n2)
d.table(["#", "Question", "Your answer"], [4, 62, 24], [[str(i + 1), q, ""] for i, (q, a) in enumerate(K.TRIVIA)],
        rowh=_rh, size=8.9)
d.end()

# ================================================================== 13 letter lists
d.start("Letter Lists", "The host calls a letter for each round. Write one answer per category that starts with it. "
        "2 minutes a round. Score 1 point for every answer no other team has.", kicker="Game 4  ·  1 per team", centered=True)
c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(L, d.y - 10, "Team name: ______________________________"); d.y -= 22
top = d.y; cw0 = 150; cw = (W - cw0) / 3
hh = 40
rh = (top - BOTTOM - hh - 30) / len(K.LETTER_CATS)
c.setFillColor(d.T); c.rect(L, top - hh, W, hh, fill=1, stroke=0)
c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawString(L + 10, top - 24, "CATEGORY")
for j in range(3):
    x = L + cw0 + j * cw
    c.setFillColor(d.D); c.setFont(d.FM, 8.6); c.drawString(x + 12, top - 24, f"ROUND {j + 1}")
    c.setStrokeColor(d.P); c.setLineWidth(1); c.setFillColor(white); c.roundRect(x + cw - 42, top - 33, 26, 26, 5, fill=1, stroke=1)
for i, cat in enumerate(K.LETTER_CATS):
    yt = top - hh - i * rh
    c.setFillColor(d.D); c.setFont(d.SB, 10.5)
    ls = gs.wrap(cat, d.SB, 10.5, cw0 - 18)
    ty = yt - rh / 2 + (len(ls) - 1) * 6.5 - 3.5
    for ln in ls: c.drawString(L + 10, ty, ln); ty -= 13
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(L, yt - rh, R, yt - rh)
for j in range(4):
    x = L + cw0 + j * cw - (0 if j < 3 else 0)
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(x, top, x, top - hh - rh * len(K.LETTER_CATS))
yb = top - hh - rh * len(K.LETTER_CATS)
c.setFillColor(d.T); c.rect(L, yb - 30, W, 30, fill=1, stroke=0)
c.setFillColor(d.D); c.setFont(d.FM, 9); c.drawString(L + 10, yb - 19, "ROUND SCORE")
d.end()

# ================================================================== 14 guess the coworker cards
d.start("Guess the Coworker", "Fill in one card. Do not write your name on the front! Fold it and hand it to the host.",
        kicker="Game 5  ·  cut 4 cards per page", centered=True)
top = d.y; gap = 16
cw_ = (W - gap) / 2; ch = (top - BOTTOM - gap) / 2
for k in range(4):
    r_, cc = divmod(k, 2)
    x = L + cc * (cw_ + gap); yt = top - r_ * (ch + gap)
    c.setDash(4, 3); c.setStrokeColor(d.MUT); c.setLineWidth(0.6)
    c.setFillColor(white); c.rect(x, yt - ch, cw_, ch, fill=1, stroke=1); c.setDash()
    reg(f"fact card {k + 1}", x, yt - ch, cw_, ch, 0)
    snowflake(x + PAD + 8, yt - PAD - 9, 8, d.P)
    c.setFillColor(d.D); c.setFont(d.S, 13); c.drawString(x + PAD + 22, yt - PAD - 13, "Mystery Coworker")
    c.setFillColor(BERRY); c.setFont(d.FM, 8.5); c.drawRightString(x + cw_ - PAD, yt - PAD - 12, "No. ____")
    yy = yt - PAD - 34
    step = (yy - (yt - ch + PAD)) / len(K.FACT_PROMPTS)
    for pr in K.FACT_PROMPTS:
        c.setFillColor(d.INK); c.setFont(d.FM, 8.4); c.drawString(x + PAD, yy - 9, pr + "...")
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.line(x + PAD, yy - step + 8, x + cw_ - PAD, yy - step + 8)
        yy -= step
d.end()

# ================================================================== 15 score sheet
d.start("Team Score Sheet", "Write team names across the top. Add each game's points as you go.", kicker="For the host", centered=True)
games = ["Coworker Holiday Bingo", "Holiday Trivia Showdown", "Holiday Word Scramble", "Letter Lists", "Sixty-Second Sprints",
         "Pocket Scavenger Hunt", "Freeze Frame", "Holiday Act-It-Out", "Two Truths and a Tale", "Bonus round", "Bonus round"]
d.table(["Game", "Team 1", "Team 2", "Team 3", "Team 4", "Team 5", "Team 6"], [30, 10, 10, 10, 10, 10, 10],
        [[g] + [""] * 6 for g in games] + [["TOTAL"] + [""] * 6], rowh=(d.y - BOTTOM - 70) / 13 - 0.01, size=9.2)
yb = d.y + 14 - 10
card(L, yb, W, yb - BOTTOM, "winner box", fill=d.T, stroke=d.P)
star(L + PAD + 10, yb - (yb - BOTTOM) / 2, 11, BERRY)
c.setFillColor(d.D); c.setFont(d.S, 14); c.drawString(L + PAD + 30, yb - (yb - BOTTOM) / 2 - 5, "And the winning team is:")
c.setStrokeColor(d.P); c.setLineWidth(0.8); c.line(L + PAD + 210, yb - (yb - BOTTOM) / 2 - 6, R - PAD, yb - (yb - BOTTOM) / 2 - 6)
d.end()

# ================================================================== 16 answer keys
d.start("Answer Keys", "For the host only. Keep this page face down until scoring time.", kicker="Host only", centered=True)
top = d.y; colw = (W - 16) / 2
for j, (ttl, data) in enumerate([("Game 2: Word Scramble", [w for s, w, h in SCR]), ("Game 3: Holiday Trivia", [a for q, a in K.TRIVIA])]):
    x = L + j * (colw + 16)
    h = top - BOTTOM
    card(x, top, colw, h, "key " + ttl, fill=white, stroke=d.P)
    c.setFillColor(d.T); c.rect(x + 1.5, top - 44, colw - 3, 42.5, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(x + PAD, top - 28, ttl)
    rh = (h - 44 - 2 * PAD) / 20
    for i, a in enumerate(data):
        yy = top - 44 - PAD - i * rh
        c.setFillColor(BERRY); c.setFont(d.FB, 9); c.drawString(x + PAD, yy - rh / 2 - 3, f"{i + 1}.")
        c.setFillColor(d.INK); c.setFont(d.FM, 10); c.drawString(x + PAD + 24, yy - rh / 2 - 3.5, a.title() if j == 0 else a)
d.end()

# ================================================================== 17 thank-you (spec text verbatim)
c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
d._frame()
for k, (sx, sy, ss) in enumerate([(PW / 2 - 120, PH - 270, 16), (PW / 2, PH - 250, 24), (PW / 2 + 120, PH - 270, 16)]):
    snowflake(sx, sy, ss, d.P if k != 1 else BERRY)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 330, "You just made my day!")
d._ornament(PW / 2, PH - 354)
y = PH - 384
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
c.showPage()
d.save()
print("built", OUT)

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
    # answer keys verified by code
    for s_, w_, h_ in SCR:
        assert sorted(s_) == sorted(w_) and s_ != w_, (s_, w_)
    assert len(SCR) == 20 and len(K.TRIVIA) == 20 and all(a for q, a in K.TRIVIA)
    print("keys OK: 20 scrambles are true anagrams, 20 trivia answers present")
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

