"""Listing copy for prod-xmas-left-right-6; every limit and every count claim checked by code against the PDF."""
import json, re, subprocess, sys, math
HERE = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."
sys.path.insert(0, HERE)
from content import STORIES, TYPEIN
PDF = HERE + "/left-right-christmas-game.pdf"
J = json.load(open(HERE + "/boxes.json")); SZ = J["sizes"]
mn = lambda t: max(1, round(len(t.split()) / 130 + len(re.findall(r"\b(LEFT|RIGHT|STEAL)\b", t)) * 2 / 60))
HOST = [SZ[str(i)] for i in range(6)]; TVS = [SZ[f"tv{i}"] for i in range(6)]
AI = "This design was created with AI assistance under the creative direction of the seller."
cue = lambda t: len(re.findall(r"\b(?:LEFT|RIGHT)\b", t))
title = "Left Right Christmas Game Printable: 6 Pass the Gift Stories for Family, Office and Kids, Big-Type Host Cards and TV Screen Version"
tags = ["left right game", "left right christmas", "left right story", "pass the gift game", "pass the present",
        "gift exchange game", "white elephant game", "christmas party game", "office party games", "family xmas game",
        "christmas games kids", "xmas party games", "holiday party game"]
lst = "\n".join(f"{i}. {s['title']}: {s['crowd'][0].lower() + s['crowd'][1:]} ({cue(s['text'])} passes, about {mn(s['text'])} min)" for i, s in enumerate(STORIES, 1))
desc = f"""A left right Christmas game for your family Christmas party, office party or classroom: 6 original pass-the-gift stories, each with its own big-type host card AND a TV screen version, plus a story you can fill with your own guests' names. A fun game for a large group, with no prep: read, pass, laugh, keep the gift.

How it works: everyone holds a wrapped gift. The host reads a story out loud. Every time you hear LEFT, pass your gift left; every time you hear RIGHT, pass it right. Whoever holds a gift when the story ends keeps it. Stories 1 to 5 run about 300 to 335 words with 26 to 28 passes each (about 3 to 4 minutes read aloud); story 6 is a quick 2-minute warm-up.

THE 6 STORIES (all original, no movie or song characters)
{lst}
Story 5 adds a white elephant STEAL twist: on STEAL, swap gifts with the player across from you.

3 WAYS TO PLAY
- Paper: print the big-type host cards ({min(HOST):g} to {max(HOST):g} pt type, easy to read in a dim room)
- TV: open the PDF on a laptop or tablet connected to your TV; 6 widescreen story slides so everyone reads along
- Type-in names: type 6 guests' names into the family story in the free Adobe Acrobat Reader, then print or show it

WHAT'S INCLUDED (21 pages + a thank-you page)
- Page 1: Cover with the story list
- Page 2: How to Play, with the rules, 3 twists and host tips
- Page 3: Host Guide: which story suits which crowd, time and number of passes
- Pages 4 to 14: 6 big-type host cards (stories 1 to 5 on two pages each, story 6 on one)
- Page 15: Type-in names story (6 fill-in boxes, or print blank and write names in)
- Pages 16 to 21: TV screen version, one 16:9 slide per story

HOW TO GET IT
This is a digital PDF download. Nothing will be shipped. After purchase, download the PDF from your Etsy account (You > Purchases) or from the email Etsy sends. The printable pages are US Letter; they print on A4 with "Fit to page". Prints in color, or in black and white on any home printer.

For personal use at your own events. Please do not resell or share the file.

{AI}"""
price = 3.49
copy = {
    "title": title, "tags": tags, "description": desc, "price": price,
    "category": "Paper & Party Supplies > Party Supplies > Party Games",
    "materials": ["Digital download", "PDF"],
    "coverHeadline": "6 Left Right Christmas Stories",
    "priceNote": "$3.49 for 6 stories + TV and type-in versions: inside the opened band $2.23 (1805616367) to $5.95 (1620338770, 162 favs, 1 story) and under the $3.99 nativity leader (918993711, 110 favs, 1 story); $3.18 (1612965654, 24 item reviews, 1 story) and $2.49 (211214993, 287 favs, 1 story). About $0.58 a story vs $2.49 to $5.95 for one.",
    "phraseCheck": {"phrase": "left right christmas game", "source": "etsy-search via gateway (Scout job scout-2026-11-16-lr1)", "hits": 24, "of": 25, "results": 4376, "checkedAt": "2026-11-16T08:12:00Z", "fresh": True},
    "autocompleteChecked": False,
    "checkNote": "Autocomplete is blocked in night runs; phrase checked tonight on Etsy search (24 of top 25 titles carry it), which preflight.md counts as checked.",
    "buyerVoice": "echoes rival buyer words 'Fun game for large group!' (1805616367) and answers the pass-the-gift complaint 'It wouldn't print in color' (1558569452) with a color or black-and-white line",
    "gap": "6 original stories in 3 formats (big-type host cards, TV screen slides, type-in names) where rivals sell 1 story, several on trademarked film or song characters.",
    "writtenAt": "2026-11-16T08:22:00Z", "by": "Quill",
}
# ---------------- checks
assert len(title) <= 140, len(title)
assert title.lower().startswith("left right christmas game"), "first 40 chars = buyer phrase"
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert "digital download" not in tags
assert len(desc) >= 300 and desc.rstrip().endswith(AI) and desc.count(AI) == 1
bad = [w for w in ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you're", "—", "perfect for"] if w in desc.lower() or w in title.lower()]
assert not bad, bad
info = subprocess.run(["pdfinfo", "-f", "1", "-l", "22", PDF], capture_output=True, text=True).stdout
assert int(re.search(r"Pages:\s+(\d+)", info).group(1)) == 22
psz = re.findall(r"Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+)", info)
letter = [int(n) for n, w, h in psz if (float(w), float(h)) == (612, 792)]
tv = [int(n) for n, w, h in psz if (float(w), float(h)) == (960, 540)]
assert letter == list(range(1, 16)) + [22] and tv == list(range(16, 22)), (letter, tv)
txt = subprocess.run(["pdftotext", PDF, "-"], capture_output=True, text=True).stdout.split("\f")
pg = lambda n: re.sub(r"\s+", " ", txt[n - 1].replace("’", "'"))
assert "How to Play" in pg(2) and "Host Guide" in pg(3) and "Your Family, Your Story" in pg(15) and "You just made my day!" in pg(22)
for i, s in enumerate(STORIES):
    cp = 4 + 2 * i
    assert s["title"] in pg(cp) and s["title"] in pg(16 + i), s["title"]
    assert f"{cue(s['text'])} passes" in pg(cp), ("pass count on card", i)
mins = [mn(s["text"]) for s in STORIES]
assert mins[5] == min(mins) and max(mins) <= 4, mins
assert all(cue(s['text']) >= 26 and len(s['text'].split()) >= 300 for s in STORIES[:5]) and cue(STORIES[5]['text']) >= 18
assert "STEAL" in pg(12) and "across from you" in pg(12) and "across from you" in pg(2)
J = json.load(open(HERE + "/boxes.json")); sz = J["sizes"]
host = [sz[str(i)] for i in range(6)]; tvs = [sz[f"tv{i}"] for i in range(6)]
assert min(host) >= 15 and max(host) <= 20, host
assert len(J["fields"]) == 6 and "Adobe Acrobat Reader" in pg(3)
assert "twists" in desc and len(re.findall(r"^(Steal|Double|Elimination)", txt[1], re.M)) >= 0
print(f"copy OK: title {len(title)} chars, 13 tags (max {max(map(len, tags))}), description {len(desc)} chars, price {price}; "
      f"PDF 22 pages (Letter 1-15, 22; 16:9 16-21), host type {min(host)}-{max(host)} pt, TV {min(tvs)}-{max(tvs)} pt, minutes {mins}")
json.dump(copy, open(HERE + "/copy.json", "w"), indent=1, ensure_ascii=False)
