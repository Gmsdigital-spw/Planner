"""Build the Christmas escape room PDF (The Bell Vault). python3 build.py <out.pdf>"""
import sys, math, random
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gm_style as gs
import puzzles as pz
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = sys.argv[1] if len(sys.argv) > 1 else "escape-room.pdf"
PAL = gs.palette("berry")
NAME = "The Bell Vault  ·  Christmas Escape Room"
d = gs.Book(OUT, NAME, PAL, cover_style="split", page_frame="rule")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
GREEN, GTINT = HexColor("#5C7A4E"), HexColor("#E7EDE1")
GOLD, GOLDT = HexColor("#B08A3E"), HexColor("#F6EEDB")
BOTTOM = M + 16          # lowest content line (footer rule sits at M - 1)


# ------------------------------------------------------------------ drawing helpers
def poly(pts, fill=None, stroke=None, lw=1.2):
    p = c.beginPath(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close()
    if fill is not None: c.setFillColor(fill)
    if stroke is not None: c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.drawPath(p, fill=1 if fill is not None else 0, stroke=1 if stroke is not None else 0)


def star(x, y, r, fill=None, stroke=None, lw=1.2):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    poly(pts, fill if fill is not None else GOLDT, stroke if stroke is not None else GOLD, lw)


def tree(x, y, s):
    """x centre, y bottom, s height."""
    c.setFillColor(HexColor("#C9B79C")); c.setStrokeColor(d.D); c.setLineWidth(0.9)
    c.rect(x - s * 0.06, y, s * 0.12, s * 0.14, fill=1, stroke=1)
    for i, (w, b, t) in enumerate(((0.5, 0.12, 0.55), (0.4, 0.38, 0.78), (0.3, 0.6, 1.0))):
        poly([(x - s * w, y + s * b), (x + s * w, y + s * b), (x, y + s * t)], GTINT, GREEN, 1.1)


def gift(x, y, s):
    """x centre, y bottom, s box width."""
    c.setStrokeColor(d.D); c.setLineWidth(1.1); c.setFillColor(d.T)
    c.rect(x - s / 2, y, s, s * 0.8, fill=1, stroke=1)
    c.setFillColor(white); c.rect(x - s * 0.58, y + s * 0.8, s * 1.16, s * 0.2, fill=1, stroke=1)
    c.setFillColor(d.P); c.rect(x - s * 0.08, y, s * 0.16, s, fill=1, stroke=0)
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.2)
    c.ellipse(x - s * 0.36, y + s * 1.0, x - s * 0.02, y + s * 1.24, fill=0, stroke=1)
    c.ellipse(x + s * 0.02, y + s * 1.0, x + s * 0.36, y + s * 1.24, fill=0, stroke=1)


def bell(x, y, s, fill=None):
    """x centre, y bottom, s height."""
    c.setStrokeColor(GOLD); c.setLineWidth(1.1); c.setFillColor(fill if fill is not None else GOLDT)
    p = c.beginPath()
    p.moveTo(x - s * 0.5, y + s * 0.14)
    p.curveTo(x - s * 0.36, y + s * 0.3, x - s * 0.36, y + s * 0.62, x - s * 0.3, y + s * 0.78)
    p.curveTo(x - s * 0.2, y + s * 0.98, x + s * 0.2, y + s * 0.98, x + s * 0.3, y + s * 0.78)
    p.curveTo(x + s * 0.36, y + s * 0.62, x + s * 0.36, y + s * 0.3, x + s * 0.5, y + s * 0.14)
    p.close(); c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(GOLD); c.circle(x, y + s * 0.08, s * 0.08, fill=1, stroke=0)
    c.circle(x, y + s * 0.98, s * 0.05, fill=1, stroke=0)


def snowflake(x, y, r, col=None, lw=1.3):
    c.setStrokeColor(col or d.P); c.setLineWidth(lw)
    for i in range(6):
        a = i * math.pi / 3; ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        c.line(x, y, ex, ey)
        for f in (0.55,):
            bx, by = x + r * f * math.cos(a), y + r * f * math.sin(a)
            for da in (-0.6, 0.6):
                c.line(bx, by, bx + r * 0.3 * math.cos(a + da), by + r * 0.3 * math.sin(a + da))


def bulb(x, y, s, label=None):
    """x centre, y = socket top (bulb hangs down), s bulb height."""
    c.setStrokeColor(d.D); c.setLineWidth(1); c.setFillColor(HexColor("#D9D2C5"))
    c.rect(x - s * 0.16, y - s * 0.22, s * 0.32, s * 0.22, fill=1, stroke=1)
    c.setFillColor(GOLDT); c.setStrokeColor(GOLD); c.setLineWidth(1.3)
    c.ellipse(x - s * 0.34, y - s * 1.05, x + s * 0.34, y - s * 0.18, fill=1, stroke=1)
    if label is not None:
        c.setFillColor(d.D); c.setFont(d.S, s * 0.42); c.drawCentredString(x, y - s * 0.78, str(label))


def tag(x, y, w, h, fill=white):
    """Gift tag with a hole on the left. x,y bottom-left."""
    k = h * 0.32
    poly([(x + k, y), (x + w, y), (x + w, y + h), (x + k, y + h), (x, y + h - k), (x, y + k)], fill, d.P, 1.3)
    c.setFillColor(white); c.setStrokeColor(d.P); c.circle(x + k * 0.8, y + h / 2, 4, fill=1, stroke=1)


def padlock(x, y, s):
    """small padlock icon, x centre, y bottom, s height."""
    c.setStrokeColor(d.D); c.setLineWidth(s * 0.09); c.setFillColor(white)
    c.arc(x - s * 0.28, y + s * 0.35, x + s * 0.28, y + s * 0.98, 0, 180)
    c.line(x - s * 0.28, y + s * 0.66, x - s * 0.28, y + s * 0.5); c.line(x + s * 0.28, y + s * 0.66, x + s * 0.28, y + s * 0.5)
    c.setFillColor(d.T); c.setLineWidth(1.1); c.roundRect(x - s * 0.42, y, s * 0.84, s * 0.56, 3, fill=1, stroke=1)
    c.setFillColor(d.D); c.circle(x, y + s * 0.3, s * 0.06, fill=1, stroke=0)


ICON = {"star": lambda x, y, s: star(x, y + s / 2, s / 2), "tree": lambda x, y, s: tree(x, y, s),
        "gift": lambda x, y, s: gift(x, y, s * 0.8), "bell": lambda x, y, s: bell(x, y, s)}
CLUE_ICON = [lambda x, y, s: tag(x - s * 0.7, y + s * 0.2, s * 1.4, s * 0.6),
             lambda x, y, s: gift(x, y, s * 0.75),
             lambda x, y, s: bulb(x, y + s, s),
             lambda x, y, s: snowflake(x, y + s / 2, s / 2)]


def answer_box(y, label, cells=1, note=None):
    """Big 'digit found' box centred on the page; returns its bottom y."""
    h = 58; w = 300
    x = (PW - w) / 2
    c.setStrokeColor(d.P); c.setLineWidth(1.4); c.setFillColor(d.T)
    c.roundRect(x, y - h, w, h, 10, fill=1, stroke=1)
    c.setFillColor(d.D); c.setFont(d.SB, 15); c.drawString(x + 20, y - h / 2 - 5, label)
    bx = x + w - 20 - 44 * cells
    for i in range(cells):
        c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2)
        c.roundRect(bx + i * 44, y - h + 9, 40, 40, 6, fill=1, stroke=1)
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


def card(x, y, w, h, title=None, fill=white, stroke=None):
    c.setStrokeColor(stroke or d.HAIR); c.setLineWidth(0.9); c.setFillColor(fill)
    c.roundRect(x, y - h, w, h, 8, fill=1, stroke=1)
    if title:
        c.setFillColor(d.T); c.roundRect(x, y - 24, w, 24, 8, fill=1, stroke=0); c.rect(x, y - 24, w, 10, fill=1, stroke=0)
        c.setFillColor(d.D); c.setFont(d.FM, 9.5); c.drawString(x + 12, y - 16, title.upper())


def level_tab(level):
    """Small level marker in the top-right corner inside the frame."""
    txt = "LEVEL 1  ·  AGES 6-9" if level == 1 else "LEVEL 2  ·  AGES 10+"
    w = stringWidth(txt, d.FM, 8) + 20
    c.setFillColor(d.T if level == 1 else GTINT); c.setStrokeColor(d.P if level == 1 else GREEN); c.setLineWidth(0.9)
    c.roundRect(R - w, PH - M - 18, w, 18, 9, fill=1, stroke=1)
    c.setFillColor(d.D); c.setFont(d.FM, 8); c.drawCentredString(R - w / 2, PH - M - 12.5, txt)
    if level == 1: snowflake(R - w - 14, PH - M - 9, 7)
    else:
        for k in (-8, 0, 8): snowflake(R - w - 30 + k * 1.8, PH - M - 9, 5)


def cutline(x0, y0, x1, y1):
    c.setStrokeColor(d.MUT); c.setLineWidth(0.6); c.setDash(4, 3); c.line(x0, y0, x1, y1); c.setDash()


# ================================================================== 1 cover
d.cover(["Christmas", "Escape Room"],
        "The Bell Vault: one story, two levels (ages 6-9 and 10+). No phone or internet needed.",
        pages=16, kicker="PRINTABLE ESCAPE GAME")

# ================================================================== 2 game master guide
d.start("Game Master Guide", "Everything you need to run a 45-minute Christmas escape game at home, in a classroom or at a party.", kicker="Read this first")
y = d.y
colw = (R - L - 16) / 2
card(L, y, colw, 280, "How the game works")
yy = para(L + 12, y - 34, "Juniper the elf locked the sleigh bells in the Bell Vault and forgot the 4-digit code. Players solve 4 clues. Each clue gives one digit. The 4 digits, in order, open the vault.", colw - 24, 10)
yy = para(L + 12, yy - 4, "Two levels, one story. Every clue comes in Level 1 (ages 6-9: counting, pictures, simple codes) and Level 2 (ages 10+: shift cipher, symbol math, a maze, a logic grid). Both levels of a clue lead to the SAME digit, so brothers, sisters and cousins of different ages play together and can check each other.", colw - 24, 10)
yy = para(L + 12, yy - 4, "Players: 1 to 12, in teams of 2 to 4. Time: about 45 minutes.", colw - 24, 10, font=d.FM)
x2 = L + colw + 16
card(x2, y, colw, 280, "What you need")
items = ["This PDF, printed (Letter or A4)", "Pencils and a few crayons", "Scissors and tape", "5 envelopes per team (or folded paper)", "A timer or clock", "No phone, app, QR code or internet"]
yy = y - 36
for it in items:
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(x2 + 12, yy - 10, 10, 10, 2, fill=0, stroke=1)
    yy = para(x2 + 30, yy + 1, it, colw - 44, 9.8) - 3
yy = para(x2 + 12, yy - 6, "Printing: ink-light pages (white paper, thin lines). Every puzzle works in black and white. On A4, choose \"Fit to page\".", colw - 24, 9.2, color=d.MUT)
yy = para(x2 + 12, yy - 6, "Play it again: the other level makes a new game, so a team that played Level 1 this year can try Level 2 next time.", colw - 24, 9.2, color=d.MUT)
yy = para(x2 + 12, yy - 6, "Big group? Print one set of clue sheets and lock tags per team and race to the vault.", colw - 24, 9.2, color=d.MUT)
y -= 280 + 14
card(L, y, R - L, y - BOTTOM + 6, "Set up in 10 minutes")
steps = [
    "Print pages 3 to 14 and 16. Each team gets the clue sheets for its level (Level 1 or Level 2). Mixed-age team? Give it both.",
    "Make one set of 5 envelopes per team. Cut out the lock tags (page 13, one page per team) and tape one on each envelope: Clue 1, Clue 2, Clue 3, Clue 4 and the Vault.",
    "Put each clue's sheets in its envelope, and the Vault sheet (page 12) in the Clue 1 envelope so teams record digits as they go. The certificates (page 16) go in the Vault envelope.",
    "Cut out the hint cards (page 14) and keep them with the Answer Key (page 15). Players never see page 15.",
    "Read the mission letter (page 3) out loud, start the 45-minute timer and hand out the Clue 1 envelope.",
    "When a team finds a digit, they write it on the next envelope's lock tag and show you. Check it on the Answer Key. Right? They open that envelope. Not yet? They keep trying or ask for a hint.",
    "Each team may ask for 3 hint cards. When the 4-digit vault code is right, read the victory note on page 15 and let the team open the Vault envelope: their certificates are inside.",
]
d.y = y - 36
d.bullets(steps, size=9.9, numbered=True, gap=6)
d.end()

# ================================================================== 3 mission letter
d.start("The Bell Vault", "Read this letter out loud to start the game.", kicker="Your mission", centered=True)
y = d.y
h = 268
c.setFillColor(GOLDT); c.setStrokeColor(GOLD); c.setLineWidth(1.2)
c.roundRect(L + 10, y - h, R - L - 20, h, 12, fill=1, stroke=1)
for sx, sy in ((L + 34, y - 26), (R - 34, y - 26), (L + 34, y - h + 26), (R - 34, y - h + 26)): snowflake(sx, sy, 9, GOLD, 1)
letter = [
    "Dear Workshop Helpers,",
    "It is Christmas Eve and I have made a terrible mistake. I locked the sleigh bells in the Bell Vault to keep them safe... and now I cannot remember the code! Without the bells, the sleigh cannot fly tonight.",
    "I am a careful elf, so I hid 4 clues around the workshop. Each clue gives one digit of the code. Solve all 4, put the digits in order and the vault will open.",
    "Please hurry. The sleigh leaves in 45 minutes!",
    "Your friend, Juniper (the youngest elf in the workshop)",
]
yy = y - 40
for i, t in enumerate(letter):
    f = d.SB if i in (0, 4) else d.SS
    yy = para(L + 46, yy, t, R - L - 92, 12.5, font=f, color=d.D, lead=1.42) - 8
y -= h + 14
card(L, y, R - L, 160, "Your team")
rows = [("Team name", None), ("Players", None), ("Level (circle):", "LEVEL 1   or   LEVEL 2   or   BOTH"), ("Start time", "Escape time")]
yy = y - 48
for lab, extra in rows:
    c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawString(L + 16, yy, lab)
    if lab == "Start time":
        c.setStrokeColor(d.HAIR); c.line(L + 90, yy - 2, L + 230, yy - 2)
        c.drawString(L + 260, yy, "Escape time"); c.line(L + 330, yy - 2, R - 16, yy - 2)
    elif extra:
        c.setFillColor(d.INK); c.setFont(d.F, 10); c.drawString(L + 120, yy, extra)
    else:
        c.setStrokeColor(d.HAIR); c.setLineWidth(0.7); c.line(L + 90, yy - 2, R - 16, yy - 2)
    yy -= 31
y -= 160 + 12
card(L, y, R - L, y - BOTTOM, "Vault code tracker: write each digit as you find it")
bw = 64; gap = (R - L - 4 * bw) / 5
for i in range(4):
    bx = L + gap + i * (bw + gap); by = BOTTOM + 22
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(bx, by, bw, 50, 8, fill=1, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.FM, 8); c.drawCentredString(bx + bw / 2, by - 12, f"CLUE {i + 1}")
d.end()

# ================================================================== 4 clue 1 level 1
d.start("The Gift Tag Code", "Juniper wrote the first digit on a gift tag in her secret number code. Each number stands for one letter.", kicker="Clue 1", centered=True)
level_tab(1)
y = d.y
card(L, y, R - L, 112, "The code key: A is 1, B is 2, C is 3...")
cw = (R - L - 24) / 13
for row in range(2):
    for i in range(13):
        n = row * 13 + i; x = L + 12 + i * cw; yy = y - 34 - row * 38
        c.setFillColor(d.T if row == 0 else GTINT); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6)
        c.rect(x, yy - 32, cw, 32, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.S, 13); c.drawCentredString(x + cw / 2, yy - 16, chr(65 + n))
        c.setFillColor(d.INK); c.setFont(d.F, 8.5); c.drawCentredString(x + cw / 2, yy - 28, str(n + 1))
y -= 128


def tag_row(y, nums, h=92, title=None):
    w = R - L - 40
    tag(L + 20, y - h, w, h, fill=white)
    if title:
        c.setFillColor(d.MUT); c.setFont(d.FM, 8.5); c.drawString(L + 70, y - 18, title)
    n = len(nums); bw = 52; gap = 12; tot = n * bw + (n - 1) * gap; x0 = L + 20 + (w - tot) / 2 + 20
    for i, v in enumerate(nums):
        x = x0 + i * (bw + gap)
        c.setFillColor(d.D); c.setFont(d.S, 20); c.drawCentredString(x + bw / 2, y - 42, str(v))
        c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1); c.roundRect(x, y - h + 10, bw, 34, 5, fill=1, stroke=1)
    return y - h


c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(L, y - 12, "Warm up: decode this tag first")
y = tag_row(y - 22, pz.a1z26(pz.A1_WARMUP), title="WRITE A LETTER IN EACH BOX")
y -= 22
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(L, y - 12, "Juniper's secret tag")
y = tag_row(y - 22, pz.a1z26(pz.A1Z26_MSG), h=100, title="THE SECRET WORD IS A NUMBER")
y -= 22
y = answer_box(y, "The first digit is")
y -= 28
c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(L, y - 10, "Bonus fun: write your own name in Juniper's code")
c.setStrokeColor(d.HAIR); c.setLineWidth(0.7)
yy = y - 40
while yy > BOTTOM + 8:
    c.line(L, yy, R, yy); yy -= 28
d.end()

# ================================================================== 5 clue 1 level 2
d.start("The Scrambled Note", "Juniper hid the first digit in a shift code: every letter moved the same number of steps along the alphabet.", kicker="Clue 1", centered=True)
level_tab(2)
y = d.y
h = 196
card(L, y, R - L, h, fill=GOLDT, stroke=GOLD)
c.setFillColor(d.MUT); c.setFont(d.FM, 8.5); c.drawString(L + 16, y - 20, "THE NOTE FOUND UNDER THE WORKBENCH")
words = pz.C1_CIPHER.split(" ")
lines_ = [words[:2], words[2:]]
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
d.text("1.  You know the note is from Juniper, so the signature MXQLSHU must spell JUNIPER. Count how many steps J moved to become M.", 10.2)
d.text("2.  Every letter in the note moved by that same number. Move each letter BACK that many steps (after A, go round to Z).", 10.2)
d.text("3.  Use the shift strip below: write the real letter under each code letter, then read the note.", 10.2)
y = d.y - 4
card(L, y, R - L, 92, "Shift strip")
cw = (R - L - 24) / 26
for i in range(26):
    x = L + 12 + i * cw
    c.setFillColor(d.T); c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.rect(x, y - 56, cw, 26, fill=1, stroke=1)
    c.setFillColor(d.D); c.setFont(d.FM, 10); c.drawCentredString(x + cw / 2, y - 47, chr(65 + i))
    c.setFillColor(white); c.rect(x, y - 82, cw, 26, fill=1, stroke=1)
c.setFillColor(d.MUT); c.setFont(d.F, 7.5); c.drawString(L + 12, y - 90 + 0.5, "")
y -= 92 + 22
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
d.start("Count the Workshop Shelf", "Juniper says: count everything on my shelf, then do my sum to find the second digit.", kicker="Clue 2", centered=True)
level_tab(1)
y = d.y
gh = 300
card(L, y, R - L, gh, fill=white, stroke=d.P)
cols, rows = pz.SCENE_COLS, pz.SCENE_ROWS
cw = (R - L - 30) / cols; ch_ = (gh - 24) / rows
rnd = random.Random(3)
for r in range(rows):
    sy = y - 12 - (r + 1) * ch_ + 8
    c.setFillColor(HexColor("#EADCC8")); c.setStrokeColor(HexColor("#B9A07E")); c.setLineWidth(0.7)
    c.rect(L + 14, sy - 6, R - L - 28, 6, fill=1, stroke=1)
for kind, (cx, cy) in pz.l1_scene():
    x = L + 15 + cx * cw + cw / 2 + rnd.uniform(-8, 8); yb = y - 12 - (cy + 1) * ch_ + 8
    ICON[kind](x, yb, 46)
y -= gh + 16
bw = (R - L - 40) / 3
for i, k in enumerate(("tree", "gift", "star")):
    x = L + i * (bw + 20)
    card(x, y, bw, 86)
    ICON[k](x + 34, y - 66, 42)
    c.setFillColor(d.D); c.setFont(d.SB, 12); c.drawString(x + 66, y - 32, {"tree": "Trees", "gift": "Gifts", "star": "Stars"}[k])
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.1); c.roundRect(x + 66, y - 74, 44, 34, 6, fill=1, stroke=1)
y -= 86 + 16
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawCentredString(PW / 2, y - 12, "Juniper's sum")
y -= 26
seq = [("box", "trees"), ("op", "+"), ("box", "gifts"), ("op", "-"), ("box", "stars"), ("op", "="), ("ans", "")]
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
d.start("Workshop Symbol Sums", "Each picture stands for a different whole number. Work out all three, then solve Juniper's last line.", kicker="Clue 2", centered=True)
level_tab(2)
y = d.y


def eq_row(y, syms, ops, result, h=64, ask=False):
    card(L, y, R - L, h, fill=GOLDT if ask else white, stroke=GOLD if ask else d.HAIR)
    n = len(syms); x = L + 40
    for i, s in enumerate(syms):
        ICON[s](x + 22, y - h + 16, 42); x += 54
        if i < n - 1:
            c.setFillColor(d.D); c.setFont(d.S, 24); c.drawCentredString(x + 10, y - h / 2 - 8, ops[i]); x += 26
    c.setFillColor(d.D); c.setFont(d.S, 24); c.drawCentredString(x + 14, y - h / 2 - 8, "=")
    if ask:
        c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.4); c.roundRect(x + 38, y - h + 12, 54, h - 24, 8, fill=1, stroke=1)
        c.setFillColor(d.MUT); c.setFont(d.F, 8.5); c.drawString(x + 100, y - h / 2 - 3, "digit 2")
    else:
        c.setFont(d.S, 26); c.drawString(x + 38, y - h / 2 - 9, str(result))
    return y - h


ops_map = {"+": "+", "x": "×"}
for i, (syms, op, tot) in enumerate(pz.L2_EQS):
    c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L, y - 9, f"LINE {i + 1}")
    y = eq_row(y - 14, syms, [ops_map[op]] * (len(syms) - 1), tot) - 12
c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawString(L, y - 9, "JUNIPER'S LAST LINE")
y = eq_row(y - 14, ["tree", "star", "gift"], ["+", "-"], None, h=76, ask=True) - 14
vh = y - BOTTOM
card(L, y, R - L, vh, "Write what each picture is worth")
bw = (R - L - 60) / 3
cyv = y - 24 - (vh - 24) / 2
for i, k in enumerate(("tree", "gift", "star")):
    x = L + 20 + i * (bw + 10)
    ICON[k](x + 26, cyv - 26, 54)
    c.setFillColor(d.D); c.setFont(d.S, 22); c.drawString(x + 62, cyv - 8, "=")
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.1); c.roundRect(x + 84, cyv - 28, 56, 50, 6, fill=1, stroke=1)
d.end()

# ================================================================== 8 clue 3 level 1
d.start("The Tangled Lights", "The workshop lights are all tangled up! Follow the strand from the STAR plug to find which bulb it lights.", kicker="Clue 3", centered=True)
level_tab(1)
y = d.y
top, bot = y - 70, BOTTOM + 170
xs = [L + 70 + i * (R - L - 140) / 3 for i in range(4)]
for i, p in enumerate(pz.PLUGS):
    x = xs[i]
    c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x - 26, top + 6, 52, 52, 8, fill=1, stroke=1)
    ICON[p](x, top + 14, 34)
    c.setFillColor(d.D); c.rect(x - 5, top - 4, 10, 10, fill=1, stroke=0)
# strands: each row of waypoints is a permutation of the 4 columns, so strands never share a
# point and every crossing happens mid-curve at a clear angle (verified: rows are permutations)
ROWS = {"star": [2, 1, 3], "tree": [0, 3, 2], "gift": [3, 0, 1], "bell": [1, 2, 0]}
JIT = {"star": 14, "tree": -10, "gift": 8, "bell": -16}
for k in range(3): assert sorted(v[k] for v in ROWS.values()) == [0, 1, 2, 3]
for p, bi in pz.STRANDS.items():
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
for i, v in enumerate(pz.BULBS):
    bulb(xs[i], bot + 8, 70, v)
y = bot - 76
para_c(y + 8, "Trace it with your finger or a crayon. The number on that bulb is the third digit.", R - L, 10, color=d.MUT)
answer_box(y - 14, "The third digit is")
d.end()

# ================================================================== 9 clue 3 level 2
d.start("The Bell Maze", "Find the only path from the Workshop door to the Sleigh. Count the bells ON your path; bells in dead ends do not count.", kicker="Clue 3", centered=True)
level_tab(2)
walls, D, path, on, off = pz.bells()
y = d.y - 6
cell = min((R - L - 20) / pz.MAZE_W, (y - BOTTOM - 84) / pz.MAZE_H)
mw, mh = cell * pz.MAZE_W, cell * pz.MAZE_H
mx = (PW - mw) / 2; my = y - 14
MAZE_GEOM = (mx, my, cell)
c.setFillColor(white); c.setStrokeColor(d.D)
for (cx, cy) in on + off:
    bell(mx + cx * cell + cell / 2, my - cy * cell - cell * 0.84, cell * 0.66)
c.setStrokeColor(d.D); c.setLineWidth(2); c.setLineCap(1)
for (cx, cy), ws in walls.items():
    x0, y0 = mx + cx * cell, my - cy * cell
    if "N" in ws and not (cx, cy) == (0, 0): c.line(x0, y0, x0 + cell, y0)
    if "W" in ws: c.line(x0, y0, x0, y0 - cell)
    if cy == pz.MAZE_H - 1 and "S" in ws and (cx, cy) != (pz.MAZE_W - 1, pz.MAZE_H - 1): c.line(x0, y0 - cell, x0 + cell, y0 - cell)
    if cx == pz.MAZE_W - 1 and "E" in ws: c.line(x0 + cell, y0, x0 + cell, y0 - cell)
c.setLineCap(0)
c.setFillColor(d.P); c.setFont(d.FM, 8.5)
c.drawString(mx, my + 5, "START: WORKSHOP DOOR")
c.drawRightString(mx + mw, my - mh - 13, "FINISH: THE SLEIGH")
answer_box(my - mh - 26, "The third digit is")
d.end()

# ================================================================== 10 clue 4 level 1
d.start("Snowflake Sudoku", "Fill the grid so every row, every column and every thick-lined box has 1, 2, 3 and 4 once each.", kicker="Clue 4", centered=True)
level_tab(1)
y = d.y - 6
gsz = 372; cs = gsz / 4; gx = (PW - gsz) / 2
for r in range(4):
    for col in range(4):
        x, yy = gx + col * cs, y - (r + 1) * cs
        star_cell = (r, col) == pz.SUDOKU_STAR
        c.setFillColor(GOLDT if star_cell else (d.T if pz.SUDOKU_GIVEN[r][col] else white)); c.setStrokeColor(d.HAIR); c.setLineWidth(0.8)
        c.rect(x, yy, cs, cs, fill=1, stroke=1)
        v = pz.SUDOKU_GIVEN[r][col]
        if v:
            c.setFillColor(d.D); c.setFont(d.S, 40); c.drawCentredString(x + cs / 2, yy + cs / 2 - 14, str(v))
        if star_cell:
            snowflake(x + cs - 16, yy + cs - 16, 11, GOLD, 1.3)
c.setStrokeColor(d.D); c.setLineWidth(2.6)
c.rect(gx, y - gsz, gsz, gsz, fill=0, stroke=1)
c.line(gx + gsz / 2, y, gx + gsz / 2, y - gsz); c.line(gx, y - gsz / 2, gx + gsz, y - gsz / 2)
y -= gsz + 20
card(L, y, R - L, 84, "How to play")
para(L + 14, y - 34, "Start with a row or box that already has 3 numbers: the missing one is easy to spot. Write in pencil so you can rub out. When the grid is full, look at the square with the gold snowflake: that number is the fourth digit.", R - L - 28, 9.8)
y -= 84 + 18
answer_box(y, "The fourth digit is")
d.end()

# ================================================================== 11 clue 4 level 2
d.start("The Elf Workbench Puzzle", "Four elves work at benches 1 to 4. Each makes one toy. Use the clues to find which bench builds the trains.", kicker="Clue 4", centered=True)
level_tab(2)
y = d.y
card(L, y, R - L, 140, "Juniper's clues")
yy = y - 34
for i, t in enumerate(pz.LOGIC_CLUES):
    c.setFillColor(d.T); c.circle(L + 24, yy - 4, 8, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 8.5); c.drawCentredString(L + 24, yy - 7, str(i + 1))
    para(L + 40, yy + 6, t, R - L - 60, 10.2); yy -= 20
y -= 156
# logic grid
benches = ["Bench 1", "Bench 2", "Bench 3", "Bench 4"]
toys = ["Drums", "Kites", "Trains", "Yo-yos"]
cs = 33; lab_w = 80; head_h = 66
gx = (PW - (lab_w + 8 * cs)) / 2 + lab_w
gy = y - head_h
c.setFillColor(d.D); c.setFont(d.FM, 8.5)
for i, t in enumerate(benches + toys):
    c.saveState(); c.translate(gx + i * cs + cs / 2 + 3, gy + 6); c.rotate(60); c.drawString(0, 0, t); c.restoreState()
for i, t in enumerate(pz.ELVES + toys):
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
y = gy - 8 * cs - 22
answer_box(y, "Trains: bench number")
d.end()

# ================================================================== 12 the vault
d.start("Open the Bell Vault", "Write the 4 digits in order. Show the Game Master. If the code is right, the vault swings open!", kicker="The final lock", centered=True)
y = d.y - 4
r = 168; cx, cy = PW / 2, y - r - 6
c.setFillColor(HexColor("#EFEAE3")); c.setStrokeColor(d.D); c.setLineWidth(2.2); c.circle(cx, cy, r, fill=1, stroke=1)
c.setFillColor(white); c.setLineWidth(1.2); c.circle(cx, cy, r - 18, fill=1, stroke=1)
for i in range(12):
    a = i * math.pi / 6
    c.setFillColor(d.D); c.circle(cx + (r - 9) * math.cos(a), cy + (r - 9) * math.sin(a), 3, fill=1, stroke=0)
c.setFillColor(GOLDT); c.setStrokeColor(GOLD); c.circle(cx, cy + 58, 30, fill=1, stroke=1)
bell(cx, cy + 40, 34)
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
          "Code right? Open the Vault envelope together: your Escape Expert certificates are inside. Write your escape time on page 3!"]
d.y = y - 34
d.bullets(checks, size=10.5, check=True, gap=9)
d.end()

# ================================================================== 13 lock tags
d.start("Envelope Lock Tags", "Cut out and tape one tag to each envelope. A team writes its digit on the tag and shows the Game Master to unlock it.", kicker="Game Master: cut out", centered=True)
y = d.y
tw = (R - L - 18) / 2; th = (y - BOTTOM - 24) / 3
tags = [("Clue 1", "Open me first!", 0, "The Gift Tag Code / The Scrambled Note"),
        ("Clue 2", "Locked: write the digit from Clue 1", 1, "Count the Workshop Shelf / Symbol Sums"),
        ("Clue 3", "Locked: write the digit from Clue 2", 1, "The Tangled Lights / The Bell Maze"),
        ("Clue 4", "Locked: write the digit from Clue 3", 1, "Snowflake Sudoku / Elf Workbench Puzzle"),
        ("The Bell Vault", "Locked: write the 4-digit vault code", 4, "Inside: Escape Expert certificates (page 16)"),
        ("Game Master", "Hint cards + answer key", 0, "Players: do not open")]
for i, (t, sub, boxes, inside) in enumerate(tags):
    col, row = i % 2, i // 2
    x = L + col * (tw + 18); yy = y - row * (th + 12)
    c.setStrokeColor(d.P if i < 5 else GREEN); c.setLineWidth(1.3); c.setFillColor(white)
    c.setDash(5, 3); c.roundRect(x, yy - th, tw, th, 10, fill=1, stroke=1); c.setDash()
    padlock(x + 34, yy - 62, 40)
    c.setFillColor(d.D); c.setFont(d.S, 19); c.drawString(x + 66, yy - 38, t)
    c.setFillColor(d.INK); para(x + 66, yy - 46, sub, tw - 80, 9.4)
    if boxes == 1:
        c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x + tw / 2 - 26, yy - th + 34, 52, 52, 8, fill=1, stroke=1)
    elif boxes:
        for k in range(boxes):
            c.setFillColor(white); c.setStrokeColor(d.D); c.setLineWidth(1.2); c.roundRect(x + tw / 2 - 98 + k * 50, yy - th + 38, 44, 48, 7, fill=1, stroke=1)
    c.setFillColor(d.MUT); c.setFont(d.F, 8); c.drawCentredString(x + tw / 2, yy - th + 16, inside)
d.end()

# ================================================================== 14 hint cards
d.start("Hint Cards", "Game Master: cut out and hand over one hint at a time (3 per team). Fold each card so Hint 2 stays hidden until it is needed.", kicker="Game Master only", centered=True)
HINTS = [
    ("Clue 1 · Level 1", "Find 19 in the code key. Which letter is above it?", "The secret word is a number word with 5 letters."),
    ("Clue 1 · Level 2", "J to M is 3 steps forward. So go 3 steps BACK for every letter.", "W goes back to T, K to H, H to E: the first word is THE."),
    ("Clue 2 · Level 1", "Count one kind of picture at a time, and dot each one.", "There are more stars than trees. Did you take the stars away last?"),
    ("Clue 2 · Level 2", "Line 1 has three of the same picture. Divide 15 by 3.", "Once you know the tree, line 2 gives the gift, then line 3 gives the star."),
    ("Clue 3 · Level 1", "Put a crayon on the star plug and never lift it off the strand.", "The star strand crosses the others. Stay on the same line at every crossing."),
    ("Clue 3 · Level 2", "Mazes are easier from the end: try starting at the sleigh.", "Shade dead ends as you find them. Only bells on the open path count."),
    ("Clue 4 · Level 1", "Row 2 already has 1 and 2. Which two numbers are missing?", "The snowflake square's row has 2 and 3, and its column has 1."),
    ("Clue 4 · Level 2", "Clues 1 and 3 together tell you where Holly sits.", "Pip makes kites or trains, but trains must sit next to Juniper."),
]
y = d.y
cw2 = (R - L - 14) / 2; chh = (y - BOTTOM - 3 * 10) / 4
for i, (t, h1, h2) in enumerate(HINTS):
    col, row = i % 2, i // 2
    x = L + col * (cw2 + 14); yy = y - row * (chh + 10)
    c.setStrokeColor(d.P if "Level 1" in t else GREEN); c.setLineWidth(1.1); c.setFillColor(white)
    c.setDash(5, 3); c.roundRect(x, yy - chh, cw2, chh, 8, fill=1, stroke=1); c.setDash()
    c.setFillColor(d.T if "Level 1" in t else GTINT); c.roundRect(x + 1, yy - 22, cw2 - 2, 21, 7, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.FM, 8.5); c.drawString(x + 10, yy - 15, t.upper())
    mid = yy - 22 - (chh - 22) / 2
    c.setFillColor(d.P); c.setFont(d.FM, 7.5); c.drawString(x + 10, yy - 36, "HINT 1")
    para(x + 10, yy - 40, h1, cw2 - 20, 9.2)
    cutline(x + 8, mid, x + cw2 - 8, mid)
    c.setFillColor(d.MUT); c.setFont(d.F, 6.5); c.drawRightString(x + cw2 - 10, mid + 3, "fold here")
    c.setFillColor(d.P); c.setFont(d.FM, 7.5); c.drawString(x + 10, mid - 14, "HINT 2")
    para(x + 10, mid - 18, h2, cw2 - 20, 9.2)
d.end()

# ================================================================== 15 answer key
d.start("Answer Key", "Game Master only: keep this page hidden from players.", kicker="Game Master only")
sol_e, sol_t = pz.verify()[1]
rows = [
    ("1", "5 12 6 = ELF; 19 5 22 5 14 = SEVEN", "Signature MXQLSHU = JUNIPER (shift 3). Note reads THE FIRST DIGIT IS SEVEN", "7"),
    ("2", "4 trees + 5 gifts - 6 stars = 3", "Tree 5, gift 4, star 2, so 5 + 2 - 4 = 3", "3"),
    ("3", "The star plug's strand ends at bulb 9", "The one path from door to sleigh passes 9 bells (see map)", "9"),
    ("4", "The gold snowflake square is 4", "Bench 1 Pip kites, 2 Holly drums, 3 Juniper yo-yos, 4 Sprout trains", "4"),
]
d.table(["Clue", "Level 1 (ages 6-9)", "Level 2 (ages 10+)", "Digit"], [0.6, 3.4, 4.2, 0.8], rows, size=9.4, rowh=24)
y = d.y
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1.3); c.roundRect(L, y - 40, R - L, 40, 8, fill=1, stroke=1)
c.setFillColor(d.D); c.setFont(d.SB, 15); c.drawString(L + 16, y - 26, "Vault code:")
c.setFont(d.S, 22); c.drawString(L + 110, y - 28, "  ".join(map(str, pz.CODE)))
c.setFillColor(d.INK); c.setFont(d.F, 9.5); c.drawRightString(R - 16, y - 25, "Both levels give the same 4 digits.")
y -= 56
# sudoku solution + maze solution side by side
c.setFillColor(d.D); c.setFont(d.SB, 11.5); c.drawString(L, y - 10, "Sudoku solution"); c.drawString(L + 190, y - 10, "Maze solution path")
y -= 20
s_cs = 34; sx = L
for r in range(4):
    for col in range(4):
        x, yy = sx + col * s_cs, y - (r + 1) * s_cs
        c.setFillColor(GOLDT if (r, col) == pz.SUDOKU_STAR else white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.rect(x, yy, s_cs, s_cs, fill=1, stroke=1)
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
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 12, "Gold dots = the 9")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 24, "bells on the path.")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 36, "Bells in dead ends")
c.drawString(mx2 + pz.MAZE_W * mc + 10, my2 - 48, "do not count.")
yv = y - 4 * s_cs - 22
c.setFillColor(d.D); c.setFont(d.SB, 11.5); c.drawString(L, yv - 10, "Read aloud when")
c.drawString(L, yv - 25, "the vault opens:")
para(L, yv - 34, "\"The vault door creaks open and there they are: the sleigh bells, shining and ringing! Juniper hugs every one of you. Thanks to your team, the sleigh flies tonight. You are official Workshop Escape Experts!\"", 170, 9.6, font=d.SS, color=d.D)
d.end()

# ================================================================== 16 certificates
d.start("Escape Expert Certificates", None, kicker="Two per page: print one for every player", centered=True)
y = d.y + 6
ch2 = (y - BOTTOM - 14) / 2
for i in range(2):
    yy = y - i * (ch2 + 14)
    c.setFillColor(white); c.setStrokeColor(GOLD); c.setLineWidth(2); c.roundRect(L, yy - ch2, R - L, ch2, 12, fill=1, stroke=1)
    c.setStrokeColor(d.P); c.setLineWidth(0.7); c.roundRect(L + 7, yy - ch2 + 7, R - L - 14, ch2 - 14, 9, fill=0, stroke=1)
    bell(L + 46, yy - 70, 44); bell(R - 46, yy - 70, 44)
    d._spaced(PW / 2, yy - 38, "THE BELL VAULT", 9, d.P, d.FM)
    c.setFillColor(d.D); c.setFont(d.S, 26); c.drawCentredString(PW / 2, yy - 72, "Certified Escape Expert")
    c.setFillColor(d.INK); c.setFont(d.SS, 12); c.drawCentredString(PW / 2, yy - 96, "This certifies that")
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.line(L + 90, yy - 128, R - 90, yy - 128)
    c.setFont(d.SS, 11.5); c.setFillColor(d.INK)
    c.drawCentredString(PW / 2, yy - 150, "opened the Bell Vault and saved Christmas Eve.")
    c.setFont(d.FM, 9); c.setFillColor(d.MUT)
    c.drawString(L + 40, yy - ch2 + 48, "LEVEL"); c.line(L + 80, yy - ch2 + 46, L + 170, yy - ch2 + 46)
    c.drawString(L + 190, yy - ch2 + 48, "ESCAPE TIME"); c.line(L + 262, yy - ch2 + 46, L + 330, yy - ch2 + 46)
    c.drawString(L + 350, yy - ch2 + 48, "DATE"); c.line(L + 382, yy - ch2 + 46, R - 40, yy - ch2 + 46)
    c.setFont(d.SS, 10.5); c.setFillColor(d.D); c.drawCentredString(PW / 2, yy - ch2 + 22, "Signed: Juniper, Keeper of the Bells")
d.end()

# ================================================================== 17 thank-you (spec text verbatim)
c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
c.setStrokeColor(d.P); c.setLineWidth(1.3); c.rect(22, 22, PW - 44, PH - 44, fill=0, stroke=1)
c.setStrokeColor(d.A); c.setLineWidth(0.6); c.rect(28, 28, PW - 56, PH - 56, fill=0, stroke=1)
bell(PW / 2, PH - 200, 70)
c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 262, "You just made my day!")
d._ornament(PW / 2, PH - 286)
y = PH - 316
y = para_c(y, "Thank you for choosing a small, one-person shop over the big guys.", 420, 13, font=d.SS, lead=1.5) - 16
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 460, 13, font=d.SS, lead=1.5) - 22
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(PW / 2 - 200, y - 50, 400, 50, 12, fill=1, stroke=1)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
parts = "How: Etsy app → You → Purchases → Leave a review".split("→")
widths = [stringWidth(p, d.FM, 12.5) for p in parts]; aw = stringWidth("→", "DejaVu", 12.5)
x = PW / 2 - (sum(widths) + aw * (len(parts) - 1)) / 2
c.setFillColor(d.D)
for i, p in enumerate(parts):
    c.setFont(d.FM, 12.5); c.drawString(x, y - 30, p); x += widths[i]
    if i < len(parts) - 1:
        c.setFont("DejaVu", 12.5); c.drawString(x, y - 30, "→"); x += aw
y -= 50 + 28
y = para_c(y, "Something not right? Message me first and I'll fix it fast.", 420, 13, font=d.SS, lead=1.5) - 40
c.setFillColor(d.P); c.setFont(d.SB, 14); c.drawCentredString(PW / 2, y - 6, "With thanks,")
c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 30, "GM's Digital Creations")
for sx in (PW / 2 - 150, PW / 2 + 150): snowflake(sx, PH - 170, 12, d.A, 1)
c.showPage()
d.save()
print("built", OUT)
