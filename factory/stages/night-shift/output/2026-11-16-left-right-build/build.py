"""Build the Left Right Christmas Game PDF. python3 build.py [out.pdf]
Pages: 1 cover, 2 how to play, 3 host guide, 4-9 six big-type host cards, 10 type-in names story,
11-16 TV screen version (16:9 slides), 17 thank-you (not counted)."""
import sys, re, math
HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, HERE)
import gm_style as gs
from content import STORIES, TYPEIN, TYPEIN_ROLES
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else HERE + "/left-right-christmas-game.pdf"
PAL = gs.palette("cranberry")
NAME = "Left Right Christmas Game  ·  6 Stories"
d = gs.Book(OUT, NAME, PAL, cover_style="band", page_frame="stripe")
c = d.c
PW, PH, M = 612, 792, gs.MARGIN
L, R = M, PW - M
W = R - L
PAPER = HexColor(PAL["paper"])
GREEN = HexColor("#2F5D4A")
FOOT_RULE = M - 1
CLEAR = 18
BOTTOM = FOOT_RULE + CLEAR + 1.5
PAD = 22
HEAD = 40
BOXES = []
PAGE_H = {}
pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
CARD_N = [1 if s.get('short') else 2 for s in STORIES]
CARD_FIRST = [4 + sum(CARD_N[:i]) for i in range(6)]
TYPE_P = 4 + sum(CARD_N)
TV_FIRST = TYPE_P + 1
CONTENT_PAGES = TV_FIRST + 5
TV_W, TV_H = 960, 540
FIELDS = []


def reg(name, x, yb, w, h, r=8):
    BOXES.append((c.getPageNumber(), name, x, yb, w, h, r))


def minutes(t):
    """Read-aloud time: 130 words a minute plus a 2-second pause per cue (LEFT, RIGHT, STEAL)."""
    w = len(t.split()); cues = len(re.findall(r"\b(LEFT|RIGHT|STEAL)\b", t))
    return w / 130 + cues * 2 / 60


def mins(t):
    return max(1, round(minutes(t)))


def cues(t, word):
    return len(re.findall(r"\b%s\b" % word, t))


def para(x, y, text, width, size=10, font=None, color=None, lead=1.42):
    c.setFillColor(color or d.INK); c.setFont(font or d.F, size)
    for ln in gs.wrap(text, font or d.F, size, width):
        c.drawString(x, y - size, ln); y -= size * lead
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


# ------------------------------------------------------------------ rich text: LEFT / RIGHT / STEAL in bold colour
CUE = {"LEFT": None, "RIGHT": None, "STEAL": None}


def tokens(par):
    out = []
    for w in par.split():
        m = re.match(r"^([^A-Za-z{]*)(LEFT|RIGHT|STEAL|\{\d\})([^A-Za-z]*)$", w)
        if m:
            if m.group(1): out.append((m.group(1), "t", False))
            out.append((m.group(2), "f" if m.group(2).startswith("{") else "c", not m.group(1)))
            if m.group(3): out.append((m.group(3), "t", True))
        else:
            out.append((w, "t", False))
    return out  # (text, kind, glued_to_previous)


def layout(par, size, width, field_w=0):
    """Return lines of [(text, kind, x_offset, w)]."""
    toks = tokens(par)
    sp = stringWidth(" ", d.F, size)
    lines, cur, x = [], [], 0.0
    # group glued tokens into words
    words = []
    for t, k, glue in toks:
        if words and glue and k == "t" and words[-1][-1][1] != "t" or (words and glue and words[-1] and k != "t" and False):
            words[-1].append((t, k))
        elif words and k == "t" and glue:
            words[-1].append((t, k))
        else:
            words.append([(t, k)])
    for wd in words:
        ww = sum(field_w if k == "f" else stringWidth(t, d.FB if k == "c" else d.F, size) for t, k in wd)
        nx = x + (sp if cur else 0)
        if cur and nx + ww > width:
            lines.append(cur); cur, x, nx = [], 0.0, 0.0
        xx = nx
        for t, k in wd:
            tw = field_w if k == "f" else stringWidth(t, d.FB if k == "c" else d.F, size)
            cur.append((t, k, xx, tw)); xx += tw
        x = xx
    if cur: lines.append(cur)
    return lines


def story_height(text, size, width, lead, pgap, field_w=0):
    pars = [p for p in text.strip().split("\n\n")]
    n = sum(len(layout(p, size, width, field_w)) for p in pars)
    return n * size * lead + (len(pars) - 1) * pgap, n


def draw_story(x, y, text, size, width, lead, pgap, field_w=0, cue_col=None, field_cb=None, hilite=True):
    for p in text.strip().split("\n\n"):
        for ln in layout(p, size, width, field_w):
            base = y - size
            for t, k, xo, tw in ln:
                if k == "c":
                    if hilite:
                        c.setFillColor(d.T); c.roundRect(x + xo - 2, base - size * 0.24, tw + 4, size * 1.08, 2.5, fill=1, stroke=0)
                    c.setFillColor(GREEN if t == "STEAL" else (cue_col or d.P)); c.setFont(d.FB, size); c.drawString(x + xo, base, t)
                elif k == "f":
                    field_cb(t, x + xo, base, tw, size)
                else:
                    c.setFillColor(d.INK); c.setFont(d.F, size); c.drawString(x + xo, base, t)
            y -= size * lead
        y -= pgap
    return y


def chips(y, items, size=9.5):
    ws = [stringWidth(t, d.FM, size) + 26 for t in items]
    gap = 10
    x = PW / 2 - (sum(ws) + gap * (len(ws) - 1)) / 2
    for t, w in zip(items, ws):
        c.setFillColor(d.T); c.setStrokeColor(d.P); c.setLineWidth(0.8)
        c.roundRect(x, y - 24, w, 24, 12, fill=1, stroke=1)
        c.setFillColor(d.D); c.setFont(d.FM, size); c.drawCentredString(x + w / 2, y - 16, t)
        x += w + gap
    return y - 24


# ================================================================== page 1: cover
d.page += 1; PAGE_H[1] = PH
c.setFillColor(PAPER); c.rect(0, 0, PW, PH, fill=1, stroke=0)
BAND = PH * 0.50
c.setFillColor(d.P); c.rect(0, BAND, PW, PH - BAND, fill=1, stroke=0)
c.setFillColor(d.A); c.rect(0, BAND - 5, PW, 5, fill=1, stroke=0)
d._spaced(PW / 2, PH - 92, "PRINTABLE CHRISTMAS PARTY GAME", 11, white, d.FM)
c.setFillColor(white); c.setFont(d.S, 66); c.drawCentredString(PW / 2, PH - 186, "Left Right")
c.drawCentredString(PW / 2, PH - 258, "Christmas Game")
c.setFont(d.SB, 24); c.setFillColor(HexColor("#F7E9D2")); c.drawCentredString(PW / 2, PH - 312, "6 Pass the Gift Stories")
c.setFont(d.F, 12.5); c.setFillColor(white)
c.drawCentredString(PW / 2, PH - 344, "Read a story. Pass the gift on every LEFT and RIGHT.")
c.drawCentredString(PW / 2, PH - 362, "Whoever holds a gift at the end keeps it.")
# three format tiles: the gap
ty = BAND - 34
tw_, tg = 152, 14
tx = PW / 2 - (3 * tw_ + 2 * tg) / 2
for i, (a, b) in enumerate([("Big-type", "host cards"), ("TV screen", "version"), ("Type-in", "names story")]):
    x = tx + i * (tw_ + tg)
    c.setFillColor(white); c.setStrokeColor(d.P); c.setLineWidth(1.2); c.roundRect(x, ty - 74, tw_, 74, 10, fill=1, stroke=1)
    reg("cover tile", x, ty - 74, tw_, 74, 10)
    c.setFillColor(d.P); c.setFont(d.S, 18); c.drawCentredString(x + tw_ / 2, ty - 33, a)
    c.setFillColor(d.INK); c.setFont(d.F, 11.5); c.drawCentredString(x + tw_ / 2, ty - 53, b)
# story list
py_ = ty - 74 - 22
ph_ = 168
c.setFillColor(white); c.setStrokeColor(d.HAIR); c.setLineWidth(0.9); c.roundRect(L + 10, py_ - ph_, W - 20, ph_, 10, fill=1, stroke=1)
reg("cover stories", L + 10, py_ - ph_, W - 20, ph_, 10)
d._spaced(PW / 2, py_ - 30, "THE 6 STORIES", 9.5, d.P, d.FM)
colx = [L + 40, PW / 2 + 10]
for i, s in enumerate(STORIES):
    col, row = i // 3, i % 3
    yy = py_ - 62 - row * 34
    c.setFillColor(d.T); c.circle(colx[col] + 9, yy + 4, 11, fill=1, stroke=0)
    c.setFillColor(d.P); c.setFont(d.FM, 10); c.drawCentredString(colx[col] + 9, yy, str(i + 1))
    c.setFillColor(d.INK); c.setFont(d.FM, 10.5); c.drawString(colx[col] + 28, yy + 4, s["title"])
    c.setFillColor(d.MUT); c.setFont(d.F, 8.6); c.drawString(colx[col] + 28, yy - 8, s["crowd"])
COVER_PANEL_BOTTOM = py_ - ph_
d._spaced(PW / 2, 62, f"{CONTENT_PAGES} PAGES  ·  PRINT AT HOME OR PLAY ON A TV  ·  INSTANT DOWNLOAD", 8.5, d.MUT, d.FM)
c.setFont(d.F, 8.5); c.setFillColor(d.MUT); c.drawCentredString(PW / 2, 42, "GM's Digital Creations")
c.showPage()

# ================================================================== pages 2-3: how to play + host guide
SZ = 10.2
GAP = 12


def num_h(items, width, size=SZ, gap=6):
    return sum(para_h(t, width - 24, size, lead=1.4) + gap for t in items) - gap


def num_draw(x, y, items, width, size=SZ, gap=6, numbered=True):
    for i, t in enumerate(items, 1):
        if numbered:
            c.setFillColor(d.T); c.circle(x + 8.5, y - size * 0.42, 9, fill=1, stroke=0)
            c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawCentredString(x + 8.5, y - size * 0.42 - 3.2, str(i))
        else:
            c.setFillColor(d.A); c.circle(x + 4, y - size * 0.62, 2.5, fill=1, stroke=0)
        y = para(x + 24, y, t, width - 24, size, lead=1.4) - gap
    return y


def stack(cards, top):
    """cards: [(title, items, numbered, fill)]; fills the page down to BOTTOM by spreading the spare height between items."""
    iw = W - 2 * PAD
    base = [HEAD + PAD + num_h(it, iw, gap=6) + PAD - 2 for _, it, _, _ in cards]
    spare = (top - BOTTOM) - sum(base) - GAP * (len(cards) - 1)
    gaps = sum(len(it) - 1 for _, it, _, _ in cards) + len(cards)
    assert spare >= 0, ("page overflow", spare)
    extra = spare / gaps
    assert extra < 22, ("page too empty", spare)
    y = top
    for (t, it, numbered, fill), h0 in zip(cards, base):
        h = h0 + extra * len(it)
        yy = card(L, y, W, h, t, fill=fill or white) - extra / 2
        num_draw(L + PAD, yy, it, iw, gap=6 + extra, numbered=numbered)
        y -= h + GAP
    return spare


d.start("How to Play", None, kicker="Start here  ·  4 to 40 players  ·  no prep", centered=True); PAGE_H[d.page] = PH
steps = ["Everyone sits in a circle. Each player holds one wrapped gift. Big group? Spread 4 to 6 gifts around the circle instead.",
         "The host reads one story out loud, slowly. The host does not pass.",
         "Every time you hear LEFT, pass the gift you are holding to your left. Every time you hear RIGHT, pass it to your right. Wrong way? Laugh and keep going.",
                  "When the story ends, the gift in your hands is yours to keep."]
twists = ["Steal twist (story 5): on the word STEAL, swap gifts with the player sitting across from you.",
          "Double round: play two stories back to back. Only the end of the second story decides who keeps a gift.",
          "Elimination: anyone who passes the wrong way twice moves to the middle and helps the host spot mistakes."]
tips = ["Read a little slower than normal and pause half a second after each LEFT and RIGHT.",
        "Office or school party? Use small gifts or candy bags so nobody worries about who wins.",
        f"Story 6 is the shortest ({len(STORIES[5]['text'].split())} words, {cues(STORIES[5]['text'], 'LEFT') + cues(STORIES[5]['text'], 'RIGHT')} passes, about {mins(STORIES[5]['text'])} minutes read aloud; the others take about {min(mins(s['text']) for s in STORIES[:5])} to {max(mins(s['text']) for s in STORIES[:5])}): a good warm-up, or the one to pick when the kids can't sit still."]
sp = stack([("The rules", steps, True, None), ("Twists to try", twists, False, None), ("Host tips", tips, False, PAPER)], d.y)
print("how-to spare %.0f" % sp)
d.end()

d.start("Host Guide", "Pick a story for your crowd, then choose paper, TV or type-in names.", kicker="Choose your story", centered=True); PAGE_H[d.page] = PH
rows = []
for i, s in enumerate(STORIES):
    t = s["text"]
    rows.append((str(i + 1), s["title"], s["crowd"], f"{mins(t)} min", str(cues(t, 'LEFT') + cues(t, 'RIGHT')), (f"{CARD_FIRST[i]}-{CARD_FIRST[i] + 1}" if CARD_N[i] == 2 else str(CARD_FIRST[i])), str(TV_FIRST + i)))
tvw = [f"Host cards, pages 4 to {TYPE_P - 1}: big type, so you can read them in a dim room. Print only the stories you want.",
       f"TV screen version, pages {TV_FIRST} to {TV_FIRST + 5}: open this PDF on a laptop or tablet connected to your TV and switch to full screen. Everyone reads along, and nobody needs to print.",
       f"Type-in names, page {TYPE_P}: open the PDF in the free Adobe Acrobat Reader, click a box, type a guest's name, then print it or show it on screen. You can also print it blank and write the names in.",
       "What you need: one wrapped gift per player (or a few for a big group), one person to read, and a circle of chairs or a spot on the floor."]
iw = W - 2 * PAD
hw = HEAD + PAD + num_h(tvw, iw) + PAD - 2
top = d.y
th = top - BOTTOM - GAP - hw
RH = (th - HEAD - 8 - 18 - 10) / len(rows)
assert 26 <= RH <= 44, ("table rows", RH)
yy = card(L, top, W, th, "Pick your story")
hd = ["#", "Story", "Best for", "Time", "Passes", "Card", "TV"]
# fix round 3: columns placed from measured widths so EVERY column gap (header and every row) is 18 pt+
COLF = lambda j: (d.FM, 9.9) if j == 1 else (d.F, 9.2)
G_ = 18.5
cw_ = [max([stringWidth(hd[j].upper(), d.FM, 7.8)] + [stringWidth(r_[j], *COLF(j)) for r_ in rows]) for j in range(7)]
xR_ = L + W - PAD
x5_ = xR_ - cw_[6] - G_ - cw_[5]; x4_ = x5_ - G_ - cw_[4]; x3_ = x4_ - G_ - cw_[3]
x1_ = L + PAD + cw_[0] + G_; x2_ = x1_ + cw_[1] + G_
cx_ = [L + PAD, x1_, x2_, x3_, x4_, x5_, xR_]
BEST_W = x3_ - G_ - x2_
yy = top - HEAD - 8
c.setFont(d.FM, 7.8); c.setFillColor(d.MUT)
for j, (xx, t) in enumerate(zip(cx_, hd)):
    (c.drawRightString if j == 6 else c.drawString)(xx, yy - 10, t.upper())
yy -= 18


def col_gaps(cells, wfn):
    """Gaps in pt between the end of each cell and the start of the next one (TV column is right-aligned)."""
    ends = [cx_[j] + wfn(j, cells[j]) for j in range(6)]
    starts = [cx_[j] for j in range(1, 6)] + [cx_[6] - wfn(6, cells[6])]
    return [round(starts[j] - ends[j], 2) for j in range(6)]


ALL_GAPS = [col_gaps([h.upper() for h in hd], lambda j, t: stringWidth(t, d.FM, 7.8))]
for r_ in rows:
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.5); c.line(L + PAD, yy, L + W - PAD, yy)
    for j, (xx, t) in enumerate(zip(cx_, r_)):
        f = d.FM if j == 1 else d.F
        sz = 9.9 if j == 1 else 9.2
        if j == 2:
            ln = gs.wrap(t, f, sz, BEST_W)
            c.setFont(f, sz); c.setFillColor(d.INK)
            assert len(ln) * 12 <= RH + 2, ("best-for wraps too deep", t, ln, RH)
            for k, l_ in enumerate(ln): c.drawString(xx, yy - RH / 2 - 3 + (len(ln) - 1) * 6 - k * 12, l_)
            continue
        c.setFont(f, sz); c.setFillColor(d.P if j == 0 else d.INK)
        (c.drawRightString if j == 6 else c.drawString)(xx, yy - RH / 2 - 3, t)
    ALL_GAPS.append(col_gaps(r_, lambda j, t: max(stringWidth(l_, *COLF(j)) for l_ in gs.wrap(t, *COLF(j), BEST_W)) if j == 2 else stringWidth(t, *COLF(j))))
    yy -= RH
assert min(min(g) for g in ALL_GAPS) >= 18, ("host guide column gap under 18 pt", ALL_GAPS)
print("host guide min column gap pt", min(min(g) for g in ALL_GAPS), "(every gap, header + 6 rows; CARD-TV min", min(g[5] for g in ALL_GAPS), ")")
yy = card(L, top - th - GAP, W, hw, "Three ways to play: paper, TV or type-in", fill=PAPER)
num_draw(L + PAD, yy, tvw, iw, numbered=False)
d.end()

# ================================================================== pages 3-8: big-type host cards
STORY_PAGE = {}
STORY_PAGES = {}
STORY_SIZE = {}
CARD_FILL = {}


def para_lines(text, size, width, field_w=0):
    return [(pi, ln) for pi, p in enumerate(text.strip().split("\n\n")) for ln in layout(p, size, width, field_w)]


def lines_h(lns, size, lead, pgap):
    h, prev = 0.0, None
    for pi, _ in lns:
        if prev is not None and pi != prev: h += pgap
        h += size * lead; prev = pi
    return h


def draw_lines(x, y, lns, size, lead, pgap, hilite=True, field_cb=None):
    prev = None
    for pi, ln in lns:
        if prev is not None and pi != prev: y -= pgap
        base = y - size
        for t, k, xo, tw in ln:
            if k == "c":
                if hilite:
                    c.setFillColor(d.T); c.roundRect(x + xo - 2, base - size * 0.24, tw + 4, size * 1.08, 2.5, fill=1, stroke=0)
                c.setFillColor(GREEN if t == "STEAL" else d.P); c.setFont(d.FB, size); c.drawString(x + xo, base, t)
            elif k == "f":
                field_cb(t, x + xo, base, tw, size)
            else:
                c.setFillColor(d.INK); c.setFont(d.F, size); c.drawString(x + xo, base, t)
        y -= size * lead; prev = pi
    return y


def card_page(i, s, part, nparts):
    """Start a host-card page; returns (box_top, note) for the text card."""
    t = s["text"]
    kick = f"Story {i + 1} of 6  ·  {s['crowd']}" + (f"  ·  card {part} of {nparts}" if nparts > 1 else "")
    d.start(s["title"] + (" (continued)" if part > 1 else ""), None, kicker=kick, centered=True); PAGE_H[d.page] = PH
    STORY_PAGES.setdefault(i, []).append(d.page)
    if part == 1:
        STORY_PAGE[i] = d.page
        nL, nR = cues(t, "LEFT"), cues(t, "RIGHT")
        items = [f"About {mins(t)} min", f"{nL + nR} passes", s["ages"]]
        if s.get("steal"): items.append(f"{cues(t, 'STEAL')} STEAL twists")
        return chips(d.y + 4, items) - 14
    return d.y - 4


inner_w = W - 2 * PAD
NOTE = "Twist: on the word STEAL, swap gifts with the player sitting across from you."
for i, s in enumerate(STORIES):
    t = s["text"]
    n = CARD_N[i]
    # measure page tops without drawing: a scratch canvas would be overkill, so use the kit's known header heights
    note_h = para_h(NOTE, inner_w - 24, 10.5, d.FM, 1.35) + 20 + 12 if s.get("steal") else 0
    tops = []
    lead = 1.40
    # page 1
    box_top = card_page(i, s, 1, n)
    A = [box_top - BOTTOM - 2 * PAD - note_h]
    if n == 2:
        A.append(A[0] + note_h + 25)
        A[0] -= 18   # room for the 'continues' line inside the card   # page 2 has no chips row: 25 to 37 pt more room (asserted below)
    size = 20.0
    while True:
        pgap = size * 0.55
        L_ = para_lines(t, size, inner_w)
        hs = [lines_h(L_[:j + 1], size, lead, pgap) for j in range(len(L_))]
        k = max([j + 1 for j, h in enumerate(hs) if h <= A[0]] or [0])
        if n == 2:
            # prefer a paragraph break if page 1 stays 85%+ full
            for kb in range(k, 0, -1):
                if L_[kb][0] != L_[kb - 1][0] if kb < len(L_) else True:
                    if hs[kb - 1] >= 0.80 * A[0]: k = kb
                    break
            ok = k > 0 and lines_h(L_[k:], size, lead, pgap) <= A[1]
        else:
            ok = k == len(L_)
        if ok or size <= 14: break
        size -= 0.25
    assert ok and size >= 15, ("host card overflow or too small", s["title"], size)
    STORY_SIZE[i] = size
    parts = [L_[:k], L_[k:]] if n == 2 else [L_]
    fills = []
    for part, lns in enumerate(parts, 1):
        if part > 1:
            box_top = card_page(i, s, part, n)
            assert box_top - BOTTOM - 2 * PAD >= A[1] - 0.5, ("page 2 room", box_top - BOTTOM - 2 * PAD, A[1])
            A[1] = box_top - BOTTOM - 2 * PAD
        av = A[part - 1]
        h0 = lines_h(lns, size, lead, pgap)
        npar = len(set(pi for pi, _ in lns)) - 1
        pg2 = pgap + (min((av - h0) / npar, size * 1.2) if npar else 0)
        hh = lines_h(lns, size, lead, pg2)
        yy = card(L, box_top, W, box_top - BOTTOM)
        if note_h and part == 1:
            nh = note_h - 12
            c.setFillColor(HexColor("#E6EFE9")); c.roundRect(L + PAD, yy - nh, inner_w, nh, 6, fill=1, stroke=0)
            para(L + PAD + 12, yy - 10, NOTE, inner_w - 24, 10.5, d.FM, GREEN, 1.35)
            yy -= note_h
        yy -= (av - hh) / 2
        draw_lines(L + PAD, yy, lns, size, lead, pg2)
        fills.append(round(hh / av * 100, 1))
        if part == 1 and n == 2:
            c.setFillColor(d.P); c.setFont(d.FM, 9); c.drawRightString(R - PAD, BOTTOM + PAD + 1, "Story continues on the next page  >")
        d.end()
    CARD_FILL[i] = fills
    print(f"story {i + 1}: {size:.2f} pt on {n} page(s), text fills {fills}% of the card")

# ================================================================== page 9: type-in names version
from reportlab.lib.colors import Color
d.start("Your Family, Your Story", "Type 6 names into the boxes, then print it or play it on screen. Or print it blank and write the names in.",
        kicker="Type-in names version  ·  story 1 remix", centered=True); PAGE_H[d.page] = PH
TYPE_PAGE = d.page
box_top = d.y - 4
inner_w = W - 2 * PAD
FW = 150
FS = 12


def field_cb(t, x, base, tw, size):
    n = int(t[1:-1])
    c.setStrokeColor(d.P); c.setLineWidth(0.9); c.line(x, base - 3, x + tw, base - 3)
    c.setFillColor(d.MUT); c.setFont(d.F, 7.2); c.drawCentredString(x + tw / 2, base - 11, TYPEIN_ROLES[n - 1].lower())
    c.acroForm.textfield(name=f"name{n}", tooltip=f"Name {n}: {TYPEIN_ROLES[n - 1]}", x=x, y=base - 2.2, width=tw, height=size + 4.5,
                         fontName="Times-Roman", fontSize=FS, borderWidth=0, fillColor=Color(0.96, 0.894, 0.902, alpha=0),
                         textColor=d.D, forceBorder=False, maxlen=24, value="")
    FIELDS.append((n, x, base, tw))


avail = box_top - BOTTOM - 2 * PAD
lead, size = 2.0, 14.5
while True:
    pgap = size * 0.5
    hh, nlines = story_height(TYPEIN, size, inner_w, lead, pgap, FW)
    if hh <= avail or size <= 11: break
    size -= 0.25
assert hh <= avail, ("type-in overflow", hh, avail)
npar = TYPEIN.strip().count("\n\n")
pgap += min((avail - hh) / npar, size)
hh2, _ = story_height(TYPEIN, size, inner_w, lead, pgap, FW)
print(f"type-in: size {size:.2f}, {nlines} lines, spare {avail - hh2:.0f}")
yy = card(L, box_top, W, box_top - BOTTOM)
yy -= (avail - hh2) / 2
draw_story(L + PAD, yy, TYPEIN, size, inner_w, lead, pgap, FW, field_cb=field_cb)
assert sorted(f[0] for f in FIELDS) == [1, 2, 3, 4, 5, 6], FIELDS
d.end()

# ================================================================== pages 10-16: TV screen version (16:9)
c.setPageSize((TV_W, TV_H))
TM = 48


def tv_frame(kicker, title):
    d.page += 1; PAGE_H[d.page] = TV_H
    c.setFillColor(PAPER); c.rect(0, 0, TV_W, TV_H, fill=1, stroke=0)
    c.setFillColor(d.P); c.rect(0, TV_H - 92, TV_W, 92, fill=1, stroke=0)
    c.setFillColor(d.A); c.rect(0, TV_H - 96, TV_W, 4, fill=1, stroke=0)
    c.setFillColor(HexColor("#F7E9D2")); c.setFont(d.FM, 11); c.drawString(TM, TV_H - 34, kicker.upper())
    c.setFillColor(white); size = 34
    while stringWidth(title, d.S, size) > TV_W - 2 * TM - 260: size -= 1
    c.setFont(d.S, size); c.drawString(TM, TV_H - 74, title)
    c.setFillColor(white); c.setFont(d.FM, 13)
    c.drawRightString(TV_W - TM, TV_H - 52, "LEFT = pass left   ·   RIGHT = pass right")
    c.setFillColor(d.MUT); c.setFont(d.F, 9.5); c.drawString(TM, 18, "Left Right Christmas Game  ·  TV screen version")
    c.drawRightString(TV_W - TM, 18, f"{d.page:02d}")


TV_PAGE = {}
TV_FILL = {}
for i, s in enumerate(STORIES):
    t = s["text"]
    tv_frame(f"Story {i + 1} of 6  ·  {s['crowd']}", s["title"])
    TV_PAGE[i] = d.page
    colw = (TV_W - 2 * TM - 40) / 2
    top_ = TV_H - 120
    avail = top_ - 40
    lead, size = 1.30, 30.0
    pars = t.strip().split("\n\n")

    def flow(size):
        """Lines of every paragraph in reading order; a paragraph gap is half a line. Returns [(par index, line)]."""
        out = []
        for pi, p in enumerate(pars):
            for ln in layout(p, size, colw):
                out.append((pi, ln))
        return out

    def col_split(lines, size):
        step = size * lead; pg = size * 0.5
        hs, y, prev = [], 0.0, None
        for pi, ln in lines:
            if prev is not None and pi != prev: y += pg
            y += step; hs.append(y); prev = pi
        return hs

    while True:
        lines = flow(size)
        hs = col_split(lines, size)
        # first column takes as many lines as fit; the second column gets the rest (re-based)
        k = max(j + 1 for j, h in enumerate(hs) if h <= avail)
        rest = lines[k:]
        h2 = col_split(rest, size)[-1] if rest else 0
        if h2 <= avail or size <= 12: break
        size -= 0.25
    assert h2 <= avail and size >= 14, ("tv overflow or too small", s["title"], size)
    # balance: move lines from column 1 to column 2 while column 2 stays inside the box
    while True:
        r2 = lines[k - 1:]
        if k <= 1 or col_split(r2, size)[-1] > avail or col_split(lines[:k - 1], size)[-1] < col_split(r2, size)[-1]: break
        k -= 1
    h1 = col_split(lines[:k], size)[-1]; h2 = col_split(lines[k:], size)[-1]
    print(f"tv {i + 1}: size {size:.2f}, columns end at {h1 / avail * 100:.0f}% and {h2 / avail * 100:.0f}% of the text area")
    STORY_SIZE[f"tv{i}"] = size
    TV_FILL[i] = (round(h1 / avail * 100, 1), round(h2 / avail * 100, 1))

    def draw_lines(x, y, lns):
        prev = None
        for pi, ln in lns:
            if prev is not None and pi != prev: y -= size * 0.5
            base = y - size
            for tt, kk, xo, tw in ln:
                if kk == "c":
                    c.setFillColor(GREEN if tt == "STEAL" else d.P); c.setFont(d.FB, size); c.drawString(x + xo, base, tt)
                else:
                    c.setFillColor(d.INK); c.setFont(d.F, size); c.drawString(x + xo, base, tt)
            y -= size * lead; prev = pi
    # vertical centring of the pair so both columns sit in the text area
    if s.get("steal"):   # fix round 3: the STEAL rule line from the host card, in the strip between the band and the text area
        c.setFillColor(GREEN); c.setFont(d.FM, 12); c.drawString(TM, TV_H - 110.5, NOTE)
        assert stringWidth(NOTE, d.FM, 12) <= TV_W - 2 * TM, "tv steal note too wide"
    draw_lines(TM, top_, lines[:k])
    draw_lines(TM + colw + 40, top_, lines[k:])
    c.setStrokeColor(d.HAIR); c.setLineWidth(0.8); c.line(TV_W / 2, top_, TV_W / 2, 50)
    c.showPage()

# ================================================================== page 17: thank-you
c.setPageSize((PW, PH))
d.page += 1; PAGE_H[d.page] = PH
d._frame()
y0 = PH - 230
c.setFillColor(d.P); c.setFont(d.FM, 10); d._spaced(PW / 2, y0 + 40, "LEFT RIGHT CHRISTMAS GAME", 10, d.P, d.FM)
c.setFillColor(d.D); c.setFont(d.S, 40); c.drawCentredString(PW / 2, y0 - 10, "You just made my day!")
d._ornament(PW / 2, y0 - 36)


def para_c(y, text, width, size=14.5, font=None, lead=1.55):
    c.setFillColor(d.INK); c.setFont(font or d.SS, size)
    for ln in gs.wrap(text, font or d.SS, size, width):
        c.drawCentredString(PW / 2, y - size, ln); y -= size * lead
    return y


y = para_c(y0 - 66, "Thank you for choosing a small, one-person shop over the big guys.", 370) - 26
y = para_c(y, "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.", 360) - 34
bw = 460
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
y -= 60 + 40
y = para_c(y, "Something not right? Message me first and I'll fix it fast.", 440) - 60
c.setFillColor(d.P); c.setFont(d.SB, 14); c.drawCentredString(PW / 2, y - 6, "With thanks,")
c.setFillColor(d.D); c.setFont(d.S, 18); c.drawCentredString(PW / 2, y - 30, "GM's Digital Creations")
c.showPage()
d.save()
print("built", OUT)

# ================================================================== verification by code
import subprocess, json
RAW = OUT
from pypdf import PdfReader
rd = PdfReader(OUT)
assert len(rd.pages) == CONTENT_PAGES + 1, len(rd.pages)
sizes = [(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in rd.pages]
assert all(sizes[i] == (612, 792) for i in list(range(TYPE_P)) + [CONTENT_PAGES]), sizes
assert all(sizes[i] == (960, 540) for i in range(TYPE_P, TYPE_P + 6)), sizes
txt = subprocess.run(["pdftotext", OUT, "-"], capture_output=True, text=True).stdout.split("\f")
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'")).strip()
for i, s in enumerate(STORIES):
    body = norm(s["text"])
    for pgs in (STORY_PAGES[i], [TV_PAGE[i]]):
        if pgs[0] >= TV_FIRST:   # two text columns: read the left half, then the right half
            half = lambda x0, pg: subprocess.run(["pdftotext", "-f", str(pg), "-l", str(pg), "-x", str(x0), "-y", "0", "-W", "480", "-H", "540", OUT, "-"],
                                                 capture_output=True, text=True).stdout
            got = norm(half(0, pgs[0]) + " " + half(480, pgs[0]))
        else:
            got = " ".join(norm(txt[pg - 1]) for pg in pgs).replace(" (continued)", "")
        # every sentence of the story is on its host card and its TV slide
        # every word of the story, in order, on its host card pages and its TV slide
        want, have, j = norm(s["text"]).split(), got.split(), 0
        for wd in have:
            if j < len(want) and wd == want[j]: j += 1
        assert j == len(want), ("story text missing", s["title"], pgs, " ".join(want[j:j + 8]))
        assert got.count("LEFT") >= cues(s["text"], "LEFT") and got.count("RIGHT") >= cues(s["text"], "RIGHT"), ("cue count", pgs)
# fix round 3: the STEAL rule line is on the story 5 host card AND its TV slide
for i, s in enumerate(STORIES):
    if s.get("steal"):
        assert norm(NOTE) in norm(txt[STORY_PAGE[i] - 1]) and norm(NOTE) in norm(txt[TV_PAGE[i] - 1]), ("steal note missing", STORY_PAGE[i], TV_PAGE[i])
        print("steal note on host card p%d and TV p%d" % (STORY_PAGE[i], TV_PAGE[i]))
# how-to page numbers match where things really are
assert [STORY_PAGE[i] for i in range(6)] == CARD_FIRST and TYPE_PAGE == TYPE_P and [TV_PAGE[i] for i in range(6)] == list(range(TV_FIRST, TV_FIRST + 6))
# the how-to promises
assert f"pages {TV_FIRST} to {TV_FIRST + 5}" in norm(txt[2]) and f"page {TYPE_P}" in norm(txt[2]) and f"pages 4 to {TYPE_P - 1}" in norm(txt[2])
# no stray left/right words that are not cues (bright, alright, write...) in any story
allt = " ".join(s["text"] for s in STORIES) + TYPEIN
stray = [w for w in re.findall(r"\w*(?:left|right|wright|write|rite)\w*", allt, re.I) if w not in ("LEFT", "RIGHT")]
assert not stray, stray
BANNED = ["rudolph", "grinch", "frosty", "jingle", "santa baby", "home alone", "elf", "scrooge", "nutcracker", "disney", "polar express",
          "charlie brown", "snoopy", "billy bass", "mariah", "die hard", "kevin", "buddy", "clark", "griswold", "cindy lou", "whoville",
          "olaf", "frozen", "karen", "lyric", "night before christmas"]
hits = [b for b in BANNED if re.search(r"\b" + b + r"\b", allt.lower())]
assert not hits, ("banned", hits)
# no thank-you counted, spec text verbatim
ty = norm(txt[CONTENT_PAGES])
for line in ["You just made my day!", "Thank you for choosing a small, one-person shop over the big guys.",
             "Quick favor? If this made your party or planning even a little easier, a 30-second review helps the next family find it. I read every single one.",
             "Something not right? Message me first and I'll fix it fast.", "With thanks,", "GM's Digital Creations"]:
    assert norm(line) in ty, ("thank-you text", line)
assert "Etsy app → You → Purchases → Leave a review" in ty, ty
print(f"verify OK: {CONTENT_PAGES + 1} pages ({CONTENT_PAGES} content + thank-you), Letter 1-{TYPE_P} and {CONTENT_PAGES + 1}, 16:9 {TV_FIRST}-{TV_FIRST + 5}; every story sentence on its host card and TV slide;"
      " cue counts", {s["key"]: cues(s["text"], "LEFT") + cues(s["text"], "RIGHT") for s in STORIES}, "; 0 stray words, 0 banned names")
json.dump(dict(boxes=BOXES, page_h=PAGE_H, fields=FIELDS, sizes=STORY_SIZE, tv_fill=TV_FILL), open(HERE + "/boxes.json", "w"))
