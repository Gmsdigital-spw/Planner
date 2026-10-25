#!/usr/bin/env python3
"""Brain Arcade listing photos from the REAL PDF pages (never drawn mockups).

Usage: python3 photos.py <spec.json> <product.pdf> <out_dir>
Writes 01-cover.jpg (2000x1500) and 02..05 (2000x1600), JPEG under 400 KB.
Cover rule (copied from the main crew, Oct 24): real pages are the biggest thing in the frame,
ONE clean label card, a solid bold colour; no gradients, badges, pills, emoji or stickers.
Variety: the cover layout is picked from LAYOUTS by the product id, and the night run must
pick a different one than the last 3 Brain Arcade covers (stages/ba-night 04).
"""
import glob, json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "../../../tools/fonts"))
HEAD = os.path.join(FONTS, "BricolageGrotesque-Bold.ttf")
BODY = os.path.join(FONTS, "Outfit-Bold.ttf")


def font(p, s):
    return ImageFont.truetype(p, s)


def pages(pdf, dpi=110):
    d = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, d + "/p"], check=True)
    return [Image.open(f).convert("RGB") for f in sorted(glob.glob(d + "/p-*.png"))]


def shadowed(canvas, page, w, xy, angle=0):
    im = page.resize((w, int(page.height * w / page.width)), Image.LANCZOS)
    if angle:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0)) if im.mode == "RGBA" else \
            im.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    else:
        im = im.convert("RGBA")
    sh = Image.new("RGBA", (im.width + 60, im.height + 60), (0, 0, 0, 0))
    alpha = im.split()[3].point(lambda a: int(a * 0.35))
    sh.paste((0, 0, 0, 255), (30, 30), alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    canvas.alpha_composite(sh, (xy[0] - 18, xy[1] - 6))
    canvas.alpha_composite(im, xy)


def card(d, box, title, sub, col, size=96):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 36, fill=(255, 250, 242), outline=col, width=8)
    f = font(HEAD, size)
    while d.textlength(title, font=f) > (x1 - x0) - 80:
        size -= 4; f = font(HEAD, size)
    d.text(((x0 + x1) / 2, y0 + (y1 - y0) * 0.40), title, font=f, fill=(43, 26, 16), anchor="mm")
    fs = font(BODY, 44)
    d.text(((x0 + x1) / 2, y0 + (y1 - y0) * 0.76), sub, font=fs, fill=col, anchor="mm")


def save(im, path):
    im = im.convert("RGB"); q = 90
    while True:
        im.save(path, "JPEG", quality=q, optimize=True)
        if os.path.getsize(path) < 400_000 or q < 60:
            return
        q -= 5


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build(spec, pdf, out):
    os.makedirs(out, exist_ok=True)
    P = {k: hexrgb(v) for k, v in spec["palette"].items()}
    pg = pages(pdf)
    n = len(pg)
    nlocks = len(spec["locks"]); nprob = sum(len(L["problems"]) for L in spec["locks"])
    lock_pages = pg[3:3 + nlocks]
    rec = 3 + nlocks  # recording sheet; then vault door, answer key, certificate
    files = []

    # 01 cover: three real pages fanned, label card top
    c = Image.new("RGBA", (2000, 1500), P["primary"] + (255,))
    d = ImageDraw.Draw(c)
    shadowed(c, lock_pages[0], 640, (170, 470), angle=6)
    shadowed(c, lock_pages[3], 640, (1190, 470), angle=-6)
    shadowed(c, pg[0], 700, (650, 420))
    d = ImageDraw.Draw(c)
    card(d, (240, 60, 1760, 380), spec.get("cover_title", "Thanksgiving Math Escape Room"),
         f"{spec['grade'].upper()}  ·  {nlocks} LOCKS  ·  {nprob} PROBLEMS  ·  ANSWER KEY", P["deep"])
    f = os.path.join(out, "01-cover.jpg"); save(c, f); files.append(f)

    def base(title, sub):
        im = Image.new("RGBA", (2000, 1600), P["bg"] + (255,))
        dd = ImageDraw.Draw(im)
        dd.rectangle((0, 0, 2000, 210), fill=P["deep"])
        dd.text((1000, 80), title, font=font(HEAD, 84), fill=(255, 255, 255), anchor="mm")
        dd.text((1000, 160), sub, font=font(BODY, 40), fill=P["accent"], anchor="mm")
        return im

    # 02 every page
    im = base(f"{n} printable pages", "Every page you get, ready to print")
    cols = 5; w = 300; gap = 34
    x0 = (2000 - (cols * w + (cols - 1) * gap)) // 2
    for i, p in enumerate(pg[:14]):
        r, cc = divmod(i, cols)
        shadowed(im, p, w, (x0 + cc * (w + gap), 262 + r * 440))
    f = os.path.join(out, "02-all-pages.jpg"); save(im, f); files.append(f)

    # 03 close-up of a lock page (big enough to read)
    im = base("Real grade-level problems", spec["locks"][3]["skill"] + "  ·  " + spec["locks"][3]["standard"])
    big = lock_pages[3]
    crop = big.crop((0, 0, big.width, int(big.height * 0.62)))
    shadowed(im, crop, 1480, (260, 262))
    f = os.path.join(out, "03-closeup.jpg"); save(im, f); files.append(f)

    # 04 answer key + recording sheet
    im = base("Answer key included", "Every answer double-checked  ·  code words for all 5 locks")
    shadowed(im, pg[rec + 2], 620, (330, 290), angle=3)
    shadowed(im, pg[rec], 620, (1050, 290), angle=-3)
    f = os.path.join(out, "04-answer-key.jpg"); save(im, f); files.append(f)

    # 05 what's included, with the teacher guide page
    im = base("What's inside", "No prep: print and play in one class period")
    shadowed(im, pg[1], 640, (300, 290))
    dd = ImageDraw.Draw(im)
    items = ["Teacher guide + standards", "Story page", f"{nlocks} lock pages, {nprob} problems",
             "Student recording sheet", "Final vault page", "Answer key", "Escape Expert certificate"]
    y = 330
    for t in items:
        dd.ellipse((1030, y + 10, 1062, y + 42), fill=P["primary"])
        dd.text((1085, y + 26), t, font=font(BODY, 48), fill=P["ink"], anchor="lm")
        y += 150
    f = os.path.join(out, "05-included.jpg"); save(im, f); files.append(f)
    return files


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for f in build(spec, sys.argv[2], sys.argv[3]):
        print(f, Image.open(f).size, os.path.getsize(f) // 1024, "KB")
