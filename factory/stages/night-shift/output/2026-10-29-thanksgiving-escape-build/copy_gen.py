import json, re
title = "Thanksgiving Escape Room for Kids and Families, Printable Game with Two Levels (Ages 6-9 and 10+), No Phone Needed, Fall Party Activity"
tags = ["thanksgiving escape", "escape room for kids", "kids escape room", "family escape room", "escape room game", "escape room kit",
        "turkey escape room", "thanksgiving games", "thanksgiving puzzles", "kids thanksgiving", "fall party games", "family game night", "screen free activity"]
desc = """A printable Thanksgiving escape room for kids and families, with two levels in one story: Level 1 for ages 6-9 and Level 2 for ages 10+. Family fun for the hour before dinner, with no phone, app, QR code or internet needed.

THE STORY
Grandma Hazel baked four pies and locked them in the old Pie Safe so the dog could not reach them, then mixed up the 4-digit code. Players solve 4 clues, each clue gives one digit, and the 4 digits open the Pie Safe before the 45-minute timer runs out.

CLUES THAT CONNECT
One clue leads to the next in a single chain, and the game master checks every digit on the answer key, so nobody gets lost halfway.

TWO LEVELS, SAME DIGIT
Every clue comes in two versions that lead to the same digit, so a 7-year-old and a 12-year-old can play side by side and check each other.
- Clue 1: number code (Level 1) / shift cipher (Level 2)
- Clue 2: count the pantry shelf (Level 1) / picture math (Level 2)
- Clue 3: tangled pumpkin vines (Level 1) / acorn maze (Level 2)
- Clue 4: 4x4 number sudoku (Level 1) / kids' table logic grid (Level 2)

WHAT'S INCLUDED (16 pages plus a thank-you page, one PDF)
- Cover
- Game master guide: 10-minute set-up, how to run it, supplies
- Mission letter to read aloud, team sheet and code tracker
- 8 clue sheets (4 clues x 2 levels)
- Pie Safe lock sheet (the final code)
- 6 envelope lock tags to cut out
- 8 hint cards, each with 2 fold-over hints
- Answer key with full solutions (game master only)
- Escape Expert certificates (2 per page)

GOOD TO KNOW
- Players: 1 to 12, in teams of 2 to 4. Play time about 45 minutes.
- Ink-light pages: white paper, thin lines, and every puzzle works in black and white.
- Supplies: pencils, scissors, tape, 5 envelopes per team (or folded paper) and a timer.
- US Letter size; prints on A4 with "Fit to page".
- Good for Thanksgiving Day, fall break, family gatherings and classrooms.

HOW IT WORKS
This is a digital PDF download. Nothing is shipped. After purchase, download the file from your Etsy account (Purchases) or from the email Etsy sends you, then print at home or at a print shop. For personal and classroom use.

This design was created with AI assistance under the creative direction of the seller."""
copy = {"title": title, "tags": tags, "description": desc, "price": 6.99,
        "priceNote": "$6.99, top of the $2.99-$6.99 single-kit range (SALES PUSH Oct 28): under the opened leaders 1102701627 $13.99 (254 reviews, one level) and 1306468602 $12.99, above the market page's $4.90-$4.95 one-level kits; two levels in one file.",
        "category": "Paper & Party Supplies > Party Supplies > Party Games",
        "materials": "Digital download, PDF",
        "searchPhrase": "thanksgiving escape room for kids",
        "autocompleteChecked": False,
        "checkNote": "Etsy market page etsy.com/market/thanksgiving_escape_room opened 2026-10-29 (8 listings loaded, leader 1102701627 $13.99); Etsy-scoped web search: 'Thanksgiving Escape Room for Kids' leads 1027902540 and 1802251432 titles, 'Thanksgiving Escape Room' leads 1603651217 and 1595670304. Suggest/autocomplete not used (blocked in night runs).",
        "coverHeadline": "Thanksgiving Escape Room",
        "writtenAt": None}
assert len(title) <= 140 and title.lower().startswith("thanksgiving escape room for kids")
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert len(desc) >= 300 and desc.endswith("This design was created with AI assistance under the creative direction of the seller.")
bad = ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you're", "—", "5283", "Milo", "chair 3", "pie 8"]
assert not [b for b in bad if b.lower() in desc.lower() or b.lower() in title.lower()], [b for b in bad if b.lower() in desc.lower()]
assert copy["coverHeadline"].lower() != title.lower()  # fix round 3: headline = the cover words, never the whole title
print(len(title), len(tags), len(desc), max(len(t) for t in tags))
import datetime; copy["writtenAt"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump({"copy": copy, "stage": "images", "updatedAt": copy["writtenAt"]}, open("copy.json", "w"), indent=1)
