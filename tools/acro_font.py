#!/usr/bin/env python3
"""Give a PDF's type-in fields the kit's real fonts (Lora), not the default Times.

Why (Oct 24, 2026 inspection of the Pink Bow invite): reportlab text fields can only use the
14 standard PDF fonts, so every editable invite looked like a Word document next to its Lora
headings (-2 file, -1 polish, -1 images). This tool embeds static Lora instances as TrueType
fonts in the AcroForm, points every field at them and draws a fresh, centred appearance, so the
sample text AND whatever the buyer types use Lora in Adobe Acrobat Reader.

Long entries: detail lines get auto size (DA size 0) so Acrobat shrinks a long address instead
of clipping it, and MaxLen is capped to what fits at 70% of the design size.

Usage: python3 tools/acro_font.py in.pdf out.pdf
  Times-Italic fields -> Lora Italic (semi-bold 500); Times-Roman fields -> Lora Regular.
  Fields whose design size is 18 pt or more keep their size (names, headlines); smaller ones
  (detail lines) become auto size.
"""
import io, sys, re
import pikepdf
from pikepdf import Name, Dictionary, Array, Stream
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FD = "/usr/share/fonts/truetype/google-fonts/"
ROLES = {"italic": (FD + "Lora-Italic-Variable.ttf", 500, "LoraIt"),
         "roman": (FD + "Lora-Variable.ttf", 450, "LoraRg")}


def static_font(path, wght):
    f = TTFont(path)
    if "fvar" in f:
        f = instancer.instantiateVariableFont(f, {"wght": wght})
    buf = io.BytesIO(); f.save(buf)
    data = buf.getvalue()
    f = TTFont(io.BytesIO(data))
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap(); hmtx = f["hmtx"]
    widths = []
    for code in range(32, 256):
        try:
            ch = bytes([code]).decode("cp1252")
        except UnicodeDecodeError:
            widths.append(0); continue
        g = cmap.get(ord(ch))
        widths.append(round(hmtx[g][0] * 1000 / upm) if g else 0)
    hh = f["hhea"]; os2 = f["OS/2"]; head = f["head"]
    desc = dict(asc=round(hh.ascent * 1000 / upm), dsc=round(hh.descent * 1000 / upm),
                cap=round(getattr(os2, "sCapHeight", hh.ascent * .7) * 1000 / upm),
                bbox=[round(v * 1000 / upm) for v in (head.xMin, head.yMin, head.xMax, head.yMax)])
    return data, widths, desc


def make_font(pdf, role):
    path, wght, base = ROLES[role]
    data, widths, d = static_font(path, wght)
    ff = Stream(pdf, data); ff.Length1 = len(data)
    fd = pdf.make_indirect(Dictionary(Type=Name.FontDescriptor, FontName=Name("/" + base), Flags=32 | (64 if role == "italic" else 0),
                                      FontBBox=Array(d["bbox"]), ItalicAngle=-12 if role == "italic" else 0, Ascent=d["asc"],
                                      Descent=d["dsc"], CapHeight=d["cap"], StemV=80, FontFile2=pdf.make_indirect(ff)))
    font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.TrueType, BaseFont=Name("/" + base), FirstChar=32,
                                        LastChar=255, Widths=Array(widths), Encoding=Name.WinAnsiEncoding, FontDescriptor=fd))
    return font, widths, d


def text_width(s, widths, size):
    w = 0
    for ch in s:
        try:
            code = ch.encode("cp1252")[0]
        except Exception:
            code = 63
        w += widths[code - 32] if 32 <= code <= 255 else 500
    return w * size / 1000


def esc(s):
    b = s.encode("cp1252", "replace")
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def main(src, out):
    pdf = pikepdf.open(src)
    fonts = {r: make_font(pdf, r) for r in ROLES}
    af = pdf.Root.AcroForm
    dr = af.get("/DR", Dictionary()); fdict = dr.get("/Font", Dictionary())
    for r, (font, _, _) in fonts.items():
        fdict[Name("/" + ROLES[r][2])] = font
    dr.Font = fdict; af.DR = dr
    n = 0
    for page in pdf.pages:
        for a in page.get("/Annots", []):
            if a.get("/FT") != "/Tx":
                continue
            da = str(a.get("/DA", ""))
            m = re.search(r"/(\S+)\s+([\d.]+)\s+Tf", da)
            if not m:
                continue
            old, size = m.group(1), float(m.group(2))
            role = "italic" if "It" in old or "Ital" in old else "roman"
            font, widths, d = fonts[role]; fname = ROLES[role][2]
            color = re.search(r"([\d.]+\s+[\d.]+\s+[\d.]+\s+rg)", da)
            color = color.group(1) if color else "0 0 0 rg"
            rect = [float(v) for v in a.Rect]; w, h = rect[2] - rect[0], rect[3] - rect[1]
            val = str(a.get("/V", ""))
            auto = size < 18
            a.DA = pikepdf.String(f"/{fname} {0 if auto else size:g} Tf {color}")
            a.Q = 1
            # cap length: what fits at 70% of the design size
            per = text_width("N", widths, size * 0.7) or 5
            a.MaxLen = max(12, min(int(a.get("/MaxLen", 60)), int((w - 4) / per * 1.15)))
            s = size
            while s > 5 and text_width(val, widths, s) > w - 4:
                s -= 0.25
            tw = text_width(val, widths, s)
            x = (w - tw) / 2; y = (h - s * (d["asc"] - d["dsc"]) / 1000) / 2 - s * d["dsc"] / 1000
            body = b"/Tx BMC q BT /" + fname.encode() + f" {s:.2f} Tf {color} {x:.2f} {y:.2f} Td (".encode() + esc(val) + b") Tj ET Q EMC"
            ap = Stream(pdf, body)
            ap.Type = Name.XObject; ap.Subtype = Name.Form; ap.BBox = Array([0, 0, w, h])
            ap.Resources = Dictionary(Font=Dictionary({"/" + fname: font}))
            a.AP = Dictionary(N=pdf.make_indirect(ap))
            n += 1
    af.NeedAppearances = False
    pdf.save(out)
    print("refonted", n, "fields ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
