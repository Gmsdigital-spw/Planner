import json
title = "Christmas Party Bundle Printable: 6 Games, 12 Awards, White Elephant Dice Game, Gingerbread Contest, Family or Office Party"
tags = ["christmas party", "christmas games", "xmas party games", "white elephant game", "gingerbread contest",
        "christmas awards", "office party games", "family party games", "holiday party games", "christmas trivia",
        "christmas bundle", "party game bundle", "christmas printable"]
desc = """The whole Christmas party night in one printable PDF: 6 party games, 12 award certificates, a white elephant dice game and a gingerbread house contest, for families, friend groups and office parties.
Fun for a group from the first guest to the last gift. Print it once and every part of the night is planned, in the order you will use it.

WHAT YOU GET (16 printable pages, plus a thank-you page)
1 page: Host timeline and how to use, with both answer keys
Game 1: Christmas Word Scramble (14 words, answer key)
Game 2: Christmas This or That (20 pairs)
Game 3: Christmas Would You Rather (12 questions)
Game 4: Christmas Trivia Quiz (12 multiple-choice questions, answer key)
Game 5: Find the Guest Who (25-square mingle game with a free space)
Game 6: Christmas Charades Cards (24 cut-out cards)
4 pages: Christmas Party Awards (12 awards, 3 per page: Best Ugly Sweater, Life of the Party, Gift Wrap Master and more)
3 pages: Gingerbread House Contest (rules and entry list, 4 judge score cards, 6 cut-out ribbons)
2 pages: White Elephant Dice Game (roll chart and rules) and the Left-Right Gift Story to read aloud

HOW THE NIGHT RUNS
Start with Find the Guest Who as people arrive, play the games in teams, build gingerbread houses at the snack break, swap gifts with the dice game and the left-right story, then finish with charades and the awards ceremony.

THE DETAILS
Digital PDF download. Nothing will be shipped.
US Letter size; prints on A4 with "fit to page".
Print at home or at a print shop. Cardstock is best for the awards and ribbons.
Not editable: write names and answers by hand. No apps or accounts needed.
You need pens, one six-sided die, and gingerbread kits with frosting and candy.

HOW TO DOWNLOAD
After you buy, go to Etsy > You > Purchases and download the PDF. You can also use the link in your receipt email.

For personal use. Please do not resell or share the file.

Planning more of the night? The shop also has the Christmas Murder Mystery Party Game for 8 Players and the Christmas Escape Room for Kids.

This design was created with AI assistance under the creative direction of the seller."""
AI = "This design was created with AI assistance under the creative direction of the seller."
assert len(title) <= 140, len(title)
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert desc.strip().endswith(AI) and desc.count(AI) == 1 and len(desc) >= 300
for bad in ["elevate", "unlock", "seamless", "dive into", "whether you", "look no further", "game-changer", "—"]:
    assert bad not in desc.lower(), bad
copy = {"title": title, "tags": tags, "description": desc, "price": 8.49, "currency": "USD",
        "category": "Paper & Party Supplies > Party Supplies > Party Games", "materials": ["Digital download", "PDF"],
        "coverHeadline": "Christmas Party Night", "coverSub": "16 PAGES · 6 GAMES · 12 AWARDS · GIFT SWAP · CONTEST",
        "autocompleteChecked": False,
        "searchPhraseSource": "Google suggest blocked (proxy 403, WebFetch permission unanswered); phrase from the brief and opened rival listings 1813351868 ('christmas game bundle ... christmas party') and 1123794386 ('printable christmas game bundle')",
        "priceWhy": "$8.49: inside the $8-14 bundle band and the brief's $8.49-9.99; under the $9.47 sum of the 3 included kits' prices given tonight (Party Games Bundle $2.99 + Awards $1.99 + Gingerbread $4.49; escape room not included, $21.46 with it); rivals sell games only at $4.05-$5.00",
        "crossSell": ["prod-xmas-murder-mystery-8", "prod-xmas-escape-room"], "writtenAt": "2026-10-27T08:35:00Z"}
json.dump({"copy": copy, "stage": "images", "updatedAt": "2026-10-27T08:35:00Z"}, open("copy_update.json", "w"), indent=1)
print(len(title), title[:40], "|", len(desc), max(map(len, tags)))
