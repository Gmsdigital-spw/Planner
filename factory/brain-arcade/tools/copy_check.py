#!/usr/bin/env python3
"""Listing copy rules, checked by code (copied from the main crew's Quill rules + this lane's own).

  python3 copy_check.py products/<slug>/listing.json   -> exit 0 PASS, 1 FAIL
  python3 copy_check.py --selftest
"""
import json, re, sys

AI_LINE = "This design was created with AI assistance under the creative direction of the seller."
SLOP = ["elevate", "unlock", "seamless", "game-changer", "game changer", "dive into", "look no further",
        "whether you're", "in today's busy world", "delve", "embark", "unleash", "transformative"]
NO_TAGS = {"digital download", "printable pdf", "instant download"}


def check(L):
    f = []
    t, tags, d = L.get("title", ""), L.get("tags", []), L.get("description", "")
    if not 20 <= len(t) <= 140:
        f.append(f"title is {len(t)} characters (20-140)")
    if not re.search(r"\b(grade|[2-5](st|nd|rd|th))\b", t, re.I):
        f.append("title does not name the grade")
    if len(tags) != 13:
        f.append(f"{len(tags)} tags (need 13)")
    if len({x.lower() for x in tags}) != len(tags):
        f.append("duplicate tags")
    for x in tags:
        if len(x) > 20:
            f.append(f"tag over 20 characters: {x}")
        if x.lower() in NO_TAGS:
            f.append(f"wasted tag: {x}")
    if len(d) < 300:
        f.append(f"description is {len(d)} characters (300+)")
    if not d.strip().endswith(AI_LINE):
        f.append("description must end with the exact AI line")
    if "single-classroom" not in d.lower() and "one classroom" not in d.lower():
        f.append("description is missing the single-classroom license line")
    if "nothing will be shipped" not in d.lower() and "nothing ships" not in d.lower():
        f.append("description must say it is a digital download and nothing ships")
    low = (t + " " + d).lower()
    for w in SLOP:
        if w in low:
            f.append(f"AI-sounding word: {w}")
    if re.search(r"(—.*){3,}", d):
        f.append("em-dash run")
    p = L.get("price")
    if not isinstance(p, (int, float)) or p <= 0 or round(p * 100) % 100 not in (99, 49):
        f.append(f"price {p} must be > 0 and end .99 or .49")
    return f


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        good = {"title": "Thanksgiving Math Escape Room 3rd Grade Printable", "tags": [f"tag {i}" for i in range(13)],
                "description": "x" * 300 + " Personal and single-classroom use only. Nothing will be shipped. " + AI_LINE, "price": 4.99}
        assert check(good) == [], check(good)
        assert check(dict(good, price=5.00)) and check(dict(good, tags=good["tags"][:12])) and check(dict(good, description="short"))
        assert check(dict(good, title="Math game to elevate your class grade 3"))
        print("selftest PASS"); sys.exit(0)
    fails = check(json.load(open(sys.argv[1])))
    if fails:
        print("COPY FAIL:"); [print(" -", x) for x in fails]; sys.exit(1)
    print("COPY PASS")
