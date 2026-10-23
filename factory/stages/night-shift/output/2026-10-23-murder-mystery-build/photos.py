import sys, os, glob
sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from PIL import Image, ImageDraw
pal = gs.palette("berry")
P = sorted(glob.glob("/home/claude/kit/pages/prod-xmas-murder-mystery-8/p-*.png"))
pages = [Image.open(p).convert("RGB") for p in P]
OUT = "/home/claude/build/mystery"
IW, IH = gs.IW, gs.IH

def grid(idxs, cols, w, gx, gy, y0, title, sub, bg):
    im = gs.paper(pal[bg]); d = ImageDraw.Draw(im); gs._header(d, pal, title, sub)
    ph = int(w * 1650 / 1275); rows = -(-len(idxs) // cols)
    total = cols * w + (cols - 1) * gx; x0 = (IW - total) // 2
    for k, i in enumerate(idxs):
        gs.place(im, pages[i], w, (x0 + (k % cols) * (w + gx), y0 + (k // cols) * (ph + gy)), shadow=0.22)
    assert y0 + rows * ph + (rows - 1) * gy < IH - 20
    gs._check_safe(); return im

# 2: all 8 character sheets (pages 5-12; Clem's sheet index 6 shows only its top half in the grid, no spoiler text readable at this size)
p2 = grid([4, 5, 7, 8, 9, 10, 11, 12], 4, 440, 22, 22, 300, "A Sheet for Every Guest", "Secret, alibi, costume and 3 rounds of lines, plus 9 clue cards", "paper")
gs.save_jpeg(p2, f"{OUT}/photo2.jpg")
# 3: host side, big: host guide + timeline/script
p3 = grid([1, 2], 2, 900, 40, 0, 300, "Host-Ready in 10 Minutes", "Setup checklist, timeline and a read-aloud script", "tint")
gs.save_jpeg(p3, f"{OUT}/photo3.jpg")
# 4: what's included
p4 = gs.preview_included(pages, pal, "16 Pages", ["Host guide + setup", "Timeline + host script", "Invitations, 2 per sheet",
        "8 character sheets", "9 clue cards, 3 rounds", "Detective Notes sheet", "Sealed solution page", "Name tags + 2 awards"], pages[0])
gs.save_jpeg(p4, f"{OUT}/photo4.jpg")
# 5: party extras: invitations, detective notes, name tags
p5 = grid([3, 13, 15], 3, 600, 40, 0, 300, "Invites, Notes and Name Tags", "Print at home on US Letter or A4", "paper")
gs.save_jpeg(p5, f"{OUT}/photo5.jpg")
for i in (2, 3, 4, 5): print(i, os.path.getsize(f"{OUT}/photo{i}.jpg"))
row = Image.new("RGB", (2000, 400), "white")
for k, i in enumerate((2, 3, 4, 5)): row.paste(Image.open(f"{OUT}/photo{i}.jpg").resize((500, 400)), (k * 500, 0))
row.save(f"{OUT}/photos_row.png")
