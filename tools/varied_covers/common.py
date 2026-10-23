import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

ROOT = "/home/claude/planner"
import os
OUT = os.environ.get("COVERS_OUT", "/tmp/varied_covers")
W, H = 2000, 1500
FD = ROOT + "/tools/fonts/"

def F(name, size):
    return ImageFont.truetype(FD + name + ".ttf", size)

def src(rel):
    return Image.open(os.path.join(ROOT, rel)).convert("RGB")

def up(im, w=None, h=None):
    """Resize with LANCZOS, add a little sharpening when upscaling."""
    if w and not h: h = round(im.height * w / im.width)
    if h and not w: w = round(im.width * h / im.height)
    big = w > im.width
    im = im.resize((w, h), Image.LANCZOS)
    if big:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    return im

def shadow_paste(canvas, im, x, y, angle=0, blur=22, off=(0, 18), alpha=110, radius=0):
    """Paste RGB image with drop shadow, optional rotation and rounded corners."""
    im = im.convert("RGBA")
    if radius:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius, fill=255)
        im.putalpha(m)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    pad = blur * 3
    sh = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.split()[3].point(lambda v: v * alpha // 255)
    blk = Image.new("RGBA", im.size, (20, 10, 5, 255)); blk.putalpha(a)
    sh.paste(blk, (pad, pad), blk)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(sh, (int(x - pad + off[0]), int(y - pad + off[1])))
    canvas.alpha_composite(im, (int(x), int(y)))
    return im.size

def text_c(d, cx, y, s, font, fill, spacing=0):
    if spacing:
        w = sum(d.textlength(ch, font=font) for ch in s) + spacing * (len(s) - 1)
        x = cx - w / 2
        for ch in s:
            d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + spacing
        return w
    w = d.textlength(s, font=font)
    d.text((cx - w / 2, y), s, font=font, fill=fill)
    return w

def text_w(d, s, font, spacing=0):
    return sum(d.textlength(ch, font=font) for ch in s) + spacing * (len(s) - 1) if spacing else d.textlength(s, font=font)

def text_sp(d, x, y, s, font, fill, spacing=0):
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + spacing

def save(canvas, name):
    p = os.path.join(OUT, name)
    canvas.convert("RGB").save(p, "JPEG", quality=92)
    return p

def noise(size, amt=10, seed=1):
    random.seed(seed)
    n = Image.effect_noise(size, amt).convert("L")
    return n
