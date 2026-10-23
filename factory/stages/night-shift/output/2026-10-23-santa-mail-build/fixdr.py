"""Post-build fix: reportlab writes /DR with repeated /Font keys (only the last survives in readers),
so a viewer can't find Times/Times-Italic when the buyer types. Merge every widget's AP fonts into one /DR."""
import sys, pypdf
from pypdf.generic import NameObject, DictionaryObject
src, out = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src); w = pypdf.PdfWriter(clone_from=r)
fonts = DictionaryObject()
for p in w.pages:
    for a in p.get("/Annots", []) or []:
        a = a.get_object()
        ap = a.get("/AP", {}).get("/N")
        if ap is None: continue
        ap = ap.get_object()
        for k, v in (ap.get("/Resources", {}).get("/Font", {}) or {}).items(): fonts[NameObject(k)] = v
af = w._root_object["/AcroForm"]
dr = af.get("/DR", DictionaryObject()).get_object()
dr[NameObject("/Font")] = fonts
af[NameObject("/DR")] = dr
w.write(out)
print("DR fonts:", sorted(fonts.keys()))
