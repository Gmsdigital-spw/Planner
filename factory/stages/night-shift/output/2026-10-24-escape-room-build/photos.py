"""Listing photos for prod-xmas-escape-room. python3 photos.py <outdir>"""
import sys, os
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs
import place as atlas
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
PG = "/home/claude/kit/pages/prod-xmas-escape-room"
pages = [Image.open(f"{PG}/p-{i:02d}.png").convert("RGB") for i in range(1, 18)]
P = lambda n: pages[n - 1]
pal = gs.palette("berry")
FD = "/usr/share/fonts/truetype/google-fonts/"
LABEL = "#7E5B16"   # warm bell gold: not on any live christmas-scene cover (reds #9B2A2E/#8E2433, green #1F5A41)


def lfont(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f


def label(img, title, sub, color, pos, bottom_gap=48):
    """Same cream label system as listing-photos/atlas/make_covers.py (Oct 24 standard)."""
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    ft = lfont("Lora-Variable.ttf", 124, 650); fs = lfont("Poppins-Medium.ttf", 40)
    lh = 132; sh = 52; pad = 46
    bw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs) + 40) + pad * 2
    bh = lh + sh + pad * 2 + 6
    x0 = (W - bw) / 2; y0 = 70 if pos == "top" else H - bh - bottom_gap
    d.rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 26, fill=(0, 0, 0, 40))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 26, fill=(251, 247, 240, 245))
    d.rounded_rectangle((x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14), 18, outline=color, width=3)
    y = y0 + pad - 10
    d.text((W / 2, y), title, font=ft, fill=color, anchor="ma"); y += lh
    d.text((W / 2, y + 14), sub, font=fs, fill=(90, 82, 74), anchor="ma")
    return (x0, y0, x0 + bw, y0 + bh)


# ---------------------------------------------------------------- 1 cover
cx, cy, cw = 120, 170, 1200          # crop in scene px (5:4); tighter and lower than the live christmas covers
sc = 2000 / cw
big = atlas.place("christmas", [P(8), P(9)], scale=sc)
cover = big.crop((round(cx * sc), round(cy * sc), round(cx * sc) + 2000, round(cy * sc) + 1600)).convert("RGB")
box = label(cover, "Christmas Escape Game", "TWO LEVELS  ·  AGES 6-9 & 10+  ·  NO PHONE NEEDED", LABEL, "bottom", bottom_gap=40)
print("cover label box", [round(v) for v in box], "sheets bottom", round((879 - cy) * sc))
gs.save_jpeg(cover, f"{OUT}/1-cover.jpg")


# ---------------------------------------------------------------- helpers for inside photos
def header(d, title, sub):
    gs._text(d, (gs.IW / 2, 62), title, gs.font("serifB", 84), gs.rgb(pal["deep"]), anchor="ma")
    gs._spaced(d, gs.IW / 2, 170, sub, gs.font("sansM", 34), gs.rgb(pal["primary"]))


# ---------------------------------------------------------------- 2 the two levels grid (3x2, ~470 px pages)
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
header(d, "Every Clue Comes in Two Levels", "TOP ROW: AGES 6-9   ·   BOTTOM ROW: AGES 10+   ·   SAME ANSWER")
w = 455; ph = int(w * 1650 / 1275); gx = 60
x0 = (gs.IW - (3 * w + 2 * gx)) // 2
for k, n in enumerate((4, 6, 10, 5, 7, 11)):
    gs.place(im, P(n), w, (x0 + (k % 3) * (w + gx), 250 + (k // 3) * (ph + 26)), shadow=0.2)
gs._check_safe()
print("grid bottom", 250 + ph * 2 + 26)
gs.save_jpeg(im, f"{OUT}/2-levels.jpg")

# ---------------------------------------------------------------- 3 close-up: the mission letter (story hook)
im = gs.preview_closeup(P(3), pal, "Read the Mission, Start the Clock", "45 minutes  ·  1 to 12 players  ·  no phone or internet", crop=(0.04, 0.0, 0.96, 0.56))
gs.save_jpeg(im, f"{OUT}/3-mission.jpg")

# ---------------------------------------------------------------- 4 what's included: list + 3 real pages fanned big
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
d.rectangle([1000, 0, gs.IW, gs.IH], fill=gs.rgb(pal["tint"]))
gs.place(im, P(2), 440, (1045, 110), angle=-2, shadow=0.24)
gs.place(im, P(13), 440, (1515, 120), angle=2, shadow=0.24)
gs.place(im, P(16), 440, (1280, 790), angle=-1, shadow=0.26)
y = 150
gs._text(d, (gs.SAFE_L, y), "16 Pages", gs.font("serifB", 110), gs.rgb(pal["deep"])); y += 150
d.rectangle([gs.SAFE_L, y, gs.SAFE_L + 110, y + 6], fill=gs.rgb(pal["accent"])); y += 44
f = gs.font("sans", 44)
items = ["Game master guide", "Mission letter + team sheet", "8 clue sheets (4 clues x 2 levels)", "Vault lock sheet",
         "6 envelope lock tags", "8 two-step hint cards", "Answer key (game master only)", "Escape Expert certificates"]
for it in items:
    d.ellipse([gs.SAFE_L, y + 20, gs.SAFE_L + 18, y + 38], fill=gs.rgb(pal["primary"]))
    gs._text(d, (gs.SAFE_L + 40, y), it, f, gs.rgb(gs.INK)); y += 86
y += 20
d.rounded_rectangle([gs.SAFE_L, y, 940, y + 150], radius=22, fill=(255, 255, 255), outline=gs.rgb(pal["primary"]), width=3)
gs._text(d, (gs.SAFE_L + 30, y + 26), "Ages 6-9 and 10+", gs.font("sansM", 42), gs.rgb(pal["deep"]))
gs._text(d, (gs.SAFE_L + 30, y + 84), "1 to 12 players  ·  about 45 minutes", gs.font("sans", 36), gs.rgb(gs.INK))
y += 150
assert y < gs.IH - 130, y
gs._strip(im, d, pal, "ONE PDF  ·  PRINT AT HOME  ·  NOTHING SHIPS")
gs._check_safe()
gs.save_jpeg(im, f"{OUT}/4-included.jpg")

# ---------------------------------------------------------------- 5 how it plays: the vault page + 3 steps, ink-light proof
im = gs.paper(pal["tint"]); d = ImageDraw.Draw(im)
gray = P(12).convert("L").convert("RGB")
gs.place(im, P(12), 640, (280, 260), angle=0, shadow=0.24)
gs.place(im, gray, 360, (700, 920), angle=4, shadow=0.24)
gs._text(d, (gs.IW / 2, 62), "No Phone, No App, No QR Codes", gs.font("serifB", 84), gs.rgb(pal["deep"]), anchor="ma")
steps = [("Print and set up", "Clue sheets go in 5 envelopes. About 10 minutes."),
         ("Solve 4 clues", "Each clue gives one digit of the vault code."),
         ("Check with the key", "The game master checks every digit on paper.")]
y = 300
for i, (h1, body) in enumerate(steps):
    xs = 1040
    d.ellipse([xs, y, xs + 110, y + 110], fill=gs.rgb(pal["primary"]))
    gs._text(d, (xs + 55, y + 55), str(i + 1), gs.font("serifB", 64), (255, 255, 255), anchor="mm")
    gs._text(d, (xs + 140, y + 4), h1, gs.font("sansM", 52), gs.rgb(pal["deep"]))
    yy = y + 76
    for ln in gs._wrap_px(body, gs.font("sans", 38), 1740 - xs - 140):
        gs._text(d, (xs + 140, yy), ln, gs.font("sans", 38), gs.rgb(gs.INK)); yy += 52
    y = yy + 60
gs._text(d, (1100, 1210), "Ink-light pages: every puzzle", gs.font("sansM", 38), gs.rgb(pal["primary"]))
gs._text(d, (1100, 1262), "works in black and white.", gs.font("sansM", 38), gs.rgb(pal["primary"]))
gs._check_safe()
gs.save_jpeg(im, f"{OUT}/5-how.jpg")

for f in sorted(os.listdir(OUT)):
    if f.endswith(".jpg"): print(f, Image.open(f"{OUT}/{f}").size, os.path.getsize(f"{OUT}/{f}"))
