"""Stage 08 pins for prod-xmas-office-party-games (Oct 30, 2026): 3 layout families, real pages."""
import sys, os, random
sys.path.insert(0, "/home/claude/planner/tools/varied_covers")
from common import F, up, shadow_paste, text_c, noise
from PIL import Image, ImageDraw, ImageFilter

PG = "/home/claude/kit/pages/prod-xmas-office-party-games/p-%02d.png"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/pins"
os.makedirs(OUT, exist_ok=True)
W, H = 1000, 1500
pg = lambda n: Image.open(PG % n).convert("RGB")


def bg_grad(top, bot, seed):
    im = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    n = noise((W, H), 12, seed).convert("RGB")
    return Image.blend(im, n, 0.04).convert("RGBA")


def hook(c, lines, color, sub=None, subcol=None, y0=60, size=92):
    d = ImageDraw.Draw(c)
    f = F("Gloock-Regular", size)
    y = y0
    for s in lines:
        text_c(d, W / 2, y, s, f, color); y += int(size * 1.12)
    if sub:
        text_c(d, W / 2, y + 14, sub, F("WorkSans-Bold", 30), subcol, spacing=3); y += 60
    return y


# Pin 1: hero page close-up (buyer-voice hook), berry ground, Bingo page big
def pin1():
    # rebuilt after slop gate: no tilt, no page behind; zoomed crop of the Bingo grid, edge to edge
    c = bg_grad((122, 24, 40), (70, 12, 24), 3)
    p = up(pg(10), w=1180)
    p = p.crop((90, 40, 1090, 1040))
    c.paste(p, (0, 500))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 1440, W, H], fill=(122, 24, 40))
    hook(c, ["Very fun for the", "office party!"], (255, 244, 226),
         "COWORKER BINGO + 23 MORE GAMES", (240, 196, 120), y0=70, size=104)
    text_c(d, W / 2, 1452, "PRINTABLE · NO PREP · INSTANT DOWNLOAD", F("WorkSans-Bold", 26), (240, 196, 120), spacing=3)
    return c


# Pin 2: device (tablet) with the 45-minute plan, cream linen
def pin2():
    c = bg_grad((246, 238, 224), (228, 214, 192), 5)
    y = hook(c, ["Your whole office", "party, planned"], (92, 20, 32),
             "45-MINUTE RUN SHEET + 24 GAMES", (150, 110, 40))
    tw, th = 760, 1000
    tab = Image.new("RGB", (tw, th), (34, 34, 38))
    page = up(pg(2), w=tw - 70)
    page = page.crop((0, 0, page.width, min(page.height, th - 70)))
    tab.paste(page, (35, 35))
    tx, ty = (W - tw) // 2 - 40, y + 50
    shadow_paste(c, tab, tx, ty, angle=0, radius=46, alpha=120)
    side = up(pg(16), w=330)
    shadow_paste(c, side, W - 360, ty + 560, angle=-7, alpha=110)
    return c


# Pin 3: warm desk flat-lay, printed sheets + a pencil
def pin3():
    c = bg_grad((150, 104, 66), (112, 74, 44), 7)
    d = ImageDraw.Draw(c)
    random.seed(4)
    for i in range(40):
        x = random.randint(0, W); d.line([(x, 0), (x + random.randint(-30, 30), H)], fill=(130, 88, 54, 60), width=2)
    band = Image.new("RGBA", (W, 330), (250, 244, 232, 238))
    c.alpha_composite(band, (0, 0))
    hook(c, ["No-prep games your", "coworkers will love"], (92, 20, 32),
         "PRINTABLE · INSTANT DOWNLOAD", (150, 110, 40), y0=48, size=80)
    a = up(pg(11), w=520); shadow_paste(c, a, 30, 420, angle=5, alpha=120)
    b = up(pg(14), w=560); shadow_paste(c, b, 400, 560, angle=-4, alpha=130)
    pen = Image.new("RGB", (40, 560), (236, 178, 52))
    ImageDraw.Draw(pen).rectangle([0, 0, 40, 40], fill=(220, 140, 140))
    shadow_paste(c, pen, 860, 380, angle=-18, alpha=100)
    return c


if __name__ == "__main__":
    for i, fn in enumerate([pin1, pin2, pin3], 1):
        p = f"{OUT}/office-games-pin-s{i}.jpg"
        fn().convert("RGB").save(p, "JPEG", quality=90)
        print(p, os.path.getsize(p))
