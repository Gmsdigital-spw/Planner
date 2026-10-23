# Inspect fix (Atlas, 2026-10-23): extras photo had ~30% empty bottom band (pages 600 px wide);
# now 3 pages 636 px wide, centred between header and strip. Usage: photo5_v2.py <pages_dir> <out.jpg>
import sys, glob; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import ImageDraw, Image
pal = gs.palette("berry")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob(sys.argv[1] + "/p-*.png"))]
assert len(pages) == 17
im = gs.paper(pal["tint"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Invites, Notes and Name Tags", "Prints at home on US Letter or A4")
w, gap = 636, 12; x0 = (gs.IW - (3 * w + 2 * gap)) // 2
ph = int(w * pages[3].height / pages[3].width)
y0 = 290 + (gs.IH - 110 - 290 - ph) // 2
for k, i in enumerate((3, 13, 15)):
    gs.place(im, pages[i], w, (x0 + k * (w + gap), y0), shadow=0.22)
d = ImageDraw.Draw(im)
gs._strip(im, d, pal)
gs._check_safe()
print(gs.save_jpeg(im, sys.argv[2]))
