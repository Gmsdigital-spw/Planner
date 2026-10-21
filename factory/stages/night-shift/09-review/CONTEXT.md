# 09 Review: experiments, money, sales review, next move (rooms "intel", "treasury", "bridge", "core")

Each sub-step has its own skip rule. Skipped sub-steps are listed in the run log.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Reference | `../references/database-fields.md` | "experiments", "sprint", "lessons", "nextmove", "ads" | Field shapes |
| Spec | `../../../specs/product-floor-v6.md` | SALES PUSH (last bullet: Next Move while sales are 0) | What the top recommendation must be |
| Database | stats (newest 14), sales, spend/<month>, adlog, bills, experiments, sprint/main, ads/main, lessons | | Real numbers only |

## Process
A. Experiments (room "intel"). Skip (a) when no experiment is running with reviewDate <= today.
   (a) For each running experiment due: compute the result from stats snapshots (target's views
   and favorites 14 days before startDate vs 14 days after, and the shop's sales change; use the
   baseline object as "before" when present). Write results in plain text with the numbers,
   confidence "low" if either window has under 100 views, and a recommended call ("looks like
   keep because...", "looks like revert because...", "inconclusive: extend 14 days"). Leave
   status running and decision null: Grayson decides.
   (b) For at most ONE "looks, no sale" listing (from C) with no proposed or running experiment:
   propose ONE experiment (status "proposed") changing exactly one thing (title first phrase,
   first photo, or price), original and test spelled out, signal, success, reviewDate +14 days,
   costLimit 0, source "Atlas · Night Shift <day>".
   (c) For every experiment decided since the last run (status "decided", decision not
   "declined") with no lesson yet: write lessons/<id> with evidence (baseline and result),
   confidence, status active, expiresAt (season end, or 90 days). Never repeat a reverted
   change without a documented reason.
B. Ledger (room "treasury"). Etsy shares only the sales count, not amounts: do not write
   revenue. Only if a real spend or revenue source appears, keep spend/<month> and
   revenue/<month> current. Otherwise skip silently.
B2. Beacon (room "ads"). Skip if ads/main does not exist. Read ads/main and adlog. Never call
   Make or Etsy, never change an ads setting, never recommend spending while ads/main.unlocked
   is not true. Apply the ad plan in database-fields.md "ads" to the facts in the database.
   Update ads/main (if_version) setting ONLY review {at, text (plain, under 400 characters: the
   single most useful next ads step and why, with the numbers), actions:[up to 3]}.
C. Atlas sales review (room "bridge"). Read stats (newest 14). Fewer than 2 snapshots: write
   sprint/main saying the sprint starts once a week of data exists, and move on. Otherwise per
   listing compute views7 and favs7 (latest minus the snapshot closest to 7 days earlier) and
   the shop's sales change. Verdicts: views7 >= 30 and no sales change = "looks, no sale";
   views7 >= 30 and sales up = "working"; 10 to 29 = "warming up"; under 10 = "quiet". Write
   sprint/main {review:{at, text (under 450 chars: the one most useful finding and what to do,
   with numbers), actions:[up to 3]}, flags:[{listingId, title, views7, favs7, verdict}],
   updatedAt}. Then for at most ONE "looks, no sale" listing with no listing-update product in
   the last 14 days: investigate it (title, tags, description, price, photos from stats and any
   product doc with its listingId, plus a WebSearch of the top competitors) and create
   products/<id> as a copy-only update, stage "ready": {title:"Listing update: <name>",
   legacy:{listingId, url}, copy:{title, tags (13), description, descriptionVerified, price,
   priceNote, notes}, etsyStep (the fixed sentence in database-fields.md), summary, createdAt,
   source "Atlas sales review <day>"}. Description ONLY by rewriting the live one from stats
   (descriptionVerified true); if stats has none, description null and descriptionVerified
   false. Follow every Quill rule (stage 05) for that copy. If an active mission has a task
   about that listing, set the task's output to the new product id. For "working" listings,
   say in the review what the next product should borrow from them (format, price point,
   holiday timing). Never change the live listing yourself. Weekly lesson: if no lesson with source
   starting "Atlas weekly review" exists from the last 7 days and 7+ days of stats exist,
   write ONE lessons/<id> (under 160 chars, the numbers, confidence low under 100 views,
   expiresAt 90 days). Never a lesson without numbers.
D. Verified money (room "treasury"). From sales (this month), spend/<month>, adlog, bills:
   gross and refunds; Etsy fees = 6.5% + 3% + $0.25 per sale on net-of-refund, plus 15% where
   offsite is true; listing fees from spend; ad spend from adlog; AI costs from active bills
   (kind claude, anythingmcp). Net contribution and Recovery = (gross - refunds - Etsy fees -
   listing fees - ad spend) / the Claude plan amount. Do not write revenue/<month>. If sales is
   empty, the report says "no verified sales this month" and nothing else about money.
E. Next Move (room "core"). Pick the ONE thing that most moves the shop toward its first sale
   (while sales are 0) or toward earning back the Claude plan, from real data, in this order: a
   "looks, no sale" listing with no experiment or update; a live listing with under 5 photos
   or under 13 tags; a batch or product waiting on Grayson; pins with image and link but
   status ready; an approved brief the crew builds tonight; a measurement gap (no stats in 2
   days, no active claude bill). Write nextmove/main (shape in database-fields.md), why with
   the actual numbers, evidence naming the docs. Never a move that spends money. If nothing
   justifies a move: title "Nothing urgent: let tonight's build land", go "room:core". Log one
   event (crew "Atlas", "Next move: <title>").

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Experiment results / proposals | experiments/<id>, lessons/<id> | shapes in database-fields.md |
| Sales review | sprint/main, products/<id> (stage ready) | |
| Ads note | ads/main.review | only this field |
| Next move | nextmove/main | set once per run |
| Money lines | `../output/<day key>-run.md` "## Money" | the numbers for the report |
