import sys; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs, glob
from gm_style import ImageDraw, Image
pal = gs.palette("evergreen")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob("/home/claude/kit/pages/prod-santa-mail-bundle/p-*.png"))]
assert len(pages) == 14
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._text(d, (gs.IW/2, 48), "6 Different Letters from Santa", gs.font("serifB", 80), gs.rgb(pal["deep"]), anchor="ma")
sub = "Nice List · First Christmas · Big Sibling · Kindness · Hard Year · New Home"
f = gs._fit([sub], "sansM", 40, 1470, minsize=30)
gs._text(d, (gs.IW/2, 152), sub, f, gs.rgb(pal["primary"]), anchor="ma")
w, gap, vgap = 474, 29, 30
ph = int(w * 1650 / 1275); x0 = (gs.IW - (3*w + 2*gap)) // 2; y0 = 228
boxes = []
for k, i in enumerate([2, 3, 4, 5, 6, 7]):
    boxes.append(gs.place(im, pages[i], w, (x0 + (k % 3)*(w+gap), y0 + (k//3)*(ph+vgap)), shadow=0.22))
yb = y0 + 2*ph + vgap + 26
gs._text(d, (gs.IW/2, yb), "Type the name, 3 good things and the P.S. in free Adobe Reader", gs.font("sans", 38), gs.rgb(gs.MUTED), anchor="ma")
print(boxes, yb, f.size)
gs._check_safe()
print(gs.save_jpeg(im, "/home/claude/build/santa/photos/p2-inside-v2.jpg"))
