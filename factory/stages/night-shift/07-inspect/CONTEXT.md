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
   fix the weak parts now (up to two fix rounds per run; 85 to 91 gets a second round aimed at
   its weakest categories), re-score. A product that fails after retries reaches 2 becomes
   stage "scrapped". Never rewrite an older product's score to a different rubric.
6. Write one JSON line per scored product to `factory/scores.jsonl`:
   {"d":"<day key>","agent":"atlas","kind":"product","item":"<title>","score":<total>,"metric":null}
   (and one per Idea Judge decision from stage 02: agent "judge_ideas", kind "idea").
7. Set crew/atlas idle. Record each score and its fails in `../output/<day key>-run.md`.

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
