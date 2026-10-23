# Inspect fix (Atlas, 2026-10-23): what's-included photo had one small cover page floating over a
# half-empty right side; now 3 real pages fanned big (detective notes, host guide, name tags).
# Usage: photo4_v2.py <pages_dir> <out.jpg>
import sys, glob; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import ImageDraw, Image
pal = gs.palette("berry")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob(sys.argv[1] + "/p-*.png"))]
assert len(pages) == 17
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
d.rectangle([960, 0, gs.IW, gs.IH], fill=gs.rgb(pal["tint"]))
print(gs.place(im, pages[15], 560, (1300, 130), angle=5, shadow=0.22))
print(gs.place(im, pages[13], 580, (1060, 190), angle=-3, shadow=0.24))
print(gs.place(im, pages[1], 660, (1010, 300), angle=1.5, shadow=0.28))
d = ImageDraw.Draw(im)
x = gs.SAFE_L; y = 130
gs._text(d, (x, y), "16 Pages", gs.font("serifB", 120), gs.rgb(pal["deep"])); y += 160
d.rectangle([x, y, x + 120, y + 7], fill=gs.rgb(pal["accent"])); y += 56
f = gs.font("sans", 48)
for it in ["Host guide + setup", "Timeline + host script", "Invitations, 2 per sheet", "8 character sheets",
           "9 clue cards, 3 rounds", "Detective Notes sheet", "Sealed solution page", "Name tags + 2 awards"]:
    d.ellipse([x, y + 22, x + 20, y + 42], fill=gs.rgb(pal["primary"]))
    gs._text(d, (x + 46, y), it, f, gs.rgb(gs.INK)); y += 92
y += 20
gs._text(d, (x, y), "Sized for exactly 8 guests", gs.font("sansM", 44), gs.rgb(pal["primary"])); y += 62
assert y < gs.IH - 130, y
gs._strip(im, d, pal); gs._check_safe()
print(gs.save_jpeg(im, sys.argv[2]))
