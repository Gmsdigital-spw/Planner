"""Oct 31, 2026 (Warden cover redo, Grayson's GO of Oct 28): two new per-listing covers.
  irregular_collage()  4597096306  three real planner pages (baseline, paycheck-by-paycheck, income tracker)
                                   overlapping up from the bottom edge on deep teal, the listing's own
                                   magnifier bubble (Bills / Buffer / Savings / Fun) on top (collage family)
  adhd_tablet()        4596311765  one big tablet showing the real Today page on marigold linen, two real
                                   toolkit pages (Brain Dump, Overwhelm Reset) printed beside it, stylus
                                   (tablet-on-linen family, adapted from thanksgiving())
Rules kept: real pages only (cut from each listing's own full-size photos 1-4 in
gw/out/files/warden-1031-full), words inside x 280-1720, title >= 9% of height, no emoji stickers,
square-edge band (x 230-270, y 8-40%) left plain.
Run: COVERS_OUT=<dir> python3 covers_1031.py crops irregular_collage adhd_tablet
"""
import sys, glob
import numpy as np
import cv2
from common import *
from covers import grain

X = OUT + "/src/x/"
FULL = ROOT + "/gw/out/files/warden-1031-full/"
def g(p): return Image.open(glob.glob(FULL + p + "*")[0]).convert("RGB")
def L(n): return Image.open(X + n + ".png").convert("RGBA")

def fit_font(d, s, name, size, maxw):
    while d.textlength(s, font=F(name, size)) > maxw: size -= 2
    return F(name, size)

def crops():
    os.makedirs(X, exist_ok=True)
    # Irregular Income: pages; the magnifier bubble covers each page's right strip, so cut the clean part
    g("4597096306-r03").crop((161, 613, 1201, 1961)).save(X + "ii_base.png")
    g("4597096306-r04").crop((161, 613, 1084, 1961)).save(X + "ii_income.png")
    r2 = g("4597096306-r02")
    r2.crop((161, 521, 1086, 1937)).save(X + "ii_pay.png")  # stop before the bubble (x 1089)
    cx, cy, r = 1480, 1300, 392
    b = r2.crop((cx - r, cy - r, cx + r, cy + r)).convert("RGBA")
    m = Image.new("L", b.size, 0); ImageDraw.Draw(m).ellipse([2, 2, 2 * r - 3, 2 * r - 3], fill=255)
    b.putalpha(m); b.save(X + "ii_bubble.png")
    # ADHD: Today screen, annotation leader lines/dots painted out
    sc = g("4596311765-r01").crop((404, 433, 2096, 1614))
    a = np.array(sc); hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
    loose = (hsv[..., 1] > 14) & (hsv[..., 2] > 110)  # anything tinted on blank paper, never the dark text
    strict = (hsv[..., 1] > 50) & (hsv[..., 0] < 20) & (hsv[..., 2] > 120) & (hsv[..., 2] < 225)  # tan dot/line only
    f = sc.width / 1000  # boxes measured on a 1000 px wide view of this crop: dots + leader lines of the callouts
    mask = np.zeros(loose.shape, bool)
    for (x0, y0, x1, y1), rule in [((0, 88, 134, 110), strict), ((0, 97, 125, 111), loose), ((782, 88, 940, 136), loose), ((921, 95, 951, 125), loose), ((950, 100, 1000, 110), loose),
                                   ((0, 478, 136, 580), loose), ((456, 636, 492, 700), loose)]:
        sl = (slice(int(y0 * f), int(y1 * f)), slice(int(x0 * f), int(x1 * f)))
        mask[sl] = rule[sl]
    mask = mask.astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
    out = cv2.inpaint(a, mask, 5, cv2.INPAINT_TELEA)
    Image.fromarray(out).save(X + "ad_today.png")
    r2 = g("4596311765-r02")
    r2.crop((1255, 870, 1815, 1260)).save(X + "ad_brain.png")
    r2.crop((1825, 1380, 2385, 1770)).save(X + "ad_reset.png")
    return X

# ------------------------------------------------ IRREGULAR INCOME: page collage on deep teal + bubble
def irregular_collage():
    c = Image.new("RGBA", (W, H))
    yy = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([18, 104, 116]), np.array([12, 90, 102])
    c = Image.fromarray(np.broadcast_to(top * (1 - yy) + bot * yy, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    c = grain(c, 4)
    d = ImageDraw.Draw(c)
    cream, aqua = (250, 243, 228), (176, 226, 214)
    # round 2 (side-by-side): title moved to a right-hand column so it no longer reads like the
    # title-top-left covers (Thanksgiving Escape Room, Murder Mystery); pages collage on the left
    pw = 720
    for name, x, y, ang in [("ii_base", -10, -20, 4), ("ii_income", 360, 70, -4), ("ii_pay", 170, 600, 2)]:
        p = up(L(name).convert("RGB"), w=pw)
        shadow_paste(c, p, x, y, angle=ang, blur=26, off=(0, 22), alpha=140)
    bub = up(L("ii_bubble").convert("RGB"), w=540)
    m = Image.new("L", bub.size, 0); ImageDraw.Draw(m).ellipse([0, 0, 539, 539], fill=255)
    bub = bub.convert("RGBA"); bub.putalpha(m)
    shadow_paste(c, bub, 880, 950, blur=30, off=(0, 24), alpha=150)
    d = ImageDraw.Draw(c)
    ft = fit_font(d, "Irregular", "Gloock-Regular", 150, 560); x1 = 1720
    y = 90
    for line in ["Irregular", "Income", "Budget", "Planner"]:
        w = d.textlength(line, font=ft); d.text((x1 - w, y), line, font=ft, fill=cream); y += int(ft.size * 1.12)
    d.line([(x1 - 420, y + 26), (x1, y + 26)], fill=aqua, width=4)
    fs = fit_font(d, "GIG PAY \u00b7 FREELANCE", "WorkSans-Bold", 46, 560); y += 56
    for line in ["14 PAGES", "TIPS · COMMISSION", "GIG PAY · FREELANCE"]:
        w = text_w(d, line, fs, 3); text_sp(d, x1 - w, y, line, fs, aqua, spacing=3); y += 62
    return save(c, "4597096306.jpg")

# ------------------------------------------------ ADHD PLANNER: tablet on marigold linen
def linen(base):
    rng = np.random.default_rng(11)
    a = np.ones((H, W, 3)) * np.array(base, float)
    a += rng.normal(0, 5, (H, 1, 1)) + rng.normal(0, 5, (1, W, 1))  # warp/weft threads
    a += rng.normal(0, 3, (H, W, 1))
    v = np.linspace(-1, 1, W)[None, :] ** 2 + np.linspace(-1, 1, H)[:, None] ** 2
    a *= (1 - 0.08 * v)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

def stylus(length=760, w=30):
    s = Image.new("RGBA", (length, w + 4), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([0, 2, length - 60, w + 1], w // 2, fill=(246, 245, 241))
    d.polygon([(length - 62, 2), (length - 4, w // 2 + 2), (length - 62, w + 1)], fill=(236, 234, 228))
    d.ellipse([length - 14, w // 2 - 4, length - 4, w // 2 + 8], fill=(60, 60, 62))
    d.line([(14, 8), (length - 80, 8)], fill=(255, 255, 255), width=3)
    return s

def adhd_tablet():
    c = linen((224, 162, 46))
    d = ImageDraw.Draw(c)
    ink = (54, 36, 18)
    d.text((300, 70), "ADHD Planner", font=F("YoungSerif-Regular", 170), fill=ink)
    text_sp(d, 306, 300, "UNDATED  ·  117 HYPERLINKED PAGES  ·  iPAD + PRINT", F("WorkSans-Bold", 40), (92, 56, 14), spacing=3)
    # printed toolkit pages, left, under the tablet
    for name, x, y, ang in [("ad_reset", 40, 900, 9), ("ad_brain", 70, 640, -6)]:
        p = up(L(name).convert("RGB"), w=640)
        shadow_paste(c, p, x, y, angle=ang, blur=18, off=(0, 14), alpha=120)
    # tablet
    sw = 1400; scr = up(L("ad_today").convert("RGB"), w=sw); sh = scr.height
    bz = 44; tw, th = sw + 2 * bz, sh + 2 * bz
    t = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); td = ImageDraw.Draw(t)
    td.rounded_rectangle([0, 0, tw - 1, th - 1], 64, fill=(30, 30, 33))
    td.rounded_rectangle([3, 3, tw - 4, th - 4], 62, outline=(78, 78, 82), width=3)
    sm = Image.new("L", scr.size, 0); ImageDraw.Draw(sm).rounded_rectangle([0, 0, sw - 1, sh - 1], 22, fill=255)
    t.paste(scr, (bz, bz), sm)
    shadow_paste(c, t, 420, 400, angle=-2.5, blur=34, off=(10, 30), alpha=150)
    st = stylus().rotate(28, resample=Image.BICUBIC, expand=True)
    shadow_paste(c, st, 1380, 1120, blur=8, off=(6, 10), alpha=120)
    return save(c, "4596311765.jpg")

if __name__ == "__main__":
    for fn in sys.argv[1:]:
        print(fn, globals()[fn]())
