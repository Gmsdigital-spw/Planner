# Inspect fix (Atlas, 2026-10-23): photo 2 rebuilt with 3 character sheets big (636 px wide, was 8 at 440)
# plus the full cast line. Clem's (thief) sheet is never shown. Usage: photo2_v2.py <pages_dir> <out.jpg>
import sys, glob; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import ImageDraw, Image
pal = gs.palette("berry")
pages = [Image.open(f).convert("RGB") for f in sorted(glob.glob(sys.argv[1] + "/p-*.png"))]
assert len(pages) == 17
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "A Sheet for Every Guest", "Who you are, costume, secret, alibi and 3 rounds of lines")
w, gap = 636, 12; x0 = (gs.IW - (3 * w + 2 * gap)) // 2
ph = int(w * pages[4].height / pages[4].width); block = ph + 34 + 66 + 56
y0 = 290 + (gs.IH - 110 - 290 - block) // 2
for k, i in enumerate((4, 5, 8)):          # Ivy, Jasper, Noelle
    gs.place(im, pages[i], w, (x0 + k * (w + gap), y0), shadow=0.22)
d = ImageDraw.Draw(im)
y = y0 + ph + 34
gs._text(d, (gs.IW / 2, y), "8 characters, one page each", gs.font("sansM", 46), gs.rgb(pal["deep"]), anchor="ma"); y += 66
gs._text(d, (gs.IW / 2, y), "Ivy  ·  Jasper  ·  Clem  ·  Rupert  ·  Noelle  ·  Dash  ·  Marigold  ·  Felix", gs.font("sans", 38), gs.rgb(gs.INK), anchor="ma"); y += 56
assert y < gs.IH - 120, y
gs._strip(im, d, pal, "ANY GUEST CAN PLAY ANY ROLE  ·  HOST CAN PLAY")
gs._check_safe()
print(gs.save_jpeg(im, sys.argv[2]))
