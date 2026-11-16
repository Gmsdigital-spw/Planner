"""Listing photos for the Left Right Christmas Game (prod-xmas-left-right-6). python3 photos.py"""
import sys, os, json
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/left-right-christmas-game.pdf"
OUT = HERE + "/photos"; os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("cranberry")
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-xmas-left-right-6")
assert len(pages) == 22
P = {n: pages[n - 1].convert("RGB") for n in range(1, 23)}
P["15f"] = gs.render_pages(HERE + "/sample-filled.pdf", HERE + "/sample-pages")[14].convert("RGB")
DEEP = gs.rgb(PAL["deep"]); PRIM = gs.rgb(PAL["primary"]); ACC = gs.rgb(PAL["accent"]); TINT = gs.rgb(PAL["tint"])
WHITE = (255, 255, 255); GREY = (107, 107, 107)
font = gs.font
used = {}


# ------------------------------------------------------------------ 1 cover: DEVICE family (fix round 1).
# The family-story TV slide on a big TV is the hero (50%+ of the centred square); two whole big-type host cards
# (kids, steal) sit top right; the headline card top left. Dark cranberry room glow, no stripe, no badge, no art.
# Everything lives inside x 270-1730 so the 300 px centred square cuts nothing.
SQ0, SQ1 = 250, 1750


def cover():
    W, H = 2000, 1500
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - 1000) / 1100.0) ** 2 + ((yy - 1050) / 800.0) ** 2)
    t = np.clip(r, 0, 1)[..., None]
    c0, c1 = np.array([168, 58, 72]), np.array([74, 20, 30])
    im = Image.fromarray((c0 * (1 - t) + c1 * t).astype("uint8"), "RGB")
    rng = np.random.default_rng(7); dd = ImageDraw.Draw(im)
    for _ in range(140):
        x, y, rr = int(rng.integers(0, W)), int(rng.integers(0, H)), int(rng.integers(3, 8))
        dd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(196, 120, 130))
    mask = Image.new("L", (W, H), 0)

    def shadow(box, r, off=(10, 18), blur=22, a=140):
        sh = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh).rounded_rectangle([box[0] + off[0], box[1] + off[1], box[2] + off[0], box[3] + off[1]], r, fill=a)
        im.paste((30, 6, 12), (0, 0), sh.filter(ImageFilter.GaussianBlur(blur)))
    X0, X1, TOP = 270, 1730, 26
    bez = 22; tw = X1 - X0; sw = tw - 2 * bez; sh_ = round(sw * 540 / 960); th = sh_ + 2 * bez
    stand_h = 46
    ty0 = H - 18 - stand_h - th
    tv = (X0, ty0, X1, ty0 + th)
    cx = (tv[0] + tv[2]) // 2
    d = ImageDraw.Draw(im)
    d.rectangle([cx - 30, tv[3], cx + 30, tv[3] + stand_h - 12], fill=(28, 28, 32))
    d.rounded_rectangle([cx - 230, tv[3] + stand_h - 16, cx + 230, tv[3] + stand_h], 8, fill=(28, 28, 32))
    shadow(tv, 20)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(tv, 20, fill=(20, 20, 24))
    sx, sy = tv[0] + bez, tv[1] + bez
    im.paste(P[16].resize((sw, sh_), Image.LANCZOS), (sx, sy))
    ImageDraw.Draw(mask).rectangle([sx, sy, sx + sw - 1, sy + sh_ - 1], fill=255)
    region_bot = ty0 - 60
    ch = region_bot - TOP - 64; cw = round(ch * 612 / 792); gap = 22
    cy_ = TOP + 32
    cards = []
    for k, n in enumerate([8, 12]):
        x = X1 - (2 - k) * cw - (1 - k) * gap
        box = (x, cy_, x + cw, cy_ + ch)
        shadow(box, 4, off=(8, 14), blur=16, a=120)
        im.paste(P[n].resize((cw, ch), Image.LANCZOS), (x, cy_))
        ImageDraw.Draw(mask).rectangle([box[0], box[1], box[2] - 1, box[3] - 1], fill=255)
        cards.append(box)
    hx0, hx1 = X0, cards[0][0] - gap
    rows = ["Left Right", "Christmas", "6 Stories"]
    inner_w = hx1 - hx0 - 40
    size = 220
    while True:
        fw = font("serifB", size)
        if max(fw.getlength(t_) for t_ in rows) <= inner_w: break
        size -= 1
    lh = round(size * 0.90)
    ink_top = fw.getbbox("Left Right")[1]
    fs = font("sansM", 34); sub = "HOST CARDS  ·  TV  ·  TYPE-IN NAMES"
    while fs.getlength(sub) > inner_w: fs = font("sansM", fs.size - 1)
    sub_gap = 22
    block = 2 * lh + fw.getbbox("6 Stories")[3] - ink_top + sub_gap + fs.getbbox(sub)[3] - fs.getbbox(sub)[1]
    pad = 26
    hh = block + 2 * pad
    hy0 = TOP + ((region_bot - TOP) - hh) // 2; hy1 = hy0 + hh
    shadow((hx0, hy0, hx1, hy1), 24, off=(8, 14), blur=16, a=120)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([hx0, hy0, hx1, hy1], 24, fill=(255, 251, 246), outline=ACC, width=6)
    y = hy0 + pad - ink_top
    mid = (hx0 + hx1) // 2
    bbs = []
    for k, t_ in enumerate(rows):
        if k == 2:
            w6 = fw.getlength("6 "); wl = fw.getlength(t_); x = mid - wl / 2
            d.text((x, y), "6", font=fw, fill=PRIM, anchor="la"); d.text((x + w6, y), "Stories", font=fw, fill=DEEP, anchor="la")
            bbs.append(d.textbbox((x, y), t_, font=fw, anchor="la"))
        else:
            d.text((mid, y), t_, font=fw, fill=DEEP, anchor="ma"); bbs.append(d.textbbox((mid, y), t_, font=fw, anchor="ma"))
        y += lh
    ys = bbs[-1][3] + sub_gap - fs.getbbox(sub)[1]
    d.text((mid, ys), sub, font=fs, fill=PRIM, anchor="ma"); bbs.append(d.textbbox((mid, ys), sub, font=fs, anchor="ma"))
    assert bbs[-1][3] <= hy1 - pad + 2, (bbs[-1], hy1)
    head = (min(b[0] for b in bbs), bbs[0][1], max(b[2] for b in bbs), bbs[-1][3])
    return im, mask, dict(head=head, card=(hx0, hy0, hx1, hy1), cards=cards, tv=tv, screen=(sx, sy, sx + sw, sy + sh_), fw=fw.size)


im, mask, B = cover()
gs.save_jpeg(im, OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s_ = min(im.size); x_ = (im.width - s_) // 2
im.crop((x_, 0, x_ + s_, s_)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
CK = {"fontPx": B["fw"]}
assert B["fw"] >= 135, B["fw"]
arr = np.asarray(im.convert("RGB")).astype(int)
cx0, cy0, cx1, cy1 = B["card"]
sub = arr[cy0 + 8:cy1 - 8, cx0 + 30:cx1 - 30]
ink_rows = (np.abs(sub - np.array([255, 251, 246])).sum(-1) > 90).any(1)
bands, run = [], 0
for v in ink_rows:
    if not v: run += 1
    else:
        if run: bands.append(run)
        run = 0
bands.append(run)
CK["cardH"] = int(cy1 - cy0); CK["maxEmptyBandPct"] = round((max(bands) + 8) / (cy1 - cy0) * 100, 1)
CK["emptyRowsPct"] = round(((~ink_rows).sum() + 16) / (cy1 - cy0) * 100, 1)
assert CK["maxEmptyBandPct"] < 15, CK   # the judge target: no empty band over 15% (emptyRowsPct also counts line gaps and padding)
for nm, bx in [("head card", B["card"]), ("tv", B["tv"])] + [(f"card{k}", b) for k, b in enumerate(B["cards"])]:
    assert bx[0] >= SQ0 and bx[2] <= SQ1 and bx[1] >= 0 and bx[3] <= 1500, (nm, bx)
CK["tvGapPx"] = int(B["tv"][1] - max(b[3] for b in B["cards"]))
assert CK["tvGapPx"] >= 40, CK
CK["tvPctSquare"] = round((B["tv"][2] - B["tv"][0]) * (B["tv"][3] - B["tv"][1]) / 1500 ** 2 * 100, 1)
assert CK["tvPctSquare"] >= 45, CK
mk = np.asarray(mask) > 0
CK["realPagesPctSquare"] = round(mk[:, SQ0:SQ1].mean() * 100, 1)
print("cover checks", CK)
COVER_PAGES = [8, 12, 16]


def safe_text(d, xy, text, f, fill, anchor="la"):
    b = d.textbbox(xy, text, font=f, anchor=anchor)
    assert b[0] >= 260 and b[2] <= 1740, ("text outside the safe zone", text, b)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)
    return b


# ------------------------------------------------------------------ 2 inside: 6 pages the cover does not show
def inside():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 50), "6 Stories, 3 Ways to Play", font("serifB", 92), DEEP, "ma")
    safe_text(d, (1000, 168), "How to play, the host guide and big-type story cards", font("sans", 40), GREY, "ma")
    idxs = [2, 3, 4, 5, 10, 11]
    w, gx, gy = 470, 60, 30
    x0 = (2000 - (3 * w + 2 * gx)) // 2
    ph = int(w * 792 / 612)
    bots = [gs.place(im, P[n], w, (x0 + (k % 3) * (w + gx), 248 + (k // 3) * (ph + gy)), shadow=0.22)[3] for k, n in enumerate(idxs)]
    print("photo 2 pages end at y", max(bots))
    assert max(bots) <= 1600 and 1600 - max(bots) < 240
    used[2] = idxs
    return im


gs.save_jpeg(inside(), OUT + "/2-inside.jpg")


# ------------------------------------------------------------------ 3 close-up: the steal story host card, readable
def closeup():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    J = json.load(open(HERE + "/boxes.json")); sz = [J["sizes"][str(i)] for i in range(6)]
    safe_text(d, (1000, 44), "Big Type, Easy to Read Aloud", font("serifB", 92), DEEP, "ma")
    safe_text(d, (1000, 156), f"Every LEFT and RIGHT stands out  ·  {min(sz):g} to {max(sz):g} pt story type", font("sans", 42), GREY, "ma")
    # fix round 2: whole pages side by side, page text (footer at 8% of the page width) inside x 260-1740
    w, g = 780, 24
    x0 = (2000 - (2 * w + g)) // 2; y0 = 246
    bl = gs.place(im, P[6], w, (x0, y0), shadow=0.25)
    br = gs.place(im, P[7], w, (x0 + w + g, y0), shadow=0.25)
    y = max(bl[3], br[3]) + 40
    for line in ["Each story fits on one or two cards", "Print only the stories you want"]:
        b = safe_text(d, (1000, y), line, font("sansM", 44), PRIM, "ma"); y = b[3] + 22
    print("photo 3: two whole pages", bl, br, "pages", round((br[2] - bl[0]) / 20), "% of width, caption ends", b[3])
    assert 1600 - b[3] < 240 and (br[2] - bl[0]) >= 1400, (bl, br)
    used[3] = [6, 7]
    return im


gs.save_jpeg(closeup(), OUT + "/3-closeup.jpg")


# ------------------------------------------------------------------ 4 TV screen version: 4 slides big
def tvshot():
    J = json.load(open(HERE + "/boxes.json")); tvs = [J["sizes"][f"tv{i}"] for i in range(6)]
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 44), "TV Screen Version Included", font("serifB", 90), DEEP, "ma")
    safe_text(d, (1000, 156), "Show it full screen from a laptop or tablet so everyone reads along", font("sans", 40), GREY, "ma")
    # fix round 2: one big slide (screen 1400 px, 70% of the width; slide text keeps a 5% margin) + the other 4 small
    def screen(n, x, y, w, bz, r):
        h = round(w * 540 / 960)
        sh = Image.new("L", im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle([x - bz + 8, y - bz + 14, x + w + bz + 8, y + h + bz + 14], r, fill=110)
        im.paste((60, 40, 40), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(im).rounded_rectangle([x - bz, y - bz, x + w + bz, y + h + bz], r, fill=(22, 22, 26))
        gs.place(im, P[n], w, (x, y), shadow=0.0)
        return (x - bz, y - bz, x + w + bz, y + h + bz)
    hw = 1400
    hero = screen(18, (2000 - hw) // 2, 244, hw, 16, 16)
    tw_, gx = 330, 30; bz = 8
    tx0 = (2000 - (4 * (tw_ + 2 * bz) + 3 * gx)) // 2 + bz
    thumbs = [screen(n, tx0 + k * (tw_ + 2 * bz + gx), hero[3] + 34 + bz, tw_, bz, 8) for k, n in enumerate([17, 19, 20, 21])]
    cb = safe_text(ImageDraw.Draw(im), (1000, thumbs[0][3] + 34), f"16:9 widescreen  ·  story type {min(tvs):g} to {max(tvs):g} pt  ·  one slide per story", font("sansM", 40), PRIM, "ma")
    print("photo 4 hero", hero, "thumbs", thumbs[0], thumbs[-1], "caption ends", cb[3])
    assert 1600 - cb[3] < 240 and hero[2] - hero[0] >= 1400 and thumbs[0][0] >= 255 and thumbs[-1][2] <= 1745
    used[4] = [17, 18, 19, 20, 21]
    return im


gs.save_jpeg(tvshot(), OUT + "/4-tv.jpg")


# ------------------------------------------------------------------ 5 included: PDF cover + typed names page + short story, fanned
def included():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 40), "Everything in the 21-Page PDF", font("serifB", 88), DEEP, "ma")
    w = 760
    bl = gs.place(im, P[14], w, (240, 200), angle=6, shadow=0.3)
    br = gs.place(im, P["15f"], w, (1000, 200), angle=-6, shadow=0.3)
    bm = gs.place(im, P[1], w, (620, 168), angle=0, shadow=0.34)
    d = ImageDraw.Draw(im)
    bot = max(bl[3], br[3], bm[3])
    f = font("sansM", 40); y = bot + 22
    for line in ["How to play  ·  host guide  ·  6 big-type host cards (11 pages)",
                 "Type-in names story  ·  6 TV screen slides  ·  US Letter pages"]:
        safe_text(d, (1000, y), line, f, PRIM, "ma"); y += 62
    d.rectangle([0, 1505, 2000, 1600], fill=DEEP)
    safe_text(d, (1000, 1552), "INSTANT DOWNLOAD  ·  PRINT AT HOME OR PLAY ON A TV", font("sansM", 38), WHITE, "mm")
    span = max(bl[2], br[2], bm[2]) - min(bl[0], br[0], bm[0])
    print(f"photo 5: pages span {span / 20:.0f}% of width, end y {bot}, list ends y {y}")
    assert span >= 1600 and y <= 1505 and min(bl[0], br[0]) >= 0 and max(bl[2], br[2]) <= 2000
    used[5] = [1, 14, 15]
    return im


gs.save_jpeg(included(), OUT + "/5-included.jpg")
shown = [n for v in used.values() for n in v]
assert not set(shown) & set(COVER_PAGES), "a photo repeats a cover page"
assert 22 not in shown
for f in sorted(os.listdir(OUT)):
    if f.endswith(".jpg"):
        i_ = Image.open(OUT + "/" + f); sz = os.path.getsize(OUT + "/" + f)
        print(f, i_.size, sz); assert sz < 400_000 and i_.width == 2000
# fix round 2 (bug rule): measure ALL text in photos 2-5, page body text included, not only safe_text overlays
sys.path.insert(0, "/home/claude/planner/factory/qa")
import photo_text_zone as ptz
assert ptz.check([OUT + "/" + f for f in sorted(os.listdir(OUT)) if f[0] in "2345" and f.endswith(".jpg")]), "page text outside x 260-1740"
