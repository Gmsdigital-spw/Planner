"""Pink Cabana Stripe Birthday Invitation: cover, how-to, 2 colourways x (invite + details card), thank-you."""
import sys, math, random
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.pagesizes import letter, landscape

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cabana_raw.pdf"
NAME = "Pink Bow Birthday Invitation Set"
pal = gs.palette("blush")
d = gs.Book(OUT, NAME, pal, cover_style="frame", page_frame="none")
c = d.c
c._initialFontName = "gm-sans"; c._fontname = "gm-sans"; c.setFont("gm-sans", 10)  # no stray Helvetica in the PDF
GREEN, GREEN2, LEAF = HexColor("#2F5B45"), HexColor("#4E7D5C"), HexColor("#6E9C73")
CREAM = HexColor("#FFF9F0")
WAYS = {
    "pink": dict(stripe=HexColor("#F4C9D0"), base=HexColor("#FFF4F1"), bow=HexColor("#EBA3B2"), bowd=HexColor("#C9707F"), label="Pink cabana"),
    "sage": dict(stripe=HexColor("#C9D8C2"), base=HexColor("#F7F8F1"), bow=HexColor("#EBA3B2"), bowd=HexColor("#C9707F"), label="Sage cabana"),
}
CW, CH = 360, 504  # 5 x 7 in

# ---------------------------------------------------------------- drawing helpers
def frond(x, y, ang, L, col, col2, n=11, seed=0):
    rnd = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux
    bend = 0.18
    def pt(t):
        b = bend * L * t * t
        return x + ux * L * t + px * b, y + uy * L * t + py * b
    for i in range(n):
        t = 0.12 + 0.85 * i / (n - 1)
        sx, sy = pt(t); tx, ty = pt(min(t + 0.02, 1)); dx, dy = tx - sx, ty - sy
        dl = math.hypot(dx, dy) or 1; dx, dy = dx / dl, dy / dl
        ll = L * (0.46 - 0.30 * t) * (0.9 + 0.2 * rnd.random())
        for side in (1, -1):
            sa = math.atan2(dy, dx) + side * math.radians(48 + 10 * t)
            ex, ey = sx + math.cos(sa) * ll, sy + math.sin(sa) * ll
            nx, ny = -math.sin(sa) * ll * 0.2, math.cos(sa) * ll * 0.2
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            p = c.beginPath(); p.moveTo(sx, sy)
            p.curveTo(mx + nx, my + ny, ex, ey, ex, ey)
            p.curveTo(ex, ey, mx - nx * 0.2, my - ny * 0.2, sx, sy); p.close()
            c.setFillColor(col if (i + (side > 0)) % 2 else col2); c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(GREEN); c.setLineWidth(1.6)
    p = c.beginPath(); p.moveTo(x, y)
    for k in range(1, 21): p.lineTo(*pt(k / 20))
    c.drawPath(p, stroke=1, fill=0)

def bow(cx, cy, s, col, dark):
    c.setLineWidth(0.9); c.setStrokeColor(dark)
    for sg in (1, -1):  # tails
        p = c.beginPath(); p.moveTo(cx + sg * 3 * s, cy - 2 * s)
        p.curveTo(cx + sg * 10 * s, cy - 18 * s, cx + sg * 6 * s, cy - 22 * s, cx + sg * 14 * s, cy - 32 * s)
        p.lineTo(cx + sg * 20 * s, cy - 27 * s)
        p.curveTo(cx + sg * 15 * s, cy - 19 * s, cx + sg * 15 * s, cy - 11 * s, cx + sg * 7 * s, cy - 1 * s); p.close()
        c.setFillColor(col); c.drawPath(p, stroke=1, fill=1)
    for sg in (1, -1):  # loops
        p = c.beginPath(); p.moveTo(cx, cy)
        p.curveTo(cx + sg * 14 * s, cy + 22 * s, cx + sg * 38 * s, cy + 20 * s, cx + sg * 36 * s, cy + 4 * s)
        p.curveTo(cx + sg * 34 * s, cy - 10 * s, cx + sg * 16 * s, cy - 10 * s, cx, cy); p.close()
        c.setFillColor(col); c.drawPath(p, stroke=1, fill=1)
        c.setStrokeColor(dark); c.setLineWidth(0.6)
        p = c.beginPath(); p.moveTo(cx + sg * 6 * s, cy + 2 * s)
        p.curveTo(cx + sg * 16 * s, cy + 12 * s, cx + sg * 28 * s, cy + 12 * s, cx + sg * 31 * s, cy + 5 * s)
        c.drawPath(p, stroke=1, fill=0); c.setLineWidth(0.9)
    c.setFillColor(dark); c.roundRect(cx - 6 * s, cy - 7 * s, 12 * s, 13 * s, 4 * s, stroke=0, fill=1)
    c.setFillColor(col); c.roundRect(cx - 4.5 * s, cy - 5.5 * s, 9 * s, 10 * s, 3 * s, stroke=0, fill=1)

def scallop_panel(x, y, w, h, r=7):
    c.setFillColor(CREAM)
    c.rect(x, y, w, h, stroke=0, fill=1)
    nx, ny = int(w // (2 * r)), int(h // (2 * r))
    sx, sy = w / nx, h / ny
    for i in range(nx):
        c.circle(x + sx * (i + .5), y + h, sx / 2, stroke=0, fill=1); c.circle(x + sx * (i + .5), y, sx / 2, stroke=0, fill=1)
    for j in range(ny):
        c.circle(x, y + sy * (j + .5), sy / 2, stroke=0, fill=1); c.circle(x + w, y + sy * (j + .5), sy / 2, stroke=0, fill=1)
    c.setStrokeColor(GREEN); c.setLineWidth(1.1); c.rect(x + 6, y + 6, w - 12, h - 12)
    c.setLineWidth(0.5); c.rect(x + 10, y + 10, w - 20, h - 20)

def spaced(cx, y, text, size, col, font, track=1.6):
    w = sum(gs.stringWidth(ch, font, size) for ch in text) + track * (len(text) - 1)
    x = cx - w / 2; c.setFillColor(col); c.setFont(font, size)
    for ch in text:
        c.drawString(x, y, ch); x += gs.stringWidth(ch, font, size) + track

def field(name, cx, y, w, h, value, size, fontName="Times-Roman", tip=None, maxlen=60):
    c.acroForm.textfield(name=name, tooltip=tip or name, x=cx - w / 2, y=y, width=w, height=h,
                         value=value, fontName=fontName, fontSize=size, borderWidth=0, borderStyle="underlined",
                         fillColor=None, borderColor=None, textColor=GREEN, fieldFlags="", forceBorder=False, maxlen=maxlen)

def card_bg(x0, y0, way):
    W = WAYS[way]
    c.saveState(); p = c.beginPath(); p.rect(x0, y0, CW, CH); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(W["base"]); c.rect(x0, y0, CW, CH, stroke=0, fill=1)
    sw = 22.5; c.setFillColor(W["stripe"])
    for i in range(0, 16, 2): c.rect(x0 + i * sw, y0, sw, CH, stroke=0, fill=1)
    frond(x0 - 8, y0 + CH + 6, -40, 150, LEAF, GREEN2, seed=1)
    frond(x0 + 30, y0 + CH + 14, -70, 120, GREEN2, LEAF, n=9, seed=2)
    frond(x0 + CW + 8, y0 - 6, 140, 150, LEAF, GREEN2, seed=3)
    frond(x0 + CW - 26, y0 - 14, 110, 115, GREEN2, LEAF, n=9, seed=4)
    c.restoreState()

def big_bg(x0, y0, w, h, way):
    W = WAYS[way]; k = w / CW
    c.saveState(); p = c.beginPath(); p.rect(x0, y0, w, h); c.clipPath(p, stroke=0, fill=0)
    c.setFillColor(W["base"]); c.rect(x0, y0, w, h, stroke=0, fill=1)
    sw = 22.5 * k; c.setFillColor(W["stripe"]); i = 0
    while i * sw < w: c.rect(x0 + i * sw, y0, sw, h, stroke=0, fill=1); i += 2
    frond(x0 - 8 * k, y0 + h + 6 * k, -40, 150 * k, LEAF, GREEN2, seed=1)
    frond(x0 + 30 * k, y0 + h + 14 * k, -70, 120 * k, GREEN2, LEAF, n=9, seed=2)
    frond(x0 + w + 8 * k, y0 - 6 * k, 140, 150 * k, LEAF, GREEN2, seed=3)
    frond(x0 + w - 26 * k, y0 - 14 * k, 110, 115 * k, GREEN2, LEAF, n=9, seed=4)
    c.restoreState()

def thanks(x0, y0, way, k):
    W = WAYS[way]; card_bg(x0, y0, way)
    px, py, pw, ph = x0 + 44, y0 + 44, CW - 88, CH - 104
    scallop_panel(px, py, pw, ph)
    cx = x0 + CW / 2; top = py + ph
    bow(cx, top + 12, 1.45, W["bow"], W["bowd"])
    field(f"ty{way}{k}_from", cx, top - 66, pw - 50, 14, "FROM THE BIRTHDAY GIRL", 8, "Times-Roman", "Top line (e.g. FROM THE BIRTHDAY BOY, FROM ALL OF US)", maxlen=24)
    c.setFillColor(GREEN); c.setFont("gm-serifI", 50); c.drawCentredString(cx, top - 122, "Thank")
    c.drawCentredString(cx, top - 170, "You")
    c.setStrokeColor(W["bowd"]); c.setLineWidth(0.7); c.line(cx - 40, top - 194, cx - 8, top - 194); c.line(cx + 8, top - 194, cx + 40, top - 194)
    c.setFillColor(W["bowd"]); c.circle(cx, top - 194, 2.2, stroke=0, fill=1)
    lines = [("l1", "FOR CELEBRATING WITH ME", "Message line 1"), ("l2", "AND FOR THE SWEETEST GIFT.", "Message line 2"),
             ("l3", "IT MEANT THE WORLD TO ME!", "Message line 3")]
    yy = top - 236
    for key, val, tip in lines:
        field(f"ty{way}{k}_{key}", cx, yy, pw - 36, 18, val, 10.5, "Times-Roman", tip); yy -= 26
    field(f"ty{way}{k}_sign", cx, yy - 30, pw - 40, 34, "Love, Ava", 24, "Times-Italic", "Signature (about 16 letters)", maxlen=16)
    spaced(cx, py + 26, "XOXO", 7.4, GREEN2, d.FM, 3.0)

def sign_page(way="pink"):
    PW, PH = letter
    SW, SH = 8 * 72, 10 * 72
    x0, y0 = (PW - SW) / 2, (PH - SH) / 2
    d.page += 1
    big_bg(x0, y0, SW, SH, way)
    k = SW / CW
    px, py, pw, ph = x0 + 62, y0 + 64, SW - 124, SH - 150
    c.saveState(); c.translate(px, py); c.scale(1, 1)
    c.restoreState()
    scallop_panel(px, py, pw, ph, r=9)
    cx = x0 + SW / 2; top = py + ph
    bow(cx, top + 16, 2.1, WAYS[way]["bow"], WAYS[way]["bowd"])
    spaced(cx, top - 110, "WELCOME TO", 14, GREEN2, d.FM, 3.6)
    field(f"sign{way}_name", cx, top - 210, pw - 60, 66, "Ava's", 50, "Times-Italic", "Name on the sign (about 12 letters)", maxlen=12)
    c.setFillColor(GREEN); c.setFont("gm-serifI", 50); c.drawCentredString(cx, top - 268, "Birthday")
    c.drawCentredString(cx, top - 322, "Party")
    c.setStrokeColor(WAYS[way]["bowd"]); c.setLineWidth(1); c.line(cx - 70, top - 360, cx - 12, top - 360); c.line(cx + 12, top - 360, cx + 70, top - 360)
    c.setFillColor(WAYS[way]["bowd"]); c.circle(cx, top - 360, 3, stroke=0, fill=1)
    field(f"sign{way}_line1", cx, top - 420, pw - 70, 32, "SWEET SIXTEEN", 22, "Times-Roman", "Sign line 1 (age or theme)")
    field(f"sign{way}_line2", cx, top - 462, pw - 70, 26, "MAY 16, 2026", 15, "Times-Roman", "Sign line 2 (date)")
    spaced(cx, py + 40, "LET'S CELEBRATE", 10, GREEN2, d.FM, 3.0)
    c.setStrokeColor(HexColor("#C9C2BD")); c.setLineWidth(0.4)
    for x in (x0, x0 + SW):
        c.line(x, y0 + SH + 4, x, y0 + SH + 14); c.line(x, y0 - 4, x, y0 - 14)
    c.setFillColor(d.MUT); c.setFont(d.F, 7.5)
    c.drawString(x0, 14, f"WELCOME SIGN · {WAYS[way]['label'].upper()}  ·  8 x 10 IN  ·  PRINT AT ACTUAL SIZE, TRIM ON THE MARKS (OR FRAME IT AS IS)")
    c.setFillColor(d.P); c.setFont(d.FM, 8); c.drawRightString(x0 + SW, 14, f"{d.page:02d}")
    c.showPage()

def invite(x0, y0, way, k):
    W = WAYS[way]; card_bg(x0, y0, way)
    px, py, pw, ph = x0 + 44, y0 + 44, CW - 88, CH - 104
    scallop_panel(px, py, pw, ph)
    cx = x0 + CW / 2
    bow(cx, py + ph + 12, 1.45, W["bow"], W["bowd"])
    top = py + ph
    spaced(cx, top - 60, "PLEASE JOIN US", 8.2, GREEN2, d.FM, 2.2)
    c.setFillColor(GREEN); c.setFont("gm-serifI", 40); c.drawCentredString(cx, top - 102, "Let's")
    c.drawCentredString(cx, top - 140, "Celebrate")
    field(f"{way}{k}_name", cx, top - 184, pw - 40, 30, "Ava's Sweet Sixteen", 16, "Times-Italic", "Name and age (about 26 letters)", maxlen=26)
    c.setStrokeColor(W["bowd"]); c.setLineWidth(0.7); c.line(cx - 40, top - 196, cx - 8, top - 196); c.line(cx + 8, top - 196, cx + 40, top - 196)
    c.setFillColor(W["bowd"]); c.circle(cx, top - 196, 2.2, stroke=0, fill=1)
    rows = [("date", "SATURDAY, MAY 16, 2026", "Day and date"), ("time", "2:00 TO 5:00 PM", "Time"),
            ("place", "THE CABANA CLUB", "Place name"), ("addr", "125 PALM AVENUE, SPRINGFIELD", "Address")]
    yy = top - 232
    for key, val, tip in rows:
        field(f"{way}{k}_{key}", cx, yy, pw - 36, 18, val, 10.5, "Times-Roman", tip); yy -= 24
    spaced(cx, yy - 6, "KINDLY REPLY", 7.4, GREEN2, d.FM, 2.0)
    field(f"{way}{k}_rsvp", cx, yy - 34, pw - 36, 18, "TO JESS AT 555-0142 BY MAY 1", 10, "Times-Roman", "RSVP name, phone and date")

def details(x0, y0, way, k):
    W = WAYS[way]; card_bg(x0, y0, way)
    px, py, pw, ph = x0 + 44, y0 + 44, CW - 88, CH - 104
    scallop_panel(px, py, pw, ph)
    cx = x0 + CW / 2; top = py + ph
    bow(cx, top + 12, 1.2, W["bow"], W["bowd"])
    c.setFillColor(GREEN); c.setFont("gm-serifI", 34); c.drawCentredString(cx, top - 70, "The Details")
    c.setFillColor(W["bowd"]); c.circle(cx, top - 88, 2.2, stroke=0, fill=1)
    blocks = [("dress", "WHAT TO WEAR", "PINK, WHITE OR ANYTHING SUMMERY", "BRING A SWIMSUIT IF YOU LIKE"),
              ("gifts", "GIFTS", "YOUR COMPANY IS THE BEST GIFT", "CARDS ARE ALWAYS WELCOME"),
              ("park", "PARKING", "FREE PARKING BY THE MAIN GATE", "DROP-OFF AT THE FRONT DOOR")]
    yy = top - 124
    for key, head, v1, v2 in blocks:
        field(f"{way}{k}_{key}h", cx, yy - 4, pw - 60, 15, head, 8.4, "Times-Roman", "Heading (e.g. FOOD, SWIM, WHAT TO BRING)", maxlen=20)
        field(f"{way}{k}_{key}1", cx, yy - 26, pw - 36, 17, v1, 9.6, "Times-Roman", head.title() + " line 1")
        field(f"{way}{k}_{key}2", cx, yy - 45, pw - 36, 17, v2, 9.6, "Times-Roman", head.title() + " line 2")
        yy -= 98

def cutmarks(x0, y0):
    c.setStrokeColor(HexColor("#C9C2BD")); c.setLineWidth(0.4)
    for x in (x0, x0 + CW):
        c.line(x, y0 + CH + 6, x, y0 + CH + 20); c.line(x, y0 - 6, x, y0 - 20)
    for y in (y0, y0 + CH):
        c.line(x0 - 6, y, x0 - 18, y) if x0 < 100 else None
        c.line(x0 + CW + 6, y, x0 + CW + 18, y) if x0 > 100 else None

def card_page(fn, way, title):
    LW, LH = landscape(letter)
    c.setPageSize((LW, LH)); d.page += 1
    gap = 18; x1 = (LW - 2 * CW - gap) / 2; y0 = (LH - CH) / 2
    for k, x0 in enumerate((x1, x1 + CW + gap)):
        fn(x0, y0, way, k + 1); cutmarks(x0, y0)
    c.setFillColor(d.MUT); c.setFont(d.F, 7.5)
    c.drawString(x1, 22, f"{title.upper()}  ·  5 x 7 IN, TWO PER PAGE  ·  CUT ON THE LIGHT MARKS")
    c.setFillColor(d.P); c.setFont(d.FM, 8); c.drawRightString(LW - x1, 22, f"{d.page:02d}")
    c.showPage(); c.setPageSize(letter)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("gm-serifI", "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

# ---------------------------------------------------------------- pages
def cover_page():
    PW, PH = letter; d.page += 1
    c.setFillColor(HexColor(pal["paper"])); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    for inset, w in ((36, 1.6), (46, 0.6)):
        c.setStrokeColor(GREEN); c.setLineWidth(w); c.rect(inset, inset, PW - 2 * inset, PH - 2 * inset, fill=0, stroke=1)
    spaced(PW / 2, PH - 120, "EDITABLE PDF  ·  NO ACCOUNT NEEDED", 10, GREEN2, d.FM, 2.6)
    c.setFillColor(GREEN); c.setFont(d.S, 44)
    c.drawCentredString(PW / 2, PH - 185, "Pink Bow Birthday"); c.drawCentredString(PW / 2, PH - 235, "Invitation Set")
    c.setFillColor(d.INK); c.setFont(d.SS, 15)
    c.drawCentredString(PW / 2, PH - 272, "Invitation, details card, thank-you card and welcome sign")
    c.drawCentredString(PW / 2, PH - 292, "in pink and in sage cabana stripes")
    # mini cards (static artwork only, no fields)
    minis = [("pink", "Let's", "Celebrate"), ("sage", "The", "Details"), ("pink", "Thank", "You"), ("sage", "Welcome", "to Ava's")]
    sc = 0.31; mw, mh = CW * sc, CH * sc; gap = 14
    x = (PW - 4 * mw - 3 * gap) / 2; y = 268
    for way, l1, l2 in minis:
        c.saveState(); c.translate(x, y); c.scale(sc, sc)
        card_bg(0, 0, way); scallop_panel(44, 44, CW - 88, CH - 104)
        bow(CW / 2, CH - 48, 1.4, WAYS[way]["bow"], WAYS[way]["bowd"])
        c.setFillColor(GREEN); c.setFont("gm-serifI", 52)
        c.drawCentredString(CW / 2, CH - 190, l1); c.drawCentredString(CW / 2, CH - 250, l2)
        c.restoreState()
        c.setStrokeColor(HexColor("#E2D6CF")); c.setLineWidth(0.6); c.rect(x, y, mw, mh, fill=0, stroke=1)
        x += mw + gap
    c.setFillColor(d.INK); c.setFont(d.SS, 13)
    c.drawCentredString(PW / 2, 230, "Type straight into this PDF in the free Adobe Acrobat Reader.")
    c.drawCentredString(PW / 2, 211, "No design app, no account, no login.")
    c.setFillColor(HexColor("#F7E9E6")); c.rect(46.6, 46.6, PW - 93.2, 120, fill=1, stroke=0)
    spaced(PW / 2, 118, "8 PRINTABLE PAGES  ·  4 DESIGNS IN 2 COLORS", 11, GREEN, d.FM, 2.4)
    spaced(PW / 2, 86, "PRINT AT HOME  ·  INSTANT DOWNLOAD", 9, d.MUT, d.FM, 2.0)
    c.setFont(d.FM, 8.5); c.setFillColor(d.MUT); c.drawCentredString(PW / 2, 24, "GM's Digital Creations")
    c.showPage()

cover_page()

d.start("How to edit and print", "Everything you need to fill in your details and print at home or at a print shop.")
d.heading("Edit your invitation")
d.bullets(["Download the PDF to a computer and open it in Adobe Acrobat Reader (free). A browser preview may not save your typing.",
           "Click any green line of text on pages 3 to 10 and type over the sample words. Every changing line is its own box.",
           "Each card on a page is separate, so you can make two different versions on one sheet. Detail lines type in CAPITALS automatically, like the sample.",
           "Save the file (File, Save As) before printing. Keep the original as a clean copy for next time.",
           "The headline, stripes, bow and leaves are part of the design. Fonts and colors cannot be changed."], numbered=True)
d.heading("Print and cut")
d.bullets(["Print at 100% or Actual size on US Letter paper: pages 3 to 8 landscape, pages 9 and 10 (the signs) portrait. A4 also works at Actual size.",
           "Use white cardstock (80 to 110 lb) for a sturdy card, or ask a local print shop to print it for you.",
           "Cut on the light grey corner marks with a paper trimmer for straight edges. Each card is 5 x 7 inches.",
           "Standard A7 envelopes (5.25 x 7.25 in) fit both the invitation and the details card."], numbered=True)
d.heading("What's inside")
d.bullets(["Page 3: invitation, pink cabana stripe (2 per page)", "Page 4: invitation, sage cabana stripe (2 per page)",
           "Page 5: details card, pink cabana stripe (2 per page)", "Page 6: details card, sage cabana stripe (2 per page)",
           "Pages 7 and 8: thank-you cards, pink and sage (2 per page)", "Pages 9 and 10: 8 x 10 welcome sign, pink and sage"], cols=1, check=True)
d.heading("Wording ideas for the name line")
d.bullets(["Ava's Sweet Sixteen", "Mia Turns Seven", "Chloe's 21st Birthday", "Emma Turns Thirty",
           "Grace is Turning 40", "Lily's First Birthday"], cols=3)
d.heading("Good to know")
d.text("Name lines hold up to 26 letters on the invitation, 12 on the sign and 16 in the signature. Do a test print first. Digital file only: nothing ships. Personal use.")
d.end()

card_page(invite, "pink", "Invitation · pink cabana")
card_page(invite, "sage", "Invitation · sage cabana")
card_page(details, "pink", "Details card · pink cabana")
card_page(details, "sage", "Details card · sage cabana")
card_page(thanks, "pink", "Thank-you card · pink cabana")
card_page(thanks, "sage", "Thank-you card · sage cabana")
sign_page("pink")
sign_page("sage")

# thank-you page (spec text verbatim)
d.page += 1
from reportlab.lib.pagesizes import letter as L
PW, PH = L
c.setFillColor(HexColor(pal["paper"])); c.rect(0, 0, PW, PH, stroke=0, fill=1)
c.setFillColor(WAYS["pink"]["stripe"])
for i in range(0, 40, 2): c.rect(i * 22.5, PH - 70, 22.5, 70, stroke=0, fill=1)
bow(PW / 2, PH - 150, 2.0, WAYS["pink"]["bow"], WAYS["pink"]["bowd"])
c.setFillColor(GREEN); c.setFont("gm-serifI", 38); c.drawCentredString(PW / 2, PH - 280, "You just made my day!")
paras = ["Thank you for choosing a small, one-person shop over the big guys.",
         "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.",
         "How: Etsy app > You > Purchases > Leave a review",
         "Something not right? Message me first and I'll fix it fast."]
y = PH - 350
for t in paras:
    if t.startswith("How:"):
        c.setFont(d.FM, 14); c.setFillColor(d.D); c.drawCentredString(PW / 2, y, t); y -= 48; continue
    for ln in gs.wrap(t, d.SS, 15, PW - 2 * gs.MARGIN - 80):
        c.setFont(d.SS, 15); c.setFillColor(d.INK); c.drawCentredString(PW / 2, y, ln); y -= 23
    y -= 26
c.setStrokeColor(GREEN); c.setLineWidth(0.8); c.line(PW / 2 - 60, y, PW / 2 + 60, y); y -= 34
c.setFillColor(GREEN); c.setFont("gm-serifI", 20); c.drawCentredString(PW / 2, y, "With thanks,"); y -= 24
c.setFont(d.SB, 17); c.drawCentredString(PW / 2, y, "GM's Digital Creations")
c.setFillColor(WAYS["sage"]["stripe"])
for i in range(0, 40, 2): c.rect(i * 22.5, 0, 22.5, 60, stroke=0, fill=1)
c.showPage()
d.save()
print("built", OUT, d.page)
