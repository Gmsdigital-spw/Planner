"""Cover v2 (Oct 24 fix round): welcome sign in Grayson's oak-frame scene, real invite + thank-you cards
standing on the console in front. Different scene from the 5 clipboard covers."""
import sys, os, subprocess
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import place
from PIL import Image, ImageDraw, ImageFilter, ImageFont
B = os.path.dirname(os.path.abspath(__file__)); PDF = B + "/pink-cabana-birthday-invitation.pdf"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
subprocess.run(["pdftoppm", "-r", "200", "-png", PDF, OUT + "/pg"], check=True)
pg = lambda n: Image.open(f"{OUT}/pg-{n:02d}.png").convert("RGB")
def card(n, k):
    p = pg(n); W, H = p.size; cw, ch = int(W * 5 / 11), int(H * 7 / 8.5)
    gap = int(W * 0.25 / 11); x = (W - 2 * cw - gap) // 2 + k * (cw + gap); y = (H - ch) // 2
    return p.crop((x, y, x + cw, y + ch))
s = pg(9); W, H = s.size; sw, sh = int(W * 8 / 8.5), int(H * 10 / 11)
sign = s.crop(((W - sw) // 2, (H - sh) // 2, (W + sw) // 2, (H + sh) // 2))
# matted print: sign centred on the mat area of the slot
SC = 2000 / 1448 * 1.25
scene = place.place("frame", [sign], scale=SC)  # 2500 wide
def stand(img, c, x, y_bottom, h, ang=0):
    w = int(c.width * h / c.height); c = c.resize((w, h), Image.LANCZOS).convert("RGBA")
    if ang: c = c.rotate(ang, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (c.width + 80, c.height + 80), (0, 0, 0, 0))
    a = c.split()[3].point(lambda v: 95 if v else 0)
    blk = Image.new("RGBA", c.size, (40, 25, 15, 255)); blk.putalpha(a)
    sh.paste(blk, (52, 44), blk); sh = sh.filter(ImageFilter.GaussianBlur(18))
    y = y_bottom - c.height
    cs = Image.new('RGBA', (c.width + 60, 60), (0, 0, 0, 0)); cd = ImageDraw.Draw(cs)
    cd.ellipse((10, 18, c.width + 50, 46), fill=(30, 18, 10, 150)); cs = cs.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(cs, (x - 30, y_bottom - 34))
    img.alpha_composite(sh, (x - 40, y - 40)); img.alpha_composite(c, (x, y))
img = scene.convert("RGBA")
k = SC
top = int(882 * k)  # console top surface
stand(img, card(7, 0), int(338 * k), top, int(372 * k), 3)
stand(img, card(4, 0), int(832 * k), top + int(6 * k), int(430 * k), -2)
img = img.convert("RGB")
cx0, cy0 = int(250 * k), int(150 * k); cw = int(1000 * k)
img = img.crop((cx0, cy0, cx0 + cw, cy0 + int(cw * 0.8))).resize((2000, 1600), Image.LANCZOS)
FD = "/usr/share/fonts/truetype/google-fonts/"
def font(n, s, w=None):
    f = ImageFont.truetype(FD + n, s)
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
d = ImageDraw.Draw(img, "RGBA")
title, sub, color = "Pink Bow Invitation Set", "11 PAGES  ·  2 COLOURS  ·  EDITABLE PDF", "#B24E64"
ft = font("Lora-Variable.ttf", 100, 650); fs = font("Poppins-Medium.ttf", 34)
pad = 34; bw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs) + 40) + pad * 2; bh = 100 + 42 + pad * 2 + 6
x0 = (2000 - bw) / 2; y0 = 34
d.rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 26, fill=(0, 0, 0, 40))
d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 26, fill=(251, 247, 240, 245))
d.rounded_rectangle((x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14), 18, outline=color, width=3)
d.text((1000, y0 + pad - 8), title, font=ft, fill=color, anchor="ma")
d.text((1000, y0 + pad + 106), sub, font=fs, fill=(90, 82, 74), anchor="ma")
img.save(OUT + "/1-cover.jpg", quality=90)
img.crop((200, 0, 1800, 1600)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
print("ok", img.size)
