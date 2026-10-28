import sys, glob
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from PIL import Image
pal = gs.palette("cranberry")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob("/home/claude/kit/pages/prod-xmas-charades-120/*.png"))]
assert len(pages) == 16, len(pages)
from PIL import ImageDraw
p2 = gs.paper(pal["paper"]); d2 = ImageDraw.Draw(p2)
f = gs.font("serifB", 88); t = "What's Inside"; tw = d2.textlength(t, font=f); gs._text(d2, ((2000 - tw) / 2, 50), t, f, gs.rgb(pal["deep"]))
f2 = gs.font("sans", 42); t2 = "120 cards in 3 colour-coded levels, Draw It mode, score sheet"; tw2 = d2.textlength(t2, font=f2); gs._text(d2, ((2000 - tw2) / 2, 165), t2, f2, gs.rgb(gs.INK))
for k, idx in enumerate([1, 4, 7, 10, 12, 13]):
    r, col = divmod(k, 3)
    gs.place(p2, pages[idx], 480, (220 + col * 540, 250 + r * 650))
gs._check_safe()
gs.save_jpeg(p2, "photo2.jpg")
p3 = gs.preview_closeup(pages[11], pal, "Adults and office party cards", "40 grown-up cards, gold band, numbered A01 to A40", crop=(0, 0.0, 1, 0.7437))
gs.save_jpeg(p3, "photo3.jpg")
p4 = gs.preview_included(pages, pal, "120 Cards", ["40 Kids cards", "40 Family cards", "40 Adults cards", "How to play + scoring", "Draw It mode + timer rules", "Team score sheet", "12 blank cards", "US Letter PDF"], pages[0])
gs.save_jpeg(p4, "photo4.jpg")
from PIL import ImageDraw
gs._TEXT_BOXES.clear() if hasattr(gs._TEXT_BOXES, "clear") else None
p5 = gs.paper(pal["paper"]); dd = ImageDraw.Draw(p5)
f = gs.font("serifB", 92); t = "Act it. Draw it. Keep score."
tw = dd.textlength(t, font=f); gs._text(dd, ((2000 - tw) / 2, 70), t, f, gs.rgb(pal["deep"]))
f2 = gs.font("sans", 44); t2 = "Draw It mode, team score sheet and 12 blank cards"
tw2 = dd.textlength(t2, font=f2); gs._text(dd, ((2000 - tw2) / 2, 200), t2, f2, gs.rgb(gs.INK))
gs.place(p5, pages[12], 720, (90, 340), angle=-4)
gs.place(p5, pages[14], 720, (1190, 340), angle=4)
gs.place(p5, pages[13], 760, (620, 300), angle=0)
gs._check_safe()
gs.save_jpeg(p5, "photo5.jpg")
for i, im in enumerate([p2, p3, p4, p5], 2): print(i, im.size)
