#!/usr/bin/env python3
"""Daily listing scoreboard: what is selling, what is getting looked at, what is dead.

Grayson, Oct 24, 2026: "I want them to full on learn everything." Every crew reads
factory/notebook/scoreboard.md before working (CLAUDE.md "Notebook rule"), so buyer numbers,
not our own inspection scores, steer what gets built, re-priced, re-covered and promoted.

Usage (the Mechanic's 6:47 AM run):
  ArtifactData list stats  (limit 60, out_dir D)   -> D/stats/<day>.json
  ArtifactData list sales  (limit 500, out_dir D)  -> D/sales/<id>.json
  python3 factory/notebook/scoreboard.py D > factory/notebook/scoreboard.md

Real numbers only: a listing missing from a snapshot is "no data", never 0.
"""
import json, os, sys, glob, re
from collections import defaultdict

LANES = [("wall art", r"verse|wall art|prints? set"), ("invitations", r"invitation|invite"),
         ("money", r"budget|debt|savings|no.buy|money|spending"),
         ("party games", r"game|bingo|trivia|scavenger|escape|awards"),
         ("christmas", r"christmas|xmas|santa|gingerbread|advent|cookie|elf|holiday"),
         ("thanksgiving", r"thanksgiving|friendsgiving"), ("planners", r"planner|workbook|tracker|goal|calendar"),
         ("new year", r"new year|nye|2027")]


def lane(title):
    t = title.lower()
    for name, rx in LANES:
        if re.search(rx, t):
            return name
    return "other"


def load(d):
    snaps = {}
    for f in sorted(glob.glob(os.path.join(d, "stats", "*.json"))):
        j = json.load(open(f)); j = j.get("data", j)
        if j.get("listings"):
            snaps[j.get("day") or os.path.basename(f)[:-5]] = j
    sales = []
    for f in glob.glob(os.path.join(d, "sales", "*.json")):
        j = json.load(open(f)); j = j.get("data", j)
        if j.get("verified", True) and not j.get("test"):
            sales.append(j)
    return snaps, sales


def main(d):
    snaps, sales = load(d)
    if not snaps:
        print("# Scoreboard\n\nNo stats snapshots found: nothing to learn from yet (unverified).")
        return
    days = sorted(snaps)
    today = days[-1]; cur = snaps[today]["listings"]
    def at(day_back, lid, key):
        if len(days) <= day_back:
            return None
        return snaps[days[-1 - day_back]]["listings"].get(lid, {}).get(key)
    first_seen = {}
    for day in days:
        for lid in snaps[day]["listings"]:
            first_seen.setdefault(lid, day)
    sold = defaultdict(lambda: [0, 0.0])
    for s in sales:
        sold[str(s.get("listingId"))][0] += int(s.get("items", 1) or 1)
        sold[str(s.get("listingId"))][1] += float(s.get("gross", 0) or 0)
    rows = []
    for lid, v in cur.items():
        views = v.get("views"); favs = v.get("favs")
        def gain(n):
            old = at(n, lid, "views")
            return None if old is None or views is None else views - old
        rows.append(dict(id=lid, title=v.get("title", "")[:58], lane=lane(v.get("title", "")),
                         price=v.get("price"), views=views, favs=favs, g1=gain(1), g3=gain(3),
                         g7=gain(min(7, len(days) - 1)) if len(days) > 1 else None,
                         age=len([x for x in days if x >= first_seen[lid]]),
                         sales=sold[lid][0], gross=round(sold[lid][1], 2)))
    rows.sort(key=lambda r: (r["sales"], r["g7"] or 0, r["views"] or 0), reverse=True)
    shop = snaps[today].get("shop", {})
    span = min(7, len(days) - 1)
    out = [f"# Scoreboard {today} (buyer numbers, from {len(days)} daily snapshots)", "",
           "Every crew reads this before working. It is the only proof of what buyers want; our own",
           "inspection scores are not. Written by factory/notebook/scoreboard.py, never by hand.", "",
           f"Shop: {shop.get('active', '?')} live, {sum(r['sales'] for r in rows)} sales "
           f"(${sum(r['gross'] for r in rows):.2f}), {shop.get('favorers', '?')} shop favorites, "
           f"{shop.get('reviews', '?')} reviews, {sum(r['views'] or 0 for r in rows)} listing views.", ""]
    winners = [r for r in rows if r["sales"] or (r["g7"] or 0) >= 5 or (r["favs"] or 0)]
    out.append(f"## Winners (sold, or {span}-day views 5+, or favorited): copy what they do")
    out += [f"- {r['title']} [{r['lane']}] ${r['price']}: {r['sales']} sold, {r['views']} views "
            f"(+{r['g7']} in {span} d), {r['favs']} favs" for r in winners[:8]] or ["- none yet"]
    dead = [r for r in rows if not r["sales"] and (r["g7"] or 0) == 0 and r["age"] >= 4]
    out += ["", f"## Dead (live 4+ days, 0 views gained in {span} d, 0 sales): fix cover/title/tags or stop making this kind"]
    out += [f"- {r['title']} [{r['lane']}] ${r['price']}: {r['views']} views total" for r in dead] or ["- none"]
    by = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        b = by[r["lane"]]; b[0] += 1; b[1] += r["views"] or 0; b[2] += r["g7"] or 0; b[3] += r["sales"]
    out += ["", "## By lane (where buyers look): build more of the top lane, less of the bottom",
            "| Lane | Listings | Views | Views/listing | Views gained | Sales |", "|---|---|---|---|---|---|"]
    for name, b in sorted(by.items(), key=lambda kv: (kv[1][3], kv[1][2] / kv[1][0]), reverse=True):
        out.append(f"| {name} | {b[0]} | {b[1]} | {b[1] / b[0]:.1f} | {b[2]} | {b[3]} |")
    out += ["", "## Every listing", "| Listing | Lane | Price | Views | +1d | +3d | +7d | Favs | Sold |",
            "|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "-" if x is None else x
    for r in rows:
        out.append(f"| {r['title']} | {r['lane']} | {r['price']} | {f(r['views'])} | {f(r['g1'])} | "
                   f"{f(r['g3'])} | {f(r['g7'])} | {f(r['favs'])} | {r['sales']} |")
    out += ["", "## How crews use this",
            "- Night Shift 01/02: ideas from the top lane first; never a new product in a lane whose every listing is Dead.",
            "- Night Shift 06 Lens + Check-up: a Dead listing gets a new cover/title before any new build in its lane.",
            "- Ledger (pricing): sales and favorites here beat guesses.",
            "- Herald, Pixel, Bolt pins: promote Winners first, then the newest listing; never spend a post on a Dead listing twice in a row.",
            "- A pattern that holds 2 days in a row goes to factory/LESSONS.md and the lane's notebook \"What works\" with these numbers."]
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
