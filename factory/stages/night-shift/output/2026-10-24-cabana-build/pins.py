"""Two 1000x1500 Pinterest pins for the Pink Bow invite set, built from the real PDF pages."""
import sys, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
B = os.path.dirname(os.path.abspath(__file__)); PDF = B + "/pink-cabana-birthday-invitation.pdf"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); F = "/usr/share/fonts/truetype/google-fonts/"
subprocess.run(["pdftoppm", "-r", "150", "-png", PDF, OUT + "/pp"], check=True)
pg = lambda n: Image.open(f"{OUT}/pp-{n:02d}.png").convert("RGB")
def card(n, k=0):
    p = pg(n); W, H = p.size; cw, ch = int(W * 5 / 11), int(H * 7 / 8.5)
    gap = int(W * 0.25 / 11); x = (W - 2 * cw - gap) // 2 + k * (cw + gap); y = (H - ch) // 2
    return p.crop((x, y, x + cw, y + ch))
def sign(n):
    p = pg(n); W, H = p.size; sw, sh = int(W * 8 / 8.5), int(H * 10 / 11)
    return p.crop(((W - sw) // 2, (H - sh) // 2, (W + sw) // 2, (H + sh) // 2))
def font(n, s, w=None):
    f = ImageFont.truetype(F + n, s)
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
def lay(img, piece, w, xy, ang):
    p = piece.convert("RGBA").resize((w, int(piece.height * w / piece.width)), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (p.width + 60, p.height + 60), (0, 0, 0, 0))
    m = p.split()[3].point(lambda v: 75 if v else 0); blk = Image.new("RGBA", p.size, (70, 40, 40, 255)); blk.putalpha(m)
    sh.paste(blk, (32, 38), blk); sh = sh.filter(ImageFilter.GaussianBlur(15))
    img.alpha_composite(sh, (xy[0] - 30, xy[1] - 30)); img.alpha_composite(p, xy)
def label(img, hook, sub, color, y0):
    d = ImageDraw.Draw(img, "RGBA"); ft = font("Lora-Variable.ttf", 72, 650); fs = font("Poppins-Medium.ttf", 31)
    lines = hook.split("\n"); bw = max(max(d.textlength(l, font=ft) for l in lines), d.textlength(sub, font=fs)) + 90
    bh = 82 * len(lines) + 66 + 40; x0 = (1000 - bw) / 2
    d.rounded_rectangle((x0 + 5, y0 + 9, x0 + bw + 5, y0 + bh + 9), 24, fill=(0, 0, 0, 40))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 24, fill=(251, 247, 240, 248), outline=color, width=3)
    y = y0 + 24
    for l in lines: d.text((500, y), l, font=ft, fill=color, anchor="ma"); y += 82
    d.text((500, y + 12), sub, font=fs, fill=(90, 82, 74), anchor="ma")
def paper(rgb):
    base = Image.new("RGB", (1000, 1500), rgb)
    n = Image.effect_noise((1000, 1500), 5).convert("L").point(lambda v: 255 if v > 118 else 225)
    return Image.composite(base, Image.new("RGB", (1000, 1500), tuple(max(0, c - 6) for c in rgb)), n).convert("RGBA")
# pin 1: the whole set, pink, hook on top
im = paper((243, 226, 224))
label(im, "Pink Bow\nBirthday Party Set", "INVITE · DETAILS · THANK YOU · SIGN", (178, 78, 100), 50)
lay(im, sign(9), 520, (50, 390), -2)
lay(im, card(3), 330, (620, 380), 3)
lay(im, card(5), 300, (110, 1030), 2)
lay(im, card(7), 300, (560, 1000), -3)
im.convert("RGB").save(OUT + "/pin1.jpg", quality=90)
# pin 2: the no-Canva angle, sage
im = paper((232, 238, 228))
label(im, "Type It Into the PDF\nNo Canva Needed", "EDITABLE BIRTHDAY INVITATION · 2 COLORS", (47, 91, 69), 50)
lay(im, card(4), 420, (60, 380), -3)
lay(im, card(3), 420, (520, 400), 3)
lay(im, card(6), 300, (130, 1010), 2)
lay(im, card(8), 300, (570, 1000), -2)
im.convert("RGB").save(OUT + "/pin2.jpg", quality=90)
print("ok")
