"""Five listing photos for the Christmas Coupon Book. python3 photos.py"""
import sys, os, json, subprocess, glob
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/christmas-coupon-book.pdf"
OUT = HERE + "/photos"; os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("cranberry")
PG = "/home/claude/kit/pages/prod-xmas-coupon-book"
gs.render_pages(PDF, PG)
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob(PG + "/p-*.png"))]
assert len(pages) == 13
P = lambda n: pages[n - 1]
FD = "/usr/share/fonts/truetype/google-fonts/"
K = 150 / 72
PH, M = gs.PH, gs.MARGIN
CW, CX = 432, (gs.PW - 432) / 2
TOP, BOT = PH - M - 52, M + 14


def lora(size, w=700):
    f = ImageFont.truetype(FD + "Lora-Variable.ttf", size)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f


def slot(n, i, gap=12):
    """Pixel crop of coupon/cover slot i (0-based) of n stacked on a page (same maths as build.py)."""
    h = (TOP - BOT - (n - 1) * gap) / n
    yb = TOP - (i + 1) * h - i * gap
    return (round(CX * K) - 2, round((PH - yb - h) * K) - 2, round((CX + CW) * K) + 2, round((PH - yb) * K) + 2)


def ink_box(size, text, font, xy, anchor="ma"):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).text(xy, text, font=font, fill=255, anchor=anchor); return m.getbbox()


def check_text_gap(boxes, min_gap=12):
    gaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[2] <= b[0] or b[2] <= a[0]: continue
            g = max(b[1] - a[3], a[1] - b[3]); gaps.append(g)
            assert g >= min_gap, ("text lines' ink too close", a, b, g)
    return min(gaps) if gaps else None


def families(c):
    f = set(); txt = " ".join(str(v) for v in (c.get("coverStyle"), c.get("scene"), c.get("tool")) if v).lower()
    for key, fam in [("clipboard", "clipboard-scene"), ("christmas", "holiday-table"), ("table", "holiday-table"),
                     ("fun_covers", "fun-card"), ("collage", "collage"), ("frame", "frame"), ("tablet", "tablet"),
                     ("device", "device"), ("grid", "grid"), ("flat", "flat-lay"), ("hero", "hero-page")]:
        if key in txt: f.add(fam)
    return f


def put(canvas, img, w, center, angle, shadow=80):
    """Opaque piece (alpha 255 inside) with a soft shadow; returns its mask."""
    p = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS).convert("RGBA")
    p = p.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = round(center[0] - p.width / 2), round(center[1] - p.height / 2)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", p.size, (70, 20, 30, 255)), (x + 10, y + 20), p.split()[3].point(lambda v: shadow if v else 0))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); layer.paste(p, (x, y)); canvas.alpha_composite(layer)
    mask = Image.new("L", canvas.size, 0); mask.paste(p.split()[3], (x, y))
    return layer, mask


def check_opaque(comp, layer, mask, name):
    from scipy import ndimage
    m = ndimage.binary_erosion(np.asarray(mask) == 255, iterations=4)
    a = np.asarray(comp.convert("L"), np.float32); b = np.asarray(layer.convert("RGB").convert("L"), np.float32)
    k = m & (b > 60)
    return a[k], b[k]


# ------------------------------------------------------------------ 1 cover: flat-lay of cut coupons + covers on blush linen
HEAD = "30 Christmas Coupons"
SUB = "EDITABLE IN FREE ADOBE READER  ·  PARTNER  ·  KIDS  ·  FAMILY"


def cover():
    W, H = 2000, 1500
    base = np.array([238, 205, 210], float); base2 = np.array([228, 186, 194], float)
    g = np.linspace(0, 1, H)[:, None, None]
    bg = (base * (1 - g) + base2 * g) * np.ones((H, W, 1)) + np.random.default_rng(3).normal(0, 2.5, (H, W, 1))
    c = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(c)
    ft = lora(136, 720); fs = ImageFont.truetype(FD + "Poppins-Medium.ttf", 36)
    y0 = 28; i0 = ink_box((W, H), HEAD, ft, (1000, y0))
    ks = ink_box((W, H), SUB, fs, (1000, 0)); ys = i0[3] + 26 - ks[1]; isub = ink_box((W, H), SUB, fs, (1000, ys))
    gap = check_text_gap([i0, isub])
    d.text((1000, y0), HEAD, font=ft, fill=gs.rgb(PAL["deep"]), anchor="ma")
    d.text((1000, ys), SUB, font=fs, fill=gs.rgb(PAL["primary"]), anchor="ma")
    pieces = [  # (name, page, slot n, slot i, width, center, angle)
        ("cover family", 3, 3, 2, 960, (535, 560), 5),
        ("cover kids", 3, 3, 1, 960, (530, 880), -3),
        ("cover love", 3, 3, 0, 970, (540, 1190), 3),
        ("family 01", 9, 5, 0, 960, (1490, 480), -4),
        ("partner 02", 5, 5, 1, 960, (1500, 750), 3),
        ("kids 04", 7, 5, 3, 960, (1480, 1010), -3),
        ("partner 01", 5, 5, 0, 970, (1490, 1280), 2),
    ]
    masks, stats = [], []
    for name, pg, n, i, w, ctr, ang in pieces:
        crop = P(pg).crop(slot(n, i))
        layer, mask = put(c, crop, w, ctr, ang)
        masks.append((name, layer, mask))
    comp = c.convert("RGB")
    # opacity: the TOP piece of each fan must show its own pixels unchanged
    for name, layer, mask in [masks[2], masks[6]]:
        a, b = check_opaque(comp, layer, mask, name)
        r = float(np.percentile(a / b, 1)); stats.append(round(r, 3))
        assert r >= 0.85, (name, "see-through", r)
    union = np.zeros((H, W), bool)
    for _, _, m in masks: union |= np.asarray(m) > 0
    share = float(union.mean())
    for _, _, m in masks:
        bb = m.getbbox(); assert bb[0] >= 0 and bb[1] > isub[3] and bb[2] <= W and bb[3] <= H, ("piece off canvas or over text", bb)
    assert share >= 0.60, ('real pages under 60%', share)
    th = i0[3] - i0[1]
    assert th >= 0.09 * H, th
    assert i0[0] >= 260 and i0[2] <= 1740 and isub[0] >= 260 and isub[2] <= 1740, (i0, isub)
    last5 = json.load(open(HERE + "/last5.json"))["covers"]
    assert len(last5) == 5 and not [x["id"] for x in last5 if "flat-lay" in families(x)], "flat-lay on the last 5"
    return comp, {"pagesShare": round(share, 3), "headlinePct": round(th / H * 100, 1), "textGap": gap, "opaque": stats,
                  "last5": [x["id"] for x in last5]}


COVER_PAGES = {3, 5, 7, 9}
im, info = cover()
gs.save_jpeg(im, OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s = min(im.size); x = (im.width - s) // 2
im.crop((x, 0, x + s, s)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
print("cover", info)

# ------------------------------------------------------------------ 2 inside: 6 pages the cover does not show
idx = [2, 4, 6, 8, 11, 12]
assert not COVER_PAGES & set(idx)
p2 = gs.paper(PAL["paper"]); _d2 = ImageDraw.Draw(p2)
gs._header(_d2, PAL, "What's Inside", "11 pages  ·  30 written coupons  ·  6 blanks  ·  envelope")
_w, _gx = 450, 60; _x0 = (2000 - (3 * _w + 2 * _gx)) // 2; _ph = round(_w * 1650 / 1275)
for k, i in enumerate(idx):
    gs.place(p2, P(i), _w, (_x0 + (k % 3) * (_w + _gx), 300 + (k // 3) * (_ph + 40)), shadow=0.22)
assert 300 + 2 * _ph + 40 < 1600
gs._check_safe()
gs.save_jpeg(p2, OUT + "/2-inside.jpg")

# ------------------------------------------------------------------ 3 close-up: page 8 with names typed in (real fill)
from pypdf import PdfReader, PdfWriter
r = PdfReader(PDF); w = PdfWriter(); w.append(r)
names = {"for": "Mia", "from": "Mom and Dad"}
pg8 = w.pages[7]
vals = {a.get_object()["/T"]: names[a.get_object()["/T"].split()[-1]] for a in pg8["/Annots"]}
w.update_page_form_field_values(pg8, vals, auto_regenerate=False); w.set_need_appearances_writer(True)
w.write(HERE + "/sample-filled.pdf")
subprocess.run(["pdftoppm", "-r", "150", "-png", "-f", "8", "-l", "8", HERE + "/sample-filled.pdf", HERE + "/s8"], check=True)
s8 = Image.open(glob.glob(HERE + "/s8*.png")[0]).convert("RGB")
assert 8 not in COVER_PAGES
p3 = gs.preview_closeup(s8, PAL, "Type the Names In", "Click FOR and FROM in free Adobe Acrobat Reader", crop=(0.1, 0.06, 0.9, 0.604))
gs.save_jpeg(p3, OUT + "/3-closeup.jpg")

# ------------------------------------------------------------------ 4 included: count + items, the PDF cover page
items = ["30 written coupons", "Partner, kids, family: 10 each", "6 blank type-in coupons", "3 front + 3 back covers",
         "Fold-up gift envelope", "101 type-in fields", "US Letter PDF, print at home"]
p4 = gs.preview_included(pages, PAL, "13-Page PDF", items, P(1))
gs.save_jpeg(p4, OUT + "/4-included.jpg")

# ------------------------------------------------------------------ 5 three real pages fanned big: how-to, back covers, envelope
W5, H5 = 2000, 1600
im5 = gs.paper(PAL["tint"], (W5, H5)).convert("RGBA")
d5 = ImageDraw.Draw(im5)
gs._header(d5, PAL, "Cut, Stack and Gift It", "How-to page, back covers and a fold-up envelope")
for pg, wd, ctr, ang in [(2, 760, (560, 960), 5), (12, 760, (1440, 960), -5), (4, 780, (1000, 990), 0)]:
    assert pg not in COVER_PAGES
    put(im5, P(pg), wd, ctr, ang, shadow=60)
gs._check_safe()
gs.save_jpeg(im5.convert("RGB"), OUT + "/5-fanned.jpg")
for f in sorted(glob.glob(OUT + "/*.jpg")):
    print(os.path.basename(f), Image.open(f).size, os.path.getsize(f))
json.dump(info, open(OUT + "/cover_info.json", "w"))
