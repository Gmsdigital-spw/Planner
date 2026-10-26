# 07 Inspect: Atlas scores every product (room "inspect")

Pass = total 92 or more AND rulesPass (Grayson raised the bar from 90 to 92 on Oct 20, 2026).
Reach 92 by making the product better, never by nudging scores. An honest 87 that fails is
better than a padded 91.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/rubric.md` | Full file | Rules check, slop check, the six scores |
| Spec | `../../../specs/cover-styles.md` | "Scoring", newest section | What a cover must do |
| Skill | `../../../skills/atlas/SKILL.md` | Full file | Checklist and lessons |
| Notebook | `../../../notebook/predictions.md` | "Calibration" | How far off Atlas's past guesses were; adjust before guessing |
| Notebook | `../../../notebook/scoreboard.md` | "By lane" | Real views per listing per lane, the base for a guess |
| Reference | `../references/preflight.md` | Full file | What each fix round checks and fixes |
| Database | products (stage inspection), products (newest 3 published): cover ids | | What to score; the covers to compare |
| Reference | `../references/wall-art.md` | "Inspect" section | Only for a wallart product |
| Spec | `../../../specs/product-floor-v6.md` | "INSPECTION for the new lanes" | Only for mugwrap, sticker, invitation |

## Process
1. Set crew/atlas working ("Inspecting: <title>"). For each product in stage "inspection"
   (including ones Grayson sent back once fixed):
2. Rules check (rulesPass): every rule in rubric.md "Rules" holds.
3. Slop check: save gs.thumb_check of this cover and of the 3 newest published covers
   (download their cover assets), put them side by side in one image and Read it, then apply
   every line of rubric.md "Slop check". Record score.slopCheck {pass, fails:[short strings]}.
   A product that fails the slop check cannot score above 12 for images or 6 for polish, so it
   fails and gets fixed in the same run.
4. Score: file /25, copy /20, images /20, market /15, price /10, polish /10, total /100,
   rubric 2, a one-sentence verdict, scoredAt. A cover whose title or count is not readable at
   300 px scores images at most 14; a page with overlap, clipped text, cramped spacing or a
   cheap-looking cover cannot score above 14 for images or 7 for polish.
5. Pass (92+ and rulesPass): stage "passed". Fail: add a note with what to fix, retries + 1,
   then FIX ROUNDS (Oct 23, 2026: five builds in a row died at 73 to 85 after one round):
   up to THREE fix rounds this run. Each round: list the points lost per category, pick the
   2 categories furthest below full marks, run the matching lines of
   `../references/preflight.md`, make the product better there (rebuild the photo, rewrite the
   copy, open 3 real Etsy listings for market evidence, refill the half-empty page), then
   re-score honestly. Stop early only when it passes or a round raised nothing. A product
   still under 92 stays stage "inspection" with a note of the exact next fixes; the next
   run's 03 Pick finishes it FIRST. It becomes "scrapped" only when retries reach 4 or the
   lane itself caps it: market 11 or less after a fix round that went looking for 100+ item-review
   rivals and found none (Oct 23, 2026: such ideas top out near 89 and waste whole nights), UNLESS
   the rubric's OPEN NICHE proof holds (Oct 24, 2026): then it is fixed, not scrapped.
   Scrap it, say so in the Scout lesson, and build the next approved brief instead. Pass stays
   92; the crew's aim is 95+. Never rewrite an older product's score to a different rubric.
5b. PREDICT (Oct 26, 2026: the crew learns by guessing, then checking). For every product that
   PASSED, set products/<id>.prediction = {views7, favs7, sales7, why, at}: what it will do in its
   first 7 days live. Start from the lane's views per listing in scoreboard "By lane", then apply
   Atlas's Calibration line in predictions.md (divide or multiply as it says), then adjust for
   season and for how close it is to a Winner in winners.md. Whole numbers; why is one sentence
   with the numbers used. An honest low guess beats a hopeful one. The keeper grades it later.
6. Write one JSON line per scored product to `factory/scores.jsonl`:
   {"d":"<day key>","agent":"atlas","kind":"product","item":"<title>","score":<total>,"metric":null}.
7. Set crew/atlas idle. Write `## Inspect: <title>` in the run notes: PASS/FAIL, the six
   scores, the slop fails, the stage it ended in.

## Audit

| Check | Pass condition |
|-------|---------------|
| Side-by-side done | The comparison image exists and was Read before scoring |
| Honest | No score raised without a change to the product |
| Verdict | Leads with PASS/FAIL, the number, then one reason |
| scores.jsonl | One line per scored product this run |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Score | products/<id>.score | rubric 2 |
| Stage | products/<id>.stage | passed / scrapped / inspection |
| Score lines | `factory/scores.jsonl` | one JSON line each |
