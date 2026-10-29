"""Thanksgiving Escape Room listing photos: cover (binder scene + label) and photos 2-5."""
import sys, os
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs, place
from PIL import Image, ImageDraw, ImageFont

PG = "/home/claude/kit/pages/prod-thanksgiving-escape-room"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos"); os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("harvest")
pages = [Image.open(f"{PG}/p-{i:02d}.png").convert("RGB") for i in range(1, 18)]
FD = "/usr/share/fonts/truetype/google-fonts"


def fnt(name, size):
    for root, _, files in os.walk(FD):
        if name in files: return ImageFont.truetype(os.path.join(root, name), size)
    raise FileNotFoundError(name)


def pad_to(img, aspect):
    """Pad a page with white so it matches the slot aspect (w/h): nothing gets cropped."""
    w, h = img.size; nh = round(w / aspect)
    if nh <= h: return img
    can = Image.new("RGB", (w, nh), (255, 255, 255)); can.paste(img, (0, round((nh - h) * 0.25))); return can


def cover():
    """Fix round 2: hero-page close-up family (not the pages-on-top + title-band look of round 1 or the
    Christmas Escape Room): stacked title top-left, one real page big and tilted bottom-right (p06, warm
    pumpkins/apples), p07 fanned behind it, warm diagonal harvest ground. Whole pages only, nothing over page text."""
    from PIL import ImageFilter
    W, H = 2000, 1500
    im = Image.new("RGB", (W, H)); px = im.load()
    c1, c2 = (206, 112, 48), (150, 62, 30)                 # pumpkin -> rust, diagonal
    import numpy as np
    yy_, xx_ = np.mgrid[0:H, 0:W]; t = np.clip((xx_ * 0.45 + yy_) / (W * 0.45 + H), 0, 1)[..., None]
    im = Image.fromarray((np.array(c1) * (1 - t) + np.array(c2) * t).astype("uint8"), "RGB")
    noise = Image.effect_noise((W // 2, H // 2), 9).resize((W, H)).convert("L")
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, noise.point(lambda v: max(0, int((v - 128) * 0.10))))
    d = ImageDraw.Draw(im)

    def page_at(pg, w, cx, cy, ang, blur=22, alpha=120):
        h = round(w * pg.height / pg.width)
        p = pg.resize((w, h), Image.LANCZOS).convert("RGBA")
        sh = Image.new("RGBA", (w + 120, h + 120), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((60, 78, w + 60, h + 78), fill=(50, 20, 5, alpha))
        sh = sh.filter(ImageFilter.GaussianBlur(blur)).rotate(ang, expand=True, resample=Image.BICUBIC)
        im.paste(sh, (round(cx - sh.width / 2), round(cy - sh.height / 2)), sh)
        pr = p.rotate(ang, expand=True, resample=Image.BICUBIC)
        box = (round(cx - pr.width / 2), round(cy - pr.height / 2)); im.paste(pr, box, pr)
        return box[0], box[1], box[0] + pr.width, box[1] + pr.height

    back = page_at(pages[6], 560, 585, 1062, 5, alpha=100)      # p07 Level 2 behind, left
    hero = page_at(pages[5], 760, 1352, 980, -3, alpha=150)     # p06 Level 1 hero, right
    d = ImageDraw.Draw(im)
    cream, gold = (255, 246, 232), (252, 216, 150)
    x0 = 268
    fk = gs.font("sansM", 40); d.text((x0, 46), "PRINTABLE FAMILY GAME", font=fk, fill=gold, spacing=4)
    f1 = gs.font("serifB", 142)
    for txt, yy in (("Thanksgiving", 92), ("Escape Room", 236)):
        d.text((x0 + 5, yy + 6), txt, font=f1, fill=(96, 38, 14)); d.text((x0, yy), txt, font=f1, fill=cream)
        assert x0 + d.textlength(txt, font=f1) <= 1740, txt
    fs = gs.font("sansM", 54)
    d.text((x0, 404), "2 LEVELS  ·  AGES 6-9 & 10+", font=fs, fill=gold)
    assert x0 + d.textlength("2 LEVELS  ·  AGES 6-9 & 10+", font=fs) <= 1740
    # no text may sit over a page: title block ends above both pages' top edges
    assert 404 + 62 < min(back[1], hero[1]) or x0 + d.textlength("2 LEVELS  ·  AGES 6-9 & 10+", font=fs) < hero[0], (back, hero)
    # whole pages, no page over another page's text: the rotated page corners must not meet
    import math
    def corners(w, cx, cy, ang, pg):
        h = w * pg.height / pg.width; r = math.radians(-ang)
        return [(cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r)) for x, y in ((-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2))]
    bc = corners(560, 585, 1062, 5, pages[6]); hc = corners(760, 1352, 980, -3, pages[5])
    assert max(x for x, _ in bc) + 12 < min(x for x, _ in hc), ("pages overlap", bc, hc)
    assert max(back[3], hero[3]) <= H and hero[2] <= W and back[0] >= 0, ("page off the frame", back, hero)
    gs.save_jpeg(im, f"{OUT}/1-cover.jpg")
    gs.thumb_check(im, f"{OUT}/thumb400.jpg")
    sq = im.crop((250, 0, 1750, 1500)).resize((300, 300), Image.LANCZOS); sq.save(f"{OUT}/thumb300.png")
    return im, back, hero


if __name__ == "__main__":
    which = sys.argv[1:] or ["cover"]
    if "cover" in which: cover()


def grid(idxs, title, sub, cols, pw):
    """Real pages big in a grid, headline on top; every word inside x 260-1740."""
    from PIL import ImageFilter
    im = Image.new("RGB", (2000, 1600), (250, 245, 238)); d = ImageDraw.Draw(im)
    f1 = gs.font("serifB", 92); f2 = gs.font("sans", 42)
    for txt, y, f, col in ((title, 40, f1, (110, 50, 25)), (sub, 160, f2, (119, 113, 106))):
        w = d.textlength(txt, font=f); assert 260 <= (2000 - w) / 2, txt; d.text(((2000 - w) / 2, y), txt, font=f, fill=col)
    ph = round(pw * 1650 / 1275); rows = (len(idxs) + cols - 1) // cols
    gx = (2000 - cols * pw - (cols - 1) * 40) // 2; top = 245; gy = (1600 - top - rows * ph - (rows - 1) * 34) // 2 + top
    for k, i in enumerate(idxs):
        x = gx + (k % cols) * (pw + 40); y = gy + (k // cols) * (ph + 34)
        sh = Image.new("RGBA", (pw + 40, ph + 40), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((20, 24, pw + 20, ph + 24), fill=(60, 40, 20, 70))
        sh = sh.filter(ImageFilter.GaussianBlur(10)); im.paste(sh, (x - 20, y - 20), sh)
        im.paste(pages[i].resize((pw, ph), Image.LANCZOS), (x, y))
    return im


def fan(idxs, title, sub):
    """Fix round 1: 3 real pages fanned big (left, right, then centre on top), headline inside x 260-1740."""
    from PIL import ImageFilter
    im = Image.new("RGB", (2000, 1600), (250, 245, 238)); d = ImageDraw.Draw(im)
    f1 = gs.font("serifB", 92); f2 = gs.font("sans", 42)
    for txt, y, f, col in ((title, 34, f1, (110, 50, 25)), (sub, 150, f2, (119, 113, 106))):
        w = d.textlength(txt, font=f); assert 260 <= (2000 - w) / 2, txt; d.text(((2000 - w) / 2, y), txt, font=f, fill=col)
    pw, ph = 900, round(900 * 1650 / 1275)
    for i, (cx, cy, ang) in zip(idxs, ((560, 905, 8), (1440, 905, -8), (1000, 925, 0))):
        pg = pages[i].resize((pw, ph), Image.LANCZOS).convert("RGBA")
        sh = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((40, 50, pw + 40, ph + 50), fill=(60, 40, 20, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(16)).rotate(ang, expand=True, resample=Image.BICUBIC)
        im.paste(sh, (round(cx - sh.width / 2), round(cy - sh.height / 2) + 6), sh)
        pr = pg.rotate(ang, expand=True, resample=Image.BICUBIC)
        im.paste(pr, (round(cx - pr.width / 2), round(cy - pr.height / 2)), pr)
    return im


def rest():
    p2 = grid([2, 3, 4, 8, 10, 11], "Two Levels, One Story", "Level 1 for ages 6-9, Level 2 for ages 10+, same 4-digit code", 3, 470)
    gs.save_jpeg(p2, f"{OUT}/2-inside.jpg")
    p3 = gs.preview_closeup(pages[7], PAL, "Tangled Pumpkin Vines", "Big, clear pictures for the 6-9 level", crop=(0, 0, 1, 0.768))  # fix round 3: ends above the answer box (box top at 0.778)
    gs.save_jpeg(p3, f"{OUT}/3-closeup.jpg")
    p4 = fan([2, 9, 0], "16 Pages, Ready to Print", "8 clue sheets in 2 levels, lock tags, hint cards, certificates")
    gs.save_jpeg(p4, f"{OUT}/4-included.jpg")
    p5 = grid([1, 12, 13, 15], "Easy for the Game Master", "Set-up guide, lock tags, hint cards, certificates", 2, 480)
    gs.save_jpeg(p5, f"{OUT}/5-host.jpg")


if __name__ == "__main__" and "rest" in sys.argv[1:]:
    rest()
