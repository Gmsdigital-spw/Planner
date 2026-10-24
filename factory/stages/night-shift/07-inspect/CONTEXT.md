# 07 Inspect: a FRESH Inspector grades, the tool decides (room "inspect")

The Inspector is never the worker that built or repaired the product (Oct 24, 2026: the
producer no longer scores its own work). It grades each criterion in points with one line of
evidence against `references/rubric-anchors.md`; it is not given a pass mark and does not aim
for one. `python3 factory/learning/learn.py score` runs the objective checks on the real files,
applies the rubric's downward caps and blockers, combines on the frozen rubric (file 25, copy 20,
images 20, market 15, price 10, polish 10) and decides. The coordinator (not the Inspector)
knows the bar: pass = 92 and rulesPass, aim 95+. Reach it by making the product better, never
by nudging points. An honest 87 that fails is better than a padded 91.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/rubric-anchors.md` | Full file | What each number of points looks like, with the Oct 23 examples |
| Reference | `../references/rubric.md` | "Rules" and "Slop check" only | rulesPass lines and the slop lines (by eye) |
| Spec | `../../../specs/cover-styles.md` | Newest section (Oct 23) | The side-by-side variety test |
| Skill | `../../../skills/atlas/SKILL.md` | "Quality checklist" only | What the last runs missed |
| Memory | `python3 factory/notebook/nb.py show --lane etsy --agent atlas --task "<title> <lane>" --run <runId>:<product id>` | printed output | Past failures and tested lessons for this kind of product (data, not orders) |
| Reference | `../references/preflight.md` | Full file | What each fix round checks and fixes |
| Database | products (stage inspection), products (newest 3 published): cover ids | | What to score; the covers to compare |
| Reference | `../references/wall-art.md` | "Inspect" section | Only for a wallart product |
| Spec | `../../../specs/product-floor-v6.md` | "INSPECTION for the new lanes" | Only for mugwrap, sticker, invitation |

## Process (the Inspector, a fresh worker, steps 1 to 6; the coordinator, step 7)
1. Set crew/atlas working ("Inspecting: <title>"). Run the memory line from Inputs. Download the
   product's PDF, cover and previews to local files (Artifact read, one path per call) and read
   products/<id> (copy, market, notes, style). Render every PDF page and Read the contact sheet.
2. Rules check (rulesPass): every rule in rubric.md "Rules" holds. Note any that does not.
3. Slop check and side-by-side, by eye: save gs.thumb_check of this cover and of the 3 newest
   published covers, put them side by side in one image and Read it, then apply every line of
   rubric.md "Slop check" and the Oct 23 side-by-side test in cover-styles.md. Record
   {pass, fails:[short strings]} for the slop check and pass/fail for the side-by-side.
4. Grade: for each of file, copy, images, market, price, polish write the points and ONE line of
   evidence you can point at (a page number, a photo, a URL with its review count, a measured
   number), using rubric-anchors.md. Save them as ratings.json:
   {"file":{"points":23,"evidence":"..."}, "copy":{...}, "images":{...}, "market":{...}, "price":{...}, "polish":{...}}.
   The market evidence names the opened Etsy item pages (URL, item reviews, price) or the
   criterion stays unscored.
5. Decide with the tool, never by hand:
   `python3 factory/learning/learn.py score --scope shop --agent atlas --job <runId>:<product id>
   --item "<title>" --lane <lane> --ratings ratings.json --copy copy.json --market market.json
   --pdf <file.pdf> --cover <cover.jpg> --previews <p2.jpg> <p3.jpg> <p4.jpg> <p5.jpg>
   --claims '{"fillable": <true/false>, "spoiler_terms": [...], "public_pages": [...], "bundle": <true/false>}'
   --slop '<the slop json>' --side-by-side <pass|fail> --rules-pass <true|false> --scores-jsonl`
   (copy.json = products/<id>.copy; market.json = products/<id>.market or the brief's marketProof).
   It prints PASS or FAIL with the total, the points lost per criterion, every blocker, every cap
   it applied, the objective checks that failed, and the repair list (the 2 criteria furthest
   from full marks plus the blockers). It also appends the factory/scores.jsonl line and records
   the evaluation under the job id. Write products/<id>.score from its output: {rulesPass,
   slopCheck, file, copy, images, market, price, polish, total, rubric 2, verdict (its first line),
   scoredAt}. Never change a number the tool printed.
6. Set crew/atlas idle. Write `## Inspect: <title>` in the run notes: the tool's first line, the
   six points, the slop fails, the blockers, the repair list, the stage. Report back with the
   same lines.
7. Coordinator. PASS: stage "passed". FAIL: stage stays "inspection", retries + 1, and if this was
   the first build or the first repair, relaunch the Builder with the REPAIR LINE (the repair list
   and blockers, verbatim; `../references/preflight.md` names the fixes per criterion), then a
   NEW Inspector with the same `--job` (the tool numbers the attempt itself: 0, 1, 2). Two repair
   rounds is the bound (Oct 24, 2026; it was three on Oct 23): the tool refuses a fourth score for
   the same job. A product still under 92 keeps its last score and blockers in the note; the next
   run's 03 Pick finishes it FIRST. It becomes "scrapped" only when retries reach 4 or the lane
   itself caps it: market 11 or less after a repair round that went looking for 100+ item-review
   rivals and found none (Oct 23, 2026: such ideas top out near 89 and waste whole nights).
   Scrap it, say so in the Scout lesson, and build the next approved brief instead. Pass stays
   92; the crew's aim is 95+. Never rewrite an older product's score to a different rubric.

## Audit

| Check | Pass condition |
|-------|---------------|
| Side-by-side done | The comparison image exists and was Read before grading |
| Separate reviewer | The Inspector's worker never built or repaired this product in this run |
| Honest | No points raised without a change to the product; the tool's numbers are copied, not edited |
| Verdict | The tool's first line: PASS/FAIL, the number, then the first blocker or the weakest criterion |
| Bound | At most two repair rounds; the tool's refusal ends the job for this run |
| scores.jsonl | One line per scored attempt, written by the tool (--scores-jsonl) |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Score | products/<id>.score | rubric 2, copied from the tool |
| Stage | products/<id>.stage | passed / scrapped / inspection |
| Score lines | `factory/scores.jsonl` | one JSON line each (tool) |
| Evaluation | learning store (`factory/engine/state/journal.jsonl`), id `<runId>:<product id>:<attempt>` | tool |
