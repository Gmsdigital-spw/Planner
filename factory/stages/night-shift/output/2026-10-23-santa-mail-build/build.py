import sys, math
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/build/santa")
import gm_style as gs
from gm_style import PW, PH, MARGIN, wrap
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from content import LETTERS, TAG_LINES, TAG_NAMES

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/build/santa/santa-mail-bundle.pdf"
pal = gs.palette("evergreen")
NAME = "Santa Mail Bundle"
d = gs.Book(OUT, NAME, pal, cover_style="split", page_frame="band")
c = d.c
registerFont(TTFont("gm-serifBI", "/home/claude/planner/tools/fonts/Lora-BoldItalic.ttf"))
registerFont(TTFont("gm-serifI", "/home/claude/planner/tools/fonts/Lora-Italic.ttf"))
registerFont(TTFont("dejavu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
RED = HexColor("#A8323E")
CLEAR = Color(1, 1, 1, alpha=0)
FIELD_TINT = HexColor("#EEF4F0")
L, R = MARGIN, PW - MARGIN
BOTTOM = MARGIN + 16
FIELDS = []

def field(name, value, x, y, w, h, size=12, font="Times-Roman", line=True, tint=True):
    """Type-in field; y is the baseline line position. maxlen keeps typed text inside the box."""
    if tint:
        c.setFillColor(FIELD_TINT); c.rect(x, y, w, h, fill=1, stroke=0)
    if line:
        c.setStrokeColor(d.P); c.setLineWidth(0.8); c.line(x, y, x + w, y)
    while value and stringWidth(value, font, size) > w - 8 and size > 9.5: size -= 0.5
    assert not value or stringWidth(value, font, size) <= w - 8, (name, value)
    maxlen = max(4, len(value) + 4, int((w - 6) / (0.46 * size)))
    c.acroForm.textfield(name=name, value=value, x=x, y=y + 1, width=w, height=h - 1, fontName=font,
                         fontSize=size, borderStyle="underlined", borderWidth=0, borderColor=CLEAR,
                         fillColor=CLEAR, textColor=d.D, fieldFlags="", maxlen=maxlen, forceBorder=False,
                         tooltip=name.replace("_", " "))
    FIELDS.append((name, value, w, size, font, maxlen))

def para(text, x, y, w, font="gm-serif", size=12.6, lead=19.5, color=None):
    c.setFillColor(color or d.INK); c.setFont(font, size)
    for ln in wrap(text, font, size, w):
        c.drawString(x, y - size, ln); y -= lead
    return y

def star(x, y, r, col):
    c.setFillColor(col); p = c.beginPath()
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.42
        (p.moveTo if i == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    p.close(); c.drawPath(p, fill=1, stroke=0)

def flake(x, y, r, col, lw=1.1):
    c.setStrokeColor(col); c.setLineWidth(lw)
    for i in range(6):
        a = i * math.pi / 3; ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        c.line(x, y, ex, ey)
        for s in (-1, 1):
            mx, my = x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a)
            b = a + s * 0.6; c.line(mx, my, mx + r * 0.3 * math.cos(b), my + r * 0.3 * math.sin(b))

def holly(x, y, s=1.0):
    c.setFillColor(d.P)
    for ang in (-35, 35):
        c.saveState(); c.translate(x, y); c.rotate(ang); c.ellipse(-22 * s, -6 * s, 22 * s, 6 * s, fill=1, stroke=0); c.restoreState()
    c.setFillColor(RED)
    for dx, dy in ((-4, 2), (4, 2), (0, -4)): c.circle(x + dx * s, y + dy * s, 4 * s, fill=1, stroke=0)

def seal(x, y, r, top="NORTH POLE", bottom="OFFICIAL MAIL"):
    c.setFillColor(RED); c.circle(x, y, r, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#F3D9A4")); c.setLineWidth(1); c.circle(x, y, r - 5, fill=0, stroke=1)
    star(x, y, r * 0.32, HexColor("#F3D9A4"))
    for text, sign in ((top, 1), (bottom, -1)):
        c.setFont("gm-sansM", r * 0.17); c.setFillColor(white)
        n = len(text); span = min(150, n * 13) * math.pi / 180
        for i, ch in enumerate(text):
            a = math.pi / 2 + sign * (span / 2 - i * span / max(1, n - 1)) if sign == 1 else -math.pi / 2 - (span / 2 - i * span / max(1, n - 1))
            c.saveState(); c.translate(x + (r - 15) * math.cos(a), y + (r - 15) * math.sin(a))
            c.rotate(math.degrees(a) - 90 if sign == 1 else math.degrees(a) + 90)
            c.drawCentredString(0, -r * 0.06, ch); c.restoreState()

def corners():
    for (x, y) in ((L + 6, BOTTOM + 4), (R - 6, BOTTOM + 4)):
        pass

# ---------------------------------------------------------------- 1 cover
def my_cover():
    d.page += 1
    c.setFillColor(HexColor(pal["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    sw = PW * 0.34
    c.setFillColor(d.P); c.rect(0, 0, sw, PH, fill=1, stroke=0)
    c.setFillColor(d.A); c.rect(sw, 0, 4, PH, fill=1, stroke=0)
    for k in range(7):
        flake(sw / 2 + (-40 if k % 2 else 40), PH - 90 - k * 100, 16, HexColor("#8FB3A3"), 1.2)
    c.saveState(); c.translate(sw / 2 + 5, 70); c.restoreState()
    x0, w = sw + 44, PW - sw - 44 - MARGIN
    y = PH - 120
    c.setFillColor(d.P); c.setFont("gm-sansM", 10); c.drawString(x0, y, "EDITABLE PDF  ·  13 PAGES  ·  TYPE IN ADOBE READER"); y -= 70
    c.setFillColor(d.D); c.setFont("gm-serifB", 50); c.drawString(x0, y, "Santa Mail"); y -= 56
    c.setFillColor(RED); c.setFont("gm-serifBI", 50); c.drawString(x0, y, "Bundle"); y -= 26
    c.setStrokeColor(d.A); c.setLineWidth(2); c.line(x0, y, x0 + 70, y); y -= 34
    y = para("Letters from Santa for six different kinds of year, plus everything to deliver them on Christmas Eve.", x0, y, w, font="gm-serif", size=15, lead=21) - 20
    c.setFillColor(d.P); c.setFont("gm-sansM", 9.5); c.drawString(x0, y, "WHAT'S INSIDE"); y -= 12
    items = ["6 letters from Santa: nice list, first Christmas, new big sibling, kindness, a hard year, new home",
             "Official Nice List certificate", "Santa's Nice List, checked twice", "Dear Santa wish list",
             "4 North Pole envelope labels", "12 From Santa gift tags"]
    for it in items:
        lines = wrap(it, "gm-sans", 11.5, w - 24)
        star(x0 + 7, y - 12, 6.5, d.A)
        c.setFillColor(d.INK); c.setFont("gm-sans", 11.5)
        for ln in lines: c.drawString(x0 + 22, y - 16, ln); y -= 17
        y -= 8
    seal(x0 + w - 70, 150, 64)
    c.setFillColor(d.MUT); c.setFont("gm-sansM", 9.5); c.drawString(x0, 120, "PRINTABLE  ·  INSTANT DOWNLOAD")
    c.drawString(x0, 104, "US LETTER  ·  FITS A4")
    c.setFont("gm-sans", 8.5); c.drawString(x0, 40, "GM's Digital Creations")
    c.showPage()
my_cover()

# ---------------------------------------------------------------- 2 how to use
d.start("How to Use Your Santa Mail", "Everything types right into the free Adobe Acrobat Reader. No Canva account, no app, no sign-up.", kicker="Start here")
d.heading("Make a letter in 5 minutes")
d.bullets(["Download the PDF from Etsy (You > Purchases > Download Files) and open it in the free Adobe Acrobat Reader on a computer.",
           "Click any pale green box and type: the child's name, the date, three good things they did and the P.S.",
           "The sample words are already in every box. Select them and type over them, or keep the ones you like.",
           "Print on plain paper, or on cream or parchment cardstock for a real North Pole look. Print at 100% (Actual size).",
           "Sign it in gold or red pen, fold it in three and slip it into an envelope with a North Pole label."], numbered=True, gap=5)
d.heading("Pick the right letter")
rows = [["1  The Nice List", "Any child, any year: the classic letter"],
        ["2  Baby's First Christmas", "A keepsake for a baby or toddler's first December"],
        ["3  New Big Sibling", "A child who became a big brother or sister this year"],
        ["4  The Kindness Star", "A child who shared, helped or included others"],
        ["5  A Hard Year, Done Well", "A move, a loss, an illness or a big change, handled bravely"],
        ["6  A New Home", "A family that moved house before Christmas"]]
d.table(["Letter", "Best for"], [1, 1.6], rows, rowh=24, size=9.6)
d.heading("Ideas for Christmas Eve")
d.bullets(["Leave the letter by the empty cookie plate.", "Roll it up and tie it with red ribbon.",
           "Hide the Nice List certificate in a stocking.", "Tuck a gift tag on the biggest present.",
           "Have the child fill in the wish list in early December.", "Frame the first Christmas letter as a keepsake."], cols=2, gap=6)
d.heading("Good to know")
d.text("Fonts and colors are fixed so every page prints the way you see it. On a phone or tablet, use the Adobe Acrobat Reader app; other phone viewers may not show the type-in boxes. US Letter size; choose Fit to page for A4. Personal use only. This is a digital file: nothing will be shipped.", size=9.8)
d.end()

# ---------------------------------------------------------------- 3-8 letters
for i, Lt in enumerate(LETTERS, 1):
    d.start("From the Desk of Santa Claus", None, kicker=Lt["kicker"])
    y = d.y - 4
    # address block
    c.setFillColor(d.P); c.setFont("gm-sansM", 8.5); c.drawString(L, y - 9, "SANTA'S WORKSHOP  ·  1 CANDY CANE LANE  ·  NORTH POLE")
    field(f"l{i}_date", "Christmas Eve, 2026", R - 170, y - 14, 170, 18, size=11, font="Times-Italic")
    y -= 44
    c.setFillColor(d.D); c.setFont("gm-serifB", 20); c.drawString(L, y - 20, "Dear")
    nx = L + stringWidth("Dear ", "gm-serifB", 20)
    field(f"l{i}_name", Lt["name"], nx, y - 24, 260, 26, size=20, font="Times-BoldItalic")
    c.setFont("gm-serifB", 20); c.setFillColor(d.D); c.drawString(nx + 264, y - 20, ",")
    y -= 44
    for ptxt in Lt["paras"]:
        y = para(ptxt, L, y, R - L) - 10
    y = para(Lt["lead"], L, y, R - L, font="gm-serifSB", size=12.6, color=d.P) - 6
    for k, g in enumerate(Lt["good"], 1):
        star(L + 7, y - 13, 6.5, d.A)
        field(f"l{i}_good{k}", g, L + 22, y - 23, R - L - 22, 22, size=13, font="Times-Roman")
        y -= 33
    y -= 8
    y = para(Lt["close"], L, y, R - L) - 10
    c.setFillColor(d.INK); c.setFont("gm-serif", 12.6); c.drawString(L, y - 13, "With love and a sleigh full of joy,")
    y -= 26
    c.setFillColor(RED); c.setFont("gm-serifBI", 40); c.drawString(L, y - 40, "Santa Claus")
    sig_y = y - 48
    c.setStrokeColor(d.A); c.setLineWidth(1); c.line(L, sig_y, L + 200, sig_y)
    seal(R - 62, sig_y + 4, 54)
    assert sig_y + 4 + 54 < sig_y + 48 + 26 + 10 - 6
    y = sig_y - 30
    field(f"l{i}_ps", Lt["ps"], L, y - 22, R - L - 140, 22, size=12, font="Times-Italic")
    FIELD_BOTTOM = y - 22
    assert FIELD_BOTTOM > BOTTOM + 4, (i, FIELD_BOTTOM)
    # fill the space below with a holly and snow strip so the page never looks half empty
    gap = FIELD_BOTTOM - BOTTOM
    if gap > 30:
        cy = BOTTOM + min(gap / 2, 40)
        n = 7
        for k in range(n):
            xk = L + 30 + k * (R - L - 60) / (n - 1)
            if k % 2 == 0: holly(xk, cy, 0.8)
            else: flake(xk, cy, 9, d.A, 1.0)
    LETTER_GAPS = globals().setdefault("LETTER_GAPS", []); LETTER_GAPS.append(round(gap))
    d.end()

# ---------------------------------------------------------------- 9 certificate
d.start("Official Nice List Certificate", None, kicker="Certificate")
top = d.y - 6; bot = BOTTOM + 6
c.setStrokeColor(d.P); c.setLineWidth(2.2); c.roundRect(L, bot, R - L, top - bot, 10, fill=0, stroke=1)
c.setStrokeColor(d.A); c.setLineWidth(0.8); c.roundRect(L + 8, bot + 8, R - L - 16, top - bot - 16, 7, fill=0, stroke=1)
for (x, y) in ((L + 34, top - 34), (R - 34, top - 34), (L + 34, bot + 34), (R - 34, bot + 34)): holly(x, y, 0.9)
cx = PW / 2; y = top - 70
d._spaced(cx, y, "THE NORTH POLE PROUDLY ANNOUNCES", 10, d.P, d.FM); y -= 22
c.setFillColor(d.D); c.setFont("gm-serifB", 40); c.drawCentredString(cx, y - 40, "Nice List"); y -= 50
c.setFont("gm-serifB", 26); c.drawCentredString(cx, y - 26, "Certificate"); y -= 46
d._ornament(cx, y); y -= 30
c.setFillColor(d.INK); c.setFont("gm-serif", 13); c.drawCentredString(cx, y - 13, "This certifies that"); y -= 30
field("cert_name", "Olivia Rose", cx - 190, y - 40, 380, 40, size=30, font="Times-BoldItalic"); y -= 62
c.setFillColor(d.INK); c.setFont("gm-serif", 13)
for ln in ["has been checked twice and is officially on", "Santa's Nice List for Christmas 2026"]:
    c.drawCentredString(cx, y - 13, ln); y -= 20
y -= 8
c.setFillColor(d.P); c.setFont("gm-serifSB", 12); c.drawCentredString(cx, y - 12, "Special note from the elves"); y -= 22
field("cert_reason", "for being a kind friend and a wonderful helper", cx - 200, y - 22, 400, 22, size=13, font="Times-Italic"); y -= 30
sy = bot + 70
seal_cy = (y + sy + 30) / 2
seal(cx, seal_cy, 40, "NICE LIST", "APPROVED")
assert seal_cy + 40 < y - 2 and seal_cy - 40 > sy + 26, (seal_cy, y, sy)
for x0, lab, val, nm in ((L + 50, "SIGNED", "Santa Claus", "cert_sign"), (R - 50 - 190, "DATE", "December 24, 2026", "cert_date")):
    field(nm, val, x0, sy, 190, 24, size=16 if nm == "cert_sign" else 13, font="Times-BoldItalic" if nm == "cert_sign" else "Times-Roman")
    c.setFillColor(d.MUT); c.setFont("gm-sansM", 8); c.drawCentredString(x0 + 95, sy - 13, lab)
c.setFillColor(d.MUT); c.setFont("gm-sansM", 8); c.drawCentredString(cx, sy - 36, "HEAD ELF  ·  REINDEER DEPARTMENT  ·  NORTH POLE RECORDS OFFICE")
CERT_LOW = sy - 36; CERT_REASON_Y = y
d.end()

# ---------------------------------------------------------------- 10 the official nice list
d.start("Santa's Nice List 2026", "Type in every child in the house (or the whole family). The two ticks show the list was checked twice.", kicker="Checked twice")
y = d.y - 4
cols = [("NAME", 0.36), ("WHY THEY MADE THE LIST", 0.46), ("ONCE", 0.09), ("TWICE", 0.09)]
xs = [L]; [xs.append(xs[-1] + w * (R - L)) for _, w in cols]
c.setFillColor(d.T); c.roundRect(L, y - 24, R - L, 24, 4, fill=1, stroke=0)
c.setFillColor(d.D); c.setFont("gm-sansM", 8.6)
for (lab, _), x in zip(cols, xs): c.drawString(x + 7, y - 16, lab)
y -= 24
nrows = 14; rh = (y - BOTTOM - 8) / nrows
samples = [("Olivia", "Helped bake cookies for the neighbors"), ("Mason", "Shared his toys with his little sister"), ("Ava", "Read a bedtime story to her brother")]
for r in range(nrows):
    yy = y - (r + 1) * rh
    if r % 2 == 0:
        c.setFillColor(HexColor("#F5F8F6")); c.rect(L, yy, R - L, rh, fill=1, stroke=0)
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.6); c.line(L, yy, R, yy)
    nm, why = samples[r] if r < 3 else ("", "")
    field(f"list_name{r+1}", nm, xs[0] + 4, yy + 4, xs[1] - xs[0] - 10, rh - 10, size=12, font="Times-Roman", line=False, tint=False)
    field(f"list_why{r+1}", why, xs[1] + 4, yy + 4, xs[2] - xs[1] - 10, rh - 10, size=11, font="Times-Italic", line=False, tint=False)
    for k in (2, 3):
        bx = xs[k] + (xs[k + 1] - xs[k]) / 2 - 7
        c.setStrokeColor(d.P); c.setLineWidth(0.9); c.roundRect(bx, yy + rh / 2 - 7, 14, 14, 2.5, fill=0, stroke=1)
        c.acroForm.checkbox(name=f"list_chk{r+1}_{k-1}", x=bx, y=yy + rh / 2 - 7, size=14, checked=(r < 3), buttonStyle="check",
                            borderWidth=0, borderColor=CLEAR, fillColor=CLEAR, textColor=RED, fieldFlags="", forceBorder=False)
for x in xs[1:-1]:
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.line(x, y, x, y - nrows * rh)
d.end()

# ---------------------------------------------------------------- 11 wish list
d.start("Dear Santa: My Wish List", "For the child to fill in. Type it together, or print it and let them write and draw.", kicker="Wish list")
y = d.y - 2
c.setFillColor(d.D); c.setFont("gm-serifB", 17); c.drawString(L, y - 17, "Dear Santa,"); y -= 34
def labeled(label, name, w_label, y, default=""):
    c.setFillColor(d.INK); c.setFont("gm-serif", 12); c.drawString(L, y - 14, label)
    field(name, default, L + w_label, y - 18, R - L - w_label, 20, size=12)
    return y - 30
y = labeled("My name is", "wish_name", 70, y)
y = labeled("I am this many years old:", "wish_age", 150, y)
y = labeled("This year I was kind when I", "wish_kind", 165, y)
y = labeled("I am proud that I learned to", "wish_learn", 170, y)
y -= 4
c.setFillColor(d.P); c.setFont("gm-serifSB", 13); c.drawString(L, y - 13, "My Christmas wishes"); y -= 24
for k in range(1, 7):
    c.setFillColor(d.T); c.circle(L + 9, y - 10, 9, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont("gm-sansM", 9); c.drawCentredString(L + 9, y - 13, str(k))
    field(f"wish_item{k}", "", L + 26, y - 20, R - L - 26, 20, size=12)
    y -= 28
y -= 2
y = labeled("A gift I would like to give someone:", "wish_give", 205, y)
y = labeled("Cookies I will leave for you:", "wish_cookies", 160, y)
y -= 4
bh = y - BOTTOM - 26
c.setStrokeColor(d.P); c.setLineWidth(1); c.setDash(4, 3); c.roundRect(L, BOTTOM + 8, (R - L) * 0.64, bh, 8, fill=0, stroke=1); c.setDash()
c.setFillColor(d.MUT); c.setFont("gm-sansM", 8.5); c.drawString(L + 10, BOTTOM + 8 + bh - 16, "DRAW YOUR #1 WISH HERE")
bx = L + (R - L) * 0.68
c.setFillColor(d.INK); c.setFont("gm-serif", 12); c.drawString(bx, y - 12, "Love from,")
field("wish_from", "", bx, y - 46, R - bx, 24, size=14, font="Times-Italic")
seal(bx + (R - bx) / 2, BOTTOM + 8 + 60, 52, "LETTER TO", "SANTA")
WISH_BOX = bh
d.end()

# ---------------------------------------------------------------- 12 envelope labels
d.start("North Pole Envelope Labels", "Print on full-sheet sticker paper or plain paper and glue on. Cut along the light marks.", kicker="Sleigh mail")
top = d.y - 4; gw = (R - L - 14) / 2; gh = (top - BOTTOM - 14) / 2
names = [("Olivia Rose", "24 Evergreen Lane", "Your Town, Your State"), ("Mason James", "", ""), ("Ava Grace", "", ""), ("Liam Carter", "", "")]
for idx in range(4):
    col, row = idx % 2, idx // 2
    x0 = L + col * (gw + 14); y1 = top - row * (gh + 14); y0 = y1 - gh
    c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.setDash(2, 3); c.rect(x0, y0, gw, gh, fill=0, stroke=1); c.setDash()
    ix, iy, iw, ih = x0 + 8, y0 + 8, gw - 16, gh - 16
    # airmail stripe border
    c.saveState(); p = c.beginPath(); p.rect(ix, iy, iw, ih); c.clipPath(p, stroke=0, fill=0)
    for k, x in enumerate(range(int(ix) - int(ih), int(ix + iw) + 20, 14)):
        c.setFillColor(RED if k % 2 == 0 else d.P)
        q = c.beginPath(); q.moveTo(x, iy); q.lineTo(x + 7, iy); q.lineTo(x + 7 + ih, iy + ih); q.lineTo(x + ih, iy + ih); q.close(); c.drawPath(q, fill=1, stroke=0)
    c.restoreState()
    c.setFillColor(white); c.rect(ix + 8, iy + 8, iw - 16, ih - 16, fill=1, stroke=0)
    tx = ix + 18; ty = iy + ih - 22
    c.setFillColor(d.D); c.setFont("gm-serifB", 13); c.drawString(tx, ty - 6, "North Pole Express")
    c.setFillColor(d.P); c.setFont("gm-sansM", 7.2); c.drawString(tx, ty - 20, "SPECIAL DELIVERY  ·  BY SLEIGH")
    # stamp
    sx, sy_ = ix + iw - 66, iy + ih - 78
    c.setStrokeColor(d.A); c.setLineWidth(1); c.setDash(1.5, 1.5); c.rect(sx, sy_, 48, 58, fill=0, stroke=1); c.setDash()
    c.setFillColor(d.T); c.rect(sx + 4, sy_ + 4, 40, 50, fill=1, stroke=0)
    star(sx + 24, sy_ + 34, 12, RED); c.setFillColor(d.D); c.setFont("gm-sansM", 6.5); c.drawCentredString(sx + 24, sy_ + 10, "NP 2026")
    c.setFillColor(d.MUT); c.setFont("gm-sans", 7.5)
    for k, ln in enumerate(["From: Santa Claus", "1 Candy Cane Lane", "North Pole"]): c.drawString(tx, ty - 38 - k * 10, ln)
    fy = iy + ih * 0.40
    c.setFillColor(d.P); c.setFont("gm-sansM", 8); c.drawString(tx, fy + 34, "DELIVER TO")
    n, a1, a2 = names[idx]
    fw = iw - 36
    field(f"env{idx+1}_name", n, tx, fy + 6, fw, 26, size=18, font="Times-BoldItalic")
    field(f"env{idx+1}_addr1", a1, tx, fy - 26, fw, 22, size=12)
    field(f"env{idx+1}_addr2", a2, tx, fy - 56, fw, 22, size=12)
    c.setFillColor(d.MUT); c.setFont("gm-sansM", 6.8); c.drawString(tx, iy + 18, "HANDLE WITH CARE  ·  DO NOT OPEN UNTIL CHRISTMAS EVE")
d.end()

# ---------------------------------------------------------------- 13 gift tags
d.start("From Santa Gift Tags", "12 tags. Type each child's name, print on cardstock, cut, punch the hole and tie on with ribbon.", kicker="Gift tags")
top = d.y - 4; cols_, rows_ = 3, 4; gx, gy = 10, 10
tw = (R - L - gx * (cols_ - 1)) / cols_; th = (top - BOTTOM - gy * (rows_ - 1)) / rows_
for idx in range(12):
    col, row = idx % cols_, idx // cols_
    x0 = L + col * (tw + gx); y1 = top - row * (th + gy); y0 = y1 - th
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.setDash(2, 3); c.rect(x0, y0, tw, th, fill=0, stroke=1); c.setDash()
    # tag shape with clipped top corners
    ix, iy, iw, ih = x0 + 6, y0 + 6, tw - 12, th - 12
    cut = 16
    p = c.beginPath(); p.moveTo(ix, iy); p.lineTo(ix + iw, iy); p.lineTo(ix + iw, iy + ih - cut); p.lineTo(ix + iw - cut, iy + ih); p.lineTo(ix + cut, iy + ih); p.lineTo(ix, iy + ih - cut); p.close()
    fillc = d.P if idx % 2 == 0 else RED
    c.setFillColor(fillc); c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(white); c.roundRect(ix + 7, iy + 7, iw - 14, ih - 34, 5, fill=1, stroke=0)
    c.setFillColor(white); c.circle(ix + iw / 2, iy + ih - 13, 5, fill=1, stroke=0)
    c.setStrokeColor(d.A); c.setLineWidth(1); c.circle(ix + iw / 2, iy + ih - 13, 5, fill=0, stroke=1)
    tcx = ix + iw / 2; ty = iy + ih - 44
    c.setFillColor(fillc); c.setFont("gm-serifB", 11.5)
    line = TAG_LINES[idx]
    sz = 11.5
    while stringWidth(line, "gm-serifB", sz) > iw - 26: sz -= 0.5
    c.setFont("gm-serifB", sz); c.drawCentredString(tcx, ty, line)
    flake(tcx, ty - 18, 7, d.A, 0.8)
    c.setFillColor(d.MUT); c.setFont("gm-sansM", 7.5); c.drawString(ix + 14, ty - 44, "TO")
    field(f"tag{idx+1}_to", TAG_NAMES[idx], ix + 30, ty - 48, iw - 44, 18, size=13, font="Times-BoldItalic")
    c.setFillColor(d.MUT); c.setFont("gm-sansM", 7.5); c.drawString(ix + 14, ty - 66, "FROM")
    c.setFillColor(RED); c.setFont("gm-serifBI", 13); c.drawString(ix + 44, ty - 68, "Santa")
d.end()

# ---------------------------------------------------------------- thank-you (spec text verbatim)
d.page += 1; d._frame()
c.setFillColor(white); c.setFont(d.S, 22); c.drawString(L, PH - 44, "Thank You")
y = PH - 250
for k in range(5): star(PW / 2 - 80 + k * 40, y + 60, 7, d.A)
c.setFillColor(d.D); c.setFont("gm-serifB", 34); c.drawCentredString(PW / 2, y, "You just made my day!"); y -= 26
d._ornament(PW / 2, y); y -= 36
body = ["Thank you for choosing a small, one-person shop over the big guys.",
        "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one."]
for t in body:
    c.setFillColor(d.INK); c.setFont("gm-serif", 14)
    for ln in wrap(t, "gm-serif", 14, R - L - 60): c.drawCentredString(PW / 2, y, ln); y -= 22
    y -= 14
# "How:" line with DejaVu arrows
parts = ["How: Etsy app ", "→", " You ", "→", " Purchases ", "→", " Leave a review"]
fonts = [("gm-sansM" if p.strip() != "→" else "dejavu") for p in parts]
wtot = sum(stringWidth(p, f, 12.5) for p, f in zip(parts, fonts))
bw = wtot + 40
c.setFillColor(d.T); c.roundRect(PW / 2 - bw / 2, y - 14, bw, 34, 17, fill=1, stroke=0)
x = PW / 2 - wtot / 2
for p, f in zip(parts, fonts):
    c.setFillColor(d.D); c.setFont(f, 12.5); c.drawString(x, y - 1, p); x += stringWidth(p, f, 12.5)
y -= 64
c.setFillColor(d.INK); c.setFont("gm-serif", 14); c.drawCentredString(PW / 2, y, "Something not right? Message me first and I'll fix it fast."); y -= 100
holly(PW / 2, y + 10, 1.5); y -= 50
c.setFillColor(d.P); c.setFont("gm-serifBI", 16); c.drawCentredString(PW / 2, y, "With thanks,"); y -= 24
c.setFillColor(d.D); c.setFont("gm-serifB", 18); c.drawCentredString(PW / 2, y, "GM's Digital Creations")
c.showPage()
d.save()
import json
json.dump({"fields": FIELDS, "letter_gaps": LETTER_GAPS, "cert_low": CERT_LOW, "wish_box": WISH_BOX}, open(OUT + ".meta.json", "w"))
print("built", OUT, len(FIELDS), "text fields", "letter gaps", LETTER_GAPS, "cert low", round(CERT_LOW), "wish box", round(WISH_BOX))
