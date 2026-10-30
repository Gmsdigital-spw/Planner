"""Five listing photos for Office Christmas Party Games. python3 photos.py <pdf> <outdir>"""
import sys, os
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs, place
from PIL import Image, ImageDraw, ImageFont

PDF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("honey")
BERRY = (156, 58, 65)
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-xmas-office-party-games")
pages = [Image.open(f"/home/claude/kit/pages/prod-xmas-office-party-games/p-{i:02d}.png").convert("RGB") for i in range(1, 18)]
P = lambda n: pages[n - 1]          # n = PDF page number (footer number)
FD = "/usr/share/fonts/truetype/google-fonts/"


def lora(size, w=650):
    f = ImageFont.truetype(FD + "Lora-Variable.ttf", size)
    try: f.set_variation_by_axes([w])
    except Exception: pass
    return f


def pad_to(page, aspect):
    """Pad a page with white at the sides so the slot shows the WHOLE page (footer included)."""
    w = round(page.height * aspect)
    if w <= page.width: return page
    im = Image.new("RGB", (w, page.height), (255, 255, 255)); im.paste(page, ((w - page.width) // 2, 0)); return im


# ------------------------------------------------------------------ cover checks (Oct 30 fix round 1, root check)
import json, numpy as np
from PIL import ImageFilter
FAMILY_BY_NUM = {1: "collage", 2: "device", 3: "tablet", 4: "hero-page", 5: "grid", 6: "flat-lay"}


def families(c):
    """Layout families a published cover belongs to, from coverStyle / coverLook.scene / coverLook.tool."""
    f = set(); cs = c.get("coverStyle")
    if isinstance(cs, int): f.add(FAMILY_BY_NUM.get(cs, str(cs)))
    txt = " ".join(str(v) for v in (cs, c.get("scene"), c.get("tool")) if v).lower()
    for key, fam in [("clipboard", "clipboard-scene"), ("christmas", "holiday-table"), ("table", "holiday-table"),
                     ("fun_covers", "fun-card"), ("collage", "collage"), ("frame", "frame"), ("tablet", "tablet"),
                     ("device", "device"), ("grid", "grid"), ("flat", "flat-lay"), ("hero", "hero-page")]:
        if key in txt: f.add(fam)
    return f


def check_family(mine, last5_path):
    last5 = json.load(open(last5_path))["covers"]
    hits = [c["id"] for c in last5 if mine in families(c)]
    assert len(last5) == 5, ("need the last 5 published covers", len(last5))
    assert not hits, ("cover layout family already on the last 5 published covers", mine, hits)
    return [sorted(families(c)) for c in last5]


def check_opaque(comp, layer_rgb, mask, name):
    """Page must not let the scene print through: inside the page (eroded), the composite keeps >= 85%
    of the page's own brightness at the 1st percentile (soft shading allowed, see-through is not)."""
    from scipy import ndimage
    m = ndimage.binary_erosion(np.asarray(mask) == 255, iterations=4)
    a = np.asarray(comp.convert("L"), np.float32)[m]; b = np.asarray(layer_rgb.convert("L"), np.float32)[m]
    k = b > 60
    ratio = np.percentile(a[k] / b[k], 1)
    assert ratio >= 0.85, (name, "page is see-through / darkened by the scene", round(float(ratio), 3))
    return round(float(ratio), 3)


def check_inside(mask, paper, name):
    """Every page pixel (alpha > 0) sits inside the scene's paper rect (x0, y0, x1, y1): no overhang."""
    bb = mask.getbbox()
    assert bb and bb[0] >= paper[0] and bb[1] >= paper[1] and bb[2] <= paper[2] and bb[3] <= paper[3], \
        (name, "page overhangs the scene paper", bb, paper)
    return bb


def check_no_outline(comp, mask, name):
    """No hard dark outline: the 1-3 px ring outside the page is not much darker than 40-60 px out."""
    from scipy import ndimage
    dist = ndimage.distance_transform_edt(np.asarray(mask) == 0)      # px distance outside the page
    L = np.asarray(comp.convert("L"), np.float32)
    near, far = L[(dist >= 1) & (dist <= 3)].mean(), L[(dist >= 40) & (dist <= 60)].mean()
    assert near >= 0.75 * far, (name, "dark outline round the page", round(near), round(far))
    return round(float(near / far), 2)


def ink_box(size, text, font, xy, anchor="ma"):
    """Real ink bbox of one text line (descenders included), drawn alone on a blank mask."""
    m = Image.new("L", size, 0); ImageDraw.Draw(m).text(xy, text, font=font, fill=255, anchor=anchor); return m.getbbox()


def check_text_gap(boxes, min_gap=12):
    """Fix round 2 (Oct 30): no two text lines' ink within min_gap px (bbox gap, stricter than pixel distance).
    Lines that overlap in x must be min_gap apart vertically; returns the smallest gap found."""
    gaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[2] <= b[0] or b[2] <= a[0]: continue
            gap = max(b[1] - a[3], a[1] - b[3]); gaps.append(gap)
            assert gap >= min_gap, ("text lines' ink too close", i, j, gap, a, b)
    return min(gaps) if gaps else None


# ------------------------------------------------------------------ 1 cover: collage of 3 real pages on pine green
HEADLINE = ["24 No-Prep", "Office Party Games"]
PINE, PINE2, GOLD, CREAM = (28, 64, 50), (17, 44, 35), (240, 198, 116), (251, 246, 236)


def put_page(canvas, page, w, center, angle):
    """Opaque page (alpha 255 inside), soft offset shadow. Returns (layer_rgb, mask) on the full canvas."""
    p = page.resize((w, round(page.height * w / page.width)), Image.LANCZOS).convert("RGBA")
    p = p.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = round(center[0] - p.width / 2), round(center[1] - p.height / 2)
    mask = Image.new("L", canvas.size, 0); mask.paste(p.split()[3], (x, y))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", p.size, (5, 15, 10, 255)), (x + 12, y + 24), p.split()[3].point(lambda v: 75 if v else 0))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); layer.paste(p, (x, y))
    canvas.alpha_composite(layer)
    return layer.convert("RGB"), mask


def cover():
    W, H = 2000, 1600
    g = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array(PINE) * (1 - g) + np.array(PINE2) * g) * np.ones((H, W, 1))
    bg += np.random.default_rng(5).normal(0, 3, (H, W, 1))
    c = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(c)
    ft = lora(160, 700); fs = ImageFont.truetype(FD + "Poppins-Medium.ttf", 40)
    sub = "PRINTABLE PDF  ·  6 TO 60 COWORKERS  ·  45-MIN RUN SHEET"
    # fix round 2: place each line from the INK of the line above (headline lines 16 px apart, subline 24 px
    # under the lowest descender of "Party"), so a descender can never run into the next line
    y0 = -16; i0 = ink_box((W, H), HEADLINE[0], ft, (1000, y0))
    k1 = ink_box((W, H), HEADLINE[1], ft, (1000, 0)); y1 = i0[3] + 16 - k1[1]; i1 = ink_box((W, H), HEADLINE[1], ft, (1000, y1))
    ks = ink_box((W, H), sub, fs, (1000, 0)); ys = i1[3] + 24 - ks[1]; isub = ink_box((W, H), sub, fs, (1000, ys))
    text_gap = check_text_gap([i0, i1, isub])
    d.text((1000, y0), HEADLINE[0], font=ft, fill=GOLD, anchor="ma")
    d.text((1000, y1), HEADLINE[1], font=ft, fill=CREAM, anchor="ma")
    d.text((1000, ys), sub, font=fs, fill=(196, 222, 205), anchor="ma")
    assert i0[1] >= 24, ("headline ink too near the top edge", i0)
    heads = [d.textbbox((1000, y0), HEADLINE[0], font=ft, anchor="ma"), d.textbbox((1000, y1), HEADLINE[1], font=ft, anchor="ma"),
             d.textbbox((1000, ys), sub, font=fs, anchor="ma")]
    paper = (0, 0, W, H)          # the scene's surface is the whole pine board
    placed = []
    for name, n, w, ctr, ang in [("bingo", 10, 800, (455, 1015), -4), ("trivia", 12, 800, (1545, 1015), 4),
                                 ("finder", 3, 900, (1000, 1030), 0)]:
        layer, mask = put_page(c, P(n), w, ctr, ang)
        placed.append((name, layer, mask))
        check_opaque(c, layer, mask, name); check_inside(mask, paper, name); check_no_outline(c, mask, name)
    # finder is on top: its eroded interior must still be the page itself after everything is drawn
    img = c.convert("RGB")
    union = Image.new("L", (W, H), 0)
    for _, _, m in placed: union = Image.fromarray(np.maximum(np.asarray(union), np.asarray(m)))
    share = (np.asarray(union) > 0).mean()
    assert share >= 0.60, ("real pages under 60% of the frame", round(float(share), 3))
    th = heads[0][3] - heads[0][1]
    assert th >= 0.09 * H, ("headline under 9% of the cover height", th)
    assert all(b[0] >= 200 and b[2] <= 1800 for b in heads), ("headline outside the centred square", heads)
    assert isub[3] < 1030 - 900 * 1.294 / 2, ("sub line hidden under the finder page", heads[2])
    fam = check_family("collage", os.path.join(os.path.dirname(os.path.abspath(__file__)), "last5.json"))
    return img, {"pagesShare": round(float(share), 3), "headlinePx": th, "headlinePct": round(th / H * 100, 1), "last5": fam, "textGapMin": text_gap,
                 "inkLines": [i0, i1, isub]}


# ------------------------------------------------------------------ 2 inside: 6 pages 3x2 at 470 px
def inside():
    im = gs.paper(PAL["paper"]); d = ImageDraw.Draw(im)
    gs._header(d, PAL, "What's Inside", "Run sheet, how-to cards, scramble, letter lists, fact cards, score sheet")
    idx = [2, 4, 11, 13, 14, 15]          # fix round 2: no cover page (3 finder, 10 bingo, 12 trivia)
    w, gx = 470, 50; ph = int(w * 1.294); x0 = (2000 - (3 * w + 2 * gx)) // 2
    for k, n in enumerate(idx):
        gs.place(im, P(n), w, (x0 + (k % 3) * (w + gx), 300 + (k // 3) * (ph + 36)), shadow=0.22)
    gs._check_safe(); return im


CROP = 0.68
# ------------------------------------------------------------------ 3 close-up: the 45-minute run sheet
def closeup():
    return gs.preview_closeup(P(2), PAL, "Your Party, Planned", "A 45-minute run sheet: just print and host",
                              crop=(0, 0, 1, CROP))


# ------------------------------------------------------------------ 4 included: a row of 4 real pages across 90% of the width
def included():
    im = gs.paper(PAL["paper"]); d = ImageDraw.Draw(im)
    gs._header(d, PAL, "24 Games, 15 Pages", "Print what your group needs, as many times as you like")
    w, gx = 440, 30; x0 = (2000 - (4 * w + 3 * gx)) // 2
    boxes = [gs.place(im, P(n), w, (x0 + k * (w + gx), 300), shadow=0.22) for k, n in enumerate([6, 7, 11, 14])]   # fix round 2: none of the cover's pages
    span = boxes[-1][2] - boxes[0][0]
    assert span >= 0.6 * 2000, ("real pages under 60% of the width", span)
    items = ["45-minute run sheet", "Game finder by group size", "24 how-to-play game cards", "Coworker bingo card",
             "Word scramble + trivia", "Letter Lists + fact cards", "Team score sheet", "Answer keys"]
    f = gs.font("sans", 44); y0 = boxes[0][3] + 70
    for i, it in enumerate(items):
        x = gs.SAFE_L + (i // 4) * 760; y = y0 + (i % 4) * 84
        d.ellipse([x, y + 16, x + 16, y + 32], fill=gs.rgb(PAL["primary"]))
        gs._text(d, (x + 36, y), it, f, gs.rgb(gs.INK))
    assert y0 + 4 * 84 < 1600 - 120, "item list runs into the strip"
    gs._strip(im, d, PAL); gs._check_safe(); return im, round(span / 2000, 2)


# ------------------------------------------------------------------ 5 close-up of game cards + bingo fanned
def fanned():
    im = gs.paper(PAL["tint"]); d = ImageDraw.Draw(im)
    gs._header(d, PAL, "No Props. No Prep.", "Pens and these pages are all you need")
    # fix round 2: letter lists, score sheet, how-to 17-20 (cover shows finder, bingo, trivia)
    gs.place(im, P(13), 720, (190, 330), angle=4, shadow=0.25)
    gs.place(im, P(15), 720, (1090, 330), angle=-4, shadow=0.25)
    gs.place(im, P(8), 840, (580, 280), angle=0, shadow=0.3)
    gs._check_safe(); return im


if __name__ == "__main__":
    c, info = cover()
    inc, inc_share = included()
    sizes = {}
    for name, im in [("1-cover", c), ("2-inside", inside()), ("3-closeup", closeup()), ("4-included", inc), ("5-fanned", fanned())]:
        sizes[name] = gs.save_jpeg(im, f"{OUT}/{name}.jpg")
    gs.thumb_check(c, f"{OUT}/thumb400.png")
    s = min(c.size); x = (c.width - s) // 2
    c.crop((x, 0, x + s, s)).resize((300, 300), Image.LANCZOS).save(f"{OUT}/thumb300.png")
    print(sizes, info, "photo 4 pages width share", inc_share)
    COVER_PAGES = {3, 10, 12}
    for name, used in [("2-inside", [2, 4, 11, 13, 14, 15]), ("4-included", [6, 7, 11, 14]), ("5-fanned", [13, 15, 8])]:
        assert not COVER_PAGES & set(used), (name, "repeats a page the cover shows", COVER_PAGES & set(used))
