import sys; sys.path.insert(0, "/home/claude/kit")
import gm_style as gs
from gm_style import ImageDraw
pal = gs.palette("evergreen")
pages = gs.render_pages("/home/claude/build/santa/santa-mail-bundle.pdf", "/home/claude/kit/pages/prod-santa-mail-bundle")
print(len(pages), pages[0].size)
O = "/home/claude/build/santa/photos/"; import os; os.makedirs(O, exist_ok=True)
sizes = {}
# 2: all six letters + certificate + tags, 4x2 filling the safe zone, caption row under
im = gs.paper(pal["paper"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "What's Inside", "6 different letters, the certificate and 12 gift tags")
w, gap = 350, 26; x0 = (gs.IW - (4 * w + 3 * gap)) // 2; ph = int(w * 1650 / 1275)
for k, i in enumerate([2, 3, 4, 5, 6, 7, 8, 12]):
    gs.place(im, pages[i], w, (x0 + (k % 4) * (w + gap), 285 + (k // 4) * (ph + 34)), shadow=0.22)
yb = 285 + 2 * ph + 34 + 40
for row, txt in enumerate(["Nice List  \u00b7  First Christmas  \u00b7  New Big Sibling", "Kindness  \u00b7  A Hard Year  \u00b7  A New Home"]):
    gs._text(d, (gs.IW / 2, yb + row * 62), txt, gs.font("sansM", 44), gs.rgb(pal["primary"]), anchor="ma")
gs._check_safe()
sizes["p2"] = gs.save_jpeg(im, O + "p2-inside.jpg")
# 3: close-up of letter 1, readable
im = gs.preview_closeup(pages[2], pal, "Type Right Into Every Letter", "Name, date, 3 good things and the P.S. are all type-in boxes", crop=(0.04, 0.10, 0.96, 0.80))
sizes["p3"] = gs.save_jpeg(im, O + "p3-closeup.jpg")
# 4: what's included
im = gs.preview_included(pages, pal, "13 Pages", ["6 letters from Santa", "Nice List certificate", "Santa's Nice List", "Dear Santa wish list", "4 envelope labels", "12 gift tags", "No Canva account needed"], pages[0])
sizes["p4"] = gs.save_jpeg(im, O + "p4-included.jpg")
# 5: the Christmas Eve extras: full certificate left, clean-cut label and tag pages right
im = gs.paper(pal["tint"]); d = ImageDraw.Draw(im)
gs._header(d, pal, "Everything for Christmas Eve", "Nice List certificate, envelope labels and gift tags")
w, gap = 700, 50; x0 = (gs.IW - (2 * w + gap)) // 2
gs.place(im, pages[8], w, (x0, 300), angle=-1.5, shadow=0.25)
y = 290
for i, cut in ((11, 0.534), (12, 0.534)):
    pg = pages[i]; cp = pg.crop((0, 0, pg.width, int(pg.height * cut)))
    gs.place(im, cp, w, (x0 + w + gap, y), shadow=0.25); y += int(cp.height * w / cp.width) + 40
gs._check_safe()
sizes["p5"] = gs.save_jpeg(im, O + "p5-extras.jpg")
print(sizes)
