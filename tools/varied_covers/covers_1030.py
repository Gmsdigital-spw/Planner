"""Oct 30, 2026 (Warden cover redo, Grayson's GO of Oct 28): two new per-listing covers.
  gingerbread_clip()  4600177516  judge's clipboard holding the real score card, contest pages tucked
                                  behind, white icing-scallop title band on mint (new family: clipboard)
  santa_flatlay()     4601798994  top-down Christmas Eve flat-lay: the real letter, Nice List certificate,
                                  North Pole envelope label and gift-tag strip on cobalt night blue,
                                  title in a bottom band (flat-lay family, adapted from gingerbread())
Rules kept: real pages only (cut from each listing's own photos 1/3/5 in listing-photos/auto/),
words inside x 280-1720, title >= 9% of height, no emoji stickers, the square-edge band
(x 230-270) kept plain so the app grid crop stays clean.
Run: COVERS_OUT=<dir> python3 covers_1030.py crops gingerbread_clip santa_flatlay
"""
import sys, random, math
import numpy as np
from common import *
from covers import bg_grad, grain

X = OUT + "/src/x/"
def L(n): return Image.open(X + n).convert("RGB")

def fit_font(d, s, name, size, maxw):
    while d.textlength(s, font=F(name, size)) > maxw: size -= 2
    return F(name, size)

def trim_white(im, thr=236, pad=0):
    a = np.array(im.convert("L")) < thr
    rows = np.where(a.mean(1) > 0.01)[0]; cols = np.where(a.mean(0) > 0.01)[0]
    return im.crop((max(0, cols.min() - pad), max(0, rows.min() - pad), cols.max() + 1 + pad, rows.max() + 1 + pad))

def crops():
    os.makedirs(X, exist_ok=True)
    g1 = src("listing-photos/auto/prod-gingerbread-contest-kit/1.jpg")
    g3 = src("listing-photos/auto/prod-gingerbread-contest-kit/3.jpg")
    g3.crop((300, 300, 1700, 1112)).save(X + "gb_score.png")
    for n, b in [("gb_guide", (1462, 344, 1890, 892)), ("gb_tally", (108, 910, 538, 1472)),
                 ("gb_signup", (1462, 910, 1890, 1472)), ("gb_judge", (108, 344, 538, 892))]:
        g1.crop(b).save(X + n + ".png")
    s3 = src("listing-photos/auto/prod-santa-mail-bundle/3.jpg")
    s3.crop((421, 301, 1578, 1529)).save(X + "sa_letter.png")
    s5 = src("listing-photos/auto/prod-santa-mail-bundle/5.jpg")
    cert = s5.crop((250, 400, 1030, 1370)).rotate(3.2, resample=Image.BICUBIC, fillcolor=(232, 238, 234))
    a = np.array(cert.convert("L")) > 246
    rows = np.where(a.mean(1) > 0.5)[0]; cols = np.where(a.mean(0) > 0.5)[0]
    cert.crop((cols.min() + 4, rows.min() - 70, cols.max() - 4, rows.max() - 2)).save(X + "sa_cert.png")
    s5.crop((1090, 512, 1362, 842)).save(X + "sa_label1.png")
    s5.crop((1390, 512, 1662, 842)).save(X + "sa_label2.png")
    s5.crop((1080, 1026, 1690, 1382)).save(X + "sa_tags.png")
    return X

# ------------------------------------------------ GINGERBREAD: judge's clipboard on mint, icing title band
def clipboard(w, h):
    b = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 34, fill=(214, 172, 118))
    rnd = random.Random(7)
    for y in range(6, h, 9):  # faint wood grain
        d.line([(18, y), (w - 18, y + rnd.randint(-3, 3))], fill=(204, 160, 106), width=2)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 34, outline=(176, 128, 78), width=5)
    d.rounded_rectangle([6, 6, w - 7, h - 7], 30, outline=(232, 200, 156), width=3)  # bevel highlight
    g = np.linspace(1.06, 0.9, h)[:, None, None]  # soft top light
    a = np.array(b).astype(float); a[..., :3] = np.clip(a[..., :3] * g, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")

def clip_metal(w):
    m = Image.new("RGBA", (w, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 40, w - 1, 132], 22, fill=(176, 180, 188))
    d.rounded_rectangle([8, 48, w - 9, 84], 16, fill=(214, 218, 226))
    d.rounded_rectangle([w // 2 - 90, 0, w // 2 + 90, 70], 30, fill=(150, 154, 162))
    d.rounded_rectangle([w // 2 - 54, 16, w // 2 + 54, 46], 14, fill=(74, 150, 140))
    return m

def gingerbread_clip():
    c = grain(bg_grad((92, 178, 160), (60, 142, 128)), 5)  # mint icing, bold (v > 0.5)
    # contest pages tucked behind the board
    shadow_paste(c, up(L("gb_guide.png"), w=560), 1300, 400, angle=-11, blur=18, off=(6, 14), alpha=120)
    shadow_paste(c, up(L("gb_tally.png"), w=540), 1400, 700, angle=-2, blur=18, off=(6, 14), alpha=120)
    # the board
    bw, bh = 1260, 980
    board = clipboard(bw, bh)
    sc = up(L("gb_score.png"), w=bw - 90)
    board.alpha_composite(sc.convert("RGBA"), (45, 158))
    cm = clip_metal(420)
    board.alpha_composite(cm, ((bw - 420) // 2, 4))
    shadow_paste(c, board, 320, 430, angle=2.2, blur=30, off=(10, 26), alpha=150)
    # pencil across the board corner
    pen = Image.new("RGBA", (700, 40), (0, 0, 0, 0)); pdr = ImageDraw.Draw(pen)
    pdr.rectangle([60, 4, 630, 36], fill=(232, 72, 60)); pdr.rectangle([60, 4, 630, 14], fill=(246, 112, 96))
    pdr.polygon([(60, 4), (0, 20), (60, 36)], fill=(232, 200, 150)); pdr.polygon([(18, 15), (0, 20), (18, 25)], fill=(50, 50, 50))
    pdr.rectangle([630, 4, 655, 36], fill=(190, 190, 196)); pdr.rounded_rectangle([652, 4, 698, 36], 8, fill=(250, 236, 220))
    shadow_paste(c, pen, 1000, 1250, angle=16, blur=6, off=(6, 8), alpha=120)
    # thin white icing drip along the top edge (kept above y 115 so the square-edge band stays plain;
    # round 1 had a 300 px white title band that tripped SQUARE_CLIP 0.49 and BLAND 28%)
    band = Image.new("RGBA", (W, 130), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rectangle([0, 0, W, 52], fill=(255, 253, 249))
    rnd = random.Random(5)
    x = -30
    while x < W + 30:
        r = rnd.choice([26, 30, 34]); dr = rnd.choice([0, 0, 18, 30])
        bd.ellipse([x, 52 - r, x + 2 * r, 52 + r], fill=(255, 253, 249))
        if dr: bd.rounded_rectangle([x + r - 10, 52, x + r + 10, min(112, 52 + r + dr)], 10, fill=(255, 253, 249))
        x += 2 * r - 4
    sh = band.split()[3].point(lambda v: v * 70 // 255).filter(ImageFilter.GaussianBlur(8))
    c.alpha_composite(Image.composite(Image.new("RGBA", (W, 130), (20, 70, 60, 255)), Image.new("RGBA", (W, 130), (0, 0, 0, 0)), sh), (0, 8))
    c.alpha_composite(band, (0, 0))
    d = ImageDraw.Draw(c)
    f1 = fit_font(d, "Gingerbread House Contest", "YoungSerif-Regular", 150, 1400)
    text_c(d, 1004, 136, "Gingerbread House Contest", f1, (40, 90, 80))  # soft shadow
    text_c(d, 1000, 130, "Gingerbread House Contest", f1, (255, 252, 244))
    f2 = F("Outfit-Bold", 46)
    text_c(d, 1000, 318, "15 PAGES  ·  SCORE CARDS  ·  BALLOTS  ·  AWARDS", f2, (110, 46, 20), spacing=2)
    return save(c, "4600177516.jpg")

# ------------------------------------------------ SANTA: Christmas Eve flat-lay on cobalt night blue
def envelope(w, h):
    e = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(e)
    d.rectangle([0, 0, w - 1, h - 1], fill=(190, 40, 44))
    d.polygon([(0, 0), (w // 2, int(h * 0.52)), (w, 0)], fill=(170, 30, 36))
    d.line([(0, 0), (w // 2, int(h * 0.52)), (w, 0)], fill=(150, 24, 30), width=3)
    return e

def santa_flatlay():
    c = grain(bg_grad((44, 84, 168), (30, 60, 132)), 5)  # cobalt night blue, bold (v > 0.5)
    rnd = random.Random(21)
    d = ImageDraw.Draw(c)
    for _ in range(60):  # a few tiny gold stars, kept off the square-edge band
        x, y = rnd.randint(300, 1990), rnd.randint(0, 1100)
        r = rnd.choice([3, 4, 5]); d.ellipse([x - r, y - r, x + r, y + r], fill=(224, 196, 120))
    # certificate (right, behind)
    shadow_paste(c, up(L("sa_cert.png"), w=700), 1180, 110, angle=-7, blur=22, off=(8, 18), alpha=150)
    # gift-tag strip (top left, behind the letter)
    shadow_paste(c, up(L("sa_tags.png"), w=560), 300, 90, angle=6, blur=16, off=(6, 12), alpha=130)
    # the letter, big, slight tilt
    shadow_paste(c, up(L("sa_letter.png"), w=1030), 470, 50, angle=3, blur=28, off=(10, 24), alpha=170)
    # envelope with the real North Pole label, bottom right over the letter's corner
    env = envelope(640, 420)
    lab = up(L("sa_label1.png"), w=300)
    env.alpha_composite(lab.convert("RGBA"), (310, 40))
    shadow_paste(c, env, 1290, 680, angle=-9, blur=20, off=(8, 16), alpha=150)
    # bottom title band
    band = Image.new("RGBA", (W, 300), (22, 40, 92, 236))
    c.alpha_composite(band, (0, H - 300))
    d = ImageDraw.Draw(c)
    d.rectangle([0, H - 300, W, H - 294], fill=(224, 190, 110))
    f1 = fit_font(d, "Letters from Santa", "Lora-BoldItalic", 170, 1400)
    text_c(d, 1000, H - 282, "Letters from Santa", f1, (255, 248, 236))
    f2 = F("Outfit-Bold", 44)
    text_c(d, 1000, H - 78, "6 EDITABLE LETTERS  ·  NICE LIST  ·  TAGS & LABELS", f2, (236, 200, 120), spacing=2)
    return save(c, "4601798994.jpg")

if __name__ == "__main__":
    for w in sys.argv[1:] or ["crops", "gingerbread_clip", "santa_flatlay"]:
        print(globals()[w]())
