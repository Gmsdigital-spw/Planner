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


# ------------------------------------------------------------------ 1 cover (fix round 1): headline on top, three real pages big underneath
def place_m(im, mask, page, w, xy, angle=0, shadow=0.45):
    """gs.place plus the same page's alpha on a mask, so the page share is measured on real page pixels."""
    bb = gs.place(im, page, w, xy, angle=angle, shadow=shadow)
    p = page.resize((w, int(page.height * w / page.width)), Image.LANCZOS).convert("RGBA")
    if angle: p = p.rotate(angle, expand=True, resample=Image.BICUBIC)
    mask.paste(255, xy, p.split()[3].point(lambda v: 255 if v > 128 else 0))
    return bb


def cover():
    """Judge fix round 1: pages were about a third of the frame. v3: cranberry ground (not the navy fan, not a scene
    card), text block on top, three real pages 800+ px wide filling the lower 70% of the frame."""
    W, H = 2000, 1500
    im = grad((W, H), (112, 24, 36), (58, 12, 20))
    d = ImageDraw.Draw(im)
    boxes = {}
    fk = font("sansM", 54); y = 28
    d.text((W / 2, y), "C H R I S T M A S", font=fk, fill=GOLD, anchor="ma")
    boxes["kicker"] = d.textbbox((W / 2, y), "C H R I S T M A S", font=fk, anchor="ma")
    f1 = font("serifB", 220)
    while f1.getlength("Escape Room") > 1120: f1 = font("serifB", f1.size - 4)
    y1 = boxes["kicker"][3] + 6
    d.text((W / 2, y1), "Escape Room", font=f1, fill=WHITE, anchor="ma")
    boxes["title"] = d.textbbox((W / 2, y1), "Escape Room", font=f1, anchor="ma")
    line2 = "8 Puzzles for Adults & Teens"
    f2 = font("serifB", 96)
    while f2.getlength(line2) > 1380: f2 = font("serifB", f2.size - 4)
    y2 = boxes["title"][3] + 14
    d.text((W / 2, y2), line2, font=f2, fill=GOLD, anchor="ma")
    boxes["count"] = d.textbbox((W / 2, y2), line2, font=f2, anchor="ma")
    mask = Image.new("L", (W, H), 0)
    top = boxes["count"][3] + 24
    ph = H - 14 - top                       # page height that fits, footer to footer, nothing cropped
    pw = int(ph / 1.294)
    placed = {}
    placed[3] = place_m(im, mask, P[3], pw - 40, (24, top + 22), angle=3)
    placed[8] = place_m(im, mask, P[8], pw - 40, (W - 24 - (pw - 40) - 60, top + 22), angle=-3)
    placed[6] = place_m(im, mask, P[6], pw, ((W - pw) // 2, top), angle=0, shadow=0.55)
    for n, bb in placed.items():
        assert bb[0] >= 0 and bb[2] <= W and bb[1] >= top - 2 and bb[3] <= H, ("page clipped", n, bb)
    return im, boxes, placed, mask


im, boxes, placed, mask = cover()
gs.save_jpeg(im, OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s = min(im.size); x = (im.width - s) // 2
im.crop((x, 0, x + s, s)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
for k, b in boxes.items():
    assert b[0] >= 250 + 20 and b[2] <= 1750 - 20, (k, b)
th = boxes["title"][3] - boxes["title"][1]
print(f"cover title ink height {th}px = {th / 1500 * 100:.1f}% of height; count line {boxes['count'][3] - boxes['count'][1]}px")
assert th / 1500 >= 0.09, "title under 9% of the cover height"
import numpy as _np
m = _np.asarray(mask) > 0
frame_share = m.mean(); sq_share = m[:, 250:1750].mean()
print(f"real page pixels: {frame_share * 100:.1f}% of the full frame, {sq_share * 100:.1f}% of the centred square")
assert frame_share >= 0.60 and sq_share >= 0.60, "pages under 60% of the frame"
pw6 = placed[6][2] - placed[6][0]
print(f"hero page width {pw6}px of 2000 = {pw6 * 300 / 1500:.0f}px wide in the 300 px square")


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
# ------------------------------------------------------------------ 3 close-up (fix round 1): cards 5 to 8, every Hint 2 folded under
# Judge fix: v2 showed puzzles 1 to 4 with Hint 2 open (C becomes T) and the PINE keyword. Now: the bottom two card rows,
# whose Hint 1 lines name no answer, and a paper flap over every Hint 2 (fold line to card edge, measured on the page).
def fold_flaps(page):
    import numpy as np
    pg = page.convert("RGB").copy(); a = np.asarray(pg.convert("L")).astype(int); h, w = a.shape
    xs = slice(int(w * .12), int(w * .45))
    full = [y for y in range(int(h * .45), h) if (a[y, xs] < 200).mean() > 0.9]
    rows = []                                   # group border rows into runs
    for y in full:
        if rows and y - rows[-1][-1] <= 2: rows[-1].append(y)
        else: rows.append([y])
    edges = [r[0] for r in rows]                # card bottom, next top, ... (pairs around each cut line)
    cols = [x for x in range(w) if (a[int(h * .66):int(h * .7), x] < 200).mean() > 0.9]
    cx = [cols[0], cols[1 if cols[1] - cols[0] > 5 else 2]]
    groups = []
    for x in cols:
        if groups and x - groups[-1][-1] <= 2: groups[-1].append(x)
        else: groups.append([x])
    lefts, rights = [g[-1] for g in groups[0::2]], [g[0] for g in groups[1::2]]
    # card rows 3 and 4: tops and bottoms from the border runs
    r3_top, r3_bot, r4_top, r4_bot = edges[1], edges[2], edges[3], edges[4]
    d = ImageDraw.Draw(pg)
    flaps = []
    for top_, bot_ in [(r3_top, r3_bot), (r4_top, r4_bot)]:
        band = a[top_ + 10:bot_ - 5, int(w * .12):int(w * .45)]
        ink = [(band[i] < 200).mean() for i in range(band.shape[0])]
        # the fold line is a THIN dashed row: 50-65% ink with near-empty rows 3 px above and below (text rows are thicker)
        dash = [i for i in range(3, len(ink) - 3) if 0.5 < ink[i] < 0.65 and ink[i - 3] < 0.05 and ink[i + 3] < 0.05]
        assert len(dash) >= 1, "fold line not found"
        fy = top_ + 10 + dash[0] - 1
        for l, r in zip(lefts, rights):
            box = [l + 5, fy + 5, r - 5, bot_ - 5]
            d.rectangle(box, fill=(236, 230, 214)); d.line([box[0], box[1], box[2], box[1]], fill=(190, 180, 160), width=3)
            d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), "Hint 2 folded under", font=font("sansM", 26),
                   fill=(120, 110, 95), anchor="mm")
            flaps.append(box)
    return pg, edges[0] + (edges[1] - edges[0]) // 2, r4_bot + 18, flaps


P12F, CUT_TOP, CUT_BOT, FLAPS = fold_flaps(P[12])
print("hint crop", CUT_TOP, CUT_BOT, "flaps", FLAPS)
assert len(FLAPS) == 4
def closeup():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    d.text((1000, 46), "Hint Cards for Every Puzzle", font=font("serifB", 88), fill=gs.rgb(PAL["deep"]), anchor="ma")
    d.text((1000, 156), "Hint 2 folds under, so a team sees only the help it asks for", font=font("sans", 44),
           fill=gs.rgb("#6B6B6B"), anchor="ma")
    cp = P12F.crop((int(P12F.width * 0.04), CUT_TOP, int(P12F.width * 0.96), CUT_BOT))
    w = 1480
    bb = gs.place(im, cp, w, ((2000 - w) // 2, 290), shadow=0.25)
    d = ImageDraw.Draw(im)
    y = bb[3] + 100
    steps = ["Cut the cards apart", "Fold Hint 2 under", "Each hint adds 2 minutes"]
    cw = 1480 // 3
    for i, t in enumerate(steps):
        cx = 260 + cw * i + cw // 2
        d.ellipse([cx - 40, y, cx + 40, y + 80], fill=gs.rgb(PAL["primary"]))
        d.text((cx, y + 40), str(i + 1), font=font("sansM", 40), fill=WHITE, anchor="mm")
        f = font("sansM", 36)
        assert f.getlength(t) < cw - 20, t
        d.text((cx, y + 110), t, font=f, fill=gs.rgb(PAL["deep"]), anchor="ma")
    end = y + 110 + 46
    print("photo 3 cards end", bb[3], "content ends at y", end, "of 1600")
    assert 1600 - end < 240, "empty band over 15%"
    return im


p3 = closeup()
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
    d.text((1000, 1545), "INSTANT DOWNLOAD  ·  PRINT AT HOME  ·  US LETTER PDF", font=font("sansM", 38), fill=WHITE, anchor="mm")
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
