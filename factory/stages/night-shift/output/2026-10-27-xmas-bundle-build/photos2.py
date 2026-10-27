import sys, os
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import IW, IH, SAFE_L, rgb, font, _text, _strip, place, paper
from PIL import Image, ImageDraw
PD = "/home/claude/kit/pages/prod-xmas-party-mega-bundle"
pages = [Image.open(os.path.join(PD, f)).convert("RGB") for f in sorted(os.listdir(PD)) if f.endswith(".png")]
pal = gs.palette("evergreen")
# photo 2: 6 pages, 3x2, 470 px wide each
im = paper(pal["paper"]); d = ImageDraw.Draw(im)
_text(d, (IW / 2, 60), "What's Inside", font("serifB", 92), rgb(pal["deep"]), anchor="ma")
_text(d, (IW / 2, 175), "6 games, 12 awards, a gift swap and a contest", font("sans", 46), rgb(gs.MUTED), anchor="ma")
w = 470; h = round(w * 11 / 8.5); gap = 52; x0 = (IW - (3 * w + 2 * gap)) // 2; y0 = 262
for k, i in enumerate([2, 4, 7, 11, 13, 16]):
    place(im, pages[i], w, (x0 + (k % 3) * (w + gap), y0 + (k // 3) * (h + 30)), shadow=0.28)
gs.save_jpeg(im, "photo2_inside.jpg")
print("p2 bottom", y0 + h * 2 + 30, "x", x0, x0 + 3 * w + 2 * gap)
# photo 4: list left, 3 real pages fanned big right
im = paper(pal["paper"]); d = ImageDraw.Draw(im)
d.rectangle([980, 0, IW, IH], fill=rgb(pal["tint"]))
for i, (x, y, a) in zip([12, 9, 3], [(985, 560, 4), (1165, 380, 0), (1335, 200, -4)]):
    place(im, pages[i], 600, (x, y), angle=a, shadow=0.3)
y = 150; _text(d, (SAFE_L, y), "16 Pages", font("serifB", 110), rgb(pal["deep"])); y += 150
d.rectangle([SAFE_L, y, SAFE_L + 110, y + 6], fill=rgb(pal["accent"])); y += 50
f = font("sans", 44)
for it in ["6 party games", "12 award certificates", "White elephant dice game", "Left-right gift story",
           "Gingerbread contest rules", "4 judge score cards", "6 contest ribbons", "Host timeline + keys"]:
    d.ellipse([SAFE_L, y + 20, SAFE_L + 18, y + 38], fill=rgb(pal["primary"]))
    _text(d, (SAFE_L + 44, y), it, f, rgb(gs.INK)); y += 78
_strip(im, d, pal); gs._check_safe()
gs.save_jpeg(im, "photo4_included.jpg")
# photo 5: host timeline close-up (top half only: the answer keys stay off the photos)
im = gs.preview_closeup(pages[1], pal, "Host Timeline", "The whole night in order, plus print tips", crop=(0, 0, 1, 0.572))
gs.save_jpeg(im, "photo5_timeline.jpg")
for fn in ["photo2_inside.jpg", "photo3_closeup.jpg", "photo4_included.jpg", "photo5_timeline.jpg"]:
    print(fn, Image.open(fn).size, os.path.getsize(fn))
