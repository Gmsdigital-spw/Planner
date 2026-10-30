"""Build last5.json: products with etsy.state active OR stage published/live, newest 5 first.
python3 build_last5.py <dir of products/*.json from an ArtifactData out_dir read>  (fix round 2, Oct 30)"""
import json, glob, sys, os
rows = []
for f in glob.glob(os.path.join(sys.argv[1], "*.json")):
    j = json.load(open(f)); d = j.get("data", j); e = d.get("etsy") if isinstance(d.get("etsy"), dict) else {}
    if not (e.get("state") == "active" or d.get("stage") in ("published", "live")): continue
    t = next((v for v in (d.get("publishedAt"), e.get("publishedAt"), d.get("confirmedActiveAt"), e.get("confirmedActiveAt"),
                          d.get("seenActiveAt"), e.get("seenActiveAt")) if v), "")
    cl = d.get("coverLook") if isinstance(d.get("coverLook"), dict) else {}
    st = d.get("style") if isinstance(d.get("style"), dict) else {}
    rows.append({"id": j.get("id", os.path.basename(f)[:-5]), "publishedAt": t, "stage": d.get("stage"), "etsyState": e.get("state"),
                 "coverStyle": d.get("coverStyle"), "styleCoverStyle": st.get("coverStyle"), "scene": cl.get("scene"), "tool": cl.get("tool")})
rows.sort(key=lambda r: r["publishedAt"], reverse=True)
json.dump({"source": "products where etsy.state active OR stage in (published, live), newest 5 by publishedAt/confirmedActiveAt/seenActiveAt, read 2026-10-30 (fix round 2)",
           "covers": rows[:5]}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "last5.json"), "w"), indent=1)
print([(r["id"], r["publishedAt"][:10]) for r in rows[:5]])
