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
# ---- photo 4: flat lay, the set as it goes out (cards + envelope on blush paper, soft shadows)
from PIL import ImageFilter as _IF, ImageFont as _F
sg = pages[8]; Ws, Hs = sg.size; sw_, sh_ = int(Ws * 8 / 8.5), int(Hs * 10 / 11)
sgn = sg.crop(((Ws - sw_) // 2, (Hs - sh_) // 2, (Ws + sw_) // 2, (Hs + sh_) // 2))
sg2 = pages[9]; sgn2 = sg2.crop(((Ws - sw_) // 2, (Hs - sh_) // 2, (Ws + sw_) // 2, (Hs + sh_) // 2))
W4, H4 = 2000, 1600
base = Image.new("RGB", (W4, H4), (243, 226, 224))
import random as _r; _r.seed(7)
noise = Image.effect_noise((W4, H4), 6).convert("L")  # fine paper grain
base = Image.composite(base, Image.new("RGB", (W4, H4), (236, 217, 215)), noise.point(lambda v: 255 if v > 120 else 200))
im4 = base.convert("RGBA")
def lay(img, piece, w, xy, ang):
    p = piece.convert("RGBA").resize((w, int(piece.height * w / piece.width)), Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (p.width + 60, p.height + 60), (0, 0, 0, 0))
    m = p.split()[3].point(lambda v: 70 if v else 0); blk = Image.new("RGBA", p.size, (70, 40, 40, 255)); blk.putalpha(m)
    sh.paste(blk, (34, 38), blk); sh = sh.filter(_IF.GaussianBlur(16))
    img.alpha_composite(sh, (xy[0] - 30, xy[1] - 30)); img.alpha_composite(p, xy)
# plain kraft-cream A7 envelope with its flap open (flat shapes, no texture tricks)
env = Image.new("RGBA", (560, 400), (0, 0, 0, 0)); de = ImageDraw.Draw(env)
de.rectangle((0, 0, 560, 400), fill=(250, 246, 238, 255)); de.polygon([(0, 0), (280, 190), (560, 0)], fill=(241, 234, 222, 255))
de.line([(0, 400), (280, 215), (560, 400)], fill=(226, 216, 202, 255), width=3)
lay(im4, env, 560, (1330, 1050), -8)
lay(im4, sgn, 640, (180, 300), 4)
lay(im4, card(4, 0), 430, (820, 250), -5)
lay(im4, card(6, 0), 430, (1300, 330), 6)
lay(im4, card(2, 0), 470, (870, 760), 2)
im4 = im4.convert("RGB"); d4 = ImageDraw.Draw(im4, "RGBA")
ft = _F.truetype("/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf", 76); fs = _F.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf", 34)
_tw = max(d4.textlength("The whole party, matched", font=ft), d4.textlength("INVITE  \u00b7  DETAILS  \u00b7  THANK YOU  \u00b7  8x10 SIGN", font=fs)) + 100
d4.rounded_rectangle((1000 - _tw / 2, 64, 1000 + _tw / 2, 240), 24, fill=(251, 247, 240, 240), outline=(178, 78, 100), width=3)
d4.text((1000, 84), "The whole party, matched", font=ft, fill=(178, 78, 100), anchor="ma")
d4.text((1000, 180), "INVITE  \u00b7  DETAILS  \u00b7  THANK YOU  \u00b7  8x10 SIGN", font=fs, fill=(90, 82, 74), anchor="ma")
gs.save_jpeg(im4, OUT + "/4-included.jpg")
# ---- photo 5: how typing works, shown on the real card (field highlight like Acrobat Reader)
hz5 = Image.open([OUT + "/" + f for f in os.listdir(OUT) if f.startswith("hz")][0]).convert("RGB")
W5, H5 = hz5.size; cw5, ch5 = int(W5 * 5 / 11), int(H5 * 7 / 8.5); gx5 = int(W5 * 0.25 / 11); x5 = (W5 - 2 * cw5 - gx5) // 2; y5 = (H5 - ch5) // 2
crd = hz5.crop((x5, y5, x5 + cw5, y5 + ch5))
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Click a line, type, print", "FREE ADOBE ACROBAT READER ON A COMPUTER  \u00b7  NO ACCOUNT")
cw_ = 760; ch_ = int(crd.height * cw_ / crd.width); cx_ = 260; cy_ = 300
crd2 = crd.resize((cw_, ch_), Image.LANCZOS); im.paste(crd2, (cx_, cy_))
s_ = cw_ / cw5
# the name field on this card: same box the PDF uses (inset 64 pt of a 360 pt card, from the top ~ 0.40 of the card)
fx0, fx1 = cx_ + int(cw_ * 64 / 360), cx_ + int(cw_ * 296 / 360)
fy0, fy1 = cy_ + int(ch_ * 0.422), cy_ + int(ch_ * 0.488)
ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
do.rectangle((fx0, fy0, fx1, fy1), fill=(204, 214, 255, 70), outline=(70, 100, 220, 255), width=4)
im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(im)
fl = _F.truetype("/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf", 50); fp = _F.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf", 28)
steps = [("1", "Open the PDF", "free Adobe Acrobat Reader, computer"), ("2", "Click a green line", "the blue box is the line you edit"),
         ("3", "Type your details", "86 type-in lines on 8 pages"), ("4", "Print and cut", "cardstock, Actual size, light marks")]
yy = 340
for n_, h_, t_ in steps:
    d.ellipse((1070, yy, 1150, yy + 80), fill=gs.rgb(pal["light"]) if "light" in pal else (247, 233, 230)); d.text((1110, yy + 40), n_, font=fl, fill=gs.rgb(pal["primary"]), anchor="mm")
    d.text((1175, yy - 2), h_, font=fl, fill=gs.rgb(pal["dark"]) if "dark" in pal else (90, 50, 50))
    for k_, ln in enumerate(gs.wrap(t_, None, 0, 0) if False else [t_]):
        d.text((1177, yy + 66), ln, font=fp, fill=(105, 96, 90))
    yy += 250
gs.save_jpeg(im, OUT + "/5-how.jpg")
print("ok")
