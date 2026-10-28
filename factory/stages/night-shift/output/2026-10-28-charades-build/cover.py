import sys, json, random
import numpy as np
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/tools/varied_covers")
import gm_style as gs
from PIL import Image, ImageDraw, ImageFilter
from common import shadow_paste, up
W, H = 2000, 1600
R = {r["id"]: r for r in json.load(open("rects.json"))}
def crop(cid):
    r = R[cid]; s = 300 / 72
    im = Image.open(f"r300/p-{r['page']:02d}.png").convert("RGB")
    x0 = (r["x"] + 5) * s; x1 = (r["x"] + r["w"] - 5) * s
    y0 = (792 - r["y"] - r["h"] + 5) * s; y1 = (792 - r["y"] - 5) * s
    return im.crop((int(x0), int(y0), int(x1), int(y1)))
# linen tablecloth, deep cranberry, fine weave (flat colour, no gradient)
rng = np.random.default_rng(5)
base = np.zeros((H, W, 3), float); base[:] = (112, 30, 44)
yy, xx = np.mgrid[0:H, 0:W]
weave = (np.sin(xx * 1.9) * 0.5 + np.sin(yy * 1.9) * 0.5) * 3.5
base += weave[..., None] + rng.normal(0, 4, (H, W, 1))
c = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
random.seed(11)
grid = [["F01", "K04", "A16", "F12"], ["A12", "F18", "K05", "A02"], ["K14", "A01", "F19", "K13"]]
angs = [-2, 1.5, -1.5, 2, 1.5, -2, 2, -1.5, -1.5, 2, -2, 1.5]
lay = []
for r, row in enumerate(grid):
    for k, cid in enumerate(row):
        lay.append((cid, 20 + k * 495, 392 + r * 400, angs[r * 4 + k]))
for cid, x, y, a in lay:
    shadow_paste(c, up(crop(cid), w=455), x, y, angle=a, blur=14, off=(6, 12), alpha=120, radius=14)
# label card
d = ImageDraw.Draw(c)
lw, lh = 1440, 300
lab = Image.new("RGBA", (lw, lh), (0, 0, 0, 0)); ld = ImageDraw.Draw(lab)
ld.rounded_rectangle([0, 0, lw - 1, lh - 1], 26, fill=(255, 250, 242))
ld.rounded_rectangle([14, 14, lw - 15, lh - 15], 18, outline=(139, 46, 60), width=4)
f1 = gs.font("serifSB", 122); f2 = gs.font("sansM", 50)
t = "Christmas Charades"; tw = ld.textlength(t, font=f1)
ld.text(((lw - tw) / 2, 40), t, font=f1, fill=(90, 28, 38))
s = "120 CARDS  ·  3 LEVELS  ·  DRAW IT MODE"; sw = ld.textlength(s, font=f2)
ld.text(((lw - sw) / 2, 206), s, font=f2, fill=(139, 46, 60))
shadow_paste(c, lab, (W - lw) // 2, 70, angle=0, blur=18, off=(0, 14), alpha=140)
out = c.convert("RGB")
gs.save_jpeg(out, "photo1-cover.jpg")
gs.thumb_check(out, "thumb400.png")
sq = out.crop(((W - H) // 2, 0, (W + H) // 2, H)).resize((300, 300), Image.LANCZOS); sq.save("thumb300.png")
print(out.size)
