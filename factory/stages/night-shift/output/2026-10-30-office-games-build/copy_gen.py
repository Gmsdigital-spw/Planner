import json
title = "Office Christmas Party Games Printable: 24 No-Prep Team Games, Bingo, Trivia and Icebreakers for Work, Coworkers and Staff Parties"
tags = ["office party games", "xmas party games", "office christmas", "work christmas party", "coworker games",
        "staff party games", "team building games", "holiday party games", "office party", "christmas icebreaker",
        "christmas trivia", "christmas bingo", "work party games"]
AI = "This design was created with AI assistance under the creative direction of the seller."
desc = """24 office Christmas party games for coworkers, ready to print. Made for whoever got handed the staff party or holiday luncheon this year: open the PDF, follow the 45-minute run sheet and you are the host.

Every game works for any coworker: no props to buy, no drinking games and no movie or song trivia. A pen and the printed sheets are all you need, and most games need nothing at all. Groups of 6 to 60.

WHAT'S INCLUDED (17-page PDF: cover, 15 pages, thank-you page)
- 45-minute party plan: a minute-by-minute run sheet, a print list, and quick swaps for 20-minute parties or groups over 30
- Game Finder: all 24 games on one page by group size, time and type (mingle, team, icebreaker, active, seated)
- 6 how-to-play pages: 4 games per page with simple steps and how to win
- Coworker Holiday Bingo card (find a coworker who...)
- Holiday Word Scramble: 20 words with hints
- Holiday Trivia Showdown: 20 general holiday and winter questions
- Letter Lists: 8 categories, 3 rounds
- Guess the Coworker fact cards (4 per page, cut out)
- Team score sheet for up to 6 teams
- Answer keys for the scramble and trivia

THE 24 GAMES
Coworker Holiday Bingo, Holiday Word Scramble, Holiday Trivia Showdown, Letter Lists, Guess the Coworker, Silent Line-Up, This or That Walk, Two Truths and a Tale, Snowball Questions, Pass the Story, Draw It on Your Head, Holiday Alphabet Chain, Pocket Scavenger Hunt, Sixty-Second Sprints, Big Word Builder, Freeze Frame, Holiday Act-It-Out, Team Holiday Haiku, Kind Words Circle, Last One Standing, Snowflake Showdown, Guess My Gift, Office Superlatives, Holiday Name Game.

HOW IT WORKS
This is a digital download. Nothing will be shipped. After purchase, go to You > Purchases on Etsy and download the PDF. Print at home or at a print shop on US Letter paper (8.5 x 11 in); black and white printing works fine. Print as many copies as your office party needs.

For personal and workplace party use. Please do not resell or share the file.

Hosting more parties? Search our shop for "Christmas Party Awards" and "Christmas Murder Mystery".

""" + AI
cover_headline = "24 No-Prep Office Party Games"
copy = {"title": title, "tags": tags, "description": desc, "price": 4.99,
        "priceNote": "$4.99 vs rivals $5.00 (21 games, 1793094436), $6.00 (1590499162), $8.00 (1591093532), $14.60 (1615021021); inside $2.99-$6.99 single-kit range",
        "category": "Paper & Party Supplies > Party Supplies > Party Games", "materials": ["Digital download", "PDF"],
        "coverHeadline": cover_headline, "autocompleteChecked": False,
        "checkNote": "Phrase 'office christmas party games': Etsy search via the gateway Oct 29 (Scout), 25 of top 25 titles carry it; not re-run tonight (Builder has no gateway write path; WebFetch of the Etsy search page blocked, permission not answered).",
        "tagNote": "fix round 2: 'christmas games' -> 'office party': buyer-voice 1591093532 'Very fun for the office party!'; in 3+ of top titles of 4 Scout gateway searches on file (gw/out scout-2026-10-30-s4 trivia 9/20, s5 mltgame 7/20, s1 mlt 6/20; scout-2026-10-29-s0 7/25). Title adds Bingo, Trivia, Icebreakers: games in the file; 'christmas trivia' 20/20 (s4), 'christmas bingo' 3/25 and 'icebreaker' 6/25 (scout-2026-10-29-s2 office search).",
        "writtenAt": "2026-10-30T07:45:00Z"}
assert len(title) <= 140 and title.lower().startswith("office christmas party games") and title.startswith("Office Christmas Party Games Printable: ")
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags)
assert len(desc) >= 300 and desc.endswith(AI)
assert len(cover_headline.split()) <= 5 and cover_headline.lower() not in title.lower()
for bad in ["elevate", "unlock", "seamless", "dive into", "whether you", "game-changer", "look no further", "—"]:
    assert bad not in desc.lower(), bad
json.dump(copy, open("copy.json", "w"), indent=1)
print(len(title), len(tags), len(desc), title[:40])
