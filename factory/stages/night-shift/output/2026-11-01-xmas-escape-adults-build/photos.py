"""Listing photos for the Christmas Escape Room for Adults. python3 photos.py"""
import sys, os
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/christmas-escape-room-adults.pdf"
OUT = HERE + "/photos"; os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("evergreen")
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-xmas-escape-room-adults")
assert len(pages) == 16
# PDF page numbers (1-based) -> index
P = {n: pages[n - 1] for n in range(1, 17)}
COVER_PAGES = [3, 6, 8, 10]        # letter, clock, scale, vault: never repeated in photos 2-5
NEVER = [14]                       # answer key: never shown anywhere (spoilers)
GOLD = (214, 178, 106); WHITE = (255, 255, 255); DEEP = (20, 38, 33)


def grad(size, c1, c2):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        g.putpixel((0, y), tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    im = g.resize((w, h))
    # soft vignette glow behind the pages
    glow = Image.new("L", (w, h), 0); ImageDraw.Draw(glow).ellipse([w * 0.12, -h * 0.2, w * 0.88, h * 0.6], fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    return Image.composite(Image.new("RGB", (w, h), (40, 58, 96)), im, glow)


def font(kind, size): return gs.font(kind, size)


# ------------------------------------------------------------------ 1 cover: page fan on a midnight-evergreen ground, big title + count
def cover():
    """Fix (side-by-side): v1 shared dark-green ground + headline-on-top with the Office Party Games cover.
    v2: midnight navy ground, page fan on top, title block underneath."""
    W, H = 2000, 1500
    im = grad((W, H), (14, 22, 44), (6, 10, 22))
    spec = [(3, 420, -7, 470), (6, 520, -2, 780), (8, 520, 2, 1220), (10, 420, 7, 1468)]
    placed = {}
    top = 50
    for k in [0, 3, 1, 2]:
        n, w, a, cx = spec[k]
        y = top + (40 if k in (0, 3) else 0)
        placed[n] = gs.place(im, P[n], w, (cx - w // 2, y), angle=a, shadow=0.5)
    for n, bb in placed.items():
        assert bb[0] >= 250 and bb[2] <= 1750, ("page outside the centred square", n, bb)
    d = ImageDraw.Draw(im)
    pb = max(bb[3] for bb in placed.values())
    fk = font("sansM", 60)
    yk = pb + 40
    d.text((W / 2, yk), "C H R I S T M A S", font=fk, fill=GOLD, anchor="ma")
    f1 = font("serifB", 230)
    while f1.getlength("Escape Room") > 1400: f1 = font("serifB", f1.size - 4)
    kb = d.textbbox((W / 2, yk), "C H R I S T M A S", font=fk, anchor="ma")
    y1 = kb[3] + 10
    d.text((W / 2, y1), "Escape Room", font=f1, fill=WHITE, anchor="ma")
    b1 = d.textbbox((W / 2, y1), "Escape Room", font=f1, anchor="ma")
    line2 = "for Adults  ·  8 Puzzles"
    f2 = font("serifB", 104)
    while f2.getlength(line2) > 1400: f2 = font("serifB", f2.size - 4)
    y2 = b1[3] + 28
    d.text((W / 2, y2), line2, font=f2, fill=GOLD, anchor="ma")
    boxes = {"kicker": kb, "title": b1, "count": d.textbbox((W / 2, y2), line2, font=f2, anchor="ma")}
    ft = "TEAMS OF 2 TO 20  ·  PRINT AT HOME  ·  HINT CARDS INCLUDED"
    fy = boxes["count"][3] + 36
    d.text((W / 2, fy), ft, font=font("sansM", 36), fill=(170, 186, 210), anchor="ma")
    boxes["facts"] = d.textbbox((W / 2, fy), ft, font=font("sansM", 36), anchor="ma")
    return im, boxes, placed


im, boxes, placed = cover()
gs.save_jpeg(im, OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s = min(im.size); x = (im.width - s) // 2
im.crop((x, 0, x + s, s)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
# measured checks: title + count inside the centred square (x 250-1750); pages share of the square
for k, b in boxes.items():
    assert b[0] >= 250 + 20 and b[2] <= 1750 - 20, (k, b)
th = boxes["title"][3] - boxes["title"][1]
print(f"cover title ink height {th}px = {th / 1500 * 100:.1f}% of height; count line {boxes['count'][3] - boxes['count'][1]}px")
assert th / 1500 >= 0.09, "title under 9% of the cover height"
assert boxes["facts"][3] <= 1480
bxs = sorted(boxes.values(), key=lambda b: b[1])
gaps = [bxs[i + 1][1] - bxs[i][3] for i in range(len(bxs) - 1)]
print("text gaps", gaps)
mask = Image.new("L", (1500, 1500), 0); md = ImageDraw.Draw(mask)
for n, (x0, y0, x1, y1) in placed.items():
    md.rectangle([max(0, x0 - 250), y0, min(1500, x1 - 250), min(1500, y1)], fill=255)
share = sum(mask.histogram()[255:]) / (1500 * 1500)
print(f"pages cover {share * 100:.0f}% of the centred square (bounding boxes)")


# ------------------------------------------------------------------ 2 inside: 6 pages the cover does not show, 470 px each
def inside(idxs, sub):
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    d.text((1000, 60), "What's Inside", font=font("serifB", 92), fill=gs.rgb(PAL["deep"]), anchor="ma")
    d.text((1000, 180), sub, font=font("sans", 42), fill=gs.rgb("#6B6B6B"), anchor="ma")
    w, gx, gy = 470, 60, 36
    x0 = (2000 - (3 * w + 2 * gx)) // 2
    ph = int(w * 1.294)
    for k, n in enumerate(idxs):
        gs.place(im, P[n], w, (x0 + (k % 3) * (w + gx), 262 + (k // 3) * (ph + gy)), shadow=0.22)
    return im


p2 = inside([2, 4, 5, 7, 9, 11], "Host guide, 4 of the 8 linked puzzles and the team lock sheet")
gs.save_jpeg(p2, OUT + "/2-inside.jpg")

# hint page rows: find the white gap between card rows 2 and 3 by scanning the rendered page
def row_gap(page):
    import numpy as np
    a = np.asarray(page.convert("L")).astype(int)
    h = a.shape[0]; xs = slice(int(a.shape[1] * 0.1), int(a.shape[1] * 0.45))
    rows = [y for y in range(int(h * 0.45), int(h * 0.62)) if (a[y, xs] < 200).sum() == 0]
    assert rows, "no gap found"
    return (rows[len(rows) // 2]) / h


HINT_CUT = row_gap(P[12])
print("hint crop bottom", round(HINT_CUT, 3))
# ------------------------------------------------------------------ 3 close-up: the hint cards (top half: puzzles 1 to 4)
p3 = gs.preview_closeup(P[12], PAL, "Hint Cards for Every Puzzle", "Two steps each, so no team stays stuck for long",
                        crop=(0.04, 0.0, 0.96, HINT_CUT))
gs.save_jpeg(p3, OUT + "/3-closeup.jpg")

# ------------------------------------------------------------------ 4 included: count + list, PDF cover page
def included():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    d.rectangle([1100, 0, 2000, 1600], fill=gs.rgb(PAL["tint"]))
    gs.place(im, P[1], 640, (1170, 200), angle=-3, shadow=0.3)
    d = ImageDraw.Draw(im)
    x = 270; y = 150
    d.text((x, y), "16-Page PDF", font=font("serifB", 110), fill=gs.rgb(PAL["deep"])); y += 150
    d.rectangle([x, y, x + 110, y + 6], fill=gs.rgb(PAL["accent"])); y += 50
    f = font("sans", 54)
    for it in ["Host guide + story", "8 linked puzzles", "Team lock sheet", "8 two-step hint cards",
               "Timer + score sheet", "Answer key (host only)", "Escape certificate"]:
        d.ellipse([x, y + 24, x + 20, y + 44], fill=gs.rgb(PAL["primary"]))
        d.text((x + 48, y), it, font=f, fill=gs.rgb("#2B2B2B")); assert x + 48 + f.getlength(it) < 1080; y += 124
    y += 30
    d.text((x, y), "2 to 20 players  ·  about an hour", font=font("sansM", 44), fill=gs.rgb(PAL["primary"]))
    d.rectangle([0, 1490, 2000, 1600], fill=gs.rgb(PAL["deep"]))
    d.text((1000, 1545), "INSTANT DOWNLOAD  ·  PRINT AT HOME  ·  US LETTER OR A4", font=font("sansM", 38), fill=WHITE, anchor="mm")
    print("photo 4 list ends at y", y + 60)
    return im


p4 = included()
gs.save_jpeg(p4, OUT + "/4-included.jpg")


# ------------------------------------------------------------------ 5 end of the night: timer sheet + certificate, big and centred
def finish():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    d.text((1000, 46), "Score It and Crown the Winners", font=font("serifB", 84), fill=gs.rgb(PAL["deep"]), anchor="ma")
    d.text((1000, 150), "Team timer, hint penalties and a certificate for the team that escapes", font=font("sans", 40),
           fill=gs.rgb("#6B6B6B"), anchor="ma")
    w = 860
    b1 = gs.place(im, P[13], w, (150, 225), angle=-3, shadow=0.3)
    b2 = gs.place(im, P[15], w, (990, 225), angle=3, shadow=0.3)
    print("photo 5 pages end at y", max(b1[3], b2[3]), "of 1600")
    return im


p5 = finish()
gs.save_jpeg(p5, OUT + "/5-finish.jpg")
for f in sorted(os.listdir(OUT)):
    if f.endswith(".jpg"):
        im_ = Image.open(OUT + "/" + f); print(f, im_.size, os.path.getsize(OUT + "/" + f))
