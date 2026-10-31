"""Five listing photos for the Christmas Coupon Book, rework Oct 31 (fix list 3 and 4). python3 photos.py"""
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
CW, CX = 460, (gs.PW - 460) / 2          # same as build.py (6.4 in coupons)
TOP, BOT = PH - M - 52, M + 20


def lora(size, w=700):
    f = ImageFont.truetype(FD + "Lora-Variable.ttf", size)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f


def slot(n, i, gap=None):
    """Pixel crop of coupon/cover slot i (0-based) of n stacked on a page (same maths as build.py)."""
    gap = gap if gap is not None else (16 if n == 3 else 12)   # covers page stacks 3 with 16 pt gaps
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
        ("partner 03", 5, 5, 2, 970, (1490, 1280), 2),   # fix round: was partner 01, a second "01" next to family 01
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
idx = [2, 4, 6, 8, 10, 11]
assert not COVER_PAGES & set(idx)
p2 = gs.paper(PAL["paper"]); _d2 = ImageDraw.Draw(p2)
gs._header(_d2, PAL, "What's Inside", "11 pages  ·  30 written coupons  ·  5 blanks  ·  envelope")
_w, _gx = 450, 60; _x0 = (2000 - (3 * _w + 2 * _gx)) // 2; _ph = round(_w * 1650 / 1275)
for k, i in enumerate(idx):
    gs.place(p2, P(i), _w, (_x0 + (k % 3) * (_w + _gx), 300 + (k // 3) * (_ph + 40)), shadow=0.22)
assert 300 + 2 * _ph + 40 < 1600
gs._check_safe()
gs.save_jpeg(p2, OUT + "/2-inside.jpg")

# ------------------------------------------------------------------ 3 close-up: page 11 (blank coupons) typed in for real
from pypdf import PdfReader, PdfWriter


def filled_page(pg, vals_by_suffix, tag):
    r = PdfReader(PDF); w = PdfWriter(); w.append(r)
    page = w.pages[pg - 1]; vals = {}
    for an in page["/Annots"]:
        t = an.get_object()["/T"]
        for suf, v in vals_by_suffix.items():
            if t.endswith(suf): vals[t] = v
    w.update_page_form_field_values(page, vals, auto_regenerate=False); w.set_need_appearances_writer(True)
    w.write(HERE + f"/sample-{tag}.pdf")
    for f in glob.glob(HERE + f"/s{tag}*.png"): os.remove(f)
    subprocess.run(["pdftoppm", "-r", "150", "-png", "-f", str(pg), "-l", str(pg), HERE + f"/sample-{tag}.pdf", HERE + f"/s{tag}"], check=True)
    return Image.open(glob.glob(HERE + f"/s{tag}*.png")[0]).convert("RGB"), len(vals)


s11, nv = filled_page(11, {"1 title": "Breakfast at the Diner", "1 line 1": "Pancakes, hot cocoa and the corner booth.",
                           "1 line 2": "Any Saturday in January, my treat.", "1 for": "GRANDMA AND GRANDPA", "1 from": "Ella and Noah",
                           "2 title": "One Snow Day Off", "2 line 1": "No homework, sledding all afternoon.",
                           "2 line 2": "Good on any day the snow sticks.", "2 for": "Lily", "2 from": "Mom and Dad",
                           "3 title": "Car Detailing Day", "3 line 1": "Washed, waxed and vacuumed inside.",
                           "3 line 2": "You pick the day, I bring the buckets.", "3 for": "Dad", "3 from": "Your favorite son",
                           "4 title": "Coffee Date with Me", "4 line 1": "Your usual order and a whole hour to talk.",
                           "4 line 2": "No phones on the table.", "4 for": "AUNT ROSE", "4 from": "Maya"}, "11")
assert nv == 20, nv
assert 11 not in COVER_PAGES
_t, _b = slot(5, 0), slot(5, 2)
_c3 = s11.crop((_t[0] - 30, _t[1] - 4, _t[2] + 30, _b[3] + 4))   # three whole 6.4 x 1.6 in blanks, typed
p3 = gs.paper(PAL["tint"]).convert("RGBA"); _d3 = ImageDraw.Draw(p3)
gs._header(_d3, PAL, "Write Your Own Coupons", "5 blanks, book size: type a title, two lines and the names")
_l3, _ = put(p3, _c3, 1500, (1000, 960), 0, shadow=60)
_bb3 = _l3.getbbox(); assert _bb3[2] - _bb3[0] >= 0.6 * 2000 and _bb3[1] > 260 and _bb3[3] <= 1600, _bb3
gs._check_safe(); p3 = p3.convert("RGB")
gs.save_jpeg(p3, OUT + "/3-closeup.jpg")

# ------------------------------------------------------------------ 4 included: the 3 front covers fanned big over their coupon stacks
# Fix round Oct 31 (Judge fix 3): was the PDF cover + thank-you page.
im4 = gs.paper(PAL["paper"]).convert("RGBA"); d4 = ImageDraw.Draw(im4)
gs._header(d4, PAL, "3 Books in One PDF", "Partner, kids, family  ·  30 written coupons  ·  5 blanks  ·  envelope")
gs._check_safe()
STACKS = [(0, 5, (720, 650), -3), (1, 7, (1280, 980), 3), (2, 9, (720, 1300), -2)]   # cover slot, first coupon page, centre, angle
union4 = np.zeros((im4.height, im4.width), bool)
for ci, cp, (cx, cy), ang in STACKS:
    for k, (dx, dy, da) in enumerate([(150, -95, 5), (80, -55, 2.5)]):            # two coupons peeking out behind
        _, mk = put(im4, P(cp).crop(slot(5, k)), 1060, (cx + dx * (1 if cx < 1000 else -1), cy + dy), ang + da, shadow=50)
        union4 |= np.asarray(mk) > 0
    _, mk = put(im4, P(3).crop(slot(3, ci)), 1100, (cx, cy), ang, shadow=70)
    union4 |= np.asarray(mk) > 0
    bb = mk.getbbox(); assert bb[0] >= 0 and bb[1] > 250 and bb[2] <= im4.width and bb[3] <= im4.height, bb
cols = np.where(union4.any(0))[0]; wshare = (cols[-1] - cols[0]) / im4.width
assert wshare >= 0.60 and union4.mean() >= 0.45, (wshare, union4.mean())
print("photo 4 width share", round(wshare, 2), "area", round(float(union4.mean()), 2))
assert 3 in COVER_PAGES   # same real pages as the cover, shown as whole books here
gs.save_jpeg(im4.convert("RGB"), OUT + "/4-included.jpg")

# ------------------------------------------------------------------ 5 the gift envelope (page 12, not in photo 2), names typed in, big and centred
s12, nv = filled_page(12, {"Envelope to": "The Carter Family", "Envelope from": "With love, Sam"}, "12")
assert nv == 2 and 12 not in idx and 12 not in COVER_PAGES
W5, H5 = 2000, 1600
im5 = gs.paper(PAL["tint"], (W5, H5)).convert("RGBA")
d5 = ImageDraw.Draw(im5)
gs._header(d5, PAL, "Fold-Up Gift Envelope", "Names typed in  ·  2.1 in deep, 0.25 in gussets, holds 3 books")
# Fix round Oct 31 (Judge fix 4): crop to the front panel with its gussets and names (no big empty back panel)
_FT = (TOP - 6) - 70 - 151.2 - 18; _ex = gs.PW / 2 - 475 / 2
crop = s12.crop((round((_ex - 26) * K), round((PH - _FT - 24) * K), round((_ex + 475 + 26) * K), round((PH - _FT + 151.2 + 8) * K)))
_l5, _ = put(im5, crop, 1760, (1000, 900), 0, shadow=60)
_bb5 = _l5.getbbox(); assert _bb5[1] > 260 and _bb5[3] <= H5 and _bb5[2] - _bb5[0] >= 0.8 * W5, _bb5
gs._check_safe()
gs.save_jpeg(im5.convert("RGB"), OUT + "/5-envelope.jpg")
for f in sorted(glob.glob(OUT + "/*.jpg")):
    print(os.path.basename(f), Image.open(f).size, os.path.getsize(f))
json.dump(info, open(OUT + "/cover_info.json", "w"))
