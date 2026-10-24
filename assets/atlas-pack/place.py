"""Put REAL product pages onto the Atlas pack's blank paper, frame or phone screen.

    import sys; sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
    import place
    place.place("planner",   ["p1.png", "p2.png"], "out.jpg")   # open binder, 2 pages
    place.place("clipboard", ["p1.png"], "out.jpg")             # one page on a clipboard
    place.place("christmas", ["game1.png", "game2.png"], "out.jpg")  # 2 sheets, holiday table
    place.place("frame",     ["art.png"], "out.jpg")            # wall art in an oak frame
    place.place("phone",     ["screenshot.png"], "out.jpg")     # Ridgeline: a REAL screenshot

Each page is cropped to fill its slot (top kept), warped onto the slot's 4 corners and
multiplied by the scene's own light, so sun and shadow fall across the page. The phone only
paints where the screen is blank, so the thumb stays on top. Originals are never changed.
Output is a JPEG at the scene's size (landscape 1448x1086, vertical 941x1672).
"""
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))


def _r(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# name: (file, [slot corners TL, TR, BR, BL], keep_thumb)
SCENES = {
    "planner":   ("etsy/01_planner_mockup.png", [_r(220, 236, 676, 926), _r(778, 236, 1260, 926)], False),
    "clipboard": ("etsy/02_calendar_mockup.png", [_r(394, 142, 1020, 916)], False),
    "christmas": ("etsy/03_christmas_games_mockup.png",
                  [[(250, 274), (704, 273), (707, 879), (208, 879)],
                   [(737, 273), (1189, 273), (1231, 878), (737, 878)]], False),
    "frame":     ("etsy/04_framed_art_mockup.png", [_r(480, 136, 970, 732)], False),
    "phone":     ("ridgeline_local/07_homeowner_phone.png",
                  [[(397, 734), (583, 741), (568, 1078), (387, 1063)]], True),
}


def _fill(img, w, h):
    img = img.convert("RGB")
    s = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = (img.width - w) // 2
    return img.crop((x, 0, x + w, h))  # keep the top (titles)


def _warp(src, quad, size):
    W, H = src.size
    A, B = [], []
    for (x, y), (u, v) in zip(quad, [(0, 0), (W, 0), (W, H), (0, H)]):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        B += [u, v]
    c = np.linalg.solve(np.array(A, float), np.array(B, float))
    return np.asarray(src.transform(size, Image.PERSPECTIVE, tuple(c), Image.BICUBIC)).astype(np.float32)


def place(scene, pages, out=None, quality=90, scale=1.0):
    """scale > 1 upscales the scene first so the pages stay sharp (e.g. 1.38 -> 2000 px wide).
    With out=None the PIL image is returned instead of saved."""
    from scipy import ndimage
    fn, quads, keep_thumb = SCENES[scene]
    bg = Image.open(os.path.join(HERE, fn)).convert("RGB")
    if scale != 1.0:
        bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
        quads = [[(x * scale, y * scale) for x, y in q] for q in quads]
    a = np.asarray(bg).astype(np.float32)
    lum = a.mean(axis=2, keepdims=True)
    for page, quad in zip(pages, quads):
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        src = _fill(Image.open(page) if isinstance(page, str) else page, round(w * 2), round(h * 2))
        warped = _warp(src, quad, bg.size)
        poly = Image.new("L", bg.size, 0)
        ImageDraw.Draw(poly).polygon(quad, fill=255)
        m = np.asarray(poly) > 0
        region = lum[m]
        light = np.clip(lum / max(np.percentile(region, 97), 1), 0, 1.05)
        if keep_thumb:
            blank = (a.min(2) > 185) & ((a.max(2) - a.min(2)) < 40)
            m = ndimage.binary_closing(blank, iterations=3) & m
            light = np.full_like(lum, 0.97)
        mf = ndimage.gaussian_filter(m.astype(np.float32), 0.7)[..., None]
        a = a * (1 - mf) + np.clip(warped * light, 0, 255) * mf
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if out is None:
        return img
    img.save(out, "JPEG", quality=quality, optimize=True)
    return out
