import sys, os
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs, place
from PIL import Image, ImageDraw, ImageFont, ImageFilter
PD = "/home/claude/kit/pages/prod-xmas-party-mega-bundle"
if not os.path.exists(PD + "/p-18.png") and not any(f.endswith(".png") for f in os.listdir(PD) if os.path.isdir(PD)):
    pass
pages = gs.render_pages("bundle.pdf", PD)
files = sorted(f for f in os.listdir(PD) if f.endswith(".png"))
print(len(pages), files[:3])
def pf(i): return os.path.join(PD, files[i])
FD = "/usr/share/fonts/truetype/google-fonts/"
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
COLOR = "#2F5446"
CX, CY, CW = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
sc = 2000 / CW
big = place.place("christmas", [pf(6), pf(8)], scale=sc)
img = big.crop((round(CX * sc), round(CY * sc), round(CX * sc) + 2000, round(CY * sc) + 1600)).convert("RGB")
# two more real pages laid on the table, fanned at the bottom corners (warm light to match the scene)
def lay(i, w, xy, ang):
    p = pages[i].convert("RGB"); h = round(p.height * w / p.width); p = p.resize((w, h), Image.LANCZOS)
    warm = Image.new("RGB", p.size, (255, 244, 226)); p = p
    from PIL import ImageChops
    p = ImageChops.multiply(p, Image.new("RGB", p.size, (252, 247, 238)))
    gs.place(img, p, w, xy, angle=ang, shadow=0.38)
if len(sys.argv) > 4 and sys.argv[4] == "fan":
    lay(14, 400, (20, 1035), 5)
    lay(15, 400, (1600, 1035), -5)
d = ImageDraw.Draw(img, "RGBA")
title, sub = "Christmas Party Night", "16 PAGES  ·  6 GAMES  ·  12 AWARDS  ·  GIFT SWAP  ·  CONTEST"
ft = font("Lora-Variable.ttf", 124, 650); fs = font("Poppins-Medium.ttf", 46)
W, H = img.size; pad = 46
bw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs) + 40) + pad * 2
bh = 160 + 50 + pad * 2 + 6
x0 = (W - bw) / 2; y0 = 60
d.rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 26, fill=(0, 0, 0, 40))
d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 26, fill=(251, 247, 240, 247))
d.rounded_rectangle((x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14), 18, outline=COLOR, width=3)
d.text((W / 2, y0 + pad - 10), title, font=ft, fill=COLOR, anchor="ma")
d.text((W / 2, y0 + pad - 10 + 160 + 8), sub, font=fs, fill=(90, 82, 74), anchor="ma")
print("label box x", round(x0), round(x0 + bw), "y", y0, round(y0 + bh))
gs.save_jpeg(img, "photo1_cover.jpg")
gs.thumb_check(img, "thumb400.png")
sq = img.crop(((W - H) // 2, 0, (W - H) // 2 + H, H)).resize((300, 300), Image.LANCZOS); sq.save("thumb300.png")
print(os.path.getsize("photo1_cover.jpg"), img.size)
