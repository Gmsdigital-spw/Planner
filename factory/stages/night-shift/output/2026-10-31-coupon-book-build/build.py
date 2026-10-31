"""Christmas Coupon Book (prod-xmas-coupon-book), rework Oct 31, 2026 (fix list of the Oct 30 FAIL 82).
python3 build.py -> raw.pdf; python3 /home/claude/planner/tools/acro_font.py raw.pdf christmas-coupon-book.pdf; python3 check.py"""
import sys, os
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from reportlab.lib.colors import HexColor, white, Color
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = HERE + "/raw.pdf"
PAL = gs.palette("cranberry")
PW, PH, M = gs.PW, gs.PH, gs.MARGIN
d = gs.Book(RAW, "Christmas Coupon Book", PAL, cover_style="frame", page_frame="rule")
c = d.c
PAD = 18                       # 0.25 in inside every box
CW = 460                       # coupon width (6.4 in), centred: wide enough for 20+ ALL CAPS letters in FOR and FROM
CX = (PW - CW) / 2
TOP = PH - M - 52              # below the page title band
BOT = M + 20                   # 0.25 in+ above the kit footer rule (M - 1), checked by check.py
BOXES, FIELDS = [], []
registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

PARTNER = [
    ("Breakfast in Bed", "One slow morning: coffee or tea, something warm from the oven, and you stay put."),
    ("Movie Night, Your Pick", "Your film, your snacks, my phone in a drawer. No complaining from me."),
    ("One Long Back Rub", "Twenty minutes, no rushing, your choice of music."),
    ("Date Night Planned by Me", "I plan it, book it and drive. You just get ready and show up."),
    ("A Night Off Dishes", "Every pot, plate and pan is mine tonight."),
    ("You Win One Argument", "Hand this over and the debate ends in your favor. One use only."),
    ("Sleep In Pass", "I take the early shift. You stay under the blankets until you are ready."),
    ("A Handwritten Love Letter", "A real letter on paper, saying the things I don't say enough."),
    ("Cocoa and Christmas Lights", "Two mugs to go, warm coats, and a drive past the best lit streets."),
    ("Your Favorite Dinner", "Name the dish. I shop, cook and set the table."),
]
KIDS = [
    ("Stay Up 30 Minutes Late", "One night, half an hour extra, no questions asked."),
    ("Pick Tonight's Dinner", "Pizza, pancakes or tacos: you choose and we all eat it."),
    ("Skip One Chore", "Hand this in and one chore is done for you today."),
    ("Build a Blanket Fort", "Every pillow in the house is fair game. We can sleep in it too."),
    ("Bake Cookies Together", "You crack the eggs, pick the sprinkles and lick the spoon."),
    ("Boss for a Day", "You plan the day's fun (within reason). The grown-ups follow."),
    ("One Extra Bedtime Story", "Any book you like, with all the funny voices."),
    ("Pajama Day", "Pajamas from morning to night, even at lunch."),
    ("Ice Cream for Breakfast", "One scoop, one morning, our little secret."),
    ("Park Trip, Just Us Two", "Swings, slides and snacks: one-on-one time with me."),
]
FAMILY = [
    ("Family Game Night", "Phones away, board games out. The loser makes the popcorn."),
    ("One Free Car Wash", "Inside and out, vacuum included."),
    ("Sunday Dinner on Me", "I cook, you sit and relax. Dessert included."),
    ("Help with Any Project", "Painting, moving or sorting the garage: one afternoon of my time."),
    ("A Long Phone Call", "One call with no hurry to hang up. Tell me everything."),
    ("Lights Up and Down", "Ladder, hooks and tangles handled by me, in December and in January."),
    ("Movie Marathon Day", "Three films, warm blankets and all the snacks."),
    ("A Walk Together", "An hour outside, any weather, just the two of us."),
    ("Breakfast Out, My Treat", "Your favorite spot, my bill."),
    ("Family Photo Day", "Let's finally take the family photo you keep asking for."),
]
SETS = [("Partner", "For My Love", PARTNER), ("Kids", "For My Little Elf", KIDS), ("Family", "For the Family", FAMILY)]
assert all(len(s[2]) == 10 for s in SETS)
assert len({t for s in SETS for t, _ in s[2]}) == 30, "30 unique coupon titles"


def reg(name, x, yb, w, h, r=8, outer=0):
    """Every box registers itself; check.py sweeps the rendered pixels: no ink within 0.25 in inside it
    (and, when outer > 0, none within `outer` pt outside it)."""
    BOXES.append((d.page, name, x, yb, w, h, r, outer))


def field(name, x, y, w, h=16, size=11, italic=False):
    """Type-in field over a drawn underline (acro_font.py swaps Times for Lora afterwards)."""
    c.setStrokeColor(d.P); c.setLineWidth(0.7); c.line(x, y, x + w, y)
    c.acroForm.textfield(name=name, tooltip=name, x=x, y=y + 1, width=w, height=h, value="",
                         fontName="Times-Italic" if italic else "Times-Roman", fontSize=size,
                         borderWidth=0, fillColor=None, borderColor=None, textColor=d.D,
                         forceBorder=False, fieldFlags="", maxlen=max(8, int((w - 6) / (size * 0.668))))  # caps width
    FIELDS.append(name)


def cutmarks(x, yb, w, h):
    c.setStrokeColor(HexColor("#b9a9a9")); c.setLineWidth(0.5)
    for (px, py) in ((x, yb), (x + w, yb), (x, yb + h), (x + w, yb + h)):
        sx = -1 if px == x else 1; sy = -1 if py == yb else 1
        c.line(px + sx * 4, py, px + sx * 14, py); c.line(px, py + sy * 4, px, py + sy * 14)


def star(x, y, s, col):
    import math
    p = c.beginPath()
    for i in range(10):
        r = s if i % 2 == 0 else s * 0.42; a = math.pi / 2 + i * math.pi / 5
        (p.moveTo if i == 0 else p.lineTo)(x + r * math.cos(a), y + r * math.sin(a))
    p.close(); c.setFillColor(col); c.drawPath(p, fill=1, stroke=0)


def fit(text, font, size, width, minsize=12):
    while stringWidth(text, font, size) > width and size > minsize: size -= 0.5
    assert stringWidth(text, font, size) <= width, (text, size)
    return size


def wrapc(text, font, size, width):
    return gs.wrap(text, font, size, width)


def coupon(n, title, body, setname, yb, h):
    """One coupon: tinted stub on the left (No. + star), title, 2-line note, For/From type-in row."""
    x, w = CX, CW
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1); c.roundRect(x, yb, w, h, 8, fill=1, stroke=1)
    sw = 78
    c.setFillColor(d.T); c.roundRect(x + 1.5, yb + 1.5, sw, h - 3, 7, fill=1, stroke=0)
    c.setDash(2, 3); c.setStrokeColor(d.P); c.setLineWidth(0.8); c.line(x + sw + 2, yb + PAD + 1, x + sw + 2, yb + h - PAD - 1); c.setDash()
    mx = x + sw / 2 + 1
    c.setFillColor(d.P); c.setFont(d.FM, 7.5); c.drawCentredString(mx, yb + h - PAD - 8, "GOOD FOR")
    c.setFillColor(d.D); c.setFont(d.S, 26); c.drawCentredString(mx, yb + h / 2 - 12, f"{n:02d}")
    star(mx, yb + PAD + 6, 6, d.A)
    tx = x + sw + 2 + PAD; tw = w - sw - 2 - 2 * PAD
    ts = fit(title, d.S, 17, tw, 14)
    c.setFillColor(d.D); c.setFont(d.S, ts); c.drawString(tx, yb + h - PAD - ts + 3, title)
    lines = wrapc(body, d.F, 9.4, tw)
    assert len(lines) <= 2, (title, lines)
    yy = yb + h - PAD - ts - 12
    c.setFillColor(d.INK); c.setFont(d.F, 9.4)
    for ln in lines: c.drawString(tx, yy, ln); yy -= 12.5
    fy = yb + PAD + 2
    c.setFillColor(d.MUT); c.setFont(d.FM, 8)
    fw1 = (tw - 22 - 12 - 30) / 2                       # two equal lines, 20+ capitals each at 10 pt
    c.drawString(tx, fy + 2, "FOR"); field(f"{setname} {n:02d} for", tx + 22, fy, fw1, size=10)
    fx = tx + 22 + fw1 + 12
    c.drawString(fx, fy + 2, "FROM"); field(f"{setname} {n:02d} from", fx + 30, fy, tx + tw - fx - 30, size=10)
    reg(f"{setname} coupon {n}", x, yb, w, h)
    cutmarks(x, yb, w, h)


def stack(n, gap=12):
    h = (TOP - BOT - (n - 1) * gap) / n
    return [TOP - (i + 1) * h - i * gap for i in range(n)], h


def page_title(title, kicker):
    d._frame(); d.page += 1
    d._spaced(PW / 2, PH - M - 4, kicker.upper(), 8.5, d.P, d.FM)
    c.setFillColor(d.D); c.setFont(d.S, 24); c.drawCentredString(PW / 2, PH - M - 34, title)


# ------------------------------------------------------------------ 1 PDF cover
COVER_SUB = "30 written coupons for a partner, kids and family, plus 5 blanks to type."
# Fix 1 (Oct 30 FAIL 82): the tile row is placed from the subtitle's real last line, 0.25 in+ below its
# descenders, and the tile numbers sit 0.25 in below each tile's top (both checked on pixels by check.py)
_sub_lines = gs.wrap(COVER_SUB, d.SS, 17, PW - 220)
_title_size = 54
_ty_end = PH * 0.62 - 2 * _title_size * 1.08          # kit frame cover: ty after 2 title lines
_sub_last = _ty_end - 18 - 24 * (len(_sub_lines) - 1)
SUB_DESC = _sub_last - 17 * 0.27                      # lowest descender of the last subtitle line
TILE_H, TILE_W = 66, 106
TILE_TOP = SUB_DESC - PAD - 8
_orig = c.showPage
def _cover_extra():
    yb_t = TILE_TOP - TILE_H
    for i, t in enumerate(["10 for a partner", "10 for kids", "10 for family", "5 blanks to type"]):
        x = PW / 2 + (i - 1.5) * (TILE_W + 10)
        c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(x - TILE_W / 2, yb_t, TILE_W, TILE_H, 6, fill=1, stroke=1)
        reg("page 1 tile " + str(i + 1), x - TILE_W / 2, yb_t, TILE_W, TILE_H, r=6, outer=PAD)
        c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(x, TILE_TOP - PAD - 2 - 13, t.split()[0])
        c.setFillColor(d.MUT); c.setFont(d.FM, 7.5); c.drawCentredString(x, yb_t + PAD + 1, " ".join(t.split()[1:]).upper())
    ly = yb_t - PAD - 8 - 6
    assert ly - 2 > 166.6 + PAD, ("reader line runs into the kit's tint band", ly)
    d._spaced(PW / 2, ly, "TYPE THE NAMES IN FREE ADOBE ACROBAT READER", 8.5, d.P, d.FM)
    c.showPage = _orig; _orig()
c.showPage = _cover_extra
d.cover(["Christmas", "Coupon Book"], COVER_SUB, 13, kicker="EDITABLE PRINTABLE PDF")

# ------------------------------------------------------------------ 2 how to edit, print and assemble
d.start("How to Edit, Print and Assemble", "Everything happens in the free Adobe Acrobat Reader. No Canva, no Templett, no account.", kicker="Start here", centered=True)
steps = [
    ("Open in Adobe Acrobat Reader", "Download the PDF and open it in Adobe Acrobat Reader (free) on a computer. Some phone and browser viewers do not save typed text."),
    ("Type the names", "Click any FOR or FROM line and type. The 3 book covers have TO and FROM lines too. Leave a line empty to write by hand after printing."),
    ("Write your own", "Page 11 has 5 blank coupons, the same size as the book: type a title, two lines of detail, and the names. The fonts are fixed and cannot be changed."),
    ("Save and print", "Save, then print only the pages you need on US Letter paper at 100% (actual size). Cardstock or matte photo paper feels best."),
    ("Cut and stack", "Cut on the corner marks. Put a front cover on top and its back cover at the bottom of each set."),
    ("Bind it", "Staple the left edge twice, punch a hole and tie a ribbon, or clip it with a binder clip. Slip it into the gift envelope on page 12."),
]
top = d.y + 2; gap = 8
h = (top - BOT - gap * (len(steps) - 1)) / len(steps)
for i, (hd, body) in enumerate(steps):
    yb = top - (i + 1) * h - i * gap
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(M, yb, PW - 2 * M, h, 8, fill=1, stroke=1)
    reg("step " + str(i + 1), M, yb, PW - 2 * M, h)
    c.setFillColor(d.T); c.circle(M + PAD + 18, yb + h / 2, 16, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.S, 16); c.drawCentredString(M + PAD + 18, yb + h / 2 - 6, str(i + 1))
    tx = M + PAD + 48; tw = PW - 2 * M - 48 - 2 * PAD - 2
    ls = wrapc(body, d.F, 9.8, tw)
    blk = 15 + 6 + 13.5 * len(ls)
    yy = yb + h / 2 + blk / 2 - 12
    c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(tx, yy, hd); yy -= 19
    c.setFillColor(d.INK); c.setFont(d.F, 9.8)
    for ln in ls: c.drawString(tx, yy, ln); yy -= 13.5
d.end()

# ------------------------------------------------------------------ 3 front covers
COVERS = [("Partner", "For My Love", "10 coupons, all year long"), ("Kids", "For My Little Elf", "10 coupons for being you"),
          ("Family", "For the Family", "10 coupons from the heart")]
page_title("Front Covers", "Cut one for each book")
ys, h = stack(3, 16)
for (key, line2, sub), yb in zip(COVERS, ys):
    x = CX
    c.setFillColor(d.P); c.roundRect(x, yb, CW, h, 8, fill=1, stroke=0)
    c.setStrokeColor(white); c.setLineWidth(0.8); c.roundRect(x + 8, yb + 8, CW - 16, h - 16, 5, fill=0, stroke=1)
    reg("cover " + key, x + 8, yb + 8, CW - 16, h - 16, r=5)
    cy = yb + h - PAD - 16
    d._spaced(PW / 2, cy, "A BOOK OF CHRISTMAS COUPONS", 8.5, HexColor(PAL["tint"]), d.FM)
    c.setFillColor(white); c.setFont(d.S, 32); c.drawCentredString(PW / 2, cy - 44, line2)
    star(PW / 2 - stringWidth(line2, d.S, 32) / 2 - 22, cy - 34, 8, HexColor(PAL["accent"]))
    star(PW / 2 + stringWidth(line2, d.S, 32) / 2 + 22, cy - 34, 8, HexColor(PAL["accent"]))
    c.setFillColor(HexColor(PAL["tint"])); c.setFont(d.SS, 12); c.drawCentredString(PW / 2, cy - 68, sub)
    # white label for TO / FROM
    lw, lh = 400, 52; lx = PW / 2 - lw / 2; ly = yb + 8 + PAD + 3
    c.setFillColor(white); c.roundRect(lx, ly, lw, lh, 6, fill=1, stroke=0)
    reg("cover label " + key, lx, ly, lw, lh, r=6)
    c.setFillColor(d.MUT); c.setFont(d.FM, 8)
    c.drawString(lx + PAD, ly + PAD + 3, "TO"); field(f"Cover {key} to", lx + PAD + 18, ly + PAD + 1, 158, size=10)
    c.drawString(lx + 208, ly + PAD + 3, "FROM"); field(f"Cover {key} from", lx + 238, ly + PAD + 1, lw - 238 - PAD, size=10)
    cutmarks(x, yb, CW, h)
d.end()

# ------------------------------------------------------------------ 4 back covers
BACKS = [("Partner", ["Redeem any time, as often as the book allows.", "No expiry date. Hugs accepted as payment.", "The giver may not refuse, sulk or reschedule twice."]),
         ("Kids", ["Hand a coupon to a grown-up to cash it in.", "Good for one use each. Keep the rest safe.", "Grown-ups promise to say yes with a smile."]),
         ("Family", ["Call, text or hand it over to redeem.", "Valid any day of the year, holidays included.", "Made with love and meant to be used."])]
page_title("Back Covers", "The fine print, one for each book")
ys, h = stack(3, 16)
for (key, rules), yb in zip(BACKS, ys):
    x = CX
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1); c.roundRect(x, yb, CW, h, 8, fill=1, stroke=1)
    c.setFillColor(d.T); c.rect(x + 1.5, yb + h - 44, CW - 3, 42.5, fill=1, stroke=0)
    reg("back " + key, x, yb, CW, h)
    c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawCentredString(PW / 2, yb + h - 30, f"The Fine Print  ·  {key} Book")
    yy = yb + PAD + 16 + (h - 40 - PAD - 16) / 2 + 17 - 4
    c.setFont(d.F, 10.2)
    for r in rules:
        star(x + PAD + 52, yy + 3.5, 4.5, d.A); c.setFillColor(d.INK); c.drawString(x + PAD + 64, yy, r); yy -= 17
    c.setFillColor(d.MUT); c.setFont(d.FM, 8)
    c.drawString(x + PAD + 52, yb + PAD + 4, "MADE WITH LOVE BY"); field(f"Back {key} by", x + PAD + 52 + 90, yb + PAD + 2, 200)
    cutmarks(x, yb, CW, h)
d.end()

# ------------------------------------------------------------------ 5-10 written coupons
for key, line2, coupons in SETS:
    for half in (0, 1):
        page_title(f"{key} Coupons", f"{key} book  ·  coupons {half * 5 + 1} to {half * 5 + 5}")
        ys, h = stack(5)
        for k, yb in enumerate(ys):
            n = half * 5 + k + 1
            coupon(n, *coupons[n - 1], key, yb, h)
        d.end()

# ------------------------------------------------------------------ 11 five blank coupons, same 6.4 x 1.6 in size as pages 5-10
# Fix round Oct 31 (Judge fix 2): the old 2 x 3 blanks were ~3.5 in wide and did not stack into a book. Six 1.6 in
# coupons need 9.6 in of a 9.6 in printable height (no room for the title or footer), so the page holds 5, like 5-10.
NBLANK = 5
page_title("Write Your Own", f"{NBLANK} blank coupons, same size as the book: type every line")


def blank_coupon(i, yb, h):
    x, w = CX, CW
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.1); c.roundRect(x, yb, w, h, 8, fill=1, stroke=1)
    sw = 78
    c.setFillColor(d.T); c.roundRect(x + 1.5, yb + 1.5, sw, h - 3, 7, fill=1, stroke=0)
    c.setDash(2, 3); c.setStrokeColor(d.P); c.setLineWidth(0.8); c.line(x + sw + 2, yb + PAD + 1, x + sw + 2, yb + h - PAD - 1); c.setDash()
    mx = x + sw / 2 + 1
    c.setFillColor(d.P); c.setFont(d.FM, 7.5); c.drawCentredString(mx, yb + h - PAD - 8, "YOUR OWN")
    c.setFillColor(d.D); c.setFont(d.S, 26); c.drawCentredString(mx, yb + h / 2 - 12, f"{i:02d}")
    star(mx, yb + PAD + 6, 6, d.A)
    tx = x + sw + 2 + PAD; tw = w - sw - 2 - 2 * PAD
    field(f"Blank {i} title", tx, yb + h - PAD - 20, tw, h=19, size=14, italic=True)
    field(f"Blank {i} line 1", tx, yb + h - PAD - 38, tw, h=14, size=9.5)
    field(f"Blank {i} line 2", tx, yb + h - PAD - 55, tw, h=14, size=9.5)
    fy = yb + PAD + 2
    c.setFillColor(d.MUT); c.setFont(d.FM, 8)
    fw1 = (tw - 22 - 12 - 30) / 2
    c.drawString(tx, fy + 2, "FOR"); field(f"Blank {i} for", tx + 22, fy, fw1, size=10)
    fx = tx + 22 + fw1 + 12
    c.drawString(fx, fy + 2, "FROM"); field(f"Blank {i} from", fx + 30, fy, tx + tw - fx - 30, size=10)
    reg(f"blank {i}", x, yb, w, h)
    cutmarks(x, yb, w, h)


ys, h = stack(NBLANK)
assert abs(h / 72 - 1.6) < 0.02 and CW / 72 == 6.388888888888889, h
for k, yb in enumerate(ys):
    blank_coupon(k + 1, yb, h)
d.end()

# ------------------------------------------------------------------ 12 gift envelope
page_title("Gift Envelope", "Cut on the outer line, fold on the dashes, glue the side flaps")
# Fix round Oct 31 (Judge fix 1): panels 6.6 x 2.1 in with a 0.25 in bottom gusset and 0.25 in side gussets, so 3 stapled
# books (1.6 in coupons, ~0.36 in thick together) fit; 475 + 2 x 18 = 511 pt = the width inside the 0.7 in margins.
EW, EH, FL, SF, G = 475, 151.2, 70, 18, 18
assert EW + 2 * SF <= PW - 2 * M + 0.5 and abs(EH / 72 - 2.1) < 0.01 and G / 72 == 0.25 and SF / 72 == 0.25
ex = PW / 2 - EW / 2
top_e = TOP - 6
c.setStrokeColor(d.P); c.setLineWidth(1.1); c.setFillColor(white)
p = c.beginPath()
p.moveTo(ex + 20, top_e); p.lineTo(ex + EW - 20, top_e); p.lineTo(ex + EW, top_e - FL)        # top flap
FT = top_e - FL - EH - G                                                                       # front panel top
p.lineTo(ex + EW, FT)                                                                          # back panel + bottom gusset right
p.lineTo(ex + EW + SF, FT - 8); p.lineTo(ex + EW + SF, FT - EH + 8); p.lineTo(ex + EW, FT - EH)  # right side gusset
p.lineTo(ex, FT - EH)
p.lineTo(ex - SF, FT - EH + 8); p.lineTo(ex - SF, FT - 8); p.lineTo(ex, FT)                    # left side gusset
p.lineTo(ex, top_e - FL); p.close()
c.drawPath(p, fill=1, stroke=1)
c.setFillColor(d.T)
c.rect(ex + 1, FT - EH + 1, EW - 2, EH - 2, fill=1, stroke=0)                                 # front panel tint
c.setDash(4, 3); c.setStrokeColor(d.P); c.setLineWidth(0.8)
c.line(ex, top_e - FL, ex + EW, top_e - FL); c.line(ex, top_e - FL - EH, ex + EW, top_e - FL - EH); c.line(ex, FT, ex + EW, FT)
c.line(ex, FT, ex, FT - EH); c.line(ex + EW, FT, ex + EW, FT - EH); c.setDash()
c.setFillColor(d.MUT); c.setFont(d.FM, 7.5)
c.drawCentredString(PW / 2, top_e - FL / 2 - 3, "TOP FLAP  ·  FOLD DOWN AND TUCK IN")
c.drawCentredString(PW / 2, top_e - FL - EH / 2 - 3, "BACK  ·  2.1 IN DEEP  ·  THE PRINTED SIDE FACES OUT")
c.setFont(d.FM, 6.5); c.drawCentredString(PW / 2, FT + G / 2 - 2.5, "BOTTOM GUSSET 0.25 IN  ·  FOLD BOTH DASHES INWARD")
c.setFont(d.FM, 6.5)
c.saveState(); c.translate(ex - SF / 2, FT - EH / 2); c.rotate(90); c.drawCentredString(0, -2.5, "SIDE GUSSET  ·  GLUE"); c.restoreState()
c.saveState(); c.translate(ex + EW + SF / 2, FT - EH / 2); c.rotate(-90); c.drawCentredString(0, -2.5, "SIDE GUSSET  ·  GLUE"); c.restoreState()
fyb = FT - EH
reg("envelope front", ex, fyb, EW, EH, r=0)
c.setFillColor(d.D); c.setFont(d.S, 22); c.drawCentredString(PW / 2, fyb + EH - PAD - 22, "Merry Christmas")
star(PW / 2 - 108, fyb + EH - PAD - 14, 6, d.A); star(PW / 2 + 108, fyb + EH - PAD - 14, 6, d.A)
c.setFillColor(d.MUT); c.setFont(d.FM, 8)
c.drawString(ex + 70, fyb + PAD + 48, "TO"); field("Envelope to", ex + 100, fyb + PAD + 46, EW - 170)
c.drawString(ex + 70, fyb + PAD + 12, "FROM"); field("Envelope from", ex + 100, fyb + PAD + 10, EW - 170)
# fold steps under the envelope
sy = fyb - 30
bx, bwid = M, PW - 2 * M; bh2 = sy - BOT
c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(bx, BOT, bwid, bh2, 8, fill=1, stroke=1)
reg("fold steps", bx, BOT, bwid, bh2)
fold = ["Print this page on paper or light cardstock and cut on the solid outline.",
        "Fold the bottom gusset in on both dashed lines, so the front panel meets the back.",
        "Fold the two 0.25 in side gussets in and glue them to the back panel.",
        "Type or write the names, slip the coupon books inside and tuck in the top flap.",
        "Holds 3 stapled books of 6.4 x 1.6 in coupons: 2.1 in deep with 0.25 in gussets."]
c.setFillColor(d.D); c.setFont(d.SB, 13); c.drawString(bx + PAD, BOT + bh2 - PAD - 12, "Folding the envelope")
rowh = (bh2 - 2 * PAD - 26) / len(fold)
yy = BOT + bh2 - PAD - 26 - rowh / 2 - 4
for i, s in enumerate(fold):
    c.setFillColor(d.T); c.circle(bx + PAD + 10, yy + 3.5, 10, fill=1, stroke=0)
    c.setFillColor(d.D); c.setFont(d.FB, 9.5); c.drawCentredString(bx + PAD + 10, yy, str(i + 1))
    c.setFillColor(d.INK); c.setFont(d.F, 10.2); c.drawString(bx + PAD + 30, yy, s); yy -= rowh
d.end()

# ------------------------------------------------------------------ 13 thank-you (spec text verbatim)
c.setFillColor(HexColor(PAL["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
d._frame()
for k, (sx, sy2, ss) in enumerate([(PW / 2 - 110, PH - 250, 10), (PW / 2, PH - 236, 16), (PW / 2 + 110, PH - 250, 10)]):
    star(sx, sy2, ss, d.A if k != 1 else d.P)


def para_c(y, text, width, size, font, lead=1.5):
    c.setFillColor(d.INK); c.setFont(font, size)
    for ln in wrapc(text, font, size, width): c.drawCentredString(PW / 2, y, ln); y -= size * lead
    return y


c.setFillColor(d.D); c.setFont(d.S, 34); c.drawCentredString(PW / 2, PH - 310, "You just made my day!")
d._ornament(PW / 2, PH - 334)
y = PH - 368
y = para_c(y, "Thank you for choosing a small, one-person shop over the big guys.", 420, 13, d.SS) - 16
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 460, 13, d.SS) - 22
c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(1); c.roundRect(PW / 2 - 200, y - 56, 400, 56, 12, fill=1, stroke=1)
parts = "How: Etsy app → You → Purchases → Leave a review".split("→")
wds = [stringWidth(p_, d.FM, 12.5) for p_ in parts]; aw = stringWidth("→", "DejaVu", 12.5)
x = PW / 2 - (sum(wds) + aw * (len(parts) - 1)) / 2
c.setFillColor(d.D)
for i, p_ in enumerate(parts):
    c.setFont(d.FM, 12.5); c.drawString(x, y - 32, p_); x += wds[i]
    if i < len(parts) - 1: c.setFont("DejaVu", 12.5); c.drawString(x, y - 32, "→"); x += aw
y -= 56 + 24
y = para_c(y, "Something not right? Message me first and I'll fix it fast.", 420, 13, d.SS) - 40
c.setFillColor(d.P); c.setFont(d.SB, 14); c.drawCentredString(PW / 2, y - 6, "With thanks,")
c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 30, "GM's Digital Creations")
c.showPage()
d.save()
import json
json.dump({"boxes": BOXES, "fields": FIELDS}, open(HERE + "/boxes.json", "w"))
print("built", RAW, "pages", d.page + 1, "fields", len(FIELDS))
