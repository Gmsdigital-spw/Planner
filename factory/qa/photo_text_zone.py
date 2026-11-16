"""Photo text-zone check: measures ALL text ink in a listing photo, page body text included.

Why (bug rule, Nov 16, 2026): photos.py's safe_text() only measured the overlay headlines it drew, so
real page and slide text placed by gs.place() ran to x 102-1893 while the pre-flight said "Text inside
x 260 to 1740" passed (Left Right Christmas Game, Judge FAIL 88, rule fail).

How: a pixel is text ink when it sits 60+ levels darker than the brightest pixel within 4 px (dark text
on a light ground) or 60+ levels lighter than the darkest (light text on a dark band). Thick shapes
(page stripes, TV bezels, filled bands) are removed with a 13 px morphological opening, so only thin
strokes are left; glyph-sized pieces (200 px or less) that do not touch a thick shape and are not
long 45-degree bars (candy stripes on small pages) count. A column counts when it holds 4+ stroke pixels. Reports the first and last text column.

  python3 factory/qa/photo_text_zone.py photo2.jpg photo3.jpg ...   (exit 1 if any text is outside)
  from photo_text_zone import text_span; x0, x1 = text_span(path_or_image)
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SAFE_L, SAFE_R = 260, 1740


def _diagonal_bar(c):
    """An elongated bar at 30-60 degrees: a candy stripe on a small page, not a letter."""
    ys, xs = np.nonzero(c)
    if len(xs) < 8: return False
    ev, vec = np.linalg.eigh(np.cov(np.vstack([xs, ys])))
    if ev[0] <= 0 or ev[1] / ev[0] < 2.8: return False     # elongated (variance ratio 2.8+)
    ang = abs(np.degrees(np.arctan2(vec[1, 1], vec[0, 1]))) % 180
    return 30 <= ang <= 60 or 120 <= ang <= 150


def text_mask(im):
    im = Image.open(im) if isinstance(im, str) else im
    L = np.asarray(im.convert("L")).astype(np.int16)
    mx = ndi.maximum_filter(L, size=41); mn = ndi.minimum_filter(L, size=41)
    dark = (mx - L > 60) & (mx > 150)          # darker than the light ground within 20 px
    light = (L - mn > 60) & (mn < 110)         # lighter than the dark ground within 20 px
    st = np.ones((13, 13), bool)
    out = np.zeros_like(dark)
    dark_ground = ndi.binary_dilation(ndi.binary_opening(L < 110, structure=np.ones((25, 25), bool)), iterations=20)
    for m in (dark, light):
        if m is light: m = m & dark_ground           # light text only counts on a real dark band, not between thin stripes
        thick = ndi.binary_opening(m, structure=st)
        near = ndi.binary_dilation(thick, iterations=6)
        thin = m & ~ndi.binary_dilation(thick, iterations=2)
        lab, n = ndi.label(thin, structure=np.ones((3, 3)))
        edt = ndi.distance_transform_edt(thin)
        for k, sl in enumerate(ndi.find_objects(lab), 1):
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            # glyph-sized and not a chip off a thick shape (stripe corners, bezel and band edges)
            c = lab[sl] == k
            if max(h, w) <= 200 and min(h, w) >= 4 and c.sum() >= 20 and not (near[sl] & c).any() and not _diagonal_bar(c) \
                    and edt[sl][c].max() < 5.5:                  # strokes under about 11 px: type, not a stripe
                out[sl] |= c
    return out


def text_span(im, min_px=4):
    m = text_mask(im)
    cols = np.where(m.sum(0) >= min_px)[0]
    if not len(cols): return None, None
    return int(cols[0]), int(cols[-1])


def check(paths, lo=SAFE_L, hi=SAFE_R):
    ok = True
    for p in paths:
        x0, x1 = text_span(p)
        good = x0 is None or (x0 >= lo and x1 <= hi)
        ok &= good
        print(f"{'PASS' if good else 'FAIL'} {p}: text x {x0}-{x1} (zone {lo}-{hi})")
    return ok


if __name__ == "__main__":
    sys.exit(0 if check(sys.argv[1:]) else 1)
