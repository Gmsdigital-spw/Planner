"""Centre every field (/Q 1), merge AP fonts into /DR (fixdr), regenerate appearances, verify fields."""
import sys, pypdf
from pypdf.generic import NameObject, NumberObject, DictionaryObject, BooleanObject
src, out = sys.argv[1], sys.argv[2]
w = pypdf.PdfWriter(clone_from=pypdf.PdfReader(src))
fonts = DictionaryObject()
for p in w.pages:
    for a in p.get("/Annots", []) or []:
        a = a.get_object()
        a[NameObject("/Q")] = NumberObject(1)
        ap = a.get("/AP", {}).get("/N")
        if ap is not None:
            for k, v in (ap.get_object().get("/Resources", {}).get("/Font", {}) or {}).items(): fonts[NameObject(k)] = v
af = w._root_object["/AcroForm"]
dr = af.get("/DR", DictionaryObject()).get_object(); dr[NameObject("/Font")] = fonts; af[NameObject("/DR")] = dr
for p in w.pages:
    vals = {}
    for a in p.get("/Annots", []) or []:
        a = a.get_object(); vals[a["/T"]] = a.get("/V", "")
    if vals: w.update_page_form_field_values(p, vals, auto_regenerate=False)
af[NameObject("/NeedAppearances")] = BooleanObject(False)
w.write(out)
r = pypdf.PdfReader(out); f = r.get_fields()
print("pages", len(r.pages), "fields", len(f), "DR", sorted(fonts.keys()))
