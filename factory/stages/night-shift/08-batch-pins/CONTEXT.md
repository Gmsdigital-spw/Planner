# 08 Batches and pins (Launch Bay, room "pins")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/cover-styles.md` | "Pins", "The 6 styles" | Pin standard: 6 styles, 2:3, hook in the top third |
| Spec | `../../../specs/foreman-rules.md` | "3. Quality gates", "4. Volume" | 3 pins in 2+ styles per product; queue never below a day |
| Tool | `tools/varied_covers/README.md` + `covers.py` | Full file | The layout families pins are built from (fun_pins.py only for the 1-in-6 allowance) |
| Files | `/home/claude/kit/pages/<product id>/` (rendered by stage 06) | real page images | If missing: download the product's PDF asset and gs.render_pages it there (kit in /home/claude/kit) |
| Playbook | `../../../playbooks/tablet-mockup-pin.md` | Full file | Measured by outbound clicks |
| Skill | `../../../skills/pixel/SKILL.md` | Full file | Checklist and lessons |
| Notebook | `../../../notebook/buyer-voice.md` | "What our buyers liked", the product lane's rival words | Hooks in buyers' own words |
| Notebook | `../../../notebook/predictions.md` | "Calibration" | How far off Pixel's past guesses were |
| Shared | `../../../shared/accounts.md` | "Pinterest" | Board names |
| Database | pinstats (newest), lessons (active), pins (status ready/queued count) | | What is winning; queue depth |
| Reference | `../references/wall-art.md` | "Pixel" section | Only for a wallart product |

## Process
1. Batches: every product in stage "passed" with no batchId joins the open batch (status
   "ready" with fewer than settings.batchSize products); create a new batch with the next
   number when needed. Set product.batchId and stage "batched". Never publish a batch.
2. Set crew/pixel working ("Pins: <title>"). For each product in stage "batched" or "passed"
   with no pins (query pins where productId == id): make 3 pins, each a real 1000x1500 JPEG.
   PIN STANDARD (Grayson, Oct 27, 2026: "we gotta post better pins... all slop"; this wins over the
   older fun_pins lines in this workspace and the Oct 21 pin lines in cover-styles.md):
   - The tools/fun_pins.py card (big round count badge, emoji/3D stickers, starry or flat theme
     background, pill row) is RETIRED for new pins: at most 1 in 6 new pins, never 2 in a row, and
     never for two products on the same day. 38 of 43 pins queued on Oct 27 used it; that sameness
     is the slop.
   - Each product's 3 pins use 3 DIFFERENT layout families from cover-styles.md "The 6 styles"
     (collage, device/tablet mockup, hero page close-up, month grid, flat-lay/frame), adapted from
     tools/varied_covers/ (render at 1000x1500, hook in the top third). Not one family on more
     than 2 of the 6 pins scheduled for any one day.
   - The real product is the hero: real pages fill 55%+ of the pin and a page line is readable at
     phone size. At most 2 small props, no emoji, no fake badges ("bestseller", "#1", "sale").
   - Hook: 4-8 plain words naming the buyer's result ("Your whole Christmas party, planned").
     No AI words (elevate, unlock, seamless, perfect for). Spell-check every word on the image.
   - PIN SLOP GATE (required): put the 3 new pins in one contact sheet next to the 6 newest queued
     pins and Read it. Fail a pin if a stranger would say it shares a template with any of them, if
     text is clipped, cramped or misspelled, or if the product is not clear in a thumbnail. Rebuild a
     failed pin once; still failing = don't make it. Record qc {slopGate:"pass", checkedAt, note}.
   Record style {layout (family name), hook, hero, theme}. Use a different hero page per pin.
   When pinstats shows one family or hook clearly ahead on saves and clicks (2+ pins of
   evidence), use it for most pins and keep one pin per product trying something different.
3. Pin doc: pins/<id> {productId, listing (product name), title (100 chars max: names the
   result and the search phrase), description (500 chars max: exactly what is inside and for
   whom, holiday and count, plain sentences, no hashtags), board (a name from accounts.md),
   imageText (6 words max), angle, palette, image (asset id), link null, status "ready",
   style {layout (style number), hero, kicker}, day (a posting day in the next week like
   "Wed Oct 28"), createdAt, source}.
4. Queue depth: if fewer than 6 pins are queued or ready for the next day, make pins for the
   best-viewed active listings (from the newest stats doc) before anything else, up to 7 this
   run. While the Party Lane Push (`specs/thrive-plan-2026-10-23.md`) runs, at least 4 of every 6
   pins for a day go to party-lane focus kits, and non-holiday listings get at most 1 a day. Give any pin with image null and status not "posted" or "retired" an image the same
   way (up to 7 per run).
5. Pins with status "retired" are Grayson's removed old-style pins: never re-image, queue,
   copy or recreate them. Never a solid colour-block pin.
5b. HOOK AND GUESS (Oct 26, 2026). At least 1 of each product's pins uses a buyer-voice phrase
   for its lane as the hook when one exists (tag hook="buyer-voice" on the pin doc so the keeper
   can compare it). Every new pin gets prediction {impressions7, saves7, why} on its doc: start
   from the newest pinstats median for its style, apply Pixel's Calibration line in
   predictions.md. Whole numbers; with no pin stats yet, guess low and say "no data" in why.
6. Set crew/pixel idle. Write `## Pins` in the run notes: pins made per product, styles used,
   queue depth.

## Audit

| Check | Pass condition |
|-------|---------------|
| Count and variety | 3 pins per new product, 3 layout families, different hero pages, fun_pins at most 1 in 6 |
| Slop gate | Contact sheet with the 6 newest queued pins was Read; every new pin has qc.slopGate "pass" |
| Hook | Readable in the top third at phone size |
| Rights | No internet images, no characters, no brands |
| Queue | At least a day of pins ready or queued, or the note says why not |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Batches | batches/<id>, products/<id>.batchId | stage batched |
| Pins | pins/<id> + image assets | status ready |
