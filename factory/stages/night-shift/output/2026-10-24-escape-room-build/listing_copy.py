import json
title = "Christmas Escape Room for Kids Printable, Family Game with 2 Levels Ages 6-9 and 10+, No Phone Needed, Holiday Party Activity"
tags = ["xmas escape room", "kids escape room", "family escape room", "escape room game", "escape room kit",
        "holiday escape room", "christmas puzzles", "christmas party game", "kids christmas games",
        "christmas activity", "classroom christmas", "screen free activity", "family game night"]
desc = """A printable Christmas escape room for kids and families, with two levels in one story: Level 1 for ages 6-9 and Level 2 for ages 10+. Big and little kids play the same game together, and you need no phone, app, QR code or internet to finish it.

THE STORY
It is Christmas Eve. Juniper, the youngest elf, locked the sleigh bells in the Bell Vault and forgot the 4-digit code. Players solve 4 clues, each clue gives one digit, and the 4 digits open the vault before the 45-minute timer runs out.

TWO LEVELS, SAME DIGIT
Every clue comes in two versions. Both versions lead to the same digit, so a 7-year-old and a 12-year-old can work side by side and check each other's answers.
- Clue 1: number code (Level 1) / shift cipher (Level 2)
- Clue 2: count the shelf (Level 1) / picture math (Level 2)
- Clue 3: tangled lights (Level 1) / bell maze (Level 2)
- Clue 4: 4x4 sudoku (Level 1) / elf logic grid (Level 2)

WHAT'S INCLUDED (16 pages, one PDF)
- Cover
- Game master guide: set-up in 10 minutes, how to run it, supplies
- Mission letter to read aloud, team sheet and code tracker
- 8 clue sheets (4 clues x 2 levels)
- Vault lock sheet (the final code)
- 6 envelope lock tags to cut out
- 8 hint cards, each with 2 fold-over hints
- Answer key with full solutions (game master only)
- Escape Expert certificates (2 per page)

GOOD TO KNOW
- Players: 1 to 12, in teams of 2 to 4. Play time about 45 minutes.
- No phone needed: the game master checks each digit with the answer key.
- Ink-light design: white pages with thin lines, and every puzzle works in black and white.
- Supplies: pencils, scissors, tape, 5 envelopes per team (or folded paper) and a timer.
- US Letter size; prints on A4 with "Fit to page".
- Good for Christmas break, family parties, classrooms and Christmas Eve.

HOW IT WORKS
This is a digital PDF download. Nothing is shipped. After purchase, download the file from your Etsy account (Purchases and reviews) or from the email Etsy sends you, then print at home or at a print shop. For personal and classroom use.

This design was created with AI assistance under the creative direction of the seller."""
copy = {"title": title, "tags": tags, "description": desc, "price": 11.99,
        "category": "Paper & Party Supplies > Party Supplies > Party Favors & Games > Party Games",
        "materials": "Digital download, PDF", "autocompleteChecked": True,
        "searchPhrase": "christmas escape room for kids printable",
        "coverHeadline": "Christmas Escape Game"}
assert len(title) <= 140, len(title)
assert title[:40].lower() == "christmas escape room for kids printable", title[:40]
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert len(desc) >= 300 and desc.endswith("This design was created with AI assistance under the creative direction of the seller.")
bad = ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you", "—"]
assert not [b for b in bad if b in desc.lower() or b in title.lower()], [b for b in bad if b in desc.lower()]
json.dump({"copy": copy}, open(__file__.rsplit("/", 1)[0] + "/copy.json", "w"), indent=1)
print(len(title), len(tags), len(desc), max(len(t) for t in tags))
