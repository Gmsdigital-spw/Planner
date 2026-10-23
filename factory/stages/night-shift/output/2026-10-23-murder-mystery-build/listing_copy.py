import json, re
TITLE = "Christmas Murder Mystery Party Game for 8 Players, Printable Whodunit, Family Friendly Christmas Dinner Party Game, Host Can Play"
TAGS = ["murder mystery game", "christmas mystery", "murder mystery party", "christmas party game", "whodunit game",
        "dinner party game", "mystery party kit", "family xmas game", "8 player mystery", "holiday party game",
        "adult party game", "office party game", "christmas eve game"]
AI = "This design was created with AI assistance under the creative direction of the seller."
DESC = f"""A printable Christmas murder mystery party game for 8 players: a cozy whodunit for a Christmas dinner with friends, family or coworkers. Print it, hand out the character sheets, and you are hosting a 2-hour mystery tonight.

THE STORY: The Stolen Star of Hollyridge Lodge. Christmas Eve, a snowed-in mountain lodge. At 7:08 every light goes out. At 7:20 they come back on and the lodge's famous gold Star is gone from the top of the tree. Eight guests, eight secrets, one thief. Family friendly: no violence, nothing is hurt but a mantel clock.

ONE FAIR ANSWER: the clues point to exactly one guest, and they prove it two separate ways (alibis and a shoe print). Every innocent guest has an alibi a clue card can confirm, so no one is left guessing and the reveal makes sense to the whole table. We checked the clue logic with code before release.

WHAT'S INCLUDED (16 pages, US Letter, prints on A4):
- Page 1: Cover with contents
- Page 2: Host guide (how it works, what to print, setup checklist, host tips)
- Page 3: Party timeline and host script (opening to read aloud, 3 rounds)
- Page 4: Invitations, 2 per sheet, fill in by hand
- Pages 5 to 12: 8 character sheets, one page each: who you are, costume idea, secret, alibi, what to say in Rounds 1, 2 and 3, and questions to ask
- Page 13: 9 clue cards, 3 per round, cut apart
- Page 14: Detective Notes accusation sheet, one per player
- Page 15: The solution, with a read-aloud reveal and who is cleared by which clue
- Page 16: 8 name tags and 2 awards (Master Detective, Best in Character)
Plus a thank-you page.

HOW TO HOST:
1. Send invitations 2 to 3 weeks ahead and give each guest a character.
2. A week before, send each guest only their own sheet.
3. On the night, read the opening, then read 3 clue cards each round. Dinner fits between Rounds 1 and 2.
4. Everyone fills in Detective Notes, then you read the sealed solution.
The host can play too. Fewer than 8 guests? The host guide says which pairs to drop.

THE CHARACTERS: Ivy (lodge owner), Jasper (ski instructor), Clem (head cook), Rupert (antique dealer), Noelle (lodge singer), Dash (handyman), Marigold (travel writer), Felix (owner's nephew). All original characters, any guest can play any role.

GOOD TO KNOW:
- Digital PDF download. Nothing ships. Download from your Etsy Purchases page after checkout, then print at home or at a print shop.
- Print in color or black and white.
- For personal use. Not editable; invitations have lines to fill in by hand.
- Best for adults and teens, about 2 hours.

{AI}"""
problems = []
if len(TITLE) > 140: problems.append("title long")
if len(TAGS) != 13 or len(set(TAGS)) != 13: problems.append("tags count")
for t in TAGS:
    if len(t) > 20: problems.append("tag long " + t)
if len(DESC) < 300 or not DESC.endswith(AI): problems.append("desc")
for bad in ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you're", "—"]:
    if bad in DESC.lower() or bad in TITLE.lower(): problems.append("slop " + bad)
copy = {"title": TITLE, "tags": TAGS, "description": DESC, "price": 9.99,
        "category": "Paper & Party Supplies > Party Supplies > Party Games", "materials": "Digital download, PDF",
        "autocompleteChecked": False, "coverHeadline": "Who Stole the Star?"}
print(len(TITLE), len(TAGS), len(DESC), problems)
json.dump({"copy": copy}, open("/home/claude/build/mystery/copy.json", "w"))
