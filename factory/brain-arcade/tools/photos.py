#!/usr/bin/env python3
"""Brain Arcade listing photos from the REAL PDF pages (never drawn mockups).

Usage: python3 photos.py <spec.json> <product.pdf> <out_dir> [clipboard|fanned|christmas]
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


ATLAS = os.path.normpath(os.path.join(HERE, "../../../assets/atlas-pack"))
# Cover layouts. Each is a different look; ba-night picks one not used on the lane's last 3 covers
# (listing.json "coverLayout"). Scene layouts put the REAL page into Grayson's photo scenes
# (assets/atlas-pack/place.py, the main crew's picture tool) so the cover reads as a real photo,
# not a drawn mockup. "christmas" is Nov-Dec only.
LAYOUTS = ["clipboard", "fanned", "christmas"]


def scene_cover(spec, pg, lock_pages, out, layout):
    import sys
    sys.path.insert(0, ATLAS)
    import place
    P = {k: hexrgb(v) for k, v in spec["palette"].items()}
    nlocks = len(spec["locks"]); nprob = sum(len(L["problems"]) for L in spec["locks"])
    title = spec.get("cover_title", "Thanksgiving Math Escape Room")
    if layout == "clipboard":
        img = place.place("clipboard", [lock_pages[min(3, len(lock_pages) - 1)]], None, scale=2000 / 1448)
        box = (1290, 400, 1745, 990)  # right of the clipboard, inside the 300 px thumbnail square
    else:  # christmas table: cover page + a lock page
        img = place.place("christmas", [pg[0], lock_pages[0]], None, scale=2000 / 1448)
        box = (560, 60, 1440, 330)
    img = img.convert("RGBA").resize((2000, 1500), Image.LANCZOS)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((box[0] + 10, box[1] + 18, box[2] + 10, box[3] + 18), 36, fill=(0, 0, 0, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, 34, fill=(255, 250, 242), outline=P["primary"], width=7)
    x0, y0, x1, y1 = box
    words = title.split()
    if layout == "clipboard":  # tall card: title stacked
        lines, cur = [], ""
        for w in words:
            if len((cur + " " + w).strip()) <= 12:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        size = 92
        f = font(HEAD, size)
        while max(d.textlength(l, font=f) for l in lines) > (x1 - x0) - 70:
            size -= 4; f = font(HEAD, size)
        y = y0 + 70
        for l in lines:
            d.text(((x0 + x1) / 2, y), l, font=f, fill=P["ink"], anchor="mt"); y += size * 1.08
        d.line((x0 + 80, y + 18, x1 - 80, y + 18), fill=P["accent"], width=5)
        subs = [spec["grade"].upper(), f"{nlocks} LOCKS", f"{nprob} PROBLEMS", "ANSWER KEY"]
        fsz = 46
        fs = font(BODY, fsz)
        while max(d.textlength(s, font=fs) for s in subs) > (x1 - x0) - 60:
            fsz -= 2; fs = font(BODY, fsz)
        for i, s in enumerate(subs):
            d.text(((x0 + x1) / 2, y + 56 + i * (fsz + 14)), s, font=fs, fill=P["deep"], anchor="mt")
    else:
        card(d, box, title, f"{spec['grade'].upper()}  ·  {nlocks} LOCKS  ·  ANSWER KEY", P["deep"], size=84)
    save(img, out)


def build(spec, pdf, out, layout="fanned"):
    os.makedirs(out, exist_ok=True)
    P = {k: hexrgb(v) for k, v in spec["palette"].items()}
    pg = pages(pdf)
    n = len(pg)
    nlocks = len(spec["locks"]); nprob = sum(len(L["problems"]) for L in spec["locks"])
    lock_pages = pg[3:3 + nlocks]
    rec = 3 + nlocks  # recording sheet; then vault door, answer key, certificate
    files = []

    if layout in ("clipboard", "christmas"):
        f = os.path.join(out, "01-cover.jpg"); scene_cover(spec, pg, lock_pages, f, layout); files.append(f)
    # 01 cover (layout "fanned"): three real pages fanned on the bold theme colour, label card top.
    # With a scene cover, this fanned shot becomes photo 02 instead of the all-pages grid.
    c = Image.new("RGBA", (2000, 1500), P["primary"] + (255,))
    d = ImageDraw.Draw(c)
    shadowed(c, lock_pages[0], 640, (170, 470), angle=6)
    shadowed(c, lock_pages[3], 640, (1190, 470), angle=-6)
    shadowed(c, pg[0], 700, (650, 420))
    d = ImageDraw.Draw(c)
    card(d, (240, 60, 1760, 380), spec.get("cover_title", "Thanksgiving Math Escape Room"),
         f"{spec['grade'].upper()}  ·  {nlocks} LOCKS  ·  {nprob} PROBLEMS  ·  ANSWER KEY", P["deep"])
    if layout == "fanned":
        f = os.path.join(out, "01-cover.jpg"); save(c, f); files.append(f)
    else:
        f = os.path.join(out, "02-fanned.jpg"); save(c.resize((2000, 1500)), f); files.append(f)

    def base(title, sub):
        im = Image.new("RGBA", (2000, 1600), P["bg"] + (255,))
        dd = ImageDraw.Draw(im)
        dd.rectangle((0, 0, 2000, 210), fill=P["deep"])
        dd.text((1000, 80), title, font=font(HEAD, 84), fill=(255, 255, 255), anchor="mm")
        dd.text((1000, 160), sub, font=font(BODY, 40), fill=P["accent"], anchor="mm")
        return im

    # 02 every page (03 when the cover is a scene and 02 is the fanned shot)
    im = base(f"{n} printable pages", "Every page you get, ready to print")
    cols = 5; w = 300; gap = 34
    x0 = (2000 - (cols * w + (cols - 1) * gap)) // 2
    for i, p in enumerate(pg[:14]):
        r, cc = divmod(i, cols)
        shadowed(im, p, w, (x0 + cc * (w + gap), 262 + r * 440))
    if layout == "fanned":
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
    layout = sys.argv[4] if len(sys.argv) > 4 else "fanned"
    assert layout in LAYOUTS, f"layout must be one of {LAYOUTS}"
    for f in build(spec, sys.argv[2], sys.argv[3], layout):
        print(f, Image.open(f).size, os.path.getsize(f) // 1024, "KB")
