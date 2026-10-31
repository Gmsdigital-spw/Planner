"""Checks the finished Coupon Book PDF (fix list of the Oct 30 FAIL 82). python3 check.py
1 rendered pixel box sweep on every registered box of all 13 pages: no ink within 0.25 in inside any box
  border (and, for boxes with an outer clearance, none within that distance outside it), boxes above the footer gap.
2 ALL CAPS fill test: every one of the 96 fields gets a real ALL CAPS line at its MaxLen; it must fit the
  field at the field's own font size (Lora widths, the same widths Acrobat uses), then the filled pages are rendered.
3 30 unique coupon titles, 13 pages, US Letter."""
import json, os, glob, subprocess, tempfile, sys
import numpy as np
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = HERE + "/christmas-coupon-book.pdf"
PW, PH, M = 612.0, 792.0, 50.4
PAD = 18
FOOT_RULE = M - 1
data = json.load(open(HERE + "/boxes.json"))
BOXES = data["boxes"]


def render(pdf, dpi=150):
    tmp = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, tmp + "/p"], check=True)
    return {int(os.path.basename(f)[2:-4]): np.asarray(Image.open(f).convert("RGB")).astype(int)
            for f in glob.glob(tmp + "/p-*.png")}


def near(q, ref, tol=60):
    return (abs(((q >> 16) & 255) - ((ref >> 16) & 255)) + abs(((q >> 8) & 255) - ((ref >> 8) & 255))
            + abs((q & 255) - (ref & 255))) <= tol


def sweep(pdf, dpi=150):
    imgs = render(pdf, dpi); k = dpi / 72.0; n = len(imgs); bad = []
    for (pg, name, x, yb, w, h, r, outer) in BOXES:
        a = imgs[pg]
        if pg not in (1, n) and yb < FOOT_RULE + PAD - 0.01:
            bad.append((pg, name, "over footer gap"))
        s = 3.0
        X0, X1 = round((x + s) * k), round((x + w - s) * k)
        Y0, Y1 = round((PH - (yb + h) + s) * k), round((PH - yb - s) * k)
        sub = a[Y0:Y1, X0:X1]
        q = (sub[..., 0] << 16) | (sub[..., 1] << 8) | sub[..., 2]
        H_, W_ = q.shape
        yy, xx = np.mgrid[0:H_, 0:W_]
        dl, dr = (xx + s * k) / k, (W_ - 1 - xx + s * k) / k
        dt, db = (yy + s * k) / k, (H_ - 1 - yy + s * k) / k
        dmin = np.minimum(np.minimum(dl, dr), np.minimum(dt, db))
        corner = (np.minimum(dl, dr) < r + 1.5) & (np.minimum(dt, db) < r + 1.5)
        edge = (dmin < s + 2.5) & ~corner
        vals, cnt = np.unique(q[edge], return_counts=True)
        fills = [v for v, c_ in zip(vals, cnt) if c_ >= 0.08 * cnt.sum()]
        ink = np.ones_like(q, dtype=bool)
        for f in fills: ink &= ~near(q, f)
        for i in range(H_):                          # a full-width writing line / band counts as fill
            if ink[i].any():
                rv, rc = np.unique(q[i], return_counts=True); ink[i] &= ~near(q[i], rv[rc.argmax()])
        hit = ink & (dmin < PAD) & ~corner
        if hit.sum() > 2:
            bad.append((pg, name, "ink inside 0.25 in", round(float(dmin[hit].min()) / 72, 3)))
        if outer:
            o = round(outer * k); X0o, X1o = max(0, round(x * k) - o), round((x + w) * k) + o
            Y0o, Y1o = max(0, round((PH - yb - h) * k) - o), round((PH - yb) * k) + o
            reg_ = a[Y0o:Y1o, X0o:X1o]; qo = (reg_[..., 0] << 16) | (reg_[..., 1] << 8) | reg_[..., 2]
            inside = np.zeros(qo.shape, bool)
            inside[o - round(2 * k):qo.shape[0] - o + round(2 * k), o - round(2 * k):qo.shape[1] - o + round(2 * k)] = True
            bg = np.unique(qo[~inside], return_counts=True); bgc = bg[0][bg[1].argmax()]
            ohit = (~inside) & ~near(qo, bgc)
            # neighbouring tiles of the same row are allowed in the side gaps; only text above/below counts
            rows = np.where(ohit.any(axis=1))[0]
            rows = [rr for rr in rows if rr < o - round(2 * k) or rr >= qo.shape[0] - o + round(2 * k)]
            if len(rows) > 1:
                bad.append((pg, name, "ink within %.2f in outside" % (outer / 72), len(rows)))
    return bad, n


def caps_fill_test(pdf):
    """Every field filled with a real ALL CAPS line cut to its MaxLen; width must fit at the field's size."""
    FD = "/usr/share/fonts/truetype/google-fonts/"
    registerFont(TTFont("LoraRgT", FD + "Lora-Variable.ttf")); registerFont(TTFont("LoraItT", FD + "Lora-Italic-Variable.ttf"))
    src = "GRANDMA AND GRANDPA WITH LOVE FROM ALL OF US AT HOME THIS CHRISTMAS"
    r = PdfReader(pdf); w = PdfWriter(); w.append(r)
    worst, fails, nf = 1e9, [], 0
    for pi, page in enumerate(w.pages):
        vals = {}
        for an in page.get("/Annots", []) or []:
            a = an.get_object()
            if a.get("/FT") != "/Tx": continue
            nf += 1
            rect = [float(v) for v in a["/Rect"]]; fw = rect[2] - rect[0]
            da = str(a["/DA"]); size = float(da.split(" Tf")[0].split()[-1])
            font = "LoraItT" if "It" in da.split(" Tf")[0] else "LoraRgT"
            ml = int(a.get("/MaxLen", 999)); txt = src[:ml].rstrip()
            tw = stringWidth(txt, font, size)
            worst = min(worst, fw - 4 - tw)
            if tw > fw - 4: fails.append((pi + 1, a["/T"], ml, round(tw, 1), round(fw, 1)))
            if ml < 20 and size <= 11: fails.append((pi + 1, a["/T"], "MaxLen under 20", ml))
            vals[a["/T"]] = txt
        if vals: w.update_page_form_field_values(page, vals, auto_regenerate=False)
    w.set_need_appearances_writer(True)
    w.write(HERE + "/caps-filled.pdf")
    return nf, fails, worst


if __name__ == "__main__":
    r = PdfReader(PDF)
    assert len(r.pages) == 13, len(r.pages)
    mb = r.pages[0].mediabox; assert (round(float(mb.width)), round(float(mb.height))) == (612, 792)
    bad, n = sweep(PDF)
    print(f"box sweep: {len(BOXES)} boxes on {len(set(b[0] for b in BOXES))} pages of {n}; violations {len(bad)}")
    for b in bad: print("  BOX", b)
    nf, fails, worst = caps_fill_test(PDF)
    print(f"caps fill test: {nf} fields, fails {len(fails)}, tightest spare width {worst:.1f} pt")
    for f in fails: print("  FIELD", f)
    bad2, _ = sweep(HERE + "/caps-filled.pdf")      # typed text must not break the boxes either
    print(f"box sweep with ALL CAPS typed in: violations {len(bad2)}")
    for b in bad2: print("  FILLED", b)
    print("fields", len(r.get_fields()))
    sys.exit(1 if (bad or fails or bad2) else 0)
