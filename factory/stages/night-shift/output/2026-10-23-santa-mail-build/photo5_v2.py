import sys; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs, glob
from gm_style import ImageDraw, Image
pal = gs.palette("evergreen")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob("/home/claude/kit/pages/prod-santa-mail-bundle/p-*.png"))]
assert len(pages) == 14
im = gs.paper(pal["tint"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Everything for Christmas Eve", "Nice List certificate, envelope labels and gift tags")
w, gap = 700, 50; x0 = (gs.IW - (2 * w + gap)) // 2
crops = [pages[i].crop((0, 0, pages[i].width, int(pages[i].height * 0.534))) for i in (11, 12)]
ch = [int(c.height * w / c.width) for c in crops]
right_h = sum(ch) + 40; cert_h = int(pages[8].height * w / pages[8].width)
top, bottom = 290, gs.IH - 110 - 30
y0 = top + max(0, (bottom - top - max(right_h, cert_h)) // 2)
print(gs.place(im, pages[8], w, (x0, y0 + (max(right_h, cert_h) - cert_h) // 2), angle=-1.5, shadow=0.25))
y = y0
for c, h in zip(crops, ch):
    print(gs.place(im, c, w, (x0 + w + gap, y), shadow=0.25)); y += h + 40
d = ImageDraw.Draw(im)
gs._strip(im, d, pal, "TYPE IN FREE ADOBE READER  ·  PRINT AT HOME")
gs._check_safe()
print(gs.save_jpeg(im, sys.argv[1]))
