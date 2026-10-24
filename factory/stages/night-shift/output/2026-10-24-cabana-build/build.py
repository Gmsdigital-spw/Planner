"""Pink Cabana Stripe Birthday Invitation: cover, how-to, 2 colourways x (invite + details card), thank-you."""
import sys, math, random
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.pagesizes import letter, landscape

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cabana_raw.pdf"
NAME = "Pink Cabana Birthday Invitation"
pal = gs.palette("blush")
d = gs.Book(OUT, NAME, pal, cover_style="frame", page_frame="none")
c = d.c
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

def field(name, cx, y, w, h, value, size, fontName="Times-Roman", tip=None):
    c.acroForm.textfield(name=name, tooltip=tip or name, x=cx - w / 2, y=y, width=w, height=h,
                         value=value, fontName=fontName, fontSize=size, borderWidth=0, borderStyle="underlined",
                         fillColor=None, borderColor=None, textColor=GREEN, fieldFlags="", forceBorder=False, maxlen=60)

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
    field(f"{way}{k}_name", cx, top - 184, pw - 40, 30, "Ava's Sweet Sixteen", 21, "Times-Italic", "Name and age")
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
        spaced(cx, yy, head, 7.6, GREEN2, d.FM, 2.0)
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
d.cover(["Pink Cabana", "Birthday Invitation"], "Editable 5x7 invite and details card in two colourways", pages=6, kicker="EDITABLE PDF INVITATION")

d.start("How to edit and print", "Everything you need to fill in your details and print at home or at a print shop.")
d.heading("Edit your invitation")
d.bullets(["Download the PDF to a computer and open it in Adobe Acrobat Reader (free). A browser preview may not save your typing.",
           "Click any green line of text on pages 3 to 6 and type over the sample words. Every changing line is its own box.",
           "Each card on a page is separate, so you can make two different versions on one sheet if you want to.",
           "Save the file (File, Save As) before printing. Keep the original as a clean copy for next time.",
           "The headline, stripes, bow and leaves are part of the design. Fonts and colours cannot be changed."], numbered=True)
d.heading("Print and cut")
d.bullets(["Print at 100% or Actual size on US Letter paper, landscape. A4 also works at Actual size.",
           "Use white cardstock (80 to 110 lb) for a sturdy card, or ask a local print shop to print it for you.",
           "Cut on the light grey corner marks with a paper trimmer for straight edges. Each card is 5 x 7 inches.",
           "Standard A7 envelopes (5.25 x 7.25 in) fit both the invitation and the details card."], numbered=True)
d.heading("What's inside")
d.bullets(["Page 3: invitation, pink cabana stripe (2 per page)", "Page 4: invitation, sage cabana stripe (2 per page)",
           "Page 5: details card, pink cabana stripe (2 per page)", "Page 6: details card, sage cabana stripe (2 per page)"], cols=1, check=True)
d.heading("Wording ideas for the name line")
d.bullets(["Ava's Sweet Sixteen", "Mia Turns Seven", "Chloe's 21st Birthday", "Thirty and Thriving, Emma",
           "Grace is Turning 40", "Lily's First Birthday"], cols=3)
d.heading("Before you print")
d.bullets(["Every line typed and spelled right (check the date and the RSVP number twice)",
           "One test print on plain paper to check the size and the cut marks",
           "Printer set to Actual size, best quality, landscape"], check=True)
d.heading("Good to know")
d.text("Digital file only: no printed cards ship. For personal use. Keep lines short to fit the card.")
d.end()

card_page(invite, "pink", "Invitation · pink cabana")
card_page(invite, "sage", "Invitation · sage cabana")
card_page(details, "pink", "Details card · pink cabana")
card_page(details, "sage", "Details card · sage cabana")

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
         "How: Etsy app → You → Purchases → Leave a review",
         "Something not right? Message me first and I'll fix it fast."]
y = PH - 350
for t in paras:
    if t.startswith("How:"):
        c.setFont("DejaVu", 14); c.setFillColor(d.D); c.drawCentredString(PW / 2, y, t); y -= 48; continue
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
