"""Type-in fields for the Left Right build (fix round 1): body font (Poppins Regular, the kit's d.F), auto-size (0 Tf),
MaxLen 24. Uses tools/acro_font.py with the roman role pointed at Poppins.
python3 fields.py raw.pdf out.pdf [--fill "Name 1|Name 2|...|Name 6"]"""
import sys, re
sys.path.insert(0, "/home/claude/planner/tools")
import pikepdf
import acro_font as af

af.ROLES["roman"] = ("/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf", 400, "PoppinsRg")
MAXLEN = 24


def run(src, out, names=None):
    tmp = out + ".tmp.pdf"
    pdf = pikepdf.open(src)
    if names:
        for page in pdf.pages:
            for a in page.get("/Annots", []):
                if a.get("/FT") == "/Tx":
                    n = int(str(a.T)[4:]); a.V = pikepdf.String(names[n - 1])
    pdf.save(tmp); pdf.close()
    af.main(tmp, out + ".tmp2.pdf")
    pdf = pikepdf.open(out + ".tmp2.pdf")
    sizes = []
    for page in pdf.pages:
        for a in page.get("/Annots", []):
            if a.get("/FT") != "/Tx": continue
            da = str(a.DA)
            a.DA = pikepdf.String(re.sub(r"([\d.]+) Tf", "0 Tf", da))   # auto-size in Acrobat
            a.MaxLen = MAXLEN
            ap = a.AP.N.read_bytes().decode("latin-1")
            sizes.append(float(re.search(r"/PoppinsRg ([\d.]+) Tf", ap).group(1)))
    pdf.save(out)
    import os; os.remove(tmp); os.remove(out + ".tmp2.pdf")
    return sizes


if __name__ == "__main__":
    names = sys.argv[sys.argv.index("--fill") + 1].split("|") if "--fill" in sys.argv else None
    print("appearance sizes", run(sys.argv[1], sys.argv[2], names))
