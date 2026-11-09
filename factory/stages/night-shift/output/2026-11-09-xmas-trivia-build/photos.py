"""Listing photos for the Christmas Trivia Game (prod-xmas-trivia-200). python3 photos.py"""
import sys, os
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs
import place
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/christmas-trivia-game.pdf"
OUT = HERE + "/photos"; os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("evergreen")
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-xmas-trivia-200")
assert len(pages) == 17
P = {n: pages[n - 1] for n in range(1, 18)}
COVER_PAGES = [3, 5]           # round 1 + round 3: never repeated in photos 2-5; no answer key in any photo (no spoilers)
DEEP = gs.rgb(PAL["deep"]); PRIM = gs.rgb(PAL["primary"]); ACC = gs.rgb(PAL["accent"])
CREAM = (250, 246, 236); WHITE = (255, 255, 255); RED = (158, 59, 51)
font = gs.font
used = {}


# ------------------------------------------------------------------ 1 cover (fix round 2): side layout on a light frost-blue ground.
# Portrait tablet with a light silver bezel + soft shadow on the right (Round 1 page), one printed page (Round 3) tucked
# under its left edge, the headline stacked BESIDE the tablet in deep ink with a burnt-orange "200". No dark ground,
# no centred top headline, no gold-over-cream, no card, no table scene.
FROST = (198, 212, 223); INK = (24, 36, 56); EMBER = (184, 72, 28); SILVER = (247, 248, 250)
def cover():
    from PIL import ImageFilter
    W, H = 2000, 1500
    g = np.random.default_rng(7).normal(0, 3, (H, W, 1))
    im = Image.fromarray(np.clip(np.full((H, W, 3), FROST, float) + g, 0, 255).astype("uint8"))
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    def shadow(box, r, off=(14, 26), blur=30, a=120):
        sh = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh).rounded_rectangle([box[0] + off[0], box[1] + off[1], box[2] + off[0], box[3] + off[1]], r, fill=a)
        im.paste((92, 108, 124), (0, 0), sh.filter(ImageFilter.GaussianBlur(blur)))
    # tablet geometry (portrait), right side
    bez = 34; sh_ = 1352; sw = round(sh_ * 612 / 792)
    tw, th = sw + 2 * bez, sh_ + 2 * bez
    tx, ty = W - 46 - tw, (H - th) // 2 - 8
    # printed page under the tablet's left edge, whole (footer included)
    pw = 620; ph = round(pw * 792 / 612)
    px_, py_ = 262, H - 34 - ph
    shadow((px_, py_, px_ + pw, py_ + ph), 4, off=(8, 14), blur=16, a=110)
    im.paste(P[5].convert("RGB").resize((pw, ph), Image.LANCZOS), (px_, py_))
    md.rectangle([px_, py_, px_ + pw - 1, py_ + ph - 1], fill=255)
    shadow((tx, ty, tx + tw, ty + th), 64)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([tx, ty, tx + tw, ty + th], 64, fill=SILVER, outline=(168, 178, 190), width=4)
    d.rounded_rectangle([tx + 10, ty + 10, tx + tw - 10, ty + th - 10], 56, outline=(226, 230, 235), width=2)
    d.ellipse([tx + tw / 2 - 8, ty + bez / 2 - 8, tx + tw / 2 + 8, ty + bez / 2 + 8], fill=(150, 158, 168))
    sx, sy = tx + bez, ty + bez
    im.paste(P[3].convert("RGB").resize((sw, sh_), Image.LANCZOS), (sx, sy))
    d.rectangle([sx, sy, sx + sw - 1, sy + sh_ - 1], outline=(120, 128, 138), width=2)
    md.rectangle([px_, py_, px_ + pw - 1, py_ + ph - 1], fill=0)     # recount: page minus what the tablet covers
    vis = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(vis)
    vd.rectangle([px_, py_, px_ + pw - 1, py_ + ph - 1], fill=255); vd.rounded_rectangle([tx, ty, tx + tw, ty + th], 64, fill=0)
    mask.paste(255, (0, 0), vis); md = ImageDraw.Draw(mask); md.rectangle([sx, sy, sx + sw - 1, sy + sh_ - 1], fill=255)
    # headline, stacked beside the tablet, left-aligned at x 272, above the printed page
    x0, xmax = 272, tx - 28
    words = ["Christmas", "Trivia", "Questions"]
    fw = font("serifB", 150)
    while max(fw.getlength(w_) for w_ in words) > xmax - x0: fw = font("serifB", fw.size - 2)
    fn = font("serifB", round(fw.size * 2.3))
    while fn.getlength("200") > xmax - x0: fn = font("serifB", fn.size - 4)
    y = 30 - (d.textbbox((x0, 0), "200", font=fn, anchor="la")[1])      # ink top at y 30
    d.text((x0, y), "200", font=fn, fill=EMBER, anchor="la"); b0 = d.textbbox((x0, y), "200", font=fn, anchor="la")
    y = b0[3] + 18; bbs = [b0]
    for w_ in words:
        d.text((x0, y), w_, font=fw, fill=INK, anchor="la"); b = d.textbbox((x0, y), w_, font=fw, anchor="la"); bbs.append(b)
        y = b[3] + round(fw.size * 0.16)
    head = (min(b[0] for b in bbs), bbs[0][1], max(b[2] for b in bbs), bbs[-1][3])
    return im, mask, {"line1": bbs[0], "line2": bbs[1], "words": bbs, "card": head, "page": (px_, py_, px_ + pw, py_ + ph),
                      "tablet": (tx, ty, tx + tw, ty + th), "screen": (sx, sy, sx + sw, sy + sh_)}, sy


im, mask, boxes, page_top_px = cover()
gs.save_jpeg(im.resize((2000, 1500)), OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s_ = min(im.size); x_ = (im.width - s_) // 2
im.crop((x_, 0, x_ + s_, s_)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
card = boxes["card"]
assert card[0] >= 270 and card[2] <= 1730, ("headline outside the centred square", card)
ink = card[3] - card[1]
line_h = boxes["line1"][3] - boxes["line1"][1]; word_h = boxes["line2"][3] - boxes["line2"][1]
print(f"cover headline: 4 stacked lines beside the tablet, ink {ink}px = {ink / 1500 * 100:.1f}% of height ('200' {line_h}px = {line_h / 1500 * 100:.1f}%, word line {word_h}px = {word_h / 1500 * 100:.1f}%)", card)
assert line_h / 1500 >= 0.09 and ink / 1500 >= 0.09
assert card[2] < boxes["tablet"][0] and card[3] + 24 < boxes["page"][1], "headline must sit beside the tablet, clear of the page"
m = np.asarray(mask) > 0
print(f"real page pixels: {m.mean() * 100:.1f}% of the frame, {m[:, 250:1750].mean() * 100:.1f}% of the centred square")
assert m.mean() >= 0.60 and m[:, 250:1750].mean() >= 0.60
# whole pages: the tablet (and so every page edge and footer) sits inside the frame, nothing cut
t = boxes["tablet"]; print("tablet box", t, "printed page", boxes["page"])
pg_ = boxes["page"]; assert pg_[0] >= 8 and pg_[1] >= 0 and pg_[3] <= 1500 - 12, ("printed page cut by the frame", pg_)
assert t[0] >= 8 and t[1] >= 0 and t[2] <= 1992 and t[3] <= 1500 - 12, ("cover crop cuts the device/pages", t)
ys, xs = np.nonzero(m); assert ys.max() <= 1500 - 30 and xs.min() >= 30 and xs.max() <= 1970


def safe_text(d, xy, text, f, fill, anchor="la"):
    b = d.textbbox(xy, text, font=f, anchor=anchor)
    assert b[0] >= 260 and b[2] <= 1740, ("text outside the safe zone", text, b)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)
    return b


# ------------------------------------------------------------------ 2 inside: 6 pages the cover does not show, 470 px each
def inside():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 56), "200 Questions, 10 Themed Rounds", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 172), "Host page, history, nativity, true or false, kids and numbers rounds", font("sans", 40), (107, 107, 107), "ma")
    idxs = [2, 6, 7, 10, 11, 12]
    w, gx, gy = 470, 60, 32
    x0 = (2000 - (3 * w + 2 * gx)) // 2
    ph = int(w * 792 / 612)
    bots = []
    for k, n in enumerate(idxs):
        bb = gs.place(im, P[n], w, (x0 + (k % 3) * (w + gx), 250 + (k // 3) * (ph + gy)), shadow=0.22); bots.append(bb[3])
    print("photo 2 pages end at y", max(bots), "of 1600")
    assert 1600 - max(bots) < 240
    used[2] = idxs
    return im


gs.save_jpeg(inside(), OUT + "/2-inside.jpg")


# ------------------------------------------------------------------ 3 close-up: round 2 page, top 14 questions readable
def closeup():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 46), "Twenty Questions Per Round", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 156), "Read each one aloud twice; teams write their answers", font("sans", 42), (107, 107, 107), "ma")
    pg = P[4]
    # cut between two question rows so no row is sliced: row 13/14 boundary measured on the page grid
    top_frac, bot_frac = 0.035, 0.62
    a = np.asarray(pg.convert("L")).astype(int)
    h = a.shape[0]
    cut = int(h * bot_frac)
    # move the cut to the nearest fully-light row (between question rows)
    xs = slice(int(a.shape[1] * 0.12), int(a.shape[1] * 0.85))
    for dy in range(0, 60):
        for yy in (cut + dy, cut - dy):
            if (a[yy, xs] < 200).sum() == 0 and (a[yy - 6:yy + 6, int(a.shape[1] * 0.08):int(a.shape[1] * 0.1)] < 140).sum() == 0:
                cut = yy; break
        else:
            continue
        break
    cp = pg.crop((int(pg.width * 0.03), int(h * top_frac), int(pg.width * 0.97), cut))
    w = 1440
    bb = gs.place(im, cp, w, ((2000 - w) // 2, 250), shadow=0.25)
    print("photo 3 crop ends at y", bb[3], "of 1600")
    assert bb[3] <= 1600 and 1600 - bb[3] < 240, bb
    used[3] = [4]
    return im


gs.save_jpeg(closeup(), OUT + "/3-closeup.jpg")


# ------------------------------------------------------------------ 4 included (fix round 1): 3 real pages fanned big
# (PDF cover + Rounds 6 and 7, none shown elsewhere, never an answer key) over a 2-line list of what is inside
def included():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 40), "Everything in the 16-Page PDF", font("serifB", 88), DEEP, "ma")
    w = 790
    bl = gs.place(im, P[8], w, (175, 205), angle=6, shadow=0.3)
    br = gs.place(im, P[9], w, (1035, 205), angle=-6, shadow=0.3)
    bm = gs.place(im, P[1], w, (605, 170), angle=0, shadow=0.34)
    d = ImageDraw.Draw(im)
    span = max(bl[2], br[2], bm[2]) - min(bl[0], br[0], bm[0])
    bot = max(bl[3], br[3], bm[3])
    f = font("sansM", 41)
    y = bot + 26
    for line in ["Host script  ·  10 rounds of 20 questions  ·  answer keys for all 200",
                 "Team answer sheet  ·  score sheet for 10 teams  ·  3 tie-breakers"]:
        safe_text(d, (1000, y), line, f, PRIM, "ma"); y += 64
    d.rectangle([0, 1500, 2000, 1600], fill=DEEP)
    safe_text(d, (1000, 1550), "INSTANT DOWNLOAD  ·  PRINT AT HOME  ·  US LETTER PDF", font("sansM", 38), WHITE, "mm")
    print(f"photo 4: 3 pages span {span}px = {span / 2000 * 100:.0f}% of width, pages end y {bot}, list ends y {y}")
    assert span >= 0.8 * 2000 and y <= 1500 and min(bl[0], br[0], bm[0]) >= 0 and max(bl[2], br[2], bm[2]) <= 2000
    used[4] = [1, 8, 9]
    return im


gs.save_jpeg(included(), OUT + "/4-included.jpg")


# ------------------------------------------------------------------ 5 game night sheets: answer sheet + score sheet, big
def sheets():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 46), "Team Sheets for Game Night", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 156), "Print an answer sheet per team each round; the host keeps score", font("sans", 40), (107, 107, 107), "ma")
    w = 880
    b1 = gs.place(im, P[15], w, (130, 232), angle=-3, shadow=0.3)
    b2 = gs.place(im, P[16], w, (990, 232), angle=3, shadow=0.3)
    print("photo 5 pages end at y", max(b1[3], b2[3]), "of 1600")
    used[5] = [15, 16]
    return im


gs.save_jpeg(sheets(), OUT + "/5-sheets.jpg")
shown = [n for v in used.values() for n in v]
assert not set(shown) & set(COVER_PAGES), "a photo repeats a cover page"
assert 17 not in shown
assert not {13, 14} & (set(shown) | set(COVER_PAGES)), "an answer key is shown in a photo"
for f in sorted(os.listdir(OUT)):
    if f.endswith(".jpg"):
        im_ = Image.open(OUT + "/" + f); sz = os.path.getsize(OUT + "/" + f)
        print(f, im_.size, sz); assert sz < 400_000 and im_.width == 2000
