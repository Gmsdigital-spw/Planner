"""Oct 29, 2026 (Warden cover redo, Grayson's GO of Oct 28): three new per-listing covers.
Each adapts a family from covers.py into a new composition for one listing (not a template):
  murder_mystery()  4602816114  stacked title + cascading case sheets on midnight (hero family, asymmetric)
  escape_room()     4602402578  fan of real puzzle pages on evergreen (new family: fan)
  scavenger_line()  4599447958  clothesline of real clue cards (new family: clothesline)
Rules kept: real pages only, words inside x 280-1720, title >= 9% of height, no emoji stickers,
nothing high-contrast on the square edge (x 230-270, y 120-600) so the app grid crop stays clean.
Sources: $COVERS_OUT/src/x/ (mm_*.png cut from the murder listing's photo 2; er_p*.png rendered from
the escape room PDF at 150 dpi; scav_*.png cut from the scavenger listing's full-size photos).
"""
import sys, random, math
import numpy as np
from common import *
from covers import bg_grad, grain

X = OUT + "/src/x/"
def L(n): return Image.open(X + n).convert("RGB")

def radial(c_in, c_out, cx=1000, cy=820, r=1250):
    yy, xx = np.mgrid[0:H, 0:W]
    t = np.clip(np.hypot(xx - cx, yy - cy) / r, 0, 1)[..., None] ** 1.4
    a = np.array(c_in) * (1 - t) + np.array(c_out) * t
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")

def fit_font(d, s, name, size, maxw):
    while d.textlength(s, font=F(name, size)) > maxw: size -= 2
    return F(name, size)

# ------------------------------------------------ MURDER MYSTERY: stacked title left, case sheets cascading right
# (round 2 of the side-by-side test: round 1 copied santa()'s centred hero + two fanned, too close to Letters from Santa)
def murder_mystery():
    c = grain(radial((132, 30, 66), (94, 20, 70), cx=1400, cy=700, r=1500), 5)  # wine-plum noir: bold enough for BLAND (v > 0.35)
    for n, ang, x, y in [("mm_noelle.png", 7, 1180, 120), ("mm_jasper.png", -4, 1020, 380)]:
        shadow_paste(c, up(L(n), w=760), x, y, angle=ang, blur=26, off=(0, 20), alpha=170)
    shadow_paste(c, up(L("mm_ivy.png"), w=860), 840, 600, angle=-8, blur=34, off=(0, 28), alpha=210)
    d = ImageDraw.Draw(c)
    cream, gold = (255, 244, 230), (236, 196, 120)
    f1 = F("Gloock-Regular", 168)
    for i, w in enumerate(["Christmas", "Murder", "Mystery"]):
        d.text((300, 170 + i * 178), w, font=f1, fill=cream)
    d.rectangle([306, 742, 520, 748], fill=gold)
    d.text((300, 780), "for 8 Players", font=F("Lora-BoldItalic", 104), fill=gold)
    f3 = F("Outfit-Bold", 36)
    for i, s in enumerate(["WHO STOLE THE STAR?", "SECRETS · ALIBIS · 3 ROUNDS", "16 PRINTABLE PAGES"]):
        text_sp(d, 304, 950 + i * 58, s, f3, (230, 170, 170), spacing=2)
    return save(c, "4602816114.jpg")

# ------------------------------------------------ ESCAPE ROOM: fan of real puzzle pages on bright red
def escape_room():
    c = grain(bg_grad((34, 118, 78), (14, 66, 44)), 5)  # evergreen (round 2: red read too close to Letters from Santa)
    d = ImageDraw.Draw(c)
    rnd = random.Random(11)
    for _ in range(170):  # soft snow dots, kept off the square-edge band
        x, y, r = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([4, 6, 8])
        if 200 < x < 300 and y < 640: continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=(120, 182, 146))
    pages = ["er_p4.png", "er_p8.png", "er_p10.png", "er_p12.png", "er_p9.png"]  # maze last = front centre
    angles = [-26, 26, -13, 13, 0]
    pw = 640
    px, py = 1000, 2440  # pivot below the frame (fan kept under y 600 at the square edge)
    for n, a in zip(pages, angles):
        p = up(L(n), w=pw)
        rad = math.radians(a)
        ccx = px + math.sin(rad) * 1560; ccy = py - math.cos(rad) * 1560
        im = p.convert("RGBA").rotate(-a, resample=Image.BICUBIC, expand=True)
        shadow_paste(c, p, ccx - im.width / 2, ccy - im.height / 2 + 30, angle=-a, blur=24, off=(0, 18), alpha=150)
    d = ImageDraw.Draw(c)
    f1 = fit_font(d, "Christmas Escape Room", "BricolageGrotesque-Bold", 168, 1420)
    text_c(d, 1000, 18, "Christmas Escape Room", f1, (255, 250, 240))
    f2 = F("Outfit-Bold", 46)
    text_c(d, 1000, 222, "FOR KIDS  ·  2 LEVELS  ·  AGES 6-9 & 10+  ·  NO PHONE", f2, (255, 214, 120), spacing=2)
    return save(c, "4602402578.jpg")

# ------------------------------------------------ SCAVENGER HUNT: clue cards on a clothesline
def clothespin(angle):
    p = Image.new("RGBA", (34, 92), (0, 0, 0, 0)); pd = ImageDraw.Draw(p)
    pd.rounded_rectangle([2, 0, 32, 92], 6, fill=(214, 170, 112)); pd.line([17, 4, 17, 88], fill=(170, 124, 72), width=3)
    pd.rectangle([4, 36, 30, 44], fill=(150, 150, 156))
    return p.rotate(angle, resample=Image.BICUBIC, expand=True)

def scavenger_line(cards):
    c = grain(bg_grad((34, 92, 66), (18, 58, 42)), 6)
    d = ImageDraw.Draw(c)
    rnd = random.Random(4)
    rows = [(330, [(290, 0), (765, 0), (1240, 0)], 470),
            (735, [(-180, 0), (295, 0), (770, 0), (1245, 0), (1720, 0)], 470),
            (1140, [(60, 0), (535, 0), (1010, 0), (1485, 0)], 470)]
    it = iter(cards)
    for y, slots, cw in rows:
        # twine: a shallow curve across the full width
        pts = [(x, y + 10 + 26 * math.sin(math.pi * x / W)) for x in range(-20, W + 21, 20)]
        if y < 600:  # keep the square-edge band plain: twine on row 1 starts inside the square
            pts = [p for p in pts if 280 <= p[0] <= 1720]
        d.line(pts, fill=(222, 196, 150), width=6)
        for x, _ in slots:
            card = up(next(it), w=cw)
            ang = rnd.uniform(-3, 3)
            yy = y + 10 + 26 * math.sin(math.pi * (x + cw / 2) / W)
            shadow_paste(c, card, x, yy + 18, angle=ang, blur=10, off=(4, 10), alpha=120, radius=10)
            for k in (0.2, 0.8):
                pin = clothespin(rnd.uniform(-6, 6))
                c.alpha_composite(pin, (int(x + cw * k - pin.width / 2), int(yy - 30)))
        d = ImageDraw.Draw(c)
    f1 = fit_font(d, "Christmas Scavenger Hunt", "Gloock-Regular", 150, 1420)
    text_c(d, 1000, 30, "Christmas Scavenger Hunt", f1, (255, 250, 240))
    f2 = F("Outfit-Bold", 44)
    text_c(d, 1000, 214, "24 RHYMING CLUE CARDS  ·  AGES 4-12  ·  PRINT & HIDE", f2, (255, 206, 120), spacing=2)
    return save(c, "4599447958.jpg")

if __name__ == "__main__":
    for w in sys.argv[1:] or ["murder_mystery", "escape_room"]:
        print(globals()[w]())
