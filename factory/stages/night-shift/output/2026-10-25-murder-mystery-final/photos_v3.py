# Oct 25 final finish try: Atlas holiday-table cover (cover-styles Oct 24) + photos 2-5 from the v2 PDF.
# Page index: 0 cover,1 host,2 timeline,3 invites,4 Ivy,5 Jasper,6 Clem(thief: never shown),7 Rupert,
# 8 Noelle,9 Dash,10 Marigold,11 Felix,12 clues,13 notes,14 solution(never shown),15 tags,16 thanks.
import sys, glob, os
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs, place
from gm_style import ImageDraw, Image
from PIL import ImageFont
PD = "/home/claude/kit/pages/prod-xmas-murder-mystery-8"; OUT = os.path.dirname(os.path.abspath(__file__))
P = sorted(glob.glob(PD + "/p-*.png")); assert len(P) == 17
pages = [Image.open(f).convert("RGB") for f in P]
pal = gs.palette("berry")
FD = "/usr/share/fonts/truetype/google-fonts/"
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f
# ---- 1 cover: invitation + Marigold (innocent) sheet; clue cards left off: C9+C2 together would let a close reader deduce the thief on the holiday table, label at the bottom
cw, cx, cy = 1250, 100, 30
sc = 2000 / cw
big = place.place("clipboard", [P[3]], scale=sc)  # fix round 1: the Oct 24 escape room cover already uses the holiday table + bottom label
img = big.crop((round(cx*sc), round(cy*sc), round(cx*sc)+2000, round(cy*sc)+1600)).convert("RGB")
d = ImageDraw.Draw(img, "RGBA"); W, H = img.size; color = "#7A1F2B"
ft = font("Lora-Variable.ttf", 132, 650); fs = font("Poppins-Medium.ttf", 58)
title = "Who Stole the Star?"; sub = "8 PLAYERS  ·  PRINTABLE PARTY GAME"
pad = 44; bw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs)) + pad*2
bh = 140 + 70 + pad*2; x0 = (W-bw)/2; y0 = 60
d.rounded_rectangle((x0+6, y0+10, x0+bw+6, y0+bh+10), 26, fill=(0,0,0,45))
d.rounded_rectangle((x0, y0, x0+bw, y0+bh), 26, fill=(251,247,240,255))
d.rounded_rectangle((x0+14, y0+14, x0+bw-14, y0+bh-14), 18, outline=color, width=3)
d.text((W/2, y0+pad-8), title, font=ft, fill=color, anchor="ma")
d.text((W/2, y0+pad+146), sub, font=fs, fill=(70,62,56), anchor="ma")
print("label box x", int(x0), int(x0+bw), "y", int(y0), int(y0+bh))
gs.save_jpeg(img, OUT + "/cover_v3.jpg")
img.crop(((W-H)//2, 0, (W-H)//2+H, H)).resize((300, 300), Image.LANCZOS).save(OUT + "/cover_v3_300.png")
gs.thumb_check(img, OUT + "/cover_v3_400.png")
# ---- 2: three character sheets big (unchanged v2 layout)
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "A Sheet for Every Guest", "Who you are, costume, secret, alibi and 3 rounds of lines")
w, gap = 636, 12; x0 = (gs.IW - (3*w + 2*gap)) // 2
ph = int(w * pages[4].height / pages[4].width); block = ph + 34 + 66 + 56
y0 = 290 + (gs.IH - 110 - 290 - block) // 2
for k, i in enumerate((4, 5, 8)): gs.place(im, pages[i], w, (x0 + k*(w+gap), y0), shadow=0.22)
d = ImageDraw.Draw(im); y = y0 + ph + 34
gs._text(d, (gs.IW/2, y), "8 characters, one page each", gs.font("sansM", 46), gs.rgb(pal["deep"]), anchor="ma"); y += 66
gs._text(d, (gs.IW/2, y), "Ivy  ·  Jasper  ·  Clem  ·  Rupert  ·  Noelle  ·  Dash  ·  Marigold  ·  Felix", gs.font("sans", 38), gs.rgb(gs.INK), anchor="ma")
gs._strip(im, d, pal, "ANY GUEST CAN PLAY ANY ROLE  ·  HOST CAN PLAY"); gs._check_safe()
gs.save_jpeg(im, OUT + "/photo2_v3.jpg")
# ---- 3: host guide + timeline/script, big (from the v2 PDF: no culprit named)
im = gs.paper(pal["tint"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Host-Ready in 10 Minutes", "Setup checklist, timeline and a read-aloud script")
w, gap = 900, 40; ph = int(w * pages[1].height / pages[1].width)
x0 = (gs.IW - (2*w + gap)) // 2; y0 = 290
for k, i in enumerate((1, 2)): gs.place(im, pages[i], w, (x0 + k*(w+gap), y0), shadow=0.22)
gs._check_safe(); gs.save_jpeg(im, OUT + "/photo3_v3.jpg")
# ---- 4: what's included, 3 real pages fanned (name tags, notes, contents page)
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
d.rectangle([960, 0, gs.IW, gs.IH], fill=gs.rgb(pal["tint"]))
# fix round 2: pages were 560-660 px (about a third of the frame); now 2 real pages at 760-800 px
gs.place(im, pages[15], 760, (1170, 110), angle=4, shadow=0.22)
gs.place(im, pages[0], 800, (960, 330), angle=-2, shadow=0.28)
d = ImageDraw.Draw(im); x = gs.SAFE_L; y = 130
gs._text(d, (x, y), "16 Pages", gs.font("serifB", 120), gs.rgb(pal["deep"])); y += 160
d.rectangle([x, y, x+120, y+7], fill=gs.rgb(pal["accent"])); y += 56
f = gs.font("sans", 48)
for it in ["Host guide + setup", "Timeline + host script", "Invitations, 2 per sheet", "8 character sheets",
           "9 clue cards, 3 rounds", "Detective Notes sheet", "Sealed solution page", "Name tags + 2 awards"]:
    d.ellipse([x, y+22, x+20, y+42], fill=gs.rgb(pal["primary"])); gs._text(d, (x+46, y), it, f, gs.rgb(gs.INK)); y += 92
y += 20; gs._text(d, (x, y), "Sized for exactly 8 guests", gs.font("sansM", 44), gs.rgb(pal["primary"])); y += 62
assert y < gs.IH - 130, y
gs._strip(im, d, pal); gs._check_safe(); gs.save_jpeg(im, OUT + "/photo4_v3.jpg")
# ---- 5: close-up of one innocent guest's sheet (Rupert), readable
im = gs.preview_closeup(pages[7], pal, "Lines for All 3 Rounds", "Each guest gets a secret, an alibi and what to say", crop=(0, 0, 1, .775))
gs.save_jpeg(im, OUT + "/photo5_v3.jpg")
for n in ("cover_v3", "photo2_v3", "photo3_v3", "photo4_v3", "photo5_v3"):
    q = Image.open(f"{OUT}/{n}.jpg"); print(n, q.size, os.path.getsize(f"{OUT}/{n}.jpg"))
row = Image.new("RGB", (2500, 400), "white")
for k, n in enumerate(("cover_v3", "photo2_v3", "photo3_v3", "photo4_v3", "photo5_v3")):
    row.paste(Image.open(f"{OUT}/{n}.jpg").resize((500, 400)), (k*500, 0))
row.save(OUT + "/row_v3.png")
