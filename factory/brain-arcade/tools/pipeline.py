#!/usr/bin/env python3
"""One command per product: build -> answer key -> photos -> copy check -> QA sheet -> status.

  python3 tools/pipeline.py <slug> [--layout clipboard|fanned|christmas]

Saves a run its separate tool calls and context: everything a QA pass needs lands in
/tmp/ba/<slug>/ (PDF, build.json, qa-sheet.png to Read once) and products/<slug>/status.json.
The cover layout is picked automatically: never one of the lane's last 3 covers' layouts, and
"christmas" only Nov 1 - Dec 25. Exit 1 on any hard fail (answer key, copy rules, photo sizes).
Ruler still does the slop check and the six scores by eye on qa-sheet.png; this only removes the
mechanical work.
"""
import argparse, datetime as dt, glob, json, os, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import copy_check  # noqa: E402
import photos  # noqa: E402


def recent_layouts(skip):
    rows = []
    for f in glob.glob(os.path.join(ROOT, "products", "*", "listing.json")):
        L = json.load(open(f))
        if L.get("product_id") != skip and L.get("coverLayout"):
            rows.append((L.get("coverBuiltAt", ""), L["coverLayout"]))
    return [l for _, l in sorted(rows)[-3:]]


def pick_layout(slug, want=None):
    today = dt.date.today()
    christmas_ok = (today.month == 11) or (today.month == 12 and today.day <= 25)
    if want:
        return want
    used = recent_layouts("ba-" + slug)
    for l in photos.LAYOUTS:
        if l == "christmas" and not christmas_ok:
            continue
        if l not in used:
            return l
    return next(l for l in photos.LAYOUTS if l != (used[-1] if used else None) and (l != "christmas" or christmas_ok))


def qa_sheet(out_dir, photo_files, slug):
    """Cover next to the lane's last 3 covers + the 300 px thumbnail + the inside photos, one image."""
    others = [f for f in sorted(glob.glob(os.path.join(ROOT, "products", "*", "photos", "01-cover.jpg")),
                                key=os.path.getmtime) if f"/{slug}/" not in f][-3:]
    cover = Image.open(photo_files[0])
    tiles = [cover.resize((600, 450))] + [Image.open(f).resize((600, 450)) for f in others]
    sq = cover.crop((250, 0, 1750, 1500)).resize((300, 300))
    inside = [Image.open(f).resize((450, 360)) for f in photo_files[1:5]]
    W = max(600 * len(tiles), 450 * len(inside)) + 320
    sheet = Image.new("RGB", (W, 450 + 380), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * 600, 0))
    sheet.paste(sq, (600 * len(tiles) + 10, 0))
    for i, t in enumerate(inside):
        sheet.paste(t, (i * 455, 460))
    p = os.path.join(out_dir, "qa-sheet.png")
    sheet.save(p)
    return p, len(others)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--layout", choices=photos.LAYOUTS)
    a = ap.parse_args()
    pdir = os.path.join(ROOT, "products", a.slug)
    spec_p, list_p = os.path.join(pdir, "spec.json"), os.path.join(pdir, "listing.json")
    out = os.path.join("/tmp/ba", a.slug)
    os.makedirs(out, exist_ok=True)
    status = {"slug": a.slug, "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "fails": []}

    r = subprocess.run([sys.executable, os.path.join(HERE, "games.py"), spec_p, out], capture_output=True, text=True)
    print(r.stdout.strip())
    status["answerKey"] = "PASS" if r.returncode == 0 else "FAIL"
    if r.returncode:
        status["fails"].append("answer key: " + r.stdout.strip().splitlines()[-1])
    spec = json.load(open(spec_p))
    pdf = os.path.join(out, spec["id"] + ".pdf")

    if os.path.exists(pdf) and status["answerKey"] == "PASS":
        layout = pick_layout(a.slug, a.layout)
        for f in glob.glob(os.path.join(pdir, "photos", "*.jpg")):
            os.remove(f)
        files = photos.build(spec, pdf, os.path.join(pdir, "photos"), layout)
        bad = [f for f in files if os.path.getsize(f) > 400_000 or Image.open(f).width != 2000]
        if len(files) != 5 or bad:
            status["fails"].append(f"photos: need 5 at 2000 px under 400 KB, got {len(files)}, bad {bad}")
        status["coverLayout"] = layout
        status["photos"] = [os.path.relpath(f, pdir) for f in files]
        sheet, n = qa_sheet(out, files, a.slug)
        status["qaSheet"] = sheet
        status["comparedWith"] = n
        if os.path.exists(list_p):
            L = json.load(open(list_p))
            L["coverLayout"] = layout
            L["coverBuiltAt"] = status["at"]
            L["photos"] = status["photos"]
            json.dump(L, open(list_p, "w"), indent=1)

    if os.path.exists(list_p):
        cf = copy_check.check(json.load(open(list_p)))
        status["copy"] = "PASS" if not cf else "FAIL"
        status["fails"] += ["copy: " + x for x in cf]
    else:
        status["copy"] = "missing"
        status["fails"].append("copy: listing.json missing")

    g = subprocess.run([sys.executable, os.path.join(HERE, "shop_guard.py"), "check-dupe", list_p],
                       capture_output=True, text=True) if os.path.exists(list_p) else None
    status["dupe"] = "OK" if g and g.returncode == 0 else "BLOCKED"
    if g and g.returncode:
        status["fails"].append(g.stdout.strip())

    status["mechanical"] = "PASS" if not status["fails"] else "FAIL"
    json.dump(status, open(os.path.join(pdir, "status.json"), "w"), indent=1)
    print(json.dumps({k: status[k] for k in ("mechanical", "answerKey", "copy", "dupe", "coverLayout", "qaSheet", "fails") if k in status}, indent=1))
    print("NEXT: Read qa-sheet.png once, run the slop check and the six scores (stages/ba-night/references/rubric-ba.md).")
    sys.exit(0 if not status["fails"] else 1)


if __name__ == "__main__":
    main()
