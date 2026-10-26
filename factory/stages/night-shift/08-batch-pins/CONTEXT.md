# 08 Batches and pins (Launch Bay, room "pins")

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Spec | `../../../specs/cover-styles.md` | "Pins", "The 6 styles" | Pin standard: 6 styles, 2:3, hook in the top third |
| Spec | `../../../specs/foreman-rules.md` | "3. Quality gates", "4. Volume" | 3 pins in 2+ styles per product; queue never below a day |
| Tool | `tools/fun_pins.py` docstring (themes: `tools/fun_covers.py` THEMES dict; art names: `tools/art.py`, `tools/img3d/`) | config keys, hook, decor | How to render a pin (the bold look; cover_styles.py is retired for pins) |
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
   with no pins (query pins where productId == id): make 3 pins, each a real 1000x1500 JPEG
   from tools/fun_pins.py (one JSON config per pin, same keys as the product's fun_covers entry:
   the product's theme, a hook of 4 to 7 words with one *accent* word, the real pages cropped
   to a different hero page per pin, the count badge, 2 or 3 pills, 3 to 6 pieces of themed 3D
   art placed on the 1000x1500 canvas), then uploaded as an asset. The 3 pins must differ: a
   different hook angle each (result, who it is for, what is inside), a different hero page,
   and at least one with a different layout (card_rot, badge corner, art placement) or a second
   theme that fits the product. Record style {layout "fun", hook, hero, theme}. Never
   cover_styles.py, never cream or linen. Use a different hero page per pin. When pinstats shows one style or
   title angle clearly ahead on saves and clicks to Etsy (at least 2 pins of evidence), use it
   for most pins and keep one pin per product trying something different.
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
| Count and variety | 3 pins per new product, at least 2 styles, different hero pages |
| Hook | Readable in the top third at phone size |
| Rights | No internet images, no characters, no brands |
| Queue | At least a day of pins ready or queued, or the note says why not |

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Batches | batches/<id>, products/<id>.batchId | stage batched |
| Pins | pins/<id> + image assets | status ready |
