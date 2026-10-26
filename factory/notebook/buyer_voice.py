#!/usr/bin/env python3
"""Buyer Voice keeper (Grayson, Oct 26, 2026: "make them learn more ... know what to post").

Collects our real Etsy reviews from the gateway answers Bolt already gets (tag "reviews" in
gw/out/*.json), keeps them in notebook/reviews.jsonl (no duplicates), and rewrites the
"## Our reviews (auto)" block of notebook/buyer-voice.md.

    python3 factory/notebook/buyer_voice.py            # update, print what is new
    python3 factory/notebook/buyer_voice.py --check    # print counts only, write nothing

Real reviews only. The Etsy answer carries no buyer names; never add one by hand.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "gw", "out")
STORE = os.path.join(HERE, "reviews.jsonl")
VOICE = os.path.join(HERE, "buyer-voice.md")
RESULTS = os.path.join(HERE, "results.jsonl")
START, END = "<!-- reviews:start -->", "<!-- reviews:end -->"


def load_jsonl(path):
    rows = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return rows


def titles():
    """listing id -> short title, from what the crew already logged."""
    t = {}
    for r in load_jsonl(RESULTS):
        lid, what = str(r.get("id", "")), r.get("what", "")
        if lid.isdigit() and what and lid not in t:
            if ":" in what and what.lower().startswith(("baseline", "oct")):
                what = what.split(":", 1)[1]
            t[lid] = what.strip()[:60]
    return t


def gateway_reviews():
    found = []
    for path in glob.glob(os.path.join(OUT_DIR, "*.json")):
        try:
            with open(path) as f:
                d = json.load(f)
        except Exception:
            continue
        for res in d.get("results", []) if isinstance(d, dict) else []:
            if res.get("tag") != "reviews" or not res.get("ok"):
                continue
            for rv in (res.get("data") or {}).get("results", []) or []:
                if rv.get("create_timestamp") is None:
                    continue
                found.append({
                    "listing_id": str(rv.get("listing_id")),
                    "rating": rv.get("rating"),
                    "text": (rv.get("review") or "").strip()[:400],
                    "ts": rv.get("create_timestamp"),
                })
    return found


def render(rows, names):
    if not rows:
        return "- none yet"
    lines = []
    stars = [r["rating"] for r in rows if isinstance(r.get("rating"), (int, float))]
    avg = sum(stars) / len(stars) if stars else 0
    lines.append(f"- {len(rows)} review(s), average {avg:.1f} stars")
    import datetime
    for r in sorted(rows, key=lambda x: x["ts"], reverse=True)[:25]:
        day = datetime.datetime.fromtimestamp(r["ts"], datetime.timezone.utc).date().isoformat()
        name = names.get(r["listing_id"], "listing " + r["listing_id"])
        text = r["text"] or "(stars only, no words)"
        lines.append(f'- {day} · {r["rating"]}★ · {name} ({r["listing_id"]}): "{text}"')
    return "\n".join(lines)


def main():
    check = "--check" in sys.argv
    have = load_jsonl(STORE)
    keys = {(r["listing_id"], r["ts"]) for r in have}
    new = [r for r in gateway_reviews() if (r["listing_id"], r["ts"]) not in keys]
    # one copy of each new review even if several gateway files carry it
    seen, uniq = set(), []
    for r in new:
        k = (r["listing_id"], r["ts"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    rows = have + uniq
    print(f"reviews stored {len(have)}, new {len(uniq)}")
    for r in uniq:
        print(f'  NEW {r["rating"]}★ {r["listing_id"]}: {r["text"][:80]}')
    if check:
        return
    with open(STORE, "w") as f:
        for r in sorted(rows, key=lambda x: x["ts"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if os.path.exists(VOICE):
        with open(VOICE) as f:
            doc = f.read()
        if START in doc and END in doc:
            head, rest = doc.split(START, 1)
            _, tail = rest.split(END, 1)
            doc = head + START + "\n" + render(rows, titles()) + "\n" + END + tail
            with open(VOICE, "w") as f:
                f.write(doc)
        else:
            print("buyer-voice.md has no reviews markers; block not rewritten")


if __name__ == "__main__":
    main()
