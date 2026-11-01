"""Nov 1, 2026 (Warden cover redo, Grayson's GO of Oct 28, last on the list): one new per-listing cover.
  scavenger_grid()  4599447958  four real Little Elves clue cards, big and readable, in a 2x2 grid on
                                candy-cane stripes, title on a cream gift-tag panel (grid family)
Rules kept: real cards only (cut from the listing's own full-size photo 3 in
gw/out/files/warden-2026-11-01-full-6a81), words inside x 280-1720, title >= 9% of height,
no emoji stickers, square-edge band (x 230-270, y 8-40%) kept to plain stripes.
Run: COVERS_OUT=<dir> python3 covers_1101.py scavenger_grid
"""
import sys, glob
import numpy as np
from common import *
from covers import grain

FULL = ROOT + "/gw/out/files/warden-2026-11-01-full-6a81/"
def g(p): return Image.open(glob.glob(FULL + p + "*")[0]).convert("RGB")

RED = (155, 58, 64)  # the cards' own border colour

def card_full(box):
    return g("4599447958-r03").crop(box)

def card_rebuilt(x0, y0, w=605, h=425, cut=1522):
    """Bottom-row cards run off the photo's edge: keep the real header + rhyme, redraw the frame."""
    inner = g("4599447958-r03").crop((x0 + 4, y0 + 3, x0 + w - 4, cut))
    c = Image.new("RGB", (w, h), (255, 255, 255))
    c.paste(inner, (4, 3))
    d = ImageDraw.Draw(c)
    d.rectangle([0, cut - y0, w, h], fill=(255, 255, 255))
    d.rounded_rectangle([1, 1, w - 2, h - 2], 22, outline=RED, width=3)
    return c

def stripes():
    a = np.zeros((H, W, 3), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    band = ((xx + yy) // 70) % 2 == 0
    a[band] = (186, 36, 44); a[~band] = (206, 58, 62)
    return grain(Image.fromarray(a).convert("RGBA"), 5)

def scavenger_grid():
    c = stripes()
    cards = [card_full((380, 710, 985, 1135)), card_full((1017, 710, 1622, 1135)),
             card_rebuilt(380, 1167), card_rebuilt(1017, 1167)]
    # round 2 (side-by-side): round 1 (title band on top + card grid on red) read too close to
    # Christmas Charades, so the title moves to a tilted gift tag across the MIDDLE, cards above and below
    cw = 690
    pos = [(296, 20), (1014, 20), (296, 1004), (1014, 1004)]
    for im, (x, y), ang in zip(cards, pos, [1.2, -1.0, -0.8, 1.4]):
        p = up(im, w=cw)
        shadow_paste(c, p, x, y, angle=ang, blur=18, off=(0, 16), alpha=150, radius=20)
    tw, th = 1360, 450
    tag = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); td = ImageDraw.Draw(tag)
    n = 110  # notched gift-tag end on the left
    td.polygon([(n, 0), (tw - 30, 0), (tw - 1, 30), (tw - 1, th - 30), (tw - 30, th - 1), (n, th - 1), (0, th // 2)], fill=(255, 248, 238))
    td.line([(n + 18, 18), (tw - 34, 18), (tw - 19, 33), (tw - 19, th - 33), (tw - 34, th - 19), (n + 18, th - 19), (24, th // 2), (n + 18, 18)], fill=(46, 94, 62), width=5)
    td.ellipse([62, th // 2 - 20, 102, th // 2 + 20], fill=(186, 36, 44))
    ink = (110, 24, 32)
    ft = F("YoungSerif-Regular", 128)  # two lines so the title is >= 9% of the cover height
    while td.textlength("Scavenger Hunt", font=ft) > 1080: ft = F("YoungSerif-Regular", ft.size - 2)
    cx = n + (tw - n) // 2
    text_c(td, cx, 24, "Christmas", ft, ink)
    text_c(td, cx, 24 + int(ft.size * 1.05), "Scavenger Hunt", ft, ink)
    text_c(td, cx, 368, "24 RHYMING CLUE CARDS  \u00b7  AGES 4 TO 12", F("WorkSans-Bold", 44), (46, 94, 62), spacing=3)
    shadow_paste(c, tag, 320, 500, angle=-2.0, blur=22, off=(0, 18), alpha=160)
    # twine from the tag hole off the left edge
    d = ImageDraw.Draw(c)
    d.line([(0, 820), (150, 790), (395, 760)], fill=(236, 214, 170), width=7)
    return save(c, "4599447958.jpg")

if __name__ == "__main__":
    for fn in sys.argv[1:]:
        print(fn, globals()[fn]())
