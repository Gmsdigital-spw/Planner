"""Listing photos for the Christmas Trivia Game (prod-xmas-trivia-200). python3 photos.py"""
import sys, os
sys.path.insert(0, "/home/claude/kit")
sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs
import place
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/christmas-trivia-game.pdf"
OUT = HERE + "/photos"; os.makedirs(OUT, exist_ok=True)
PAL = gs.palette("evergreen")
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-xmas-trivia-200")
assert len(pages) == 17
P = {n: pages[n - 1] for n in range(1, 18)}
COVER_PAGES = [3, 5]           # round 1 + round 3: never repeated in photos 2-5; no answer key in any photo (no spoilers)
DEEP = gs.rgb(PAL["deep"]); PRIM = gs.rgb(PAL["primary"]); ACC = gs.rgb(PAL["accent"])
CREAM = (250, 246, 236); WHITE = (255, 255, 255); RED = (158, 59, 51)
font = gs.font
used = {}


# ------------------------------------------------------------------ 1 cover: real pages on the holiday-table scene, big cream headline card
def cover():
    W, H = 2000, 1500
    cx0, cy0, cw = 164, 55, 1110
    s = W / cw
    full = place.place("christmas", [P[3], P[5]], None, scale=s)
    im = full.crop((round(cx0 * s), round(cy0 * s), round(cx0 * s) + W, round(cy0 * s) + H))
    # page mask from the scene's slot quads (same numbers place.py uses)
    quads = place.SCENES["christmas"][1]
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for q in quads:
        md.polygon([((x - cx0) * s, (y - cy0) * s) for x, y in q], fill=255)
    page_top = min(y for q in quads for x, y in q)
    page_top_px = (page_top - cy0) * s
    d = ImageDraw.Draw(im)
    # headline card
    l1, l2 = "200 Christmas", "Trivia Questions"
    f1 = font("serifB", 138)
    while max(f1.getlength(l1), f1.getlength(l2)) > 1300: f1 = font("serifB", f1.size - 4)
    fs = font("sansM", 35)
    sub = "10 ROUNDS  ·  ANSWER KEYS  ·  TEAM SHEETS"
    b1 = d.textbbox((0, 0), l1, font=f1); b2 = d.textbbox((0, 0), l2, font=f1)
    lh = f1.size * 0.95
    q_bot = ImageDraw.Draw(Image.new('RGB', (10, 10))).textbbox((0, 0), l2, font=f1, anchor='ma')[3]   # incl. the Q tail
    card_w = max(f1.getlength(l1), f1.getlength(l2), fs.getlength(sub) + 8 * len(sub)) + 120
    card_h = 22 + lh + q_bot + 14 + 38 + 26
    x0 = (W - card_w) / 2; y0 = 22
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0 + 6, y0 + 14, x0 + card_w + 6, y0 + card_h + 14], 34, fill=(0, 0, 0, 70))
    from PIL import ImageFilter
    im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh.filter(ImageFilter.GaussianBlur(18)).split()[3])
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x0 + card_w, y0 + card_h], 34, fill=DEEP, outline=ACC, width=6)
    y = y0 + 22
    d.text((W / 2, y), l1, font=f1, fill=CREAM, anchor="ma"); bb1 = d.textbbox((W / 2, y), l1, font=f1, anchor="ma")
    y += lh
    d.text((W / 2, y), l2, font=f1, fill=CREAM, anchor="ma"); bb2 = d.textbbox((W / 2, y), l2, font=f1, anchor="ma")
    y = bb2[3] + 14
    # spaced small caps subline
    tw = sum(fs.getlength(ch) for ch in sub) + 8 * (len(sub) - 1); xx = W / 2 - tw / 2
    for ch in sub:
        d.text((xx, y), ch, font=fs, fill=(226, 196, 132)); xx += fs.getlength(ch) + 8
    card = (x0, y0, x0 + card_w, y0 + card_h)
    sb = d.textbbox((W / 2, y), sub, font=fs, anchor='ma')
    assert sb[1] >= bb2[3] + 10 and sb[3] <= card[3] - 18, ('subline crowded', sb, bb2, card)
    mask.paste(0, [int(x0), int(y0), int(x0 + card_w) + 1, int(y0 + card_h) + 1])
    return im, mask, {"line1": bb1, "line2": bb2, "card": card}, page_top_px


im, mask, boxes, page_top_px = cover()
gs.save_jpeg(im.resize((2000, 1500)), OUT + "/1-cover.jpg")
gs.thumb_check(im, OUT + "/thumb400.png")
s_ = min(im.size); x_ = (im.width - s_) // 2
im.crop((x_, 0, x_ + s_, s_)).resize((300, 300), Image.LANCZOS).save(OUT + "/thumb300.png")
card = boxes["card"]
assert card[0] >= 270 and card[2] <= 1730, ("headline card outside the centred square", card)
ink = boxes["line2"][3] - boxes["line1"][1]
line_h = boxes["line1"][3] - boxes["line1"][1]
print(f"cover headline: 2 lines, ink {ink}px = {ink / 1500 * 100:.1f}% of height (one line {line_h}px = {line_h / 1500 * 100:.1f}%)")
assert line_h / 1500 >= 0.07 and ink / 1500 >= 0.09
overlap = card[3] - page_top_px
print(f"card bottom {card[3]:.0f}px, page tops {page_top_px:.0f}px: card overlaps the pages' top stripe by {max(0, overlap):.0f}px")
# page text starts below the page's own stripe frame + kicker: about 7.5% of the page height
page_h = (879 - 273) * 2000 / 1110
assert overlap < 0.06 * page_h, ("headline card covers page text", overlap, page_h)
m = np.asarray(mask) > 0
print(f"real page pixels: {m.mean() * 100:.1f}% of the frame, {m[:, 250:1750].mean() * 100:.1f}% of the centred square")
assert m.mean() >= 0.60 and m[:, 250:1750].mean() >= 0.60
# whole pages: every slot corner (footers included) sits inside the frame
for q in place.SCENES["christmas"][1]:
    for x, y in q:
        X, Y = (x - 164) * 2000 / 1110, (y - 55) * 2000 / 1110
        assert 0 <= X <= 2000 and 0 <= Y <= 1500 - 8, ("cover crop cuts a page", X, Y)


def safe_text(d, xy, text, f, fill, anchor="la"):
    b = d.textbbox(xy, text, font=f, anchor=anchor)
    assert b[0] >= 260 and b[2] <= 1740, ("text outside the safe zone", text, b)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)
    return b


# ------------------------------------------------------------------ 2 inside: 6 pages the cover does not show, 470 px each
def inside():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 56), "200 Questions, 10 Themed Rounds", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 172), "Host page, history, nativity, true or false, kids and numbers rounds", font("sans", 40), (107, 107, 107), "ma")
    idxs = [2, 6, 7, 10, 11, 12]
    w, gx, gy = 470, 60, 32
    x0 = (2000 - (3 * w + 2 * gx)) // 2
    ph = int(w * 792 / 612)
    bots = []
    for k, n in enumerate(idxs):
        bb = gs.place(im, P[n], w, (x0 + (k % 3) * (w + gx), 250 + (k // 3) * (ph + gy)), shadow=0.22); bots.append(bb[3])
    print("photo 2 pages end at y", max(bots), "of 1600")
    assert 1600 - max(bots) < 240
    used[2] = idxs
    return im


gs.save_jpeg(inside(), OUT + "/2-inside.jpg")


# ------------------------------------------------------------------ 3 close-up: round 2 page, top 14 questions readable
def closeup():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 46), "Twenty Questions Per Round", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 156), "Read each one aloud twice; teams write their answers", font("sans", 42), (107, 107, 107), "ma")
    pg = P[4]
    # cut between two question rows so no row is sliced: row 13/14 boundary measured on the page grid
    top_frac, bot_frac = 0.035, 0.62
    a = np.asarray(pg.convert("L")).astype(int)
    h = a.shape[0]
    cut = int(h * bot_frac)
    # move the cut to the nearest fully-light row (between question rows)
    xs = slice(int(a.shape[1] * 0.12), int(a.shape[1] * 0.85))
    for dy in range(0, 60):
        for yy in (cut + dy, cut - dy):
            if (a[yy, xs] < 200).sum() == 0 and (a[yy - 6:yy + 6, int(a.shape[1] * 0.08):int(a.shape[1] * 0.1)] < 140).sum() == 0:
                cut = yy; break
        else:
            continue
        break
    cp = pg.crop((int(pg.width * 0.03), int(h * top_frac), int(pg.width * 0.97), cut))
    w = 1440
    bb = gs.place(im, cp, w, ((2000 - w) // 2, 250), shadow=0.25)
    print("photo 3 crop ends at y", bb[3], "of 1600")
    assert bb[3] <= 1600 and 1600 - bb[3] < 240, bb
    used[3] = [4]
    return im


gs.save_jpeg(closeup(), OUT + "/3-closeup.jpg")


# ------------------------------------------------------------------ 4 included: count + list, the PDF cover page big
def included():
    im = gs.paper(PAL["paper"], (2000, 1600)); d = ImageDraw.Draw(im)
    d.rectangle([1080, 0, 2000, 1600], fill=gs.rgb(PAL["tint"]))
    pw = 800
    bb = gs.place(im, P[1], pw, (1150, 170), angle=-2, shadow=0.3)
    d = ImageDraw.Draw(im)
    x = 270; y = 140
    safe_text(d, (x, y), "16-Page PDF", font("serifB", 112), DEEP); y += 150
    d.rectangle([x, y, x + 110, y + 6], fill=ACC); y += 46
    f = font("sans", 50)
    for it in ["How to play + host script", "10 rounds of 20 questions", "Answer keys for all 200",
               "Team answer sheet", "Score sheet for 10 teams", "3 tie-breaker questions", "Easy Kids' Round included"]:
        d.ellipse([x, y + 22, x + 20, y + 42], fill=PRIM)
        b = d.textbbox((x + 48, y), it, font=f); assert b[2] < 1060, it
        d.text((x + 48, y), it, font=f, fill=(43, 43, 43)); y += 118
    y += 20
    safe_text(d, (x, y), "Teams of 2 to 6  ·  mixed ages", font("sansM", 44), PRIM)
    d.rectangle([0, 1490, 2000, 1600], fill=DEEP)
    safe_text(d, (1000, 1545), "INSTANT DOWNLOAD  ·  PRINT AT HOME  ·  US LETTER PDF", font("sansM", 38), WHITE, "mm")
    print("photo 4 list ends at y", y + 56, "; PDF cover page", bb)
    assert bb[3] <= 1490 and bb[2] <= 2000
    used[4] = [1]
    return im


gs.save_jpeg(included(), OUT + "/4-included.jpg")


# ------------------------------------------------------------------ 5 game night sheets: answer sheet + score sheet, big
def sheets():
    im = gs.paper(PAL["tint"], (2000, 1600)); d = ImageDraw.Draw(im)
    safe_text(d, (1000, 46), "Team Sheets for Game Night", font("serifB", 88), DEEP, "ma")
    safe_text(d, (1000, 156), "Print an answer sheet per team each round; the host keeps score", font("sans", 40), (107, 107, 107), "ma")
    w = 880
    b1 = gs.place(im, P[15], w, (130, 232), angle=-3, shadow=0.3)
    b2 = gs.place(im, P[16], w, (990, 232), angle=3, shadow=0.3)
    print("photo 5 pages end at y", max(b1[3], b2[3]), "of 1600")
    used[5] = [15, 16]
    return im


gs.save_jpeg(sheets(), OUT + "/5-sheets.jpg")
shown = [n for v in used.values() for n in v]
assert not set(shown) & set(COVER_PAGES), "a photo repeats a cover page"
assert 17 not in shown
assert not {13, 14} & (set(shown) | set(COVER_PAGES)), "an answer key is shown in a photo"
for f in sorted(os.listdir(OUT)):
    if f.endswith(".jpg"):
        im_ = Image.open(OUT + "/" + f); sz = os.path.getsize(OUT + "/" + f)
        print(f, im_.size, sz); assert sz < 400_000 and im_.width == 2000
