"""Cut flat page/card images out of the shop's existing listing photos (product PDFs are encrypted in gw/vault)."""
import numpy as np
from PIL import Image, ImageDraw
from common import *

E = OUT + "/src/x/"
os.makedirs(E, exist_ok=True)

def refine(im, box, m=14, top_extra=0, dens=0.45):
    """Trim to a card's coloured outline: find outer columns/rows that are mostly outline-coloured."""
    x0, y0, x1, y1 = box
    X0, Y0 = max(0, x0 - m), max(0, y0 - m - top_extra)
    c = np.array(im.crop((X0, Y0, x1 + m, y1 + m))).astype(int)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    out = (r - g > 40) & (r < 235)          # reddish outline / header pixels
    cols = np.where(out.mean(0) > dens)[0]; rows = np.where(out.mean(1) > dens)[0]
    if len(cols) < 2 or len(rows) < 2:
        return im.crop(box)
    return im.crop((X0 + cols.min(), Y0 + rows.min(), X0 + cols.max() + 1, Y0 + rows.max() + 1))

def deskew_angle(im, box):
    best = None
    for a10 in range(-40, 41):
        a = a10 / 10
        r = im.rotate(a, resample=Image.BICUBIC, center=((box[0]+box[2])/2, (box[1]+box[3])/2))
        g = np.array(r.crop(box).convert("L")) > 245
        s = (g.mean(1) ** 2).sum() + (g.mean(0) ** 2).sum()
        if best is None or s > best[0]: best = (s, a)
    return best[1]

def white_bbox(im, thr=245, frac=0.5):
    a = np.array(im.convert("L")) > thr
    rows = np.where(a.mean(1) > frac)[0]; cols = np.where(a.mean(0) > frac)[0]
    return (cols.min(), rows.min(), cols.max() + 1, rows.max() + 1)

# 1 Santa letter (flat render in listing photo 3)
s3 = src("listing-photos/auto/prod-santa-mail-bundle/3.jpg")
s3.crop((421, 301, 1578, 1529)).save(E + "santa_letter.png")

# 2 Scavenger clue cards
p2 = src("pins/styled/prod-xmas-scavenger-hunt-2.jpg")
for i, b in enumerate([(207,769,539,971),(554,784,887,987),(197,1019,529,1219),(543,1034,875,1236),(185,1270,518,1472),(533,1285,865,1486)]):
    refine(p2, b, m=10, top_extra=45, dens=0.5).save(E + f"clue_big_{i}.png")
p3 = src("pins/styled/prod-xmas-scavenger-hunt-3.jpg")
approx = [(30,128,216,258),(222,124,408,258),(513,124,698,258),(705,128,890,260),
          (30,472,214,604),(222,470,408,604),(510,470,694,602),(705,472,890,606),
          (30,816,215,948),(222,816,408,948),(514,818,698,948),(706,816,890,950)]
for i, (a, b, c, d) in enumerate(approx):
    refine(p3, (a+40, b+480, c+40, d+480), m=12, dens=0.5).save(E + f"clue_sm_{i}.png")

# 3 Advent: 24 activity cards from the 6 activity pages in the styled cover
ad = src("listing-photos/styled/prod-advent-activities-cover.jpg")
pages = [(65,461,488,934),(549,463,968,933),(1034,464,1449,931),(1512,461,1935,934),
         (67,1003,485,1472),(549,1002,970,1474)]
n = 1
for (x0, y0, x1, y1) in pages:
    w, h = x1 - x0, y1 - y0
    for (ry0, ry1) in [(0.155, 0.585), (0.585, 1.0)]:
        for (rx0, rx1) in [(0.075, 0.495), (0.495, 0.925)]:
            ad.crop((int(x0 + rx0*w), int(y0 + ry0*h), int(x0 + rx1*w), int(y0 + ry1*h) - 2)).save(E + f"adv_{n:02d}.png"); n += 1

# 4 Thanksgiving pages (deskewed out of the tablet mock-up and the warm photos)
tg = src("listing-photos/styled/prod-thanksgiving-host-planner-cover.jpg")
for name, box in [("tg_timeline", (100,501,867,1498)), ("tg_turkey", (853,475,1620,1471))]:
    a = deskew_angle(tg, box)
    r = tg.rotate(a, resample=Image.BICUBIC, center=((box[0]+box[2])/2, (box[1]+box[3])/2))
    sub = r.crop((box[0]-20, box[1]-20, box[2]+20, box[3]+2))
    bb = white_bbox(sub, 240, 0.6)
    sub.crop(bb).save(E + name + ".png"); print(name, a, bb)
g5 = src("listing-photos/warm-covers/thanksgiving-planner/5-turkey.jpg")
box = (970, 100, 1900, 1160)
a = deskew_angle(g5, box)
r = g5.rotate(a, resample=Image.BICUBIC, center=((box[0]+box[2])/2, (box[1]+box[3])/2))
r.crop(box).save(E + "tg_grocery_raw.png"); print("grocery", a)

# 5 Gingerbread judge score card (flat render in listing photo 3)
gb = src("listing-photos/auto/prod-gingerbread-contest-kit/3.jpg")
gb.crop((410, 490, 1590, 1116)).save(E + "gb_card.png")
gbc = src("listing-photos/auto/prod-gingerbread-contest-kit/5.jpg")
gbc.crop((1100, 400, 1730, 780)).save(E + "gb_cert_raw.png")
