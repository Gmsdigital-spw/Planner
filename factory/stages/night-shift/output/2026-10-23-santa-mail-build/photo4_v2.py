import sys; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs, glob
from gm_style import ImageDraw, Image
pal = gs.palette("evergreen")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob("/home/claude/kit/pages/prod-santa-mail-bundle/p-*.png"))]
assert len(pages) == 14
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
d.rectangle([960, 0, gs.IW, gs.IH], fill=gs.rgb(pal["tint"]))
# fanned real pages, big: tags (back), certificate (middle), letter 1 (front)
b1=gs.place(im, pages[12], 560, (1110, 110), angle=5, shadow=0.22)
b2=gs.place(im, pages[8], 580, (1040, 190), angle=-3, shadow=0.24)
b3=gs.place(im, pages[10], 660, (990, 300), angle=1.5, shadow=0.28); print(b1,b2,b3)
d = ImageDraw.Draw(im)
x = gs.SAFE_L; y = 130
gs._text(d, (x, y), "13 Pages", gs.font("serifB", 120), gs.rgb(pal["deep"])); y += 160
d.rectangle([x, y, x + 120, y + 7], fill=gs.rgb(pal["accent"])); y += 56
f = gs.font("sans", 50)
for it in ["6 letters from Santa", "Nice List certificate", "Santa's Nice List", "Dear Santa wish list", "4 envelope labels", "12 gift tags", "How-to + delivery ideas"]:
    d.ellipse([x, y + 22, x + 20, y + 42], fill=gs.rgb(pal["primary"]))
    gs._text(d, (x + 46, y), it, f, gs.rgb(gs.INK)); y += 100
y += 20
gs._text(d, (x, y), "Type in free Adobe Reader", gs.font("sansM", 44), gs.rgb(pal["primary"])); y += 62
gs._text(d, (x, y), "No Canva account needed", gs.font("sansM", 44), gs.rgb(pal["primary"])); y += 62
assert y < gs.IH - 130, y
gs._strip(im, d, pal); gs._check_safe()
print(gs.save_jpeg(im, sys.argv[1]))
