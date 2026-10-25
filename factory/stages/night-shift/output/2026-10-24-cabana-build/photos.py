"""Lens: cover on Grayson's clipboard scene + 4 inside photos, from the real PDF pages."""
import sys, os, importlib.util
sys.path.insert(0, "/home/claude/kit"); sys.path.insert(0, "/home/claude/planner/assets/atlas-pack")
import gm_style as gs, place
from PIL import Image, ImageDraw
B = os.path.dirname(os.path.abspath(__file__)); PDF = B + "/pink-cabana-birthday-invitation.pdf"
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
spec = importlib.util.spec_from_file_location("mc_helpers", "/dev/null")
pages = gs.render_pages(PDF, "/home/claude/kit/pages/prod-invite-birthday-pink-cabana")  # 150 dpi
pal = gs.palette("blush")
def card(i, k=0):
    p = pages[i]; W, H = p.size; cw, ch = int(W * 5 / 11), int(H * 7 / 8.5)
    gap = int(W * 0.25 / 11); x = (W - 2 * cw - gap) // 2 + k * (cw + gap); y = (H - ch) // 2
    return p.crop((x, y, x + cw, y + ch))
# ---- cover: the card printed on cream paper, clipped to the board
inv = card(2, 0)
sw, sh = 626, 774; paper_w = 1300; paper_h = int(paper_w * sh / sw)
paper = Image.new("RGB", (paper_w, paper_h), (250, 247, 241))
cw = int(paper_w * 0.80); chh = int(inv.height * cw / inv.width)
paper.paste(inv.resize((cw, chh), Image.LANCZOS), ((paper_w - cw) // 2, paper_h - chh - int(paper_h * 0.035)))
cx, cy, cwid = 150, 40, 1110; sc = 2000 / cwid
big = place.place("clipboard", [paper], scale=sc)
img = big.crop((round(cx * sc), round(cy * sc), round(cx * sc) + 2000, round(cy * sc) + 1600)).convert("RGB")
FD = "/usr/share/fonts/truetype/google-fonts/"
from PIL import ImageFont
def font(n, s, w=None):
    f = ImageFont.truetype(FD + n, s)
    if w:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f
def label(img, title, sub, color, pos):
    W, H = img.size; d = ImageDraw.Draw(img, "RGBA")
    ft = font("Lora-Variable.ttf", 124, 650); fs = font("Poppins-Medium.ttf", 40)
    pad = 46; bw = max(d.textlength(title, font=ft), d.textlength(sub, font=fs) + 40) + pad * 2; bh = 128 + 50 + pad * 2 + 6
    x0 = (W - bw) / 2; y0 = 60 if pos == "top" else H - bh - 70
    d.rounded_rectangle((x0 + 6, y0 + 10, x0 + bw + 6, y0 + bh + 10), 26, fill=(0, 0, 0, 40))
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), 26, fill=(251, 247, 240, 245))
    d.rounded_rectangle((x0 + 14, y0 + 14, x0 + bw - 14, y0 + bh - 14), 18, outline=color, width=3)
    d.text((W / 2, y0 + pad - 10), title, font=ft, fill=color, anchor="ma")
    d.text((W / 2, y0 + pad + 132), sub, font=fs, fill=(90, 82, 74), anchor="ma")
    return (x0, y0, x0 + bw, y0 + bh)
box = label(img, "Editable Bow Invite", "TYPE IN THE PDF  ·  NO ACCOUNT NEEDED", "#2F5B45", "top")
print("label box", [round(v) for v in box])
gs.save_jpeg(img, OUT + "/1-cover.jpg")
gs.thumb_check(img, OUT + "/thumb400.png")
sq = img.crop((200, 0, 1800, 1600)).resize((300, 300), Image.LANCZOS); sq.save(OUT + "/thumb300.png")
# ---- photo 2: both colourways, invite + details (4 cards in a row)
cards = [card(2, 0), card(3, 0), card(4, 0), card(5, 0)]
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Two colors, every card", "PINK AND SAGE  ·  TYPE IN THE PDF, NO ACCOUNT NEEDED")
pw_ = 700
for i, pg in enumerate(pages[2:6]):
    gs.place(im, pg, pw_, ((gs.IW - 2 * pw_ - 60) // 2 + (i % 2) * (pw_ + 60), 330 + (i // 2) * 630))
gs.save_jpeg(im, OUT + "/2-colourways.jpg")
# ---- photo 3: close-up of the type-in lines (filled sample)
import subprocess
subprocess.run(["pdftoppm", "-r", "220", "-png", "-f", "3", "-l", "3", OUT + "/filled.pdf" if os.path.exists(OUT + "/filled.pdf") else PDF, OUT + "/hz"], check=True)
hz = Image.open([OUT + "/" + f for f in os.listdir(OUT) if f.startswith("hz")][0]).convert("RGB")
W, H = hz.size; cw2, ch2 = int(W * 5 / 11), int(H * 7 / 8.5); gx = int(W * 0.25 / 11); x0 = (W - 2 * cw2 - gx) // 2; y0 = (H - ch2) // 2
crop = hz.crop((x0, y0 + int(ch2 * 0.04), x0 + cw2, y0 + int(ch2 * 0.93)))
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Type your own party details", "SAMPLE TYPED IN FREE ADOBE ACROBAT READER  ·  82 TYPE-IN LINES")
cwid = 920; gs.place(im, crop, cwid, ((gs.IW - cwid) // 2, 320))
gs.save_jpeg(im, OUT + "/3-closeup.jpg")
# ---- photo 4: what's included
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "What you get: a full party set", "INVITES  \u00b7  DETAILS  \u00b7  THANK-YOU CARDS  \u00b7  8x10 WELCOME SIGN")
sg = pages[8]; Ws, Hs = sg.size; sw_, sh_ = int(Ws * 8 / 8.5), int(Hs * 10 / 11)
sgn = sg.crop(((Ws - sw_) // 2, (Hs - sh_) // 2, (Ws + sw_) // 2, (Hs + sh_) // 2))
gs.place(im, sgn, 600, (300, 540), angle=0)
for c_, x_, y_ in ((card(2, 0), 960, 340), (card(6, 0), 1340, 340), (card(4, 0), 960, 960), (card(3, 0), 1340, 960)):
    gs.place(im, c_, 400, (x_, y_))
gs.save_jpeg(im, OUT + "/4-included.jpg")
# ---- photo 5: how it works
im = gs.preview_how(pal, [("Open", "the PDF in free Adobe Acrobat Reader on a computer"), ("Type", "your names, date, place and RSVP over the green lines"), ("Print", "on cardstock at Actual size and cut on the marks")])
from PIL import ImageFont as _F
_d = ImageDraw.Draw(im); _d.rectangle((200, 975, 1800, 1060), fill=im.getpixel((100, 1000)))
_d.text((1000, 1000), "Digital PDF  \u00b7  Prints on US Letter or A4  \u00b7  Nothing ships", font=_F.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf", 44), fill=gs.rgb(pal["primary"]), anchor="ma")
sg2 = pages[9]; sgn2 = sg2.crop(((Ws - sw_) // 2, (Hs - sh_) // 2, (Ws + sw_) // 2, (Hs + sh_) // 2))
strip = [sgn2, card(3, 0), card(5, 0), card(7, 0)]
xs = 421
for c_ in strip:
    w_ = 252 if c_ is not sgn2 else 282
    gs.place(im, c_, w_, (xs, 1085)); xs += w_ + 40
gs.save_jpeg(im, OUT + "/5-how.jpg")
print("ok")
