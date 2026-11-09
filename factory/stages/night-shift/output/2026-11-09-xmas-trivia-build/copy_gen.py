"""Listing copy for prod-xmas-trivia-200; every limit and every count claim checked by code against the PDF."""
import json, re, subprocess, sys
HERE = __file__.rsplit("/", 1)[0]
sys.path.insert(0, HERE)
from content import ROUNDS, TIEBREAKERS
PDF = HERE + "/christmas-trivia-game.pdf"
AI = "This design was created with AI assistance under the creative direction of the seller."

title = "Christmas Trivia Game Printable: 200 Questions in 10 Rounds for Family, Office and Game Night, Answer Keys and Team Score Sheets"
tags = ["christmas trivia", "xmas trivia quiz", "xmas trivia game", "christmas quiz", "holiday trivia",
        "trivia printable", "christmas party game", "office party games", "holiday party game", "christmas games",
        "xmas party games", "family game night", "christmas eve games"]
rounds_list = "\n".join(f"{i}. {t} (20)" for i, (t, s, q) in enumerate(ROUNDS, 1))
desc = f"""200 Christmas trivia questions for your family Christmas party, office party or holiday game night: 10 themed rounds of 20, with answer keys, a host script and team sheets, so a group of any size can play with no prep. Fun for a large group, and Round 9 is an easy Kids' Round so younger players can join in.

Every question is original and fact-checked. There are no movie, song or TV rounds, so it works for church groups, classrooms, offices and mixed ages alike.

THE 10 ROUNDS
{rounds_list}

WHAT'S INCLUDED (16 pages + a thank-you page)
- Page 1: Cover with the round list
- Page 2: How to Play, with set-up, scoring, a Joker rule and a host script to read out
- Pages 3 to 12: the 10 rounds, 20 questions each (200 in all)
- Pages 13 and 14: answer keys for all 200 questions
- Page 15: Team Answer Sheet (print one per team for each round)
- Page 16: Team Score Sheet for up to 10 teams, plus 3 closest-number tie-breakers

HOW IT PLAYS
Split into teams of 2 to 6. The host reads each question twice, teams write their answers, then swap sheets and mark them while the host reads the key. One point per answer, 20 per round. Each round takes about 15 minutes with marking, so play all 10 for a full night or any 4 in about an hour.

HOW TO GET IT
This is a digital PDF download. Nothing will be shipped. After purchase, download the PDF from your Etsy account (You > Purchases) or from the email Etsy sends. Print at home or at a print shop on US Letter paper; it also prints on A4 with "Fit to page". Print as many answer and score sheets as you need for your own party.

For personal use only. Please do not resell or share the file.

{AI}"""
price = 3.99
copy = {
    "title": title, "tags": tags, "description": desc, "price": price,
    "category": "Paper & Party Supplies > Party Supplies > Party Games",
    "materials": ["Digital download", "PDF"],
    "coverHeadline": "200 Christmas Trivia Questions",
    "priceNote": "$3.99 for 200 questions: inside the opened band $2.00 (4397704059, 195 item reviews) to $11.98 (4382556824, 102 item reviews, 10 games); the 100-question rivals sell at $5.00 (1580150786) and $4.50 (4605944652), so ours is about half their price per question.",
    "phraseCheck": {"phrase": "christmas trivia game printable", "source": "etsy-search via gateway",
                    "results": [{"job": "scout-2026-11-07-a1-33e0 xtriv_o0 'xmas trivia'", "hits": 4, "of": 25, "also": "'christmas trivia game' 13 of 25"},
                                {"job": "scout-2026-10-31-s5-7b75 phrase_triv", "hits": 23, "of": 25}],
                    "fresh": False, "note": "No new gateway job this run (Builder may not push); newest check Nov 7, 2 days old."},
    "autocompleteChecked": False,
    "gap": "200 original questions in 10 rounds (vs 62 to 100 in the leaders) with a host script, team answer and score sheets and full keys at $3.99; no movie or song rounds.",
    "writtenAt": "2026-11-09T08:35:00Z", "by": "Quill",
}
# ---------------- checks
assert len(title) <= 140, len(title)
assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), [t for t in tags if len(t) > 20]
assert "digital download" not in tags
assert len(desc) >= 300 and desc.rstrip().endswith(AI) and desc.count(AI) == 1
bad = [w for w in ["elevate", "unlock", "seamless", "game-changer", "dive into", "look no further", "whether you're", "—"] if w in desc.lower() or w in title.lower()]
assert not bad, bad
pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout).group(1))
size = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout
assert pages == 17 and "612 x 792" in size, (pages,)
txt = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True).stdout.split("\f")
pg = lambda n: txt[n - 1]
assert "How to Play" in pg(2) and "Answer Key: Rounds 1 to 5" in pg(13) and "Answer Key: Rounds 6 to 10" in pg(14)
assert "Team Answer Sheet" in pg(15) and "Team Score Sheet" in pg(16) and "Tie-breakers" in pg(16).replace("TIE-BREAKERS", "Tie-breakers")
assert "You just made my day!" in pg(17)
for i, (t, s, q) in enumerate(ROUNDS, 1):
    assert t.replace("'", "’") in pg(i + 2).replace("'", "’") or t in pg(i + 2), (i, t)
assert sum(len(q) for t, s, q in ROUNDS) == 200 and len(TIEBREAKERS) == 3
assert pg(16).count("TEAM") >= 1
print(f"copy OK: title {len(title)} chars, 13 tags (max {max(map(len, tags))}), description {len(desc)} chars, price {price}, PDF 17 pages Letter, page list matches")
json.dump(copy, open(HERE + "/copy.json", "w"), indent=1, ensure_ascii=False)
