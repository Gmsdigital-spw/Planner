import sys, random
import numpy as np
from common import *
X = OUT + "/src/x/"
def L(n): return Image.open(X + n).convert("RGB")

def bg_grad(c1, c2, vertical=True):
    a = np.linspace(0, 1, H if vertical else W)[:, None] if vertical else np.linspace(0, 1, W)[None, :]
    c1, c2 = np.array(c1), np.array(c2)
    img = (c1 * (1 - a[..., None]) + c2 * a[..., None]) if True else None
    img = np.broadcast_to(img, (H, W, 3)).astype(np.uint8)
    return Image.fromarray(img).convert("RGBA")

def grain(c, amt=6):
    n = np.random.default_rng(3).normal(0, amt, (H, W, 1))
    a = np.array(c.convert("RGB")).astype(float) + n
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- 1 SANTA: hero page close-up
def santa():
    c = bg_grad((150, 34, 44), (104, 18, 28))
    c = grain(c, 5)
    d = ImageDraw.Draw(c)
    # faint airmail stripe border top + bottom (envelope feel)
    for y0 in (0, H - 26):
        for i in range(-2, 60):
            x = i * 70
            col = (236, 226, 208) if i % 2 else (40, 92, 64)
            d.polygon([(x, y0), (x + 35, y0), (x + 35 + 26, y0 + 26), (x + 26, y0 + 26)], fill=col)
    # two other letters fanned behind
    for name, ang, x, y in [("santa_l1.png", 9, 210, 330), ("santa_l4.png", -8, 1150, 330)]:
        p = up(L(name), w=640)
        shadow_paste(c, p, x, y, angle=ang, blur=18, alpha=90)
    # hero letter
    hero = up(L("santa_letter.png"), w=1110)
    shadow_paste(c, hero, 445, 268, angle=-1.6, blur=30, off=(0, 26), alpha=150)
    d = ImageDraw.Draw(c)
    # headline: page's own idea
    f1 = F("Lora-BoldItalic", 128)
    text_c(d, 1000, 38, "Letters from Santa", f1, (255, 244, 225))
    f2 = F("Outfit-Bold", 40)
    text_c(d, 1000, 196, "6 EDITABLE LETTERS  •  TYPE THE NAME  •  PRINT AT HOME", f2, (246, 210, 140), spacing=3)
    return save(c, "santa-new.jpg")

# ---------------------------------------------------------------- 2 SCAVENGER: contents collage
def scavenger():
    c = Image.new("RGBA", (W, H), (246, 236, 222, 255))
    random.seed(7)
    big = [L(f"clue_big_{i}.png") for i in range(6)]
    sm = [L(f"clue_sm_{i}.png") for i in range(12)]
    cw, ch = 500, 318
    # rows of cards, edge to edge; centre 3 columns use the sharp big cards
    uniq = iter(big + sm[2:])
    edge = iter(sm[2:][::-1] + sm[2:])
    rows_y = [372, 690, 1008, 1326]
    for r, y in enumerate(rows_y):
        xs = [-260, 252, 764, 1276, 1788] if r % 2 == 0 else [-4, 508, 1020, 1532]
        for x in xs:
            centre = 260 < x + cw / 2 < 1740
            im = next(uniq) if centre else next(edge)
            im = up(im, w=cw + random.randint(-10, 20))
            shadow_paste(c, im, x + random.randint(-12, 12), y + random.randint(-14, 8),
                         angle=random.uniform(-3.5, 3.5), blur=12, off=(0, 8), alpha=95, radius=10)
    d = ImageDraw.Draw(c)
    # title banner across the top
    d.rectangle([0, 0, W, 348], fill=(146, 30, 42))
    for i in range(-2, 50):  # candy stripe edge
        x = i * 56
        d.polygon([(x, 348), (x + 28, 348), (x + 56, 372), (x + 28, 372)], fill=(255, 255, 255))
        d.polygon([(x + 28, 348), (x + 56, 348), (x + 84, 372), (x + 56, 372)], fill=(146, 30, 42))
    f = F("Gloock-Regular", 118)
    text_c(d, 1000, 46, "Christmas Scavenger Hunt", f, (255, 248, 236))
    f2 = F("Outfit-Bold", 42)
    s = "24 CLUES   |   RHYMES FOR AGES 4-7   |   RIDDLES FOR 8-12"
    text_c(d, 1000, 236, s, f2, (255, 214, 140), spacing=2)
    return save(c, "scavenger-new.jpg")

# ---------------------------------------------------------------- 3 ADVENT: bright grid
def advent():
    c = Image.new("RGBA", (W, H), (255, 250, 240, 255))
    d = ImageDraw.Draw(c)
    cols = [(232, 72, 85), (36, 128, 84), (255, 184, 28), (66, 150, 230), (240, 120, 170), (150, 96, 220)]
    # header: giant 24
    f24 = F("BricolageGrotesque-Bold", 330)
    d.text((292, -78), "24", font=f24, fill=(232, 52, 66))
    fa = F("BricolageGrotesque-Bold", 84)
    d.text((780, 30), "Days of Christmas", font=fa, fill=(28, 92, 60))
    fb = F("Lora-BoldItalic", 76)
    d.text((780, 122), "Family Activities", font=fb, fill=(40, 40, 40))
    fc = F("Outfit-Bold", 34)
    text_sp(d, 784, 222, "ONE SCREEN-FREE CARD FOR EVERY DECEMBER NIGHT", F("Outfit-Bold", 29), (232, 52, 66), spacing=1)
    # 6 x 4 calendar grid of colour tiles holding the real cards
    x0, y0, gw, gh = 280, 300, 240, 298
    for i in range(24):
        r, k = divmod(i, 6)
        x, y = x0 + k * gw, y0 + r * gh
        col = cols[(k + r * 2) % 6]
        d.rounded_rectangle([x + 4, y + 4, x + gw - 4, y + gh - 4], 22, fill=col)
        card = up(L(f"adv_{i+1:02d}.png"), w=gw - 30)
        card = card.crop((0, 0, card.width, min(card.height, gh - 30)))
        shadow_paste(c, card, x + 15, y + 15, blur=6, off=(0, 4), alpha=70, radius=8)
        d = ImageDraw.Draw(c)
    # side bands of colour (outside the square crop)
    rnd = random.Random(5)
    for k in range(70):
        side = k % 2
        x = rnd.randint(20, 230) if side == 0 else rnd.randint(1770, 1980)
        y = rnd.randint(20, 1480); r = rnd.choice([10, 14, 18, 24])
        d.ellipse([x - r, y - r, x + r, y + r], fill=cols[k % 6])
    return save(c, "advent-new.jpg")

# ---------------------------------------------------------------- 4 THANKSGIVING: device dashboard
def thanksgiving():
    c = bg_grad((196, 86, 34), (140, 50, 20))
    c = grain(c, 4)
    d = ImageDraw.Draw(c)
    text_c(d, 1000, 14, "First-Time Host", F("Lora-Italic", 80), (255, 226, 190))
    text_c(d, 1000, 100, "Thanksgiving Planner", F("Gloock-Regular", 124), (255, 255, 255))
    fl = F("Outfit-Bold", 34)
    text_c(d, 1000, 254, "REVERSE COOKING TIMELINE  ·  TURKEY THAW GUIDE  ·  GROCERY LIST", fl, (255, 214, 160), spacing=2)
    # tablet
    tx, ty, tw, th = 280, 330, 1290, 860
    tab = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    td = ImageDraw.Draw(tab)
    td.rounded_rectangle([0, 0, tw - 1, th - 1], 64, fill=(28, 28, 32))
    td.rounded_rectangle([6, 6, tw - 7, th - 7], 60, outline=(70, 70, 76), width=3)
    sx, sy, sw, sh = 40, 40, tw - 80, th - 80
    td.rectangle([sx, sy, sx + sw, sy + sh], fill=(255, 255, 255))
    pw = (sw - 30) // 2
    for i, n in enumerate(["tg_timeline.png", "tg_turkey.png"]):
        p = L(n)
        p = p.crop((0, 0, p.width - 28, p.height)) if i == 0 else p.crop((28, 0, p.width, p.height))
        p = up(p, w=pw)
        p = p.crop((0, 0, pw, min(p.height, sh - 20)))
        tab.paste(p, (sx + 10 + i * (pw + 10), sy + 10))
    shadow_paste(c, tab.convert("RGB"), tx, ty, blur=34, off=(0, 30), alpha=150, radius=64)
    # phone with grocery list
    g = L("tg_grocery_raw.png")
    g = g.crop((60, 40, g.width - 40, g.height))
    pw2, ph2 = 360, 720
    ph = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
    pd = ImageDraw.Draw(ph)
    pd.rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], 52, fill=(22, 22, 26))
    sw2, sh2 = pw2 - 36, ph2 - 60
    g2 = g.crop((0, 0, g.width, min(g.height, int(g.width * sh2 / sw2))))
    scr = up(g2, w=sw2).crop((0, 0, sw2, sh2)) if up(g2, w=sw2).height >= sh2 else up(g2, h=sh2).crop((0, 0, sw2, sh2))
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], 36, fill=255)
    ph.paste(scr, (18, 30), m)
    pd.rounded_rectangle([pw2 // 2 - 50, 12, pw2 // 2 + 50, 24], 6, fill=(22, 22, 26))
    shadow_paste(c, ph.convert("RGB"), 1360, 740, blur=26, off=(0, 24), alpha=160, radius=52)
    return save(c, "thanksgiving-new.jpg")

# ---------------------------------------------------------------- 5 GINGERBREAD: flat-lay
def gingerbread():
    base = np.zeros((H, W, 3), float); base[:] = (250, 244, 236)
    red = np.array((176, 52, 46), float)
    yy, xx = np.mgrid[0:H, 0:W]
    sq = 110
    a = ((xx // sq) % 2 == 0).astype(float) * 0.45 + ((yy // sq) % 2 == 0).astype(float) * 0.45
    base = base * (1 - a[..., None]) + red * a[..., None]
    c = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
    c = grain(c, 7)
    # certificate underneath
    cert = up(L("gb_cert_raw.png"), w=820)
    shadow_paste(c, cert, 220, 930, angle=5, blur=14, off=(6, 10), alpha=110)
    # score cards
    card = L("gb_card.png")
    shadow_paste(c, up(card, w=1060), 250, 400, angle=-5, blur=16, off=(8, 12), alpha=120)
    shadow_paste(c, up(card, w=1060), 690, 800, angle=3.5, blur=16, off=(8, 12), alpha=120)
    # pencil
    pen = Image.new("RGBA", (760, 40), (0, 0, 0, 0)); pdr = ImageDraw.Draw(pen)
    pdr.rectangle([60, 4, 690, 36], fill=(246, 190, 40)); pdr.rectangle([60, 4, 690, 14], fill=(255, 214, 90))
    pdr.polygon([(60, 4), (0, 20), (60, 36)], fill=(232, 200, 150)); pdr.polygon([(18, 15), (0, 20), (18, 25)], fill=(50, 50, 50))
    pdr.rectangle([690, 4, 715, 36], fill=(190, 190, 196)); pdr.rounded_rectangle([712, 4, 758, 36], 8, fill=(236, 120, 140))
    shadow_paste(c, pen.convert("RGB") if False else pen, 1080, 1330, angle=-14, blur=6, off=(6, 8), alpha=120)
    # two cookie stickers (the 1-of-5 allowance)
    for code, x, y, s in [("1f36a", 1560, 330, 200), ("1f36a", 1500, 560, 140)]:
        e = Image.open(ROOT + f"/tools/img3d/emoji_u{code}.png").convert("RGBA").resize((s, s), Image.LANCZOS)
        shadow_paste(c, e, x, y, blur=10, off=(6, 10), alpha=90)
    # title card (paper on the table)
    tw, th = 1260, 300
    tcard = Image.new("RGB", (tw, th), (255, 252, 246)); td = ImageDraw.Draw(tcard)
    td.rectangle([14, 14, tw - 15, th - 15], outline=(160, 70, 40), width=4)
    f1 = F("Gloock-Regular", 96)
    text_c(td, tw / 2, 34, "Gingerbread House Contest", f1, (120, 50, 28))
    f2 = F("Outfit-Bold", 38)
    text_c(td, tw / 2, 196, "JUDGE SCORE CARDS · BALLOTS · AWARDS · 15 PAGES", f2, (176, 52, 46), spacing=2)
    shadow_paste(c, tcard, 370, 50, angle=-1.2, blur=16, off=(6, 12), alpha=120)
    return save(c, "gingerbread-new.jpg")

if __name__ == "__main__":
    which = sys.argv[1:] or ["santa", "scavenger", "advent", "thanksgiving", "gingerbread"]
    for w in which: print(globals()[w]())
