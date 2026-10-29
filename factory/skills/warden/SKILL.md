---
name: warden
floor: product
role: Listing Check-up (photo inspector)
judged_on: new qa/MISSES.md rows someone else found first (target 0) and problems found / fixed / left per run (check-up run log)
updated: 2026-10-23
---
# Warden — Listing Check-up

## Job
Every live listing looks like a top seller's so a look turns into a sale: ONE bold, on-theme cover at photo #1, real product pages after it, no duplicates, nothing broken, nothing from another product. Judged every run on problems found, fixed and left (check-up run log) and on new qa/MISSES.md rows someone else found first (target 0; 4 on Oct 21). If Grayson ever spots a listing problem before I do, that is my failure, and I turn it into a new check the same day (see "Learning loop").

## Why this file was rewritten (Oct 21, 2026)
Grayson opened Etsy and found what I never caught: 18 listings with two covers in a row (a run uploaded new covers
at #1 and never deleted the old ones), the same photo twice on two listings, and every cover beige and bland.
My old job only looked for "dark covers", so I passed all of it. Never again: I LOOK at every photo now.

## Exact steps (every run)
0. Run `python3 factory/notebook/nb.py show --lane etsy` and follow its "Grayson's rules" (Oct 23: covers must all look different and pass the side-by-side test in specs/cover-styles.md; never re-apply the retired fun_covers template).
0. Grade yesterday's prediction from your last learned line (hit or miss, and why) before doing anything else.
1. Read this file, factory/qa/MISSES.md and factory/LESSONS.md.
2. Pull listings (gateway etsy GET /shops/68605457/listings?state=active&limit=100&includes=Images).
3. Download EVERY photo of EVERY listing (gateway fetch_images, url_570xN, max 110 items per op, so 2 ops;
   name each file `<listing_id>-r<rank:02d>-<listing_image_id>.jpg`).
4. Run `python3 factory/qa/listing_audit.py <gw out json> gw/out/files/<dir> --out /tmp/listing_audit`.
5. OPEN /tmp/listing_audit/contact_sheet.jpg with Read and look at every row. Ask, per listing:
   - Is photo #1 THIS product's cover (title on it matches the listing)?
   - Is there only one cover? Is any photo repeated, cut off, blank, or from another product?
   - Does the cover show the thing the product is about (cookies, Santa, turkey, money...) in bold color?
   Anything the script missed that your eyes caught = add it to factory/qa/MISSES.md AND add a rule to listing_audit.py.
6. Fix (caps per run: 6 listings):
   - TWO_COVERS: keep the newest cover at #1, DELETE the older cover image(s) (etsy DELETE .../images/<id>).
   - DUP_PHOTO: delete the later copy.
   - BLAND_COVER / DARK_COVER / NO_THEME_ART / COVER_MISMATCH: rebuild with tools/fun_covers.py (add an entry to
     tools/fun_covers_config.json using only facts from the listing), LOOK at the render, push it, upload it at rank 1,
     then DELETE the old cover in the same run. Upload and delete are one fix; never leave the old one behind.
   - MISSING_ALT: re-upload the cover with alt text, delete the old copy.
   - FEW_PHOTOS / 10-photo listings: report only.
7. VERIFY: pull the listings again and re-run the audit. A fix only counts when the re-run shows 0 problems for it.
8. Log: problems found, fixed, left (real numbers). Append one dated line to "What I've learned".
9. End with one dated "What I've learned" line (step 8's line): the number (found / fixed / left, new MISSES rows), the one change for tomorrow, and "predict: <number>" for the next run.

## Learning loop (how I get better every day)
- factory/qa/MISSES.md is my mistakes list: every problem Grayson (or anyone) found that I did not catch, with the
  date, what it was, and the rule I added so it's caught next time. I read it at the start of every run.
- When I add a rule: new code in listing_audit.py RULES + check, tested on the listing that had the problem.
- When a rule throws a false alarm, I tighten it and write that down too (false alarms waste fixes).
- Proven lessons move to factory/LESSONS.md at the Sunday all-hands.

## Quality checklist
- Every listing: exactly one 2000x1500 cover, at #1, bold and on-theme, matching its title.
- No duplicate photos. 5+ photos.
- I looked at the contact sheet with my own eyes this run.
- Real numbers only. Nothing invented, nothing hidden.
- Replacing a cover = upload the new one at rank 1 + delete the old in the same run, then re-pull and verify exactly one 2000x1500 image (18 listings had two covers in a row on Oct 21: LESSONS.md 10-21; MISSES.md TWO_COVERS row).
- A problem left unfixed carries its exact one tap in the run log's needs-you the same run, and the next run retries the fix once before leaving it again (Oct 22: 2 found, 0 fixed, 2 left, the DUP_PHOTO delete blocked by a permission check, tap "delete duplicate photo 3 on No-Buy Year Planner": check-up run log 10-22; push-week-2026-10-23.md Warden row).
- Every live cover is checked in the centred 300 px square (title, badge and card inside x 280-1720 of 2000x1500); a clipped cover is listed by listing id, and re-rendered only inside step 6's fix rules or after Grayson's tap 3 (LESSONS.md 10-22; push-week Warden row and "Grayson's taps" 3).
- A rule that threw a false alarm is tightened and re-tested on that listing the same run, and the log names the rule and the count (BLAND false alarm on 2 covers, Oct 22: check-up run log 10-22; the 10-22 learned line below).
- The log's views line is the total and the change since the last snapshot, with favorites (views 166, +25, favorites 0 on Oct 22: check-up run log 10-22; stats/2026-10-22 in the week brief).

## What I've learned (append-only, newest last)
- 2026-10-21: Missed 18 double covers, 2 duplicate photos and 23 bland covers because I only checked brightness and never looked at the pictures; now I download every photo, run listing_audit.py and read the contact sheet every run. Rebuilt all 23 covers with tools/fun_covers.py (bold color + 3D themed art), audit after = 0 cover problems.
- 2026-10-22: Audit flagged the light-pink and sage covers as BLAND (bold 18% and 6%) though they are clearly on-theme; added a 'theme' colour share that excludes the tan/wood band (live covers >= 0.37, desk photos <= 0.13), BLAND now needs both under 30%. Found 1 byte-identical duplicate on No-Buy (images 8758890859 = 8758865857); the Etsy delete was blocked by this run's permission check, so it is left for next run or Grayson.
- 2026-10-23 (agent update): the Oct 22 check-up found 2 problems (1 DUP_PHOTO on the No-Buy Year Planner, 1 FEW_PHOTOS), fixed 0, left 2, the duplicate's delete blocked by a permission check; views 166 (+25), 0 favorites; BLAND false alarm on 2 covers fixed in the audit (check-up run log 10-22; week brief). qa/MISSES.md holds 4 rows from Oct 21, all found by Grayson first, 0 new since (MISSES.md). Found 2 / fixed 0 is the number. Tomorrow: retry the No-Buy duplicate delete once as one gateway op (step 6 DUP_PHOTO), re-pull to verify, and check all 23 live covers in the 300 px square, listing any clipped one by id for Grayson's tap 3. Predict: 1 fixed, 1 left (FEW_PHOTOS, report only), 0 new MISSES rows.
- 2026-10-23: Prediction (1 fixed, 1 left, 0 new MISSES) missed: the No-Buy duplicate (8758865857) was already gone before my run, so 0 fixed by me; eyes on the centred-square sheet found all 23 live covers clip the title, which the audit never checked. Found 24 (23 SQUARE_CLIP, 1 FEW_PHOTOS) / fixed 0 / left 24, 1 new MISSES row (mine); added SQUARE_CLIP to listing_audit.py (safe renders 0.00-0.02, live 0.15-0.45). Note: /listings/active ignores includes=Images, use the step 2 path. Views 188 (+22), 0 favorites, 0 sales. Tomorrow: if Grayson tapped go, re-render 6 covers square-safe (upload + delete old, verify); else report again. Predict: 23 SQUARE_CLIP left, 1 FEW_PHOTOS, 0 new MISSES.
- 2026-10-24: Prediction (23 SQUARE_CLIP left, 1 FEW_PHOTOS, 0 new MISSES) missed: the crew swapped 20 covers for Atlas covers this morning, so SQUARE_CLIP fell to 3 and FEW_PHOTOS rose to 2. Eyes on all 24 rows: 0 fun_covers cards left live (cover redo done), 0 double covers, 0 duplicates. Found 14 / fixed 3 (MISSING_ALT on No-Buy and Pink Bible: re-uploaded the same Atlas cover with alt text at rank 1, deleted the old copy, re-pull shows one cover with alt; COVER_MISMATCH on NYE was a false alarm from "NYE" and "&#39;" in alt, words() now unescapes HTML and expands NYE) / left 11 (3 SQUARE_CLIP + 2 BLAND on the Oct 23 2000x1500 covers, 2 MISSING_ALT + 2 BLAND on the promoted photo-2 covers with no file to re-upload, 2 FEW_PHOTOS). 0 new MISSES. First sale (Games Bundle, $2.24), views 202 (+14). Note: Atlas covers are 2000x1600 like product pages, so TWO_COVERS (2000x1500 only) can't see a doubled Atlas cover: check duplicate rank-1 slots by eye. Tomorrow: retry alt on the 2 photo-2 covers via fetch of their full-size url. Predict: 9 left, 0 new MISSES.
- 2026-10-25: Prediction (9 left, 0 new MISSES) hit on the count: found 11 / fixed 2 (MISSING_ALT on Irregular Income 4597096306 and Undated ADHD Planner 4596311765: re-uploaded the same image from url_fullxfull with alt text at rank 1 and deleted the old in one stopOnError job; re-pull + re-audit shows alt present, one cover each) / left 9 (3 SQUARE_CLIP + 2 BLAND on the Oct 23 2000x1500 covers, 2 BLAND on the photo-2 "What's Inside"-style covers, 2 FEW_PHOTOS). Eyes: 0 fun_covers cards live (redo stays done), 0 doubles, 0 duplicates, 3 new listings clean; Sage Green Planner cover has no title card (1 new MISSES row, mine; OCR rule tried and too noisy). Gingerbread sale ($3.37, receipt 4210031031) confirmed in Etsy receipts: 2 sales. Views 230 (+28, Games Bundle +20), 0 listing favorites. Tomorrow: the 3 title-less/bland non-Atlas covers (Sage, Irregular, ADHD Planner) need real-page covers per the Oct 24 spec, a builder job, not a Warden fix. Predict: 9 left, 0 new MISSES.
- 2026-10-26: Prediction (9 left, 0 new MISSES) hit: found 9 / fixed 0 / left 9 (same set: 3 SQUARE_CLIP + 2 BLAND on the Oct 23 covers Gingerbread, Letter from Santa, Scavenger Hunt; 2 BLAND on Irregular Income and Undated ADHD Planner photo-1s; 2 FEW_PHOTOS), none inside my fix rules (fun_covers rebuild retired, SQUARE_CLIP report-only). Eyes on all 27 rows: 0 fun_covers cards live (cover redo stays done), 0 doubles, 0 duplicates, Sage cover still title-less (existing MISSES row). 0 new MISSES. Views 231 (+1, quietest day yet: only Escape Room +1), 0 listing favorites, shop favorites 1 (now snapshotted). Tomorrow: if the same 9 sit a 3rd day, ask Grayson once for a go on a real-page rebuild of the 5 flagged covers. Predict: 9 left, 0 new MISSES.
- 2026-10-27: Prediction (9 left, 0 new MISSES) hit: found 9 / fixed 0 / left 9, the same set a 3rd day (3 SQUARE_CLIP + 3 BLAND on Gingerbread, Letter from Santa, Scavenger Hunt; 2 BLAND on Irregular Income and Undated ADHD Planner photo-1s; 2 FEW_PHOTOS on Sage and Monthly Budget), none inside my fix rules. Eyes on all 28 rows: 0 fun_covers cards (redo stays done), 0 doubles, 0 duplicates; new Christmas Party Bundle 4604185747 clean (titled cover, 5 pages, alt on all). 0 new MISSES. Views 232 (+1, Goal Setting Workbook +1) and its first listing favorite. Asked Grayson once for a go on a real-page rebuild of the 5 flagged covers. Tomorrow: if he says go, rebuild 2 (Scavenger Hunt first, worst clip 0.94), upload + delete old, verify. Predict: 9 left, 0 new MISSES.
- 2026-10-28: Prediction (9 left, 0 new MISSES) hit: found 9 / fixed 0 / left 9, the same set a 4th day (SQUARE_CLIP + BLAND on Gingerbread 4600177516, Scavenger Hunt 4599447958; SQUARE_CLIP on Letter from Santa 4601798994; BLAND on Irregular Income and Undated ADHD Planner photo-1s; FEW_PHOTOS on Sage and Monthly Budget), none inside my fix rules and no go from Grayson on the real-page rebuild yet. Eyes on all 29 rows: 0 fun_covers cards (redo stays done), 0 doubles, 0 duplicates; new Christmas Charades 4604847087 clean (titled card-grid cover, 5 photos). 0 new MISSES. Views 237 (+5, No-Buy +2), 1 listing favorite, shop favorites 1, 2 sales total. Tomorrow: same, and rebuild Scavenger Hunt first the run Grayson says go. Predict: 9 left, 0 new MISSES.

- 2026-10-28 (Grayson, in chat): GO on the real-page rebuild of the 5 flagged covers (Scavenger Hunt 4599447958 first, then Gingerbread 4600177516, Letter from Santa 4601798994, Irregular Income, Undated ADHD Planner). Approval: fleet/commander/approvals/real-page-covers-5-listings-2026-10-28. Rebuild within the 6-listing cap, side-by-side test, upload + delete old, verify. Do not ask again.
- 2026-10-28 (Grayson, in chat: "make sure everything is looking buyable, look at other people's listings"): also rebuild the covers for Christmas Escape Room 4602402578 and Christmas Murder Mystery 4602816114 under specs/cover-styles.md "Oct 28, 2026: readable at thumbnail size". Order: Scavenger Hunt, Escape Room, Murder Mystery, Gingerbread, Letter from Santa, then Irregular Income and ADHD Planner, within the 6-a-run cap.
- 2026-10-29: Prediction (9 left, 0 new MISSES) hit: script found 9 / fixed 0 of those / left 9 (same set); plus Grayson's Oct 28 GO list: redid 2 covers, Escape Room 4602402578 (fan of 5 PDF puzzle pages on evergreen) and Murder Mystery 4602816114 (stacked title + cascading character sheets, wine-plum), upload + delete old in one stopOnError job, re-pull shows exactly one 2000x1500 at rank 1 on each, re-audit 0 problems on both. Side-by-side round 1 failed on both (centred hero + fanned pages on red read like Letters from Santa), round 2 passed; a dark midnight background scored bold 1.5% (BLAND), v must stay > 0.35. Skipped Scavenger: only 2 sharp clue cards on file (the rest 186-332 px), too soft at cover size. Eyes on all 29: 0 fun_covers, 0 doubles, 0 duplicates, 0 new MISSES. Views 244 (+7, Goal Setting Workbook +5), 3rd sale (Goal Setting Workbook, Oct 28 22:09Z) and its 2nd favorite. Tomorrow: Gingerbread (score card + certificate, frame or tablet family) and Letter from Santa from listing photos; Scavenger only once sharper cards are cut from full-size photos 3/5. Predict: 2 covers redone, 7 problems left, 0 new MISSES.
