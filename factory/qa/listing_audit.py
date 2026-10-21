#!/usr/bin/env python3
"""Warden's listing photo inspector (built Oct 21, 2026 after Grayson found what the crew missed:
two covers in a row on 18 listings, a duplicate photo, and bland beige covers).

It does two passes:
  1. DATA pass on the Etsy listings JSON (gateway etsy GET .../listings?state=active&includes=Images).
  2. PICTURE pass on the downloaded photos (gateway fetch_images, small 570xN size is enough).
It writes a JSON report and a contact sheet (one row per listing, photos in order) that the
Warden MUST open and look at with its own eyes. The script catches the mechanical problems;
your eyes catch "this cover has nothing to do with this product".

Usage:
  python3 factory/qa/listing_audit.py <listings.json> [<photos dir>] [--out <dir>]
    listings.json : the gateway result file (gw/out/<id>.json) or the raw Etsy {"results":[...]}
    photos dir    : folder of <listing_id>-r<rank>-<image_id>.jpg files (from fetch_images)
Make the fetch_images items with:  name = f"{listing_id}-r{rank:02d}-{listing_image_id}.jpg", url = url_570xN

Exit code 0 always; read report["problems"]. Each problem: {listing_id, title, code, detail, fix}.
Codes (add new ones at the bottom of RULES when Grayson finds something this missed; see factory/qa/MISSES.md):
"""
import colorsys, glob, json, os, re, sys

RULES = {
    "TWO_COVERS":     "More than one cover-size (2000x1500) image in the listing (a new cover was added without deleting the old one).",
    "DUP_PHOTO":      "The same picture appears twice in one listing.",
    "BLAND_COVER":    "Cover is beige/grey with weak color. Covers must be bold and on-theme (tools/fun_covers.py).",
    "DARK_COVER":     "Cover is too dark to read as a thumbnail.",
    "NO_THEME_ART":   "Cover has no themed art (cookies on cookie swap, Santa on Secret Santa...). Checked by eye: see contact sheet.",
    "COVER_MISMATCH": "Cover words don't match the listing (wrong product's cover).",
    "MISSING_ALT":    "Cover has no alt text.",
    "FEW_PHOTOS":     "Fewer than 5 photos. Top sellers use 7-10.",
    "COVER_NOT_FIRST":"The cover-style image is not photo #1.",
}

STOP = set("the a an and or of for with to in on your my 2026 2027 pdf digital download printable kit set planner tracker games game party".split())

def words(s):
    return {w for w in re.findall(r"[a-z]+", (s or "").lower()) if w not in STOP and len(w) > 2}

def load_listings(p):
    d = json.load(open(p))
    if "results" in d and d["results"] and isinstance(d["results"][0], dict) and "data" in d["results"][0]:
        for r in d["results"]:
            if isinstance(r.get("data"), dict) and "results" in r["data"]:
                return r["data"]["results"]
    return d if isinstance(d, list) else d.get("results", d)

def is_cover_shape(im):
    # Every cover our crew renders is exactly 2000x1500 (tools/fun_covers.py, cover_styles.py, warm_covers.py
    # downscaled). Detail photos are 2000x1600, 1000x1500 pins, or the old listings' own sizes.
    return (im.get("full_width"), im.get("full_height")) == (2000, 1500)

def pic_stats(path):
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((64, 48))
    px = list(im.get_flattened_data()) if hasattr(im, "get_flattened_data") else list(im.getdata())
    sats, vals = [], []
    for r, g, b in px:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        sats.append(s); vals.append(v)
    # share of strongly colored pixels = "is this a bold cover or beige?"
    bold = sum(1 for s, v in zip(sats, vals) if s > 0.45 and v > 0.35) / len(px)
    from PIL import Image as _I
    g = _I.open(path).convert("L").resize((33, 32))
    gp = list(g.get_flattened_data()) if hasattr(g, "get_flattened_data") else list(g.getdata())
    dhash = "".join("1" if gp[y * 33 + x] > gp[y * 33 + x + 1] else "0" for y in range(32) for x in range(32))
    return {"bold": round(bold, 3), "bright": round(sum(vals) / len(vals), 3), "hash": dhash}

def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))

def audit(listings, photos=None):
    problems, rows = [], []
    files = {}
    if photos:
        for f in glob.glob(os.path.join(photos, "*.jpg")):
            m = re.match(r"(\d+)-r(\d+)-(\d+)\.jpg", os.path.basename(f))
            if m:
                files[int(m.group(3))] = f
    for l in listings:
        lid, title = l["listing_id"], l["title"]
        ims = sorted(l.get("images") or [], key=lambda i: i["rank"])
        def add(code, detail, fix):
            problems.append({"listing_id": lid, "title": title[:60], "code": code, "detail": detail, "fix": fix})
        if len(ims) < 5:
            add("FEW_PHOTOS", f"{len(ims)} photos", "add product page photos (what's inside, close-ups, how it works)")
        if not ims:
            continue
        covers = [i for i in ims if is_cover_shape(i)]
        if len(covers) > 1:
            add("TWO_COVERS", f"cover-style photos at ranks {[c['rank'] for c in covers]} ids {[c['listing_image_id'] for c in covers]}",
                "keep the NEWEST cover at #1, DELETE the older cover image(s)")
        if covers and ims[0] is not covers[0]:
            add("COVER_NOT_FIRST", f"cover at rank {covers[0]['rank']}", "re-upload the cover with rank 1, then delete the old copy")
        if not (ims[0].get("alt_text") or "").strip():
            add("MISSING_ALT", "photo #1", "re-upload the cover with alt text (title + count + 3 benefits)")
        aw, tw = words(ims[0].get("alt_text")), words(title)
        if aw and tw and not (aw & tw):
            add("COVER_MISMATCH", f"cover alt '{(ims[0].get('alt_text') or '')[:60]}' shares no words with the title",
                "look at the cover; if it's another product's, rebuild this listing's cover")
        stats = {}
        for i in ims:
            f = files.get(i["listing_image_id"])
            if f:
                stats[i["listing_image_id"]] = pic_stats(f)
        c = stats.get(ims[0]["listing_image_id"])
        if c:
            if c["bright"] < 0.35:
                add("DARK_COVER", f"brightness {c['bright']}", "rebuild with tools/fun_covers.py")
            elif c["bold"] < 0.30:
                add("BLAND_COVER", f"only {int(c['bold']*100)}% bold color (needs 30%+)", "rebuild with tools/fun_covers.py (bold theme color + themed 3D art)")
        ids = [i["listing_image_id"] for i in ims if i["listing_image_id"] in stats]
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                if hamming(stats[ids[a]]["hash"], stats[ids[b]]["hash"]) <= 40:  # of 1024 bits: near-identical pictures only
                    add("DUP_PHOTO", f"images {ids[a]} and {ids[b]} look identical", f"delete {ids[b]}")
        rows.append((lid, title, [files.get(i["listing_image_id"]) for i in ims]))
    return problems, rows

def contact_sheet(rows, out):
    from PIL import Image, ImageDraw
    TW, TH, LBL = 200, 150, 240
    s = Image.new("RGB", (LBL + 10 * TW, max(1, len(rows)) * (TH + 6)), "white")
    d = ImageDraw.Draw(s)
    for r, (lid, title, fs) in enumerate(rows):
        y = r * (TH + 6)
        d.text((4, y + 60), f"{lid}\n{title[:34]}", fill="black")
        for c, f in enumerate(fs[:10]):
            if f:
                im = Image.open(f).convert("RGB"); im.thumbnail((TW - 6, TH)); s.paste(im, (LBL + c * TW, y))
    s.save(out, quality=80)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/listing_audit"
    if "--out" in sys.argv:
        args = [a for a in args if a != out]
    os.makedirs(out, exist_ok=True)
    listings = load_listings(args[0])
    problems, rows = audit(listings, args[1] if len(args) > 1 else None)
    rep = {"listings": len(listings), "problems": problems, "rules": RULES}
    json.dump(rep, open(os.path.join(out, "report.json"), "w"), indent=1)
    if len(args) > 1:
        contact_sheet(rows, os.path.join(out, "contact_sheet.jpg"))
    print(f"{len(listings)} listings, {len(problems)} problems -> {out}/report.json" + (f" + {out}/contact_sheet.jpg (LOOK AT IT)" if len(args) > 1 else ""))
    for p in problems:
        print(f"- {p['code']}: {p['listing_id']} {p['title'][:40]} | {p['detail']}")
