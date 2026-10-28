import json
title = "Christmas Charades Printable Game: 120 Cards in 3 Levels for Kids, Family and Adults, Draw It Mode, Holiday Party Game"
tags = ["christmas charades","charades printable","christmas games","christmas party game","family game night","holiday party games","office party game","kids christmas game","xmas charades","christmas printable","charades cards","party games adults","christmas eve games"]
desc = """Christmas charades for the whole family: 120 printable cards in 3 colour-coded levels, so the kids, the family and the grown-ups all play from one print. Fun for the whole family at a holiday party, a classroom party, an office party or Christmas Eve at home.

Every prompt is original and easy to act out: no movie or song titles that kids don't know, just Christmas moments everyone has lived (untangling the lights, stepping on a toy in the dark, the Secret Santa reveal).

WHAT'S INCLUDED (16-page PDF)
- Cover
- How to Play: setup, rounds, scoring, the 3 levels, mixed-age rules (1 page)
- 120 charades cards, 12 per page with dashed cut lines (10 pages)
   Kids: 40 cards (green)
   Family: 40 cards (red)
   Adults and office: 40 cards (gold)
- Draw It Mode: play the same cards as a drawing game, plus timer rules and 4 party variations (1 page)
- Team Score Sheet for up to 4 teams and 12 rounds (1 page)
- 12 blank cards, 4 per level, to write your own (1 page)
- Thank-you page

HOW IT WORKS
Each actor picks a card from their own level and acts it out in 60 seconds. A correct guess scores 1 point, under 30 seconds scores 2. Switch to Draw It mode any time: same cards, drawn instead of acted.

PRINTING
US Letter PDF. Print at home or at a print shop at 100% / Actual size; on A4 paper choose Fit to page. Cardstock works best for cards. Print as many copies as you need for your own family or party.

THIS IS A DIGITAL DOWNLOAD
Nothing ships. After purchase, download the PDF from Etsy (You > Purchases). No app or account needed, it opens in any PDF reader.

For personal use only. Please do not resell or share the file.

Planning the whole party? Search our shop for "Christmas Party Games Bundle" and "Christmas Murder Mystery".

This design was created with AI assistance under the creative direction of the seller."""
AI = "This design was created with AI assistance under the creative direction of the seller."
assert len(title) <= 140, len(title)
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags)
assert len(desc) >= 300 and desc.endswith(AI) and desc.count(AI) == 1
bad = ["elevate","unlock","seamless","game-changer","dive into","look no further","whether you're","—"]
assert not [b for b in bad if b in desc.lower()+title.lower()]
print(len(title), repr(title[:40]), len(desc))
copy = {"title": title, "tags": tags, "description": desc, "price": 3.99,
  "category": "Paper & Party Supplies > Party Supplies > Party Games", "materials": "Digital download, PDF",
  "autocompleteChecked": False, "searchPhraseSource": "suggestqueries blocked (proxy 403 + WebFetch permission); phrase from opened Etsy market page /market/christmas_charades_printable and rival 1344334302 (114 item reviews, slug christmas-charades-christmas-printable)",
  "coverHeadline": "Act It or Draw It", "coverBadge": "120 CARDS · 3 LEVELS"}
json.dump({"copy": copy}, open("copy_out.json","w"))
